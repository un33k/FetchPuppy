"""
Terminal color utilities for Claudia CLI
Provides consistent colored output across the application
"""


class Colors:
    """ANSI color codes for terminal output"""
    
    # Reset
    NC = '\033[0m'  # No Color
    
    # Regular Colors
    BLACK = '\033[0;30m'
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[0;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[0;37m'
    
    # Bold
    BOLD_BLACK = '\033[1;30m'
    BOLD_RED = '\033[1;31m'
    BOLD_GREEN = '\033[1;32m'
    BOLD_YELLOW = '\033[1;33m'
    BOLD_BLUE = '\033[1;34m'
    BOLD_PURPLE = '\033[1;35m'
    BOLD_CYAN = '\033[1;36m'
    BOLD_WHITE = '\033[1;37m'


def colored_text(text: str, color: str) -> str:
    """Apply color to text with proper reset"""
    return f"{color}{text}{Colors.NC}"


def success(text: str) -> str:
    """Green text for success messages"""
    return colored_text(text, Colors.GREEN)


def error(text: str) -> str:
    """Red text for error messages"""
    return colored_text(text, Colors.RED)


def warning(text: str) -> str:
    """Yellow text for warning messages"""
    return colored_text(text, Colors.YELLOW)


def info(text: str) -> str:
    """Blue text for info messages"""
    return colored_text(text, Colors.BLUE)


def header(text: str) -> str:
    """Cyan text for headers"""
    return colored_text(text, Colors.CYAN)


def bold(text: str) -> str:
    """Bold white text"""
    return colored_text(text, Colors.BOLD_WHITE)