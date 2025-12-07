from pythonjsonlogger.json import JsonFormatter

from src.settings import settings

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json_log_formatter": {
            "format": "%(service_name)s %(levelname)s %(type)s %(pathname)s %(lineno)d %(thread)d %(message)s",
            "()": JsonFormatter,
            "static_fields": {
                "service_name": settings.service_name,
                "type": "app",
            },
            "rename_fields_keep_missing": True,
            "json_ensure_ascii": False,
            "timestamp": True,
        },
    },
    "handlers": {
        "stream_handler": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "json_log_formatter",
        },
        "file_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "json_log_formatter",
            "filename": settings.logging_file_path,
            "maxBytes": settings.logging_max_bytes,
            "backupCount": settings.logging_backup_count,
        },
    },
    "loggers": {
        "logger": {
            "handlers": ["stream_handler", "file_handler"],
            "level": settings.log_level,
            "propagate": False,
        }
    },
}
