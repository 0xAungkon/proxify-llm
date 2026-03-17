import json
import os
import time
from typing import Any


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
