"""
Lightweight console utilities using ANSI escape codes
Replaces rich dependency
"""

import sys


class Console:
    """Simple console formatter"""

    # ANSI Colors
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

    @staticmethod
    def print(message: str, color: str = ""):
        """Print message with color"""
        if color:
            print(f"{color}{message}{Console.ENDC}")
        else:
            print(message)

    @staticmethod
    def success(message: str):
        """Print success message"""
        Console.print(f"✓ {message}", Console.OKGREEN)

    @staticmethod
    def error(message: str):
        """Print error message"""
        Console.print(f"✗ {message}", Console.FAIL)

    @staticmethod
    def info(message: str):
        """Print info message"""
        Console.print(f"ℹ {message}", Console.OKBLUE)

    @staticmethod
    def warning(message: str):
        """Print warning message"""
        Console.print(f"⚠ {message}", Console.WARNING)

    @staticmethod
    def bold(message: str):
        """Print bold message"""
        Console.print(message, Console.BOLD)


def print_success(message: str):
    Console.success(message)


def print_error(message: str):
    Console.error(message)


def print_info(message: str):
    Console.info(message)


def print_warning(message: str):
    Console.warning(message)


def print_header(message: str):
    Console.print(message, Console.HEADER + Console.BOLD)
