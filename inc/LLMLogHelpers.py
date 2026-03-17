import os
import sys
import time
from typing import Any

from loguru import logger


def create_log_file(log_folder: str, request_id: str, path: str, method: str, request_data: Any) -> str:
	log_dir = os.path.join(log_folder, *path.strip("/").split("/"))
	os.makedirs(log_dir, exist_ok=True)
	log_file = os.path.join(log_dir, f"{time.strftime('%Y%m%d_%H%M%S')}_{request_id}.log")

	with open(log_file, "wb") as file:
		file.write(f"Request ID: {request_id}\n".encode())
		file.write(f"Path: /{path}\n".encode())
		file.write(f"Method: {method}\n".encode())
		file.write(f"Request: {request_data}\n".encode())
		file.write(b"--- RESPONSE START ---\n")

	return log_file


def write_response_chunk(log_file: str, chunk: bytes) -> None:
	with open(log_file, "ab") as file:
		file.write(chunk)


def append_assistant_response(log_file: str, assistant_response: str) -> None:
	with open(log_file, "ab") as file:
		file.write(f"Assistant response: {assistant_response}\n".encode())


def append_response_end(log_file: str, latency: float) -> None:
	with open(log_file, "ab") as file:
		file.write(b"\n--- RESPONSE END ---\n")
		file.write(f"Latency: {latency:.3f} sec\n".encode())
