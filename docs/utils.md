# Utilities

DAIE provides various utility modules for common tasks like audio processing, camera access, encryption, logging, and serialization.

## Audio Utilities

### AudioManager

The `AudioManager` provides audio recording and playback capabilities:

```python
from daie.utils.audio import AudioManager

# Create audio manager
audio_manager = AudioManager()

# List available audio devices
devices = audio_manager.list_devices()
print("Available audio devices:", devices)

# Record audio
audio_manager.record(
    duration=5.0,  # Record for 5 seconds
    sample_rate=16000,
    channels=1
)

# Save recording
audio_manager.save("recording.wav")

# Play audio
audio_manager.play("recording.wav")
```

### Audio Functions

```python
from daie.utils.audio import (
    record_audio,
    play_audio,
    list_audio_devices,
    get_default_device
)

# Record audio
audio_data = record_audio(duration=5.0, sample_rate=16000)

# Play audio
play_audio(audio_data, sample_rate=16000)

# List devices
devices = list_audio_devices()

# Get default device
default_device = get_default_device()
```

---

## Camera Utilities

### CameraManager

The `CameraManager` provides camera access for vision tasks:

```python
from daie.utils.camera import CameraManager

# Create camera manager
camera = CameraManager()

# List available cameras
cameras = camera.list_cameras()
print("Available cameras:", cameras)

# Capture image
image = camera.capture()

# Save image
camera.save_image(image, "photo.jpg")

# Start video stream
camera.start_stream()

# Get frame from stream
frame = camera.get_frame()

# Stop stream
camera.stop_stream()
```

### Camera Functions

```python
from daie.utils.camera import (
    capture_image,
    list_cameras,
    get_default_camera
)

# Capture image
image = capture_image(camera_id=0)

# List cameras
cameras = list_cameras()

# Get default camera
default_camera = get_default_camera()
```

---

## Encryption Utilities

### EncryptionManager

The `EncryptionManager` provides encryption and decryption capabilities:

```python
from daie.utils.encryption import EncryptionManager

# Create encryption manager
encryption = EncryptionManager()

# Generate key
key = encryption.generate_key()

# Encrypt data
encrypted = encryption.encrypt("sensitive data", key)

# Decrypt data
decrypted = encryption.decrypt(encrypted, key)

# Hash data
hash_value = encryption.hash("data to hash")
```

### Encryption Functions

```python
from daie.utils.encryption import (
    generate_key,
    encrypt,
    decrypt,
    hash_data,
    generate_token
)

# Generate encryption key
key = generate_key()

# Encrypt data
encrypted = encrypt("sensitive data", key)

# Decrypt data
decrypted = decrypt(encrypted, key)

# Hash data
hash_value = hash_data("data to hash")

# Generate random token
token = generate_token(length=32)
```

---

## Logging Utilities

### Logger

DAIE provides a comprehensive logging system:

```python
from daie.utils.logger import get_logger, setup_logger

# Get logger
logger = get_logger(__name__)

# Setup custom logger
setup_logger(
    name="my_logger",
    level="INFO",
    log_file="app.log",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Use logger
logger.info("Information message")
logger.warning("Warning message")
logger.error("Error message")
logger.debug("Debug message")
```

### Logging Functions

```python
from daie.utils.logger import (
    get_logger,
    setup_logger,
    set_log_level,
    get_log_level
)

# Get logger
logger = get_logger(__name__)

# Setup logger
setup_logger(name="custom", level="DEBUG")

# Set log level
set_log_level("INFO")

# Get current log level
level = get_log_level()
```

---

## Serialization Utilities

### Serializer

The `Serializer` provides data serialization and deserialization:

```python
from daie.utils.serialization import Serializer

# Create serializer
serializer = Serializer()

# Serialize object
data = {"key": "value", "number": 42}
serialized = serializer.serialize(data)

# Deserialize object
deserialized = serializer.deserialize(serialized)

# Serialize to JSON
json_str = serializer.to_json(data)

# Deserialize from JSON
data_from_json = serializer.from_json(json_str)

# Serialize to file
serializer.to_file(data, "data.json")

# Deserialize from file
data_from_file = serializer.from_file("data.json")
```

### Serialization Functions

```python
from daie.utils.serialization import (
    serialize,
    deserialize,
    to_json,
    from_json,
    to_file,
    from_file
)

# Serialize
serialized = serialize({"key": "value"})

# Deserialize
deserialized = deserialize(serialized)

# To JSON
json_str = to_json({"key": "value"})

# From JSON
data = from_json(json_str)

# To file
to_file({"key": "value"}, "data.json")

# From file
data = from_file("data.json")
```

---

## Common Utilities

### Common Functions

```python
from daie.utils.common import (
    generate_id,
    generate_uuid,
    timestamp,
    format_timestamp,
    parse_timestamp,
    validate_email,
    validate_url,
    sanitize_string,
    truncate_string,
    merge_dicts,
    deep_merge,
    flatten_dict,
    unflatten_dict
)

# Generate unique ID
id = generate_id()

# Generate UUID
uuid = generate_uuid()

# Get current timestamp
ts = timestamp()

# Format timestamp
formatted = format_timestamp(ts, format="%Y-%m-%d %H:%M:%S")

# Parse timestamp
parsed = parse_timestamp("2024-01-15 10:30:00")

# Validate email
is_valid = validate_email("user@example.com")

# Validate URL
is_valid = validate_url("https://example.com")

# Sanitize string
clean = sanitize_string("Hello <script>alert('xss')</script>")

# Truncate string
truncated = truncate_string("Long text...", max_length=50)

# Merge dictionaries
merged = merge_dicts({"a": 1}, {"b": 2})

# Deep merge
merged = deep_merge({"a": {"b": 1}}, {"a": {"c": 2}})

# Flatten dictionary
flat = flatten_dict({"a": {"b": {"c": 1}}})
# Result: {"a.b.c": 1}

# Unflatten dictionary
unflat = unflatten_dict({"a.b.c": 1})
# Result: {"a": {"b": {"c": 1}}}
```

---

## Integration with Agents

Utilities are automatically integrated with agents:

```python
from daie import Agent, AgentConfig

# Agent can use audio utilities
agent = Agent(config=AgentConfig(
    name="AudioAgent",
    enable_audio=True
))

# Agent can use camera utilities
agent = Agent(config=AgentConfig(
    name="VisionAgent",
    enable_camera=True
))
```

---

## Next Steps

- [Getting Started](getting-started.md) — Installation and basic concepts
- [Agents](agents.md) — Agent configuration and the ReAct loop
- [Tools](tools.md) — Pre-built tools and creating custom tools
- [Communication](communication.md) — P2P networking and file transfers
