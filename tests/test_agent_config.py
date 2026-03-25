#!/usr/bin/env python3
"""
Test script to demonstrate audio and camera configuration
"""

import asyncio
from daie.agents import AgentConfig
from daie.agents import Agent
from daie.tools import ToolRegistry
from daie.utils import AudioManager, CameraManager


async def main():
    """Test agent configuration with audio and camera settings"""

    print("=== Agent Configuration Test ===\n")

    # Create an agent with audio and camera access
    config = AgentConfig(
        name="AudioVisualAgent",
        role="specialized",
        goal="Test audio and camera configuration",
        backstory="An AI agent with audio and camera capabilities",
        system_prompt="You are an AI agent capable of audio and camera operations",
        enable_audio_input=True,
        enable_audio_output=True,
        audio_device_index=0,
        audio_sample_rate=16000,
        audio_chunk_size=1024,
        enable_camera=True,
        camera_device_index=0,
        camera_resolution="640x480",
        camera_fps=30,
    )

    print("1. Agent Configuration:")
    print(f"   - Name: {config.name}")
    print(f"   - Role: {config.role}")
    print(f"   - Audio Input: {config.enable_audio_input}")
    print(f"   - Audio Output: {config.enable_audio_output}")
    print(f"   - Audio Sample Rate: {config.audio_sample_rate} Hz")
    print(f"   - Audio Chunk Size: {config.audio_chunk_size}")
    print(f"   - Camera: {config.enable_camera}")
    print(f"   - Camera Resolution: {config.camera_resolution}")
    print(f"   - Camera FPS: {config.camera_fps}")
    print()

    # Validate configuration
    validation_errors = config.validate()
    if validation_errors:
        print("2. Configuration Errors:")
        for error in validation_errors:
            print(f"   - {error}")
    else:
        print("2. Configuration Validation: ✓ PASSED")
    print()

    # Test AudioManager
    print("3. Audio Manager Test:")
    audio_manager = AudioManager(config)
    if audio_manager.pyaudio:
        audio_devices = audio_manager.list_audio_devices()
        print(f"   - Audio Devices Found: {len(audio_devices)}")
        for device in audio_devices:
            print(f"     Device {device['id']}: {device['name']}")
    else:
        print("   - PyAudio not available")
    print()

    # Test CameraManager
    print("4. Camera Manager Test:")
    camera_manager = CameraManager(config)
    if camera_manager.capture and camera_manager.capture.isOpened():
        print(f"   - Camera Available: ✓ Yes")
        if camera_info := camera_manager.get_camera_info():
            print(f"   - Resolution: {camera_info['width']}x{camera_info['height']}")
            print(f"   - FPS: {camera_info['fps']}")
    else:
        print("   - Camera not available")
    print()

    # Create and test the agent
    print("5. Agent Creation Test:")
    try:
        tool_registry = ToolRegistry()
        agent = Agent(config, tool_registry)

        print(f"   - Agent Created: ✓ {agent.config.name}")
        print(f"   - Agent Role: {agent.config.role}")

        # Start and stop agent (to test lifecycle)
        await agent.start()
        await asyncio.sleep(0.5)
        await agent.stop()

        print(f"   - Agent Lifecycle: ✓ Start/Stop Tested")

    except Exception as e:
        print(f"   - Error: {e}")
    print()

    # Cleanup
    audio_manager.cleanup()
    camera_manager.release()

    print("=== Test Completed ===\n")


if __name__ == "__main__":
    asyncio.run(main())
