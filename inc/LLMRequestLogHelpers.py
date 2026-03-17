import asyncio
import json
import os
import random
import time
from typing import Any


_RETENTION_TASKS: dict[str, asyncio.Task[None]] = {}

# In-memory state for pending log entries keyed by the pending file path.
_LOG_STATE: dict[str, dict[str, Any]] = {}


def _enforce_log_retention(log_dir: str, retention_days: int) -> None:
	if retention_days <= 0:
		return

	cutoff = time.time() - (retention_days * 24 * 60 * 60)
	for file_name in os.listdir(log_dir):
		if not file_name.endswith(".json"):
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
	"""Register an in-progress log entry and return the pending file path.

	The file is not written to disk until :func:`finalize_log_file` is called,
	at which point the response code is known and the filename can be finalised.
	"""
	log_dir = build_log_dir(log_folder=log_folder, path=path)
	os.makedirs(log_dir, exist_ok=True)

	timestamp = time.strftime("%Y%m%d_%H%M%S")
	random_suffix = random.randint(100, 999)
	method_upper = method.upper()

	# Reserve the slot with a PENDING filename so the path is known up-front.
	pending_path = os.path.join(
		log_dir, f"{method_upper}_{timestamp}_PENDING_{random_suffix}.json"
	)

	_LOG_STATE[pending_path] = {
		"request_id": request_id,
		"path": f"/{path}",
		"method": method_upper,
		"_timestamp": timestamp,
		"_random_suffix": random_suffix,
		"_log_dir": log_dir,
		"request": request_data,
		"_response_chunks": bytearray(),
		"assistant_response": None,
	}

	return pending_path


def write_response_chunk(log_file: str, chunk: bytes) -> None:
	"""Accumulate a response chunk in memory."""
	state = _LOG_STATE.get(log_file)
	if state is not None:
		state["_response_chunks"].extend(chunk)


def append_assistant_response(log_file: str, assistant_response: str) -> None:
	"""Store the parsed assistant reply in the pending log state."""
	state = _LOG_STATE.get(log_file)
	if state is not None:
		state["assistant_response"] = assistant_response


def append_full_response_body(log_file: str, response_body: Any) -> None:
	"""Store the complete response body (including metadata) in the pending log state."""
	state = _LOG_STATE.get(log_file)
	if state is not None:
		state["_response_body_complete"] = response_body


def finalize_log_file(log_file: str, response_code: int, latency: float) -> str:
	"""Write the completed log as a JSON file and rename it with the response code.

	Filename format: ``<METHOD>_<TIMESTAMP>_<RESPONSE_CODE>_<3DIGIT>.json``

	Returns the final file path.
	"""
	state = _LOG_STATE.pop(log_file, {})

	method_upper = state.get("method", "UNKNOWN")
	timestamp = state.get("_timestamp", time.strftime("%Y%m%d_%H%M%S"))
	random_suffix = state.get("_random_suffix", random.randint(100, 999))
	log_dir = state.get("_log_dir", os.path.dirname(log_file))
	response_chunks: bytearray = state.pop("_response_chunks", bytearray())
	response_body_complete: Any = state.pop("_response_body_complete", None)

	# Discard internal tracking keys before persisting.
	for internal_key in ("_timestamp", "_random_suffix", "_log_dir"):
		state.pop(internal_key, None)

	# Use the complete response body if available, otherwise parse from chunks
	if response_body_complete is not None:
		response_body = response_body_complete
	else:
		try:
			response_body: Any = json.loads(response_chunks.decode("utf-8", errors="replace"))
		except (json.JSONDecodeError, ValueError):
			response_body = response_chunks.decode("utf-8", errors="replace") or None

	log_data = {
		**state,
		"response_code": response_code,
		"response_body": response_body,
		"latency_sec": latency,
	}

	final_path = os.path.join(
		log_dir, f"{method_upper}_{timestamp}_{response_code}_{random_suffix}.json"
	)

	with open(final_path, "w", encoding="utf-8") as file:
		json.dump(log_data, file, indent=2, default=str)

	return final_path
