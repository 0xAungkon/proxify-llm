import time
import uuid
import logging
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import uvicorn
from config.settings import settings
from inc.utils import create_log_file, extract_chat_response

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", handlers=[logging.StreamHandler()])

app = FastAPI()

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

    log_file = create_log_file(settings.log_folder, request_id, path, method, request_data)

    async def stream_generator():
        url = f"http://{settings.ollama_host}:{settings.ollama_port}/{path}"
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
                    clear_response = extract_chat_response(response_bytes)

                    with open(log_file, "ab") as f:
                        f.write(f"Assistant response: {clear_response}\n".encode())

                latency = round(time.time() - start, 3)
                with open(log_file, "ab") as f:
                    f.write(b"\n--- RESPONSE END ---\n")
                    f.write(f"Latency: {latency:.3f} sec\n".encode())

    return StreamingResponse(stream_generator(), media_type="application/json")

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.proxy_host, port=settings.proxy_port, reload=True)