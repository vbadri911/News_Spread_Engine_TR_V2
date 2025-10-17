import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': self.formatTime(record, '%Y-%m-%d %H:%M:%S'),
            'level': record.levelname,
            'message': record.msg % record.args if record.args else record.msg,
            'module': record.module,
            'line': record.lineno
        }
        return json.dumps(log_data)


def setup_logging(script_name):
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # File handler with rotation
    file_handler = RotatingFileHandler(f'logs/{script_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.log', maxBytes=1 * 1024 * 1024, backupCount=5)
    file_handler.setFormatter(JsonFormatter())

    logging.basicConfig(handlers=[file_handler], level=logging.INFO)

    # Console handler for real-time output
    #console_handler = logging.StreamHandler()
    #console_handler.setFormatter(JsonFormatter())

    # Configure logger with both handlers
    #logging.basicConfig(handlers=[file_handler, console_handler], level=logging.INFO)