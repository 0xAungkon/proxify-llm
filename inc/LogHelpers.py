import os
import sys
import time
from loguru import logger


def configure_logger(log_folder: str, retention_days: int = 10, level: str = "INFO") -> None:
	os.makedirs(log_folder, exist_ok=True)
	app_log_file = os.path.join(log_folder, "app.log")

	logger.remove()
	logger.add(
		sink=sys.stdout,
		level=level.upper(),
		format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
	)
	logger.add(
		app_log_file,
		level=level.upper(),
		rotation="10 MB",
		retention=f"{retention_days} days",
		compression="zip",
		format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
	)

