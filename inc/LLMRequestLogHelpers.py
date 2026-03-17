import os
import asyncio
import time
from typing import Any


_RETENTION_TASKS: dict[str, asyncio.Task[None]] = {}


def _enforce_log_retention(log_dir: str, retention_days: int) -> None:
	if retention_days <= 0:
		return

	cutoff = time.time() - (retention_days * 24 * 60 * 60)
	for file_name in os.listdir(log_dir):
		if not file_name.endswith(".log"):
			continue

		file_path = os.path.join(log_dir, file_name)
		if not os.path.isfile(file_path):
			continue

		try:
			if os.path.getmtime(file_path) < cutoff:
				os.remove(file_path)
		except OSError:
			continue


def build_log_dir(log_folder: str, path: str) -> str:
	return os.path.join(log_folder, *path.strip("/").split("/"))


def schedule_log_retention_cleanup(log_dir: str, retention_days: int) -> None:
	if retention_days <= 0:
		return

	existing_task = _RETENTION_TASKS.get(log_dir)
	if existing_task and not existing_task.done():
		return

	async def _cleanup() -> None:
		try:
			await asyncio.to_thread(_enforce_log_retention, log_dir, retention_days)
		finally:
			_RETENTION_TASKS.pop(log_dir, None)

	_RETENTION_TASKS[log_dir] = asyncio.create_task(_cleanup())


def create_log_file(
	log_folder: str,
	request_id: str,
	path: str,
	method: str,
	request_data: Any,
) -> str:
	log_dir = build_log_dir(log_folder=log_folder, path=path)
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
