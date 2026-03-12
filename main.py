import os
import time
import uuid
import logging
import json
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import uvicorn

# Config
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "127.0.0.1")
OLLAMA_PORT = int(os.getenv("OLLAMA_PORT", 11434))
PROXY_HOST = os.getenv("PROXY_HOST", "0.0.0.0")
PROXY_PORT = int(os.getenv("PROXY_PORT", 8000))
LOG_FOLDER = os.getenv("LOG_FOLDER", "logs/ollama")

os.makedirs(LOG_FOLDER, exist_ok=True)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", handlers=[logging.StreamHandler()])

app = FastAPI()

def create_log_file(request_id: str, path: str, method: str, request_data: any):
    log_dir = os.path.join(LOG_FOLDER, *path.strip("/").split("/"))
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{time.strftime('%Y%m%d_%H%M%S')}_{request_id}.log")

    with open(log_file, "wb") as f:
        f.write(f"Request ID: {request_id}\n".encode())
        f.write(f"Path: /{path}\n".encode())
        f.write(f"Method: {method}\n".encode())
        f.write(f"Request: {request_data}\n".encode())
        f.write(b"--- RESPONSE START ---\n")

    return log_file

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def proxy(path: str, request: Request):
    request_id = str(uuid.uuid4())
    start = time.time()
    method = request.method

    # Get request data
    if method in ["POST", "PUT", "PATCH"]:
        try:
            request_data = await request.json()
        except Exception:
            request_data = (await request.body()).decode(errors="ignore")
    else:
        request_data = dict(request.query_params)

    log_file = create_log_file(request_id, path, method, request_data)

    async def stream_generator():
        url = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/{path}"
        normalized_path = path.strip("/")
        is_chat_path = normalized_path == "api/chat"

        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(method, url, json=request_data if isinstance(request_data, dict) else None, params=request_data if isinstance(request_data, dict) else None) as r:
                response_bytes = bytearray()

                with open(log_file, "ab") as f:
                    async for chunk in r.aiter_bytes():
                        response_bytes.extend(chunk)

                        if not is_chat_path:
                            f.write(chunk)

                        yield chunk

                if is_chat_path:
                    decoded = response_bytes.decode(errors="ignore")
                    assistant_text_parts = []

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
                        clear_response = "<empty>"

                    with open(log_file, "ab") as f:
                        f.write(f"Assistant response: {clear_response}\n".encode())

                latency = round(time.time() - start, 3)
                with open(log_file, "ab") as f:
                    f.write(b"\n--- RESPONSE END ---\n")
                    f.write(f"Latency: {latency:.3f} sec\n".encode())

    return StreamingResponse(stream_generator(), media_type="application/json")

if __name__ == "__main__":
    uvicorn.run("ollama_proxy:app", host=PROXY_HOST, port=PROXY_PORT, reload=True)