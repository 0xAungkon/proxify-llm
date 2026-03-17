import time

import psutil
from fastapi import APIRouter

router = APIRouter(tags=["Health"])

_service_start = time.time()
_UPTIME_WINDOW = 30 * 24 * 3600  # 30-day SLA window in seconds


@router.get("/health")
async def health_check():
    return {"status": "ok"}


@router.get("/health/detail")
async def health_detail():
    mem = psutil.virtual_memory()

    system_uptime_s = time.time() - psutil.boot_time()
    service_uptime_s = time.time() - _service_start

    return {
        "status": "ok",
        "cpu_usage_pct": psutil.cpu_percent(interval=0.1),
        "memory_usage_pct": mem.percent,
        "memory_used_mb": round(mem.used / 1024 / 1024, 2),
        "memory_total_mb": round(mem.total / 1024 / 1024, 2),
        "system_uptime_seconds": round(system_uptime_s, 2),
        "system_uptime_pct": round(min(system_uptime_s / _UPTIME_WINDOW * 100, 100.0), 4),
        "service_uptime_seconds": round(service_uptime_s, 2),
        "service_uptime_pct": round(min(service_uptime_s / _UPTIME_WINDOW * 100, 100.0), 4),
    }
