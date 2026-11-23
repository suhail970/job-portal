import httpx
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from app.core.config import settings

logger = logging.getLogger("skillbridge.telegram")

class TelegramWorker:
    """
    Asynchronous Telegram Notification Worker for SkillBridge AI.
    Dispatches real-time recruitment drive alerts, countdown reminders,
    and placement results to institutional Telegram channels and student groups.
    """

    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None

    def format_drive_alert(self, drive: Dict[str, Any], college_name: str = "Anna University CEG") -> str:
        drive_date_str = str(drive.get("drive_date", ""))[:10]
        deadline_str = str(drive.get("registration_deadline", ""))[:10]

        message = (
            f"🎓 *CAMPUS PLACEMENT ALERT — {college_name.upper()}*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏢 *Company*: {drive.get('company_name')}\n"
            f"💼 *Role*: {drive.get('role_title')}\n"
            f"💰 *Package*: {drive.get('salary_package', 'Not Disclosed')}\n"
            f"📍 *Location*: {drive.get('location', 'Pan India')}\n"
            f"🎯 *Eligibility*: Min CGPA {drive.get('min_cgpa', 6.0)} | Max Arrears {drive.get('max_arrears', 0)}\n"
            f"📚 *Eligible Branches*: {drive.get('allowed_departments', 'All Branches')}\n"
            f"📅 *Drive Date*: {drive_date_str}\n"
            f"⏰ *Apply By*: {deadline_str}\n\n"
            f"⚡ *Action Required*:\n"
            f"1. Login to SkillBridge AI Portal\n"
            f"2. Check ATS Resume Score & Skill Gaps\n"
            f"3. Start your 1-Day / 3-Day Countdown Prep Sprint & Voice Mock Interview!\n\n"
            f"🔗 *Portal*: http://localhost:3000/student"
        )
        return message

    async def broadcast_drive_alert(
        self,
        drive: Dict[str, Any],
        college_name: str = "Anna University CEG",
        chat_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Broadcasts drive announcement. If live bot token exists, calls Telegram API;
        otherwise runs high-fidelity local simulation with zero external dependencies.
        """
        message_text = self.format_drive_alert(drive, college_name)
        target_chat = chat_id or "@SkillBridgeAlertsDemo"

        if self.bot_token:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    payload = {
                        "chat_id": target_chat,
                        "text": message_text,
                        "parse_mode": "Markdown"
                    }
                    response = await client.post(f"{self.base_url}/sendMessage", json=payload)
                    res_data = response.json()
                    if response.is_success:
                        logger.info(f"Telegram alert sent successfully to {target_chat}")
                        return {
                            "status": "SENT",
                            "mode": "LIVE_TELEGRAM_API",
                            "target_channel": target_chat,
                            "message_preview": message_text,
                            "telegram_response": res_data
                        }
                    else:
                        logger.warning(f"Telegram API error: {res_data}")
                        return {
                            "status": "FAILED",
                            "mode": "LIVE_TELEGRAM_API",
                            "error": res_data.get("description", "Unknown Telegram error"),
                            "message_preview": message_text
                        }
            except Exception as e:
                logger.error(f"Telegram network exception: {e}")

        # Local Zero-Cost Simulation Mode
        logger.info(f"[TELEGRAM SIMULATION] Alert generated for {drive.get('company_name')} -> {target_chat}")
        return {
            "status": "SIMULATED_SUCCESS",
            "mode": "DEMO_SIMULATION (Zero-Cost Mode)",
            "target_channel": target_chat,
            "message_preview": message_text,
            "note": "Configure TELEGRAM_BOT_TOKEN in .env for live channel broadcasting."
        }

telegram_worker = TelegramWorker()

