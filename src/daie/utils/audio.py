"""
Audio handling module using PyAudio
"""

import logging
import threading
import queue
from typing import Optional, Callable, List
from daie.agents.config import AgentConfig

try:
    import pyaudio
    import wave

    PYAUDIO_AVAILABLE = True
except ImportError:
    pyaudio = None
    wave = None
    PYAUDIO_AVAILABLE = False

logger = logging.getLogger(__name__)


class AudioManager:
    """
    Manages audio input and output using PyAudio

    This class provides an interface to:
    - List available audio devices
    - Record audio from microphone
    - Play audio to speakers
    - Manage audio streaming
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize audio manager

        Args:
            config: Agent configuration (optional)
        """
        self.config = config
        self.pyaudio = None
        self.input_stream = None
        self.output_stream = None
        self.is_recording = False
        self.is_playing = False
        self.input_queue = queue.Queue()
        self.output_queue = queue.Queue()
        self.recording_thread = None
        self.playback_thread = None

        if PYAUDIO_AVAILABLE and config and config.enable_audio_input:
            self.initialize_audio()

    def initialize_audio(self):
        """Initialize PyAudio"""
        if not PYAUDIO_AVAILABLE:
            logger.error("PyAudio not available")
            return False

        try:
            self.pyaudio = pyaudio.PyAudio()
            logger.info("PyAudio initialized successfully")
            return True
        except Exception as e:
            logger.error("Failed to initialize PyAudio: %s", e)
            self.pyaudio = None
            return False

    def list_audio_devices(self) -> List[dict]:
        """
        List available audio input and output devices

        Returns:
            List of device dictionaries with id, name, and capabilities
        """
        if not PYAUDIO_AVAILABLE:
            logger.warning("PyAudio not available for device listing")
            return []

        if not self.pyaudio:
            if not self.initialize_audio():
                return []

        devices = []
        try:
            for i in range(self.pyaudio.get_device_count()):
                try:
                    device_info = self.pyaudio.get_device_info_by_index(i)
                    devices.append(
                        {
                            "id": i,
                            "name": device_info.get("name", "Unknown"),
                            "max_input_channels": device_info.get(
                                "maxInputChannels", 0
                            ),
                            "max_output_channels": device_info.get(
                                "maxOutputChannels", 0
                            ),
                            "default_sample_rate": device_info.get(
                                "defaultSampleRate", 0
                            ),
                        }
                    )
                except Exception as e:
                    logger.warning("Error getting device info for index %d: %s", i, e)
        except Exception as e:
            logger.error("Error listing audio devices: %s", e)

        return devices

    def start_recording(self, callback: Optional[Callable[[bytes], None]] = None):
        """
        Start audio recording from microphone

        Args:
            callback: Optional callback function to process audio data

        Returns:
            True if recording started successfully
        """
        if not PYAUDIO_AVAILABLE:
            logger.error("PyAudio not available for audio recording")
            return False

        if self.is_recording:
            logger.warning("Already recording")
            return False

        if not self.pyaudio:
            if not self.initialize_audio():
                return False

        try:
            # Get audio parameters from config
            sample_rate = self.config.audio_sample_rate if self.config else 16000
            chunk_size = self.config.audio_chunk_size if self.config else 1024
            device_index = self.config.audio_device_index if self.config else -1

            self.input_stream = self.pyaudio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=sample_rate,
                input=True,
                input_device_index=device_index if device_index >= 0 else None,
                frames_per_buffer=chunk_size,
                stream_callback=self._input_callback,
            )

            self.is_recording = True
            self.input_stream.start_stream()

            if callback:
                self.recording_thread = threading.Thread(
                    target=self._processing_thread, args=(callback,), daemon=True
                )
                self.recording_thread.start()

            logger.info("Recording started")
            return True

        except Exception as e:
            logger.error("Failed to start recording: %s", e)
            if self.input_stream:
                try:
                    self.input_stream.stop_stream()
                    self.input_stream.close()
                except Exception as close_e:
                    logger.warning("Error closing stream: %s", close_e)
                self.input_stream = None
            return False

    def _input_callback(self, in_data, _, __, ___):
        """Internal callback for audio input stream"""
        self.input_queue.put(in_data)
        return (in_data, pyaudio.paContinue)

    def _processing_thread(self, callback: Callable[[bytes], None]):
        """Thread to process audio data from input queue"""
        while self.is_recording:
            try:
                data = self.input_queue.get(timeout=1)
                callback(data)
                self.input_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error("Error in audio processing thread: %s", e)
                break

    def stop_recording(self):
        """Stop audio recording"""
        if not self.is_recording:
            return

        self.is_recording = False

        if self.input_stream:
            try:
                self.input_stream.stop_stream()
                self.input_stream.close()
            except Exception as e:
                logger.warning("Error closing input stream: %s", e)
            self.input_stream = None

        if self.recording_thread:
            try:
                self.recording_thread.join(timeout=1)
            except Exception as e:
                logger.warning("Error joining recording thread: %s", e)

        logger.info("Recording stopped")

    def play_audio(self, audio_data: bytes, sample_rate: int = 16000):
        """
        Play audio data to speakers

        Args:
            audio_data: Audio data as bytes
            sample_rate: Sample rate in Hz (default: 16000)

        Returns:
            True if playback started successfully
        """
        if not PYAUDIO_AVAILABLE:
            logger.error("PyAudio not available for audio playback")
            return False

        if self.is_playing:
            logger.warning("Already playing audio")
            return False

        if not self.pyaudio:
            if not self.initialize_audio():
                return False

        try:
            self.output_queue.put(audio_data)
            self.playback_thread = threading.Thread(
                target=self._playback_thread, args=(sample_rate,), daemon=True
            )
            self.playback_thread.start()

            logger.info("Audio playback started")
            return True

        except Exception as e:
            logger.error("Failed to start audio playback: %s", e)
            return False

    def _playback_thread(self, sample_rate: int):
        """Thread for audio playback"""
        try:
            chunk_size = self.config.audio_chunk_size if self.config else 1024
            device_index = self.config.audio_device_index if self.config else -1

            self.is_playing = True
            self.output_stream = self.pyaudio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=sample_rate,
                output=True,
                output_device_index=device_index if device_index >= 0 else None,
                frames_per_buffer=chunk_size,
            )

            audio_data = self.output_queue.get()

            # Play audio data in chunks
            chunk_size = min(1024, len(audio_data))
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i : i + chunk_size]
                self.output_stream.write(chunk)

            logger.info("Audio playback completed")

        except Exception as e:
            logger.error("Error in audio playback: %s", e)
        finally:
            self.is_playing = False
            if self.output_stream:
                try:
                    self.output_stream.stop_stream()
                    self.output_stream.close()
                except Exception as close_e:
                    logger.warning("Error closing output stream: %s", close_e)
                self.output_stream = None

    def is_busy(self) -> bool:
        """Check if audio manager is busy (recording or playing)"""
        return self.is_recording or self.is_playing

    def cleanup(self):
        """Cleanup audio resources"""
        self.stop_recording()

        if self.pyaudio:
            try:
                self.pyaudio.terminate()
                logger.info("PyAudio terminated")
            except Exception as e:
                logger.warning("Error terminating PyAudio: %s", e)
            self.pyaudio = None

    def __del__(self):
        """Cleanup on deletion"""
        self.cleanup()


