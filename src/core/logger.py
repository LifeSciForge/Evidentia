"""
Logging configuration for GTM Simulator
Sets up structured logging for the application
"""

import logging
import logging.handlers
import json
from pathlib import Path
from datetime import datetime

from src.core.settings import settings


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs JSON"""
    
    def format(self, record):
        """Format log record as JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


def setup_logging(
    name: str = "gtm_simulator",
    log_level: str = None,
    log_file: str = None,
) -> logging.Logger:
    """
    Set up logging configuration
    
    Args:
        name: Logger name
        log_level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_file: Path to log file
        
    Returns:
        Configured logger instance
    """
    if log_level is None:
        log_level = settings.LOG_LEVEL
    
    if log_file is None:
        log_file = settings.LOG_FILE
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level))
    
    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console Handler (human-readable)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level))
    console_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File Handler (JSON format for parsing)
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10_000_000,  # 10MB
        backupCount=5,
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = JSONFormatter()
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    return logger


# Module-level logger
logger = setup_logging()


# ============================================================================
# Utility Functions
# ============================================================================

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module
    
    Usage:
        from src.core.logger import get_logger
        logger = get_logger(__name__)
        logger.info("This is an info message")
    """
    return logging.getLogger(name)


def log_agent_execution(
    agent_name: str,
    status: str,
    duration: float = None,
    tokens_used: int = None,
):
    """
    Log agent execution details
    
    Args:
        agent_name: Name of agent
        status: Status (running, complete, error)
        duration: Execution time in seconds
        tokens_used: Tokens used by LLM
    """
    extra = {
        "agent": agent_name,
        "status": status,
    }
    if duration is not None:
        extra["duration_seconds"] = duration
    if tokens_used is not None:
        extra["tokens_used"] = tokens_used
    
    logger.info(f"Agent execution: {agent_name} - {status}", extra=extra)


if __name__ == "__main__":
    # Test logging
    test_logger = get_logger("test")
    
    print("📝 Testing logging...")
    test_logger.debug("This is a DEBUG message")
    test_logger.info("This is an INFO message")
    test_logger.warning("This is a WARNING message")
    test_logger.error("This is an ERROR message")
    
    print(f"✅ Logs written to: {settings.LOG_FILE}")