import logging
from logging.handlers import TimedRotatingFileHandler


class FileLogger:
    def __init__(self, log_file, set_level=logging.INFO):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(set_level)
        file_handler = TimedRotatingFileHandler(log_file, backupCount=5)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def log(self, level, message):
        if level == "debug":
            self.logger.debug(message)
        elif level == "info":
            self.logger.info(message)
        elif level == "warning":
            self.logger.warning(message)
        elif level == "error":
            self.logger.error(message)
        elif level == "critical":
            self.logger.critical(message)
