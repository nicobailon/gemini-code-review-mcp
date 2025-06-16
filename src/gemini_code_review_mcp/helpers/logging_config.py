"""
Logging configuration for the application.

This module provides centralized logging configuration with support for
both development (human-readable) and production/MCP (JSON) formats.
"""

import logging
import os
import sys
from typing import Any, Optional, Union

# Try to import structlog for structured logging
try:
    import structlog  # type: ignore[import-not-found]
    _has_structlog = True
    structlog_module: Any = structlog
except ImportError:
    _has_structlog = False
    structlog_module = None


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
    
    if _has_structlog and use_json and structlog_module is not None:
        # Configure structlog with JSON renderer for MCP/production
        structlog_module.configure(
            processors=[
                structlog_module.stdlib.filter_by_level,
                structlog_module.stdlib.add_logger_name,
                structlog_module.stdlib.add_log_level,
                structlog_module.stdlib.PositionalArgumentsFormatter(),
                structlog_module.processors.TimeStamper(fmt="iso"),
                structlog_module.processors.StackInfoRenderer(),
                structlog_module.processors.format_exc_info,
                structlog_module.processors.UnicodeDecoder(),
                structlog_module.processors.JSONRenderer()  # JSON output for log aggregation
            ],
            context_class=dict,
            logger_factory=structlog_module.stdlib.LoggerFactory(),
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


def get_logger(name: str) -> Union[logging.Logger, Any]:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance (structlog or standard logging)
    """
    if _has_structlog and _is_structlog_configured() and structlog_module is not None:
        return structlog_module.get_logger(name)
    else:
        return logging.getLogger(name)


def _is_structlog_configured() -> bool:
    """Check if structlog is configured."""
    if not _has_structlog or structlog_module is None:
        return False
    
    try:
        # Try to get the current configuration
        if structlog_module and hasattr(structlog_module, '_config'):
            config_module = getattr(structlog_module, '_config')
            return hasattr(config_module, '_CONFIG') and config_module._CONFIG is not None
        return False
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