import logging
import os
import sys
from logging.handlers import RotatingFileHandler
import config

def setup_logger(name: str) -> logging.Logger:
    """
    Setup a standardized logger that writes to _logs directory and stdout.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if logger.hasHandlers():
        logger.handlers.clear()

    # Log file path
    log_file = os.path.join(config.LOGS_DIR, f'{name}.log')
    
    # Rotating file handler (5MB, keep 3 backups)
    file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(logging.StreamHandler(sys.stdout))
    
    return logger
