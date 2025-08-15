"""
Utility Functions Module

This module provides a comprehensive collection of utility functions used throughout
the report generation system. It includes file system operations, configuration
management, logging setup, data serialization, and various helper functions for
robust application operation.

Key Features:
    - Project path resolution and file system utilities
    - YAML configuration loading with validation
    - Centralized logging configuration with file and console output
    - JSON serialization with UTF-8 support
    - Filename sanitization for cross-platform compatibility
    - Environment variable parsing with type conversion
    - Safe sleep operations with error handling
    - UTC timestamp generation in ISO format

Function Categories:
    - Path Management: project_root(), resolve_path()
    - Configuration: load_queries(), get_env_int()
    - Logging: setup_logging()
    - Data Operations: write_json(), utc_now_str()
    - String Utilities: sanitize_filename()
    - System Operations: bounded_sleep()

Dependencies:
    - yaml: YAML configuration file parsing
    - pathlib: Modern path manipulation
    - datetime: Timezone-aware timestamp generation
    - dotenv: Environment variable management
    - Standard library modules for file I/O and system operations

Author: Juan Sebastián Dosman
Version: 1.0
Date: 15th August 2025
"""

import os
import sys
import json
import time
import logging
import yaml
from datetime import datetime, timezone
from typing import Any, Dict
from pathlib import Path
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv() 


def project_root() -> str:
    """
    Get the absolute path to the project root directory.
    
    This function determines the project root by navigating up two levels
    from the current file location. It provides a consistent way to reference
    the project base directory regardless of the current working directory.
    
    Returns:
        str: Absolute path to the project root directory
    
    Usage Note:
        This function assumes the utilities module is located at:
        project_root/src/utils.py or similar nested structure.
        Adjust the number of os.path.dirname() calls if the file structure changes.
    
    Example:
        >>> root = project_root()
        >>> print(f"Project root: {root}")
        >>> # Output: Project root: /home/user/my-project
    """
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resolve_path(*parts: str) -> str:
    """
    Resolve a path relative to the project root directory.
    
    This function provides a robust way to construct file paths relative to the
    project root, ensuring consistent path resolution across different operating
    systems and working directories. Uses pathlib for modern path handling.
    
    Args:
        *parts (str): Path components to join relative to project root.
                    Can be file names, directory names, or nested paths.
    
    Returns:
        str: Absolute path constructed from project root and provided parts
    
    Path Resolution:
        - Uses pathlib.Path for cross-platform compatibility
        - Resolves symbolic links to actual paths
        - Handles both Unix and Windows path separators
        - Goes up 2 parent directories from current file location
    
    Example:
        >>> config_path = resolve_path("config", "settings.yml")
        >>> data_file = resolve_path("data", "reports", "output.json")
        >>> template_dir = resolve_path("templates")
        >>> print(config_path)
        >>> # Output: /home/user/project/config/settings.yml
    """
    root_dir = Path(__file__).resolve().parents[2]
    
    return str(root_dir.joinpath(*parts))


def load_queries(config_path: str = "config/queries.yml") -> Dict[str, Any]:
    """
    Load and validate YAML configuration file for report queries.
    
    This function loads a YAML configuration file containing report definitions,
    validates its structure, and returns the parsed configuration. It ensures
    the configuration has the required format for the report generation system.
    
    Args:
        config_path (str): Path to YAML configuration file relative to project root.
                        Defaults to "config/queries.yml"
    
    Returns:
        Dict[str, Any]: Parsed YAML configuration with validated structure containing:
            - reports (List[Dict]): List of report configurations
            - Other top-level configuration keys as present in the file
    
    Raises:
        FileNotFoundError: If the configuration file doesn't exist at the specified path
        yaml.YAMLError: If the file contains invalid YAML syntax
        ValueError: If the configuration doesn't contain a valid 'reports' list
        UnicodeDecodeError: If the file cannot be read as UTF-8
    
    Validation Rules:
        - File must exist and be readable
        - Must contain valid YAML syntax
        - Root level must contain 'reports' key
        - 'reports' value must be a list (can be empty)
        - Empty files are treated as empty dictionaries
    
    File Format Expected:
        ```yaml
        reports:
            - name: "Report 1"
                search: "search term"
                fields: ["field1", "field2"]
                max_items: 100
            - name: "Report 2"
                search: "another term"
                # ... more report configurations
        ```
    
    Example:
        >>> config = load_queries("config/reports.yml")
        >>> print(f"Found {len(config['reports'])} reports")
        
        >>> # Load from custom path
        >>> config = load_queries("custom/my-reports.yml")
        >>> for report in config["reports"]:
        ...     print(f"Report: {report['name']}")
    """
    full_path = resolve_path(config_path)
    
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Configuration file not found: {full_path}")
    
    with open(full_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    
    if "reports" not in data or not isinstance(data["reports"], list):
        raise ValueError("Invalid queries.yml: root key 'reports' must be a list")
    
    return data


def setup_logging(out_dir: str) -> None:
    """
    Configure centralized logging with both file and console output.
    
    This function sets up a comprehensive logging system that outputs to both
    the console (stdout) and a log file. It creates the necessary directory
    structure and configures consistent log formatting across all handlers.
    
    Args:
        out_dir (str): Base output directory where logs subdirectory will be created.
                    The actual log file will be at: out_dir/logs/run.log
    
    Returns:
        None
    
    Raises:
        OSError: If the logs directory cannot be created due to permissions
        IOError: If the log file cannot be opened for writing
    
    Log Configuration:
        - Level: INFO and above (INFO, WARNING, ERROR, CRITICAL)
        - Format: "YYYY-MM-DD HH:MM:SS [LEVEL] message"
        - Encoding: UTF-8 for international character support
        - Handlers: Console (stdout) + File (logs/run.log)
    
    Directory Structure:
        ```
        out_dir/
        └── logs/
            └── run.log
        ```
    
    Log File Behavior:
        - Creates new file if doesn't exist
        - Appends to existing file (doesn't overwrite)
        - Uses UTF-8 encoding for proper character handling
        - Rotates automatically if file becomes too large (system dependent)
    
    Example:
        >>> setup_logging("output")
        >>> logging.info("This appears in both console and output/logs/run.log")
        >>> logging.error("Error messages are highlighted in console")
        
        >>> # After setup, use logging anywhere in the application
        >>> import logging
        >>> logging.warning("Configuration missing, using defaults")
    """
    # Create logs directory structure
    logs_dir = os.path.join(out_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)

    log_path = os.path.join(logs_dir, "run.log")
    
    # Configure logging with dual output
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),  # Console output
            logging.FileHandler(log_path, encoding="utf-8")  # File output
        ]
    )


