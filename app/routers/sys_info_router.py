from fastapi import APIRouter
import psutil

sys_info_router = APIRouter()

@sys_info_router.get("/system-info")
async def get_system_info():
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    cpu_percent = psutil.cpu_percent(interval=1)

    return {
        "cpu_usage_percent": f"{cpu_percent}%",
        "memory_usage": {
            "total": f"{memory.total / 1_073_741_824:.2f} GB",
            "used": f"{memory.used / 1_073_741_824:.2f} GB",
            "available": f"{memory.available / 1_073_741_824:.2f} GB",
            "usage_percent": f"{memory.percent}%",
        },
        "disk_usage": {
            "total": f"{disk.total / 1_073_741_824:.2f} GB",
            "used": f"{disk.used / 1_073_741_824:.2f} GB",
            "free": f"{disk.free / 1_073_741_824:.2f} GB",
            "usage_percent": f"{disk.percent}%",
        },
    }
