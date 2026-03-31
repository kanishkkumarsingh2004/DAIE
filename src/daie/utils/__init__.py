"""
Utility functions for the Decentralized AI Library
"""

from daie.utils import serialization
from daie.utils.common import generate_id, validate_email, validate_url
from daie.utils.encryption import decrypt_data, encrypt_data
from daie.utils.logger import setup_logger

__all__ = [
    "generate_id",
    "validate_email",
    "validate_url",
    "setup_logger",
    "encrypt_data",
    "decrypt_data",
    "serialization",
]

# Optional audio support
try:
    from daie.utils.audio import (AudioManager, play_audio_file,
                                  record_audio_file)

    __all__ += ["AudioManager", "record_audio_file", "play_audio_file"]
except ImportError:
    pass

# Optional camera support
try:
    from daie.utils.camera import (CameraManager, capture_image,
                                   list_camera_devices, test_camera)

    __all__ += ["CameraManager", "list_camera_devices", "capture_image", "test_camera"]
except ImportError:
    pass
