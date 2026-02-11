"""
Logger utility functions
"""

import logging
import sys
import os
from typing import Optional
from datetime import datetime
from pathlib import Path

from daie.config import SystemConfig


def ensure_directory_exists(directory: str) -> str:
    """
    Ensure a directory exists, creating it if necessary

    Args:
        directory: Directory path to check/create

    Returns:
        Absolute path to the directory
    """
    dir_path = Path(directory)
    dir_path.mkdir(parents=True, exist_ok=True)
    return str(dir_path.resolve())


def setup_logger(
    name: str = "daie",
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_str: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
):
    """
    Set up a logger with specified configuration

    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (if None, logs to console)
        format_str: Log message format

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(format_str)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler with rotation
    if log_file:
        try:
            from logging.handlers import RotatingFileHandler

            # Rotate log files when they reach 10MB, keep 5 backup files
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Failed to set up rotating log handler: {e}")
            # Fallback to simple file handler
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger


def setup_logging(*args, **kwargs):
    """
    Alias for setup_logger to maintain backward compatibility
    """
    return setup_logger(*args, **kwargs)


def setup_system_logger(config: SystemConfig):
    """
    Set up logger based on system configuration

    Args:
        config: System configuration

    Returns:
        Configured logger instance
    """
    log_file = config.log_file

    if config.enable_logging and log_file is None:
        # Create log directory if it doesn't exist
        log_dir = ensure_directory_exists(config.log_directory)
        log_file = os.path.join(log_dir, "daie.log")

    return setup_logger(
        level=config.log_level.value, log_file=log_file, format_str=config.log_format
    )


def log_exception(
    logger: logging.Logger, exception: Exception, message: str = "Exception occurred"
):
    """
    Log an exception with detailed information

    Args:
        logger: Logger instance
        exception: Exception to log
        message: Custom message
    """
    import traceback

    logger.error(
        f"{message}: {str(exception)}\n" f"Stack trace:\n{traceback.format_exc()}"
    )


def log_performance(
    logger: logging.Logger, operation: str, duration: float, level: int = logging.INFO
):
    """
    Log performance information

    Args:
        logger: Logger instance
        operation: Operation name
        duration: Duration in seconds
        level: Logging level
    """
    logger.log(level, f"Performance: {operation} took {duration:.2f} seconds")


def log_metrics(logger: logging.Logger, metrics: dict, level: int = logging.INFO):
    """
    Log metrics as a single log entry

    Args:
        logger: Logger instance
        metrics: Dictionary of metrics
        level: Logging level
    """
    metric_str = ", ".join(f"{k}: {v}" for k, v in metrics.items())
    logger.log(level, f"Metrics: {metric_str}")


class LogContext:
    """
    Context manager for logging operations with timing information

    Example:
        >>> from daie.utils.logger import LogContext
        >>> import logging

        >>> logger = logging.getLogger(__name__)
        >>> with LogContext(logger, "operation_name"):
        ...     # Perform operation
        ...     pass
    """

    def __init__(
        self,
        logger: logging.Logger,
        operation: str,
        start_level: int = logging.DEBUG,
        end_level: int = logging.INFO,
        error_level: int = logging.ERROR,
    ):
        """
        Initialize log context

        Args:
            logger: Logger instance
            operation: Operation name
            start_level: Log level for start message
            end_level: Log level for end message
            error_level: Log level for error message
        """
        self.logger = logger
        self.operation = operation
        self.start_level = start_level
        self.end_level = end_level
        self.error_level = error_level
        self.start_time = None

    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.log(self.start_level, f"Starting: {self.operation}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()

        if exc_type:
            self.logger.log(
                self.error_level,
                f"Failed: {self.operation} after {duration:.2f} seconds - {exc_val}",
            )
        else:
            self.logger.log(
                self.end_level, f"Completed: {self.operation} in {duration:.2f} seconds"
            )


class LogTimer:
    """
    Timer context manager for logging performance

    Example:
        >>> from daie.utils.logger import LogTimer
        >>> import logging

        >>> logger = logging.getLogger(__name__)
        >>> with LogTimer(logger, "operation_name"):
        ...     # Perform operation
        ...     pass
    """

    def __init__(
        self, logger: logging.Logger, operation: str, level: int = logging.INFO
    ):
        """
        Initialize log timer

        Args:
            logger: Logger instance
            operation: Operation name
            level: Log level for results
        """
        self.logger = logger
        self.operation = operation
        self.level = level
        self.start_time = None

    def __enter__(self):
        self.start_time = datetime.now()

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        log_performance(self.logger, self.operation, duration, self.level)


class LogMemoryUsage:
    """
    Context manager for logging memory usage

    Example:
        >>> from daie.utils.logger import LogMemoryUsage
        >>> import logging

        >>> logger = logging.getLogger(__name__)
        >>> with LogMemoryUsage(logger, "operation_name"):
        ...     # Perform operation
        ...     pass
    """

    def __init__(
        self, logger: logging.Logger, operation: str, level: int = logging.DEBUG
    ):
        """
        Initialize log memory usage

        Args:
            logger: Logger instance
            operation: Operation name
            level: Log level
        """
        self.logger = logger
        self.operation = operation
        self.level = level
        self.start_memory = None

    def __enter__(self):
        try:
            import psutil

            self.start_memory = psutil.virtual_memory().used
        except ImportError:
            self.logger.warning("psutil not installed, cannot measure memory usage")

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_memory is not None:
            try:
                import psutil

                end_memory = psutil.virtual_memory().used
                memory_used = end_memory - self.start_memory

                # Convert to MB
                memory_used_mb = memory_used / (1024 * 1024)

                self.logger.log(
                    self.level,
                    f"Memory Usage: {self.operation} used {memory_used_mb:.2f} MB",
                )
            except Exception as e:
                self.logger.warning(f"Failed to measure memory usage: {e}")
