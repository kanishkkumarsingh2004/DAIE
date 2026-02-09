"""
Camera handling module using OpenCV
"""

import logging
import threading
import queue
from typing import Optional, Callable, List, TYPE_CHECKING

if TYPE_CHECKING:
    from ..agents.config import AgentConfig

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    cv2 = None
    np = None
    CV2_AVAILABLE = False

logger = logging.getLogger(__name__)


class CameraManager:
    """
    Manages camera access using OpenCV

    This class provides an interface to:
    - List available cameras
    - Capture video frames from camera
    - Take photos
    - Manage camera streaming
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize camera manager

        Args:
            config: Agent configuration (optional)
        """
        self.config = config
        self.capture = None
        self.is_streaming = False
        self.frame_queue = queue.Queue()
        self.streaming_thread = None
        self.frame_callback = None

        if config and config.enable_camera:
            self.initialize_camera()

    def initialize_camera(self, device_index: Optional[int] = None):
        """Initialize camera capture

        Args:
            device_index: Camera device index to use (None for config value or default)
        """
        try:
            if device_index is None:
                device_index = self.config.camera_device_index if self.config else 0

            self.capture = cv2.VideoCapture(device_index)

            if self.capture.isOpened():
                # Set camera properties from config if specified
                if self.config:
                    resolution = self.config.camera_resolution.split('x')
                    if len(resolution) == 2:
                        width = int(resolution[0])
                        height = int(resolution[1])
                        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

                    if self.config.camera_fps > 0:
                        self.capture.set(cv2.CAP_PROP_FPS, self.config.camera_fps)

                logger.info("Camera initialized successfully")
                return True
            else:
                logger.error("Failed to open camera device")
                self.capture = None
                return False

        except Exception as e:
            logger.error(f"Failed to initialize camera: {e}")
            self.capture = None
            return False

    def list_available_cameras(self) -> List[int]:
        """
        List available camera device indices

        Returns:
            List of available camera indices
        """
        available = []

        # Try to open first 10 possible camera indices
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available.append(i)
                cap.release()

        logger.info(f"Found {len(available)} available cameras: {available}")
        return available

    def start_streaming(self, callback: Optional[Callable[[object], None]] = None):
        """
        Start camera streaming

        Args:
            callback: Optional callback to receive frames

        Returns:
            True if streaming started successfully
        """
        if self.is_streaming:
            logger.warning("Already streaming")
            return False

        if not CV2_AVAILABLE:
            logger.error("OpenCV not available for camera streaming")
            return False

        if not self.capture:
            if not self.initialize_camera():
                return False

        try:
            self.frame_callback = callback
            self.is_streaming = True
            self.streaming_thread = threading.Thread(
                target=self._streaming_thread,
                daemon=True
            )
            self.streaming_thread.start()

            logger.info("Camera streaming started")
            return True

        except Exception as e:
            logger.error(f"Failed to start camera streaming: {e}")
            self.is_streaming = False
            return False

    def _streaming_thread(self):
        """Internal streaming thread"""
        while self.is_streaming and CV2_AVAILABLE:
            try:
                ret, frame = self.capture.read()

                if ret:
                    # Convert to RGB format
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                    if self.frame_callback:
                        self.frame_callback(frame)
                    else:
                        # If no callback, put in queue
                        try:
                            self.frame_queue.put_nowait(frame)
                        except queue.Full:
                            # If queue is full, drop oldest frame
                            try:
                                self.frame_queue.get_nowait()
                                self.frame_queue.put_nowait(frame)
                            except queue.Empty:
                                pass

            except Exception as e:
                logger.error(f"Error in streaming thread: {e}")
                break

        logger.info("Camera streaming stopped")

    def stop_streaming(self):
        """Stop camera streaming"""
        if not self.is_streaming:
            return

        self.is_streaming = False

        if self.streaming_thread:
            try:
                self.streaming_thread.join(timeout=1)
            except Exception as e:
                logger.warning(f"Error joining streaming thread: {e}")

    def get_frame(self, timeout: float = 0.5) -> Optional[object]:
        """
        Get a single frame from the camera
        
        Args:
            timeout: Timeout in seconds for frame capture
            
        Returns:
            Frame as numpy array, or None if capture failed
        """
        if not CV2_AVAILABLE:
            logger.error("OpenCV not available for camera access")
            return None
            
        if not self.capture:
            if not self.initialize_camera():
                return None
                
        try:
            ret, frame = self.capture.read()
            
            if ret:
                return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
            logger.warning("Failed to capture frame")
            return None
                
        except Exception as e:
            logger.error("Error capturing frame: %s", e)
            return None

    def take_photo(self, file_path: str) -> bool:
        """
        Take a photo and save to file

        Args:
            file_path: Output file path

        Returns:
            True if photo was taken successfully
        """
        frame = self.get_frame()

        if frame is not None:
            try:
                # Convert back to BGR for OpenCV
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                cv2.imwrite(file_path, frame)
                logger.info(f"Photo saved to {file_path}")
                return True
            except Exception as e:
                logger.error(f"Error saving photo: {e}")
                return False

        return False

    def show_preview(self, window_name: str = "Camera Preview",
                    preview_time: int = 0):
        """
        Show camera preview (blocks until window is closed)

        Args:
            window_name: Name of the preview window
            preview_time: Time in seconds to show preview (0 = indefinite)
        """
        if not self.capture:
            if not self.initialize_camera():
                return

        try:
            logger.info("Camera preview started")

            start_time = cv2.getTickCount()

            while True:
                ret, frame = self.capture.read()

                if ret:
                    cv2.imshow(window_name, frame)

                key = cv2.waitKey(1)
                if key == ord('q') or key == 27:
                    logger.info("Preview closed by user")
                    break

                if preview_time > 0:
                    elapsed_time = (cv2.getTickCount() - start_time) / cv2.getTickFrequency()
                    if elapsed_time >= preview_time:
                        logger.info(f"Preview completed after {preview_time} seconds")
                        break

        except Exception as e:
            logger.error(f"Error in camera preview: {e}")
        finally:
            cv2.destroyWindow(window_name)
            logger.info("Preview window closed")

    def get_camera_info(self) -> Optional[dict]:
        """
        Get camera information

        Returns:
            Dictionary with camera properties, or None if unavailable
        """
        if not self.capture:
            return None

        try:
            width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(self.capture.get(cv2.CAP_PROP_FPS))
            return {
                "width": width,
                "height": height,
                "fps": fps
            }
        except Exception as e:
            logger.error(f"Error getting camera info: {e}")
            return None

    def is_available(self) -> bool:
        """Check if camera is available"""
        if not self.capture:
            return False

        return self.capture.isOpened()

    def release(self):
        """Release camera resources"""
        self.stop_streaming()

        if self.capture:
            try:
                self.capture.release()
                logger.info("Camera released")
            except Exception as e:
                logger.warning(f"Error releasing camera: {e}")
            self.capture = None

    def __del__(self):
        """Cleanup on deletion"""
        self.release()