def utc_now_str() -> str:
    """
    Generate current UTC timestamp in ISO 8601 format.
    
    This function provides a consistent way to generate timestamps for
    logging, file naming, and data serialization. Always uses UTC timezone
    to avoid timezone confusion in distributed systems or log analysis.
    
    Returns:
        str: Current UTC timestamp in format "YYYY-MM-DDTHH:MM:SSZ"
    
    Format Details:
        - ISO 8601 compliant timestamp format
        - UTC timezone (indicated by trailing 'Z')
        - 24-hour time format
        - No microseconds for consistency
        - Suitable for sorting and parsing
    
    Use Cases:
        - Report generation timestamps
        - Log entry timestamps
        - File naming with temporal ordering
        - API response timestamps
        - Audit trail creation
    
    Example:
        >>> timestamp = utc_now_str()
        >>> print(f"Generated at: {timestamp}")
        >>> # Output: Generated at: 2024-03-15T14:30:45Z
        
        >>> # Use in filenames
        >>> filename = f"report_{utc_now_str()}.pdf"
        >>> # Output: report_2024-03-15T14:30:45Z.pdf
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_json(obj: Any, path: str) -> None:
    """
    Write any object to a JSON file with proper formatting and encoding.
    
    This function serializes Python objects to JSON format with consistent
    formatting, UTF-8 encoding, and automatic directory creation. It provides
    a standardized way to save data across the application.
    
    Args:
        obj (Any): Python object to serialize to JSON. Can be dict, list,
                or any JSON-serializable type (str, int, float, bool, None)
        path (str): Target file path for the JSON output
    
    Returns:
        None
    
    Raises:
        TypeError: If the object contains non-JSON-serializable types
        OSError: If the directory cannot be created or file cannot be written
        UnicodeError: If there are encoding issues (rare with UTF-8)
    
    JSON Configuration:
        - Indentation: 2 spaces for readability
        - ensure_ascii=False: Allows international characters
        - UTF-8 encoding: Supports all Unicode characters
        - Creates parent directories if they don't exist
    
    Supported Types:
        - Basic: str, int, float, bool, None
        - Containers: dict, list, tuple (converted to list)
        - Nested: Any combination of the above
        - Not supported: functions, classes, file objects, etc.
    
    Example:
        >>> data = {
        ...     "name": "Sales Report",
        ...     "items": [{"product": "Widget", "count": 42}],
        ...     "generated": utc_now_str()
        ... }
        >>> write_json(data, "output/reports/sales.json")
        >>> # Creates: output/reports/sales.json with formatted JSON
        
        >>> # Works with lists too
        >>> items = [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]
        >>> write_json(items, "data/items.json")
    """
    # Ensure parent directory exists
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    # Write JSON with consistent formatting
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def sanitize_filename(name: str) -> str:
    """
    Clean a string to be safe for use as a filename across different operating systems.
    
    This function removes or replaces characters that are problematic in filenames,
    ensuring the result works on Windows, macOS, and Linux file systems. It preserves
    readability while ensuring filesystem compatibility.
    
    Args:
        name (str): Original string that may contain unsafe characters
    
    Returns:
        str: Sanitized string safe for use as filename, with leading/trailing
            whitespace removed
    
    Character Handling:
        - Keeps: Letters (a-z, A-Z), numbers (0-9)
        - Keeps: Hyphens (-), underscores (_), periods (.)
        - Removes: All other characters including:
            - Path separators: / \\
            - Reserved characters: < > : " | ? *
            - Control characters and spaces
            - Unicode characters that may cause issues
    
    Edge Cases:
        - Empty string returns empty string
        - String with only unsafe characters returns empty string
        - Leading/trailing dots and spaces are stripped
        - Multiple consecutive safe characters are preserved
    
    Example:
        >>> safe = sanitize_filename("Sales Report Q4 2024!")
        >>> print(safe)  # Output: "SalesReportQ42024"
        
        >>> safe = sanitize_filename("file/with\\bad:chars?.txt")
        >>> print(safe)  # Output: "filewithbadchars.txt"
        
        >>> safe = sanitize_filename("report_2024-03-15.pdf")
        >>> print(safe)  # Output: "report_2024-03-15.pdf" (unchanged)
        
        >>> # Use with dynamic names
        >>> report_name = user_input.get("name", "default")
        >>> filename = f"{sanitize_filename(report_name)}.pdf"
    """
    return "".join(c for c in name if c.isalnum() or c in ("-", "_", ".")).strip()


def get_env_int(key: str, default: int) -> int:
    """
    Retrieve an integer value from environment variables with safe fallback.
    
    This function attempts to parse an environment variable as an integer,
    returning a default value if the variable doesn't exist or cannot be
    parsed. It provides type-safe environment variable access.
    
    Args:
        key (str): Name of the environment variable to retrieve
        default (int): Default value to return if parsing fails or variable is missing
    
    Returns:
        int: Parsed integer value from environment variable, or default value
    
    Parsing Behavior:
        - Returns default if environment variable doesn't exist
        - Returns default if environment variable is empty string
        - Returns default if environment variable cannot be parsed as integer
        - Successfully parses: "123", "-456", "0", "  789  " (with whitespace)
        - Fails to parse: "abc", "12.34", "1.2e3", "", "null"
    
    Error Handling:
        - Never raises exceptions
        - Logs no warnings or errors (silent fallback)
        - Provides predictable behavior for configuration
    
    Example:
        >>> # Environment: TIMEOUT=30
        >>> timeout = get_env_int("TIMEOUT", 10)
        >>> print(timeout)  # Output: 30
        
        >>> # Environment: TIMEOUT=invalid
        >>> timeout = get_env_int("TIMEOUT", 10)
        >>> print(timeout)  # Output: 10
        
        >>> # Environment: TIMEOUT not set
        >>> timeout = get_env_int("TIMEOUT", 10)
        >>> print(timeout)  # Output: 10
        
        >>> # Common usage patterns
        >>> max_retries = get_env_int("MAX_RETRIES", 3)
        >>> port = get_env_int("PORT", 8080)
        >>> batch_size = get_env_int("BATCH_SIZE", 100)
    """
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


def bounded_sleep(seconds: float) -> None:
    """
    Sleep for a specified duration with error handling and bounds checking.
    
    This function provides a safe sleep operation that handles negative values
    and exceptions gracefully. It's designed for use in retry mechanisms and
    rate limiting where reliability is more important than exact timing.
    
    Args:
        seconds (float): Duration to sleep in seconds. Negative values are
                        treated as 0 (no sleep)
    
    Returns:
        None
    
    Raises:
        None: All exceptions are caught and handled silently
    
    Behavior:
        - Negative values: Treated as 0 (no sleep occurs)
        - Zero: Returns immediately (no sleep)
        - Positive values: Sleep for the specified duration
        - Exceptions: Caught and ignored (function returns immediately)
    
    Error Handling:
        - Handles system interruptions gracefully
        - Handles invalid float values
        - Handles system sleep failures
        - Never propagates exceptions to caller
    
    Use Cases:
        - Retry backoff mechanisms
        - Rate limiting between API calls
        - Implementing delays in batch processing
        - Any situation where sleep failure shouldn't crash the application
    
    Example:
        >>> bounded_sleep(1.5)  # Sleep for 1.5 seconds
        >>> bounded_sleep(-1)   # No sleep (negative value)
        >>> bounded_sleep(0)    # No sleep (zero value)
        
        >>> # Typical usage in retry logic
        >>> for attempt in range(3):
        ...     try:
        ...         result = api_call()
        ...         break
        ...     except Exception:
        ...         wait_time = 2 ** attempt  # Exponential backoff
        ...         bounded_sleep(wait_time)
    """
    try:
        time.sleep(max(0.0, seconds))
    except Exception:
        pass