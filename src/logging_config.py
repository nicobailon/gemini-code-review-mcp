"""
Logging configuration for the application.

This module provides centralized logging configuration with support for
both development (human-readable) and production/MCP (JSON) formats.
"""

import logging
import os
import sys
from typing import Any, Dict, Optional

# Try to import structlog for structured logging
try:
    import structlog
    HAS_STRUCTLOG = True
except ImportError:
    HAS_STRUCTLOG = False


def configure_logging(
    level: str = "INFO",
    format_type: str = "auto",
    log_file: Optional[str] = None
) -> None:
    """
    Configure logging for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Log format type ('auto', 'json', 'console')
                    - 'auto': JSON in MCP context, console otherwise
                    - 'json': Always use JSON format
                    - 'console': Always use human-readable format
        log_file: Optional log file path
    """
    # Detect if running in MCP context
    is_mcp_context = os.environ.get("MCP_CONTEXT") == "1" or "mcp" in sys.argv[0].lower()
    
    # Determine format based on settings
    use_json = format_type == "json" or (format_type == "auto" and is_mcp_context)
    
    if HAS_STRUCTLOG and use_json:
        # Configure structlog with JSON renderer for MCP/production
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()  # JSON output for log aggregation
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
        
        # Configure standard logging to work with structlog
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stderr,
            level=getattr(logging, level.upper()),
        )
        
        if log_file:
            # Add file handler for JSON logs
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter("%(message)s"))
            logging.getLogger().addHandler(file_handler)
            
    else:
        # Fallback to standard logging with human-readable format
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
        handlers = [logging.StreamHandler(sys.stderr)]
        if log_file:
            handlers.append(logging.FileHandler(log_file))
            
        logging.basicConfig(
            format=log_format,
            level=getattr(logging, level.upper()),
            handlers=handlers
        )


def get_logger(name: str) -> Any:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance (structlog or standard logging)
    """
    if HAS_STRUCTLOG and _is_structlog_configured():
        return structlog.get_logger(name)
    else:
        return logging.getLogger(name)


def _is_structlog_configured() -> bool:
    """Check if structlog is configured."""
    if not HAS_STRUCTLOG:
        return False
    
    try:
        # Try to get the current configuration
        import structlog._config
        return structlog._config._CONFIG is not None
    except (ImportError, AttributeError):
        return False


# Environment-based configuration helper
def setup_mcp_logging() -> None:
    """
    Setup logging specifically for MCP server context.
    
    This enables JSON logging for better log aggregation and parsing.
    """
    configure_logging(
        level=os.environ.get("LOG_LEVEL", "INFO"),
        format_type="json",
        log_file=os.environ.get("LOG_FILE")
    )


def setup_cli_logging() -> None:
    """
    Setup logging for CLI context.
    
    This uses human-readable console format.
    """
    configure_logging(
        level=os.environ.get("LOG_LEVEL", "INFO"),
        format_type="console",
        log_file=os.environ.get("LOG_FILE")
    )