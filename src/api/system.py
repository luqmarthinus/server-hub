import asyncio
import time
import tempfile
import os
from fastapi import APIRouter, Depends, HTTPException
from src.api.auth import get_current_user
from src.models.user import User

router = APIRouter(prefix="/api/v1/system", tags=["system"])


async def require_superuser(current_user: User = Depends(get_current_user)):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Super admin access required")
    return current_user


@router.get("/info")
async def get_system_info(current_user: User = Depends(get_current_user)):
    """
    Returns system information: hostname, OS, Python version, CPU cores,
    memory total/used/percent, disk total/used/free/percent.
    """
    import platform
    import psutil
    import sys

    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return {
        "hostname": platform.node(),
        "system": platform.system(),
        "release": platform.release(),
        "python_version": sys.version.split()[0],
        "cpu_cores": psutil.cpu_count(logical=True),
        "memory_total_gb": round(mem.total / (1024**3), 2),
        "memory_used_gb": round(mem.used / (1024**3), 2),
        "memory_percent": mem.percent,
        "disk_total_gb": round(disk.total / (1024**3), 2),
        "disk_used_gb": round(disk.used / (1024**3), 2),
        "disk_free_gb": round(disk.free / (1024**3), 2),
        "disk_percent": disk.percent,
    }


@router.post("/stress/cpu")
async def stress_cpu(admin: User = Depends(require_superuser)):
    """Simulate high CPU usage for 5 seconds. Super admin only."""

    async def _burn():
        end = time.time() + 5
        while time.time() < end:
            _ = [i**2 for i in range(10000)]

    await asyncio.to_thread(_burn)
    return {"status": "CPU stress test completed (5 seconds)"}


@router.post("/stress/memory")
async def stress_memory(admin: User = Depends(require_superuser)):
    """Allocate memory (200 MB) and then free it. Super admin only."""
    await asyncio.to_thread(lambda: [bytearray(1024 * 1024) for _ in range(200)])
    return {"status": "Memory stress test completed (200 MB allocated and freed)"}


@router.post("/stress/disk")
async def stress_disk(admin: User = Depends(require_superuser)):
    """Create a 200 MB temporary file and delete it. Super admin only."""

    async def _write():
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"\0" * (200 * 1024 * 1024))
            path = f.name
        os.unlink(path)

    await asyncio.to_thread(_write)
    return {"status": "Disk stress test completed (200 MB written and deleted)"}
