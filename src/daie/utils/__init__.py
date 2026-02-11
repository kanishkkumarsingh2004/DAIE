"""
Utility functions for the Decentralized AI Library
"""

from daie.utils.common import generate_id, validate_email, validate_url
from daie.utils.logger import setup_logger
from daie.utils.encryption import encrypt_data, decrypt_data
from daie.utils import serialization
from daie.utils.audio import AudioManager, record_audio_file, play_audio_file
from daie.utils.camera import (
    CameraManager,
    list_camera_devices,
    capture_image,
    test_camera,
)

__all__ = [
    "generate_id",
    "validate_email",
    "validate_url",
    "setup_logger",
    "encrypt_data",
    "decrypt_data",
    "serialization",
    "AudioManager",
    "record_audio_file",
    "play_audio_file",
    "CameraManager",
    "list_camera_devices",
    "capture_image",
    "test_camera",
]