def record_audio_file(
    file_path: str,
    duration: float,
    sample_rate: int = 16000,
    chunk_size: int = 1024,
    device_index: int = -1,
) -> bool:
    """
    Record audio to a WAV file

    Args:
        file_path: Output file path
        duration: Recording duration in seconds
        sample_rate: Sample rate in Hz (default: 16000)
        chunk_size: Chunk size for recording (default: 1024)
        device_index: Audio device index (default: -1 for default)

    Returns:
        True if recording succeeded
    """
    if not PYAUDIO_AVAILABLE:
        logger.error("PyAudio not available for audio recording")
        return False

    audio_manager = AudioManager()
    if not audio_manager.pyaudio:
        return False

    frames = []

    try:
        stream = audio_manager.pyaudio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=sample_rate,
            input=True,
            input_device_index=device_index if device_index >= 0 else None,
            frames_per_buffer=chunk_size,
        )

        logger.info("Recording for %f seconds to %s", duration, file_path)

        for _ in range(0, int(sample_rate / chunk_size * duration)):
            data = stream.read(chunk_size)
            frames.append(data)

        stream.stop_stream()
        stream.close()

        wf = wave.open(file_path, "wb")
        wf.setnchannels(1)
        wf.setsampwidth(audio_manager.pyaudio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(sample_rate)
        wf.writeframes(b"".join(frames))
        wf.close()

        logger.info("Recording saved to %s", file_path)
        return True

    except Exception as e:
        logger.error("Error recording to file: %s", e)
        if "stream" in locals() and stream:
            try:
                stream.stop_stream()
                stream.close()
            except Exception:
                pass
        return False
    finally:
        audio_manager.cleanup()


def play_audio_file(file_path: str) -> bool:
    """
    Play audio from a WAV file

    Args:
        file_path: Path to WAV file

    Returns:
        True if playback succeeded
    """
    if not PYAUDIO_AVAILABLE:
        logger.error("PyAudio not available for audio playback")
        return False

    audio_manager = AudioManager()
    if not audio_manager.pyaudio:
        return False

    try:
        wf = wave.open(file_path, "rb")

        stream = audio_manager.pyaudio.open(
            format=audio_manager.pyaudio.get_format_from_width(wf.getsampwidth()),
            channels=wf.getnchannels(),
            rate=wf.getframerate(),
            output=True,
        )

        logger.info("Playing audio from %s", file_path)

        chunk_size = 1024
        data = wf.readframes(chunk_size)
        while data != b"":
            stream.write(data)
            data = wf.readframes(chunk_size)

        stream.stop_stream()
        stream.close()
        wf.close()

        logger.info("Audio playback completed: %s", file_path)
        return True

    except Exception as e:
        logger.error("Error playing audio file: %s", e)
        if "stream" in locals() and stream:
            try:
                stream.stop_stream()
                stream.close()
            except Exception:
                pass
        return False
    finally:
        audio_manager.cleanup()
