import json
from typing import Any

from fastapi import Request


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


def extract_chat_response(response_bytes: bytearray) -> str:
	decoded = response_bytes.decode(errors="ignore")
	assistant_text_parts: list[str] = []

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

	clear_response = "".join(assistant_text_parts).strip()
	if not clear_response:
		return "<empty>"

	return clear_response
