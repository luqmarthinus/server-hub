import os
import httpx
from loguru import logger

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")


async def send_slack_alert(metric: str, value: float, threshold: float):
    if not SLACK_WEBHOOK_URL:
        logger.warning("SLACK_WEBHOOK_URL not set, skipping alert")
        return
    message = f":warning: Server Hub Alert\n*{metric}* is at {value:.1f}% (threshold {threshold}%)"
    async with httpx.AsyncClient() as client:
        try:
            await client.post(SLACK_WEBHOOK_URL, json={"text": message})
            logger.info(f"Alert sent to Slack for {metric}")
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")


async def check_and_alert(cpu: float, memory: float, disk: float):
    cpu_threshold = float(os.getenv("ALERT_CPU_THRESHOLD", "80"))
    mem_threshold = float(os.getenv("ALERT_MEMORY_THRESHOLD", "90"))
    disk_threshold = float(os.getenv("ALERT_DISK_THRESHOLD", "90"))
    if cpu >= cpu_threshold:
        await send_slack_alert("CPU usage", cpu, cpu_threshold)
    if memory >= mem_threshold:
        await send_slack_alert("Memory usage", memory, mem_threshold)
    if disk >= disk_threshold:
        await send_slack_alert("Disk usage", disk, disk_threshold)
