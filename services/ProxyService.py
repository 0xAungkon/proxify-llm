import time
import uuid

import httpx
from fastapi import Request
from fastapi.responses import StreamingResponse

from config.settings import settings
from inc.LogHelpers import  logger
from inc.LLMLogHelpers import append_assistant_response, append_response_end, create_log_file, write_response_chunk
from inc.ProxyHelpers import build_upstream_url, extract_chat_response, is_chat_path, prepare_request_payload


async def handle_proxy_request(path: str, request: Request) -> StreamingResponse:
    request_id = str(uuid.uuid4())
    start = time.time()
    method = request.method
    logger.info(f"[{request_id}] Incoming request {method} /{path}")

    request_data = await prepare_request_payload(request=request)
    log_file = create_log_file(
        log_folder=settings.log_folder,
        request_id=request_id,
        path=path,
        method=method,
        request_data=request_data,
    )

    async def stream_generator():
        url = build_upstream_url(path=path, host=settings.ollama_host, port=settings.ollama_port)
        chat_path = is_chat_path(path=path)

        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                method,
                url,
                json=request_data if isinstance(request_data, dict) else None,
                params=request_data if isinstance(request_data, dict) else None,
            ) as response:
                response_bytes = bytearray()

                async for chunk in response.aiter_bytes():
                    response_bytes.extend(chunk)

                    if not chat_path:
                        write_response_chunk(log_file=log_file, chunk=chunk)

                    yield chunk

                if chat_path:
                    clear_response = extract_chat_response(response_bytes=response_bytes)
                    append_assistant_response(log_file=log_file, assistant_response=clear_response)

                latency = round(time.time() - start, 3)
                append_response_end(log_file=log_file, latency=latency)
                logger.info(f"[{request_id}] Completed request in {latency:.3f}s")

    return StreamingResponse(stream_generator(), media_type="application/json")