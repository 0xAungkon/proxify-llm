import json
from typing import Any

from fastapi import Request


def convert_nanoseconds_to_readable(nanoseconds: int | float) -> str:
	"""Convert nanoseconds to milliseconds or seconds for readability.
	
	Returns a formatted string with appropriate units (ms or s).
	"""
	if not isinstance(nanoseconds, (int, float)):
		return str(nanoseconds)
	
	milliseconds = nanoseconds / 1_000_000
	
	# Use seconds if >= 1000 ms (1 second), otherwise use milliseconds
	if milliseconds >= 1000:
		seconds = milliseconds / 1000
		return f"{seconds:.2f}s"
	else:
		return f"{milliseconds:.2f}ms"


async def prepare_request_payload(request: Request) -> Any:
	method = request.method
	if method in ["POST", "PUT", "PATCH"]:
		try:
			return await request.json()
		except Exception:
			return (await request.body()).decode(errors="ignore")

	return dict(request.query_params)


def build_upstream_url(path: str, host: str, port: int) -> str:
	return f"http://{host}:{port}/{path}"


def is_chat_path(path: str) -> bool:
	return path.strip("/") == "api/chat"


def extract_chat_response(response_bytes: bytearray) -> tuple[str, dict[str, Any]]:
	"""Extract assistant response text and the final response metadata.
	
	Returns a tuple of (assistant_text, final_response_object).
	The final_response_object contains metadata like done, done_reason, durations, etc.
	Duration values are converted from nanoseconds to readable format (ms or s).
	"""
	decoded = response_bytes.decode(errors="ignore")
	assistant_text_parts: list[str] = []
	final_response: dict[str, Any] = {}

	for line in decoded.splitlines():
		line = line.strip()
		if not line:
			continue

		try:
			item = json.loads(line)
		except json.JSONDecodeError:
			continue

		message = item.get("message") or {}
		content = message.get("content")
		if isinstance(content, str):
			assistant_text_parts.append(content)
		
		# Capture the final response object (the one with "done": true)
		if item.get("done") is True:
			final_response = item.copy()
			
			# Convert nanosecond durations to readable format
			duration_fields = [
				"total_duration",
				"load_duration",
				"prompt_eval_duration",
				"eval_duration"
			]
			for field in duration_fields:
				if field in final_response:
					final_response[field] = convert_nanoseconds_to_readable(final_response[field])

	clear_response = "".join(assistant_text_parts).strip()
	if not clear_response:
		clear_response = "<empty>"

	return clear_response, final_response