def list_camera_devices() -> List[int]:
    """
    List available camera devices

    Returns:
        List of available camera indices
    """
    manager = CameraManager()
    devices = manager.list_available_cameras()
    manager.release()
    return devices


def capture_image(file_path: str, device_index: int = 0, 
                  width: int = 640, height: int = 480) -> bool:
    """
    Capture a single image from camera
    
    Args:
        file_path: Output file path
        device_index: Camera device index (default: 0)
        width: Frame width (default: 640)
        height: Frame height (default: 480)
        
    Returns:
        True if image capture succeeded
    """
    manager = CameraManager()
    
    try:
        manager.initialize_camera(device_index)
        
        frame = manager.get_frame()
        if frame is not None:
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            cv2.imwrite(file_path, frame)
            logger.info("Image saved to %s", file_path)
            return True
            
    except Exception as e:
        logger.error("Error capturing image: %s", e)
        
    finally:
        manager.release()
        
    return False


# Helper function for testing camera functionality
def test_camera(device_index: int = 0, duration: int = 3):
    """
    Test camera functionality

    Args:
        device_index: Camera device index to test
        duration: Test duration in seconds
    """
    print(f"Testing camera {device_index}...")

    manager = CameraManager()

    if not manager.initialize_camera(device_index):
        print("Failed to initialize camera")
        return False

    print(f"Camera info: {manager.get_camera_info()}")
    print("Camera preview will open (press 'q' or ESC to close)")

    manager.show_preview(preview_time=duration)

    test_file = "camera_test_image.jpg"
    if manager.take_photo(test_file):
        print(f"Test photo saved to {test_file}")
    else:
        print("Failed to take test photo")

    manager.release()
    print("Camera test completed")
    return True


if __name__ == "__main__":
    # Test camera functionality if run directly
    logging.basicConfig(level=logging.INFO)

    devices = list_camera_devices()
    if devices:
        print(f"Available cameras: {devices}")
        test_camera(devices[0], duration=3)
    else:
        print("No cameras detected")

