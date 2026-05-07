import platform
import psutil
import sys
from fastapi import APIRouter, Depends
from src.api.auth import get_current_user
from src.models.user import User

router = APIRouter(prefix="/api/v1/system", tags=["system"])


@router.get("/info")
async def get_system_info(current_user: User = Depends(get_current_user)):
    """
    Returns system information: hostname, OS, Python version, CPU cores,
    memory total/used/percent, disk total/used/free/percent.
    """
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    return {
        "hostname": platform.node(),
        "system": platform.system(),
        "release": platform.release(),
        "python_version": sys.version.split()[0],
        "cpu_cores": psutil.cpu_count(logical=True),
        "memory_total_gb": round(mem.total / (1024 ** 3), 2),
        "memory_used_gb": round(mem.used / (1024 ** 3), 2),
        "memory_percent": mem.percent,
        "disk_total_gb": round(disk.total / (1024 ** 3), 2),
        "disk_used_gb": round(disk.used / (1024 ** 3), 2),
        "disk_free_gb": round(disk.free / (1024 ** 3), 2),
        "disk_percent": disk.percent,
    }