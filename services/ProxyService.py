import time
import uuid

import httpx
from fastapi import Request
from fastapi.responses import JSONResponse, StreamingResponse

from config.settings import settings
from inc.LogHelpers import  logger
from inc.LLMRequestLogHelpers import (
    append_assistant_response,
    append_full_response_body,
    build_log_dir,
    create_log_file,
    finalize_log_file,
    schedule_log_retention_cleanup,
    write_response_chunk,
)
from inc.ProxyHelpers import build_upstream_url, extract_chat_response, is_chat_path, prepare_request_payload


async def handle_proxy_request(path: str, request: Request) -> StreamingResponse:
    normalized_path = path.lstrip("/")
    if normalized_path == "favicon.ico" or normalized_path == ".well-known" or normalized_path.startswith(".well-known/") or normalized_path.startswith("/common"):
        return JSONResponse(content={})

    request_id = str(uuid.uuid4())
    start = time.time()
    method = request.method
    logger.info(f"[{request_id}] Incoming request {method} /{path}")

    request_data = await prepare_request_payload(request=request)
    log_dir = build_log_dir(log_folder=settings.log_folder, path=path)
    schedule_log_retention_cleanup(log_dir=log_dir, retention_days=settings.log_retention_days)

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
                    assistant_response, final_response_meta = extract_chat_response(response_bytes=response_bytes)
                    append_assistant_response(log_file=log_file, assistant_response=assistant_response)
                    # Store the complete response metadata (with done, durations, etc.)
                    append_full_response_body(log_file=log_file, response_body=final_response_meta)

                latency = round(time.time() - start, 3)
                finalize_log_file(
                    log_file=log_file,
                    response_code=response.status_code,
                    latency=latency,
                )
                logger.info(f"[{request_id}] Completed request in {latency:.3f}s")

    return StreamingResponse(stream_generator(), media_type="application/json")