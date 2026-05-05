"""
CLI Logger - Display pipeline progress and events in real-time.
"""

import logging
import sys
from datetime import datetime
from enum import Enum
from typing import Optional


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"


class Colors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"


class CLILogger:
    """Custom logger for pipeline CLI output."""

    def __init__(self, name: str = "Email Pipeline"):
        self.name = name
        self.setup_logger()

    def setup_logger(self):
        """Configure the logger."""
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.DEBUG)

        # Remove existing handlers
        self.logger.handlers.clear()

        # Console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)

        # Simple formatter
        formatter = logging.Formatter(
            "%(message)s"
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def _format_message(
        self,
        level: LogLevel,
        message: str,
        icon: Optional[str] = None,
    ) -> str:
        """Format a log message with color and icon."""
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Color mapping
        color_map = {
            LogLevel.DEBUG: Colors.DIM,
            LogLevel.INFO: Colors.BLUE,
            LogLevel.SUCCESS: Colors.GREEN,
            LogLevel.WARNING: Colors.YELLOW,
            LogLevel.ERROR: Colors.RED,
        }

        color = color_map.get(level, Colors.WHITE)

        # Format prefix
        if icon:
            prefix = f"{color}{icon} {level.value} {Colors.RESET}[{timestamp}]"
        else:
            prefix = f"{color}[{level.value}]{Colors.RESET} {timestamp}"

        return f"{prefix} {message}"

    def debug(self, message: str):
        """Log debug message."""
        formatted = self._format_message(LogLevel.DEBUG, message, "🔍")
        self.logger.debug(formatted)

    def info(self, message: str):
        """Log info message."""
        formatted = self._format_message(LogLevel.INFO, message, "ℹ️")
        self.logger.info(formatted)

    def success(self, message: str):
        """Log success message."""
        formatted = self._format_message(LogLevel.SUCCESS, message, "✅")
        self.logger.info(formatted)

    def warning(self, message: str):
        """Log warning message."""
        formatted = self._format_message(LogLevel.WARNING, message, "⚠️")
        self.logger.warning(formatted)

    def error(self, message: str):
        """Log error message."""
        formatted = self._format_message(LogLevel.ERROR, message, "❌")
        self.logger.error(formatted)

    def stage_start(self, stage_name: str):
        """Log stage start."""
        separator = "─" * 70
        self.logger.info(f"\n{Colors.BOLD}{Colors.CYAN}{separator}{Colors.RESET}")
        self.logger.info(
            f"{Colors.BOLD}{Colors.CYAN}[STAGE] {stage_name}{Colors.RESET}"
        )
        self.logger.info(f"{Colors.BOLD}{Colors.CYAN}{separator}{Colors.RESET}\n")

    def stage_complete(self, stage_name: str, duration: float):
        """Log stage completion."""
        formatted = self._format_message(
            LogLevel.SUCCESS,
            f"Stage '{stage_name}' completed in {duration:.2f}s",
            "✨",
        )
        self.logger.info(formatted)

    def stage_failed(self, stage_name: str, error: str):
        """Log stage failure."""
        formatted = self._format_message(
            LogLevel.ERROR,
            f"Stage '{stage_name}' failed: {error}",
            "💥",
        )
        self.logger.error(formatted)

    def llm_call_start(self, stage: str, model: str):
        """Log LLM call start."""
        formatted = self._format_message(
            LogLevel.INFO,
            f"LLM call -> {Colors.BOLD}{stage}{Colors.RESET} using {Colors.BOLD}{model}{Colors.RESET}",
            "🤖",
        )
        self.logger.info(formatted)

    def llm_call_complete(self, stage: str, tokens: Optional[int] = None):
        """Log LLM call completion."""
        msg = f"LLM response received for {Colors.BOLD}{stage}{Colors.RESET}"
        if tokens:
            msg += f" ({tokens} tokens)"
        formatted = self._format_message(LogLevel.SUCCESS, msg, "🎯")
        self.logger.info(formatted)

    def validation_start(self, artifact: str):
        """Log validation start."""
        formatted = self._format_message(
            LogLevel.INFO,
            f"Validating {Colors.BOLD}{artifact}{Colors.RESET}",
            "🔎",
        )
        self.logger.info(formatted)

    def validation_pass(self, artifact: str, checks: int):
        """Log validation pass."""
        formatted = self._format_message(
            LogLevel.SUCCESS,
            f"{artifact}: {Colors.BOLD}{checks} checks passed{Colors.RESET}",
            "✔️",
        )
        self.logger.info(formatted)

    def validation_fail(self, artifact: str, error: str):
        """Log validation failure."""
        formatted = self._format_message(
            LogLevel.ERROR,
            f"{artifact} validation failed: {error}",
            "✗",
        )
        self.logger.error(formatted)

    def artifact_saved(self, filepath: str, records: int):
        """Log artifact saved."""
        formatted = self._format_message(
            LogLevel.SUCCESS,
            f"Artifact saved: {Colors.BOLD}{filepath}{Colors.RESET} ({records} records)",
            "💾",
        )
        self.logger.info(formatted)

    def summary(self, stats: dict):
        """Log summary statistics."""
        self.logger.info(f"\n{Colors.BOLD}{Colors.CYAN}{'─' * 70}{Colors.RESET}")
        self.logger.info(f"{Colors.BOLD}{Colors.CYAN}[PIPELINE SUMMARY]{Colors.RESET}")
        self.logger.info(f"{Colors.BOLD}{Colors.CYAN}{'─' * 70}{Colors.RESET}\n")

        for key, value in stats.items():
            if isinstance(value, float):
                self.logger.info(f"  {Colors.BOLD}{key}:{Colors.RESET} {value:.2f}s")
            else:
                self.logger.info(f"  {Colors.BOLD}{key}:{Colors.RESET} {value}")

        self.logger.info(f"\n{Colors.BOLD}{Colors.GREEN}Pipeline execution complete!{Colors.RESET}\n")


# Global logger instance
_logger_instance = None


def get_logger() -> CLILogger:
    """Get or create the global logger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = CLILogger()
    return _logger_instance


def log_debug(message: str):
    """Log debug message."""
    get_logger().debug(message)


def log_info(message: str):
    """Log info message."""
    get_logger().info(message)


def log_success(message: str):
    """Log success message."""
    get_logger().success(message)


def log_warning(message: str):
    """Log warning message."""
    get_logger().warning(message)


def log_error(message: str):
    """Log error message."""
    get_logger().error(message)


def log_stage_start(stage_name: str):
    """Log stage start."""
    get_logger().stage_start(stage_name)


def log_stage_complete(stage_name: str, duration: float):
    """Log stage completion."""
    get_logger().stage_complete(stage_name, duration)


def log_llm_call_start(stage: str, model: str):
    """Log LLM call start."""
    get_logger().llm_call_start(stage, model)


def log_llm_call_complete(stage: str):
    """Log LLM call completion."""
    get_logger().llm_call_complete(stage)


def log_validation_start(artifact: str):
    """Log validation start."""
    get_logger().validation_start(artifact)


def log_validation_pass(artifact: str, checks: int):
    """Log validation pass."""
    get_logger().validation_pass(artifact, checks)


def log_artifact_saved(filepath: str, records: int):
    """Log artifact saved."""
    get_logger().artifact_saved(filepath, records)


def log_summary(stats: dict):
    """Log summary."""
    get_logger().summary(stats)
