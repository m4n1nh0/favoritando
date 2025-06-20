import logging
import json
from logging import LogRecord
from app.core.config import settings


class JsonFormatter(logging.Formatter):
    def format(self, record: LogRecord) -> str:
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "filename": record.filename,
            "lineno": record.lineno,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)

        if record.stack_info:
            log_record["stack_info"] = self.formatStack(record.stack_info)

        return json.dumps(log_record, ensure_ascii=False)


class AppLogger:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AppLogger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.logger = logging.getLogger("aiqfome_api")
        self.logger.setLevel(settings.LOG_LEVEL.upper())

        json_formatter = JsonFormatter(datefmt="%Y-%m-%dT%H:%M:%S%z")

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(json_formatter)
        self.logger.addHandler(console_handler)

        self.logger.propagate = False
        self._initialized = True


logger = AppLogger().logger
