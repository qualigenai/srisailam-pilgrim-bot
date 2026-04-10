import datetime
import json
import os
import logging

logger = logging.getLogger("uvicorn.error")


class AWPAuditor:
    def __init__(self, session_id):
        self.session_id = session_id
        self.logs = []

        # 1. HARD-CODED PROJECT ROOT PATH
        # This reaches up from app/utils/ to the main project folder
        current_file = os.path.abspath(__file__)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
        self.log_dir = os.path.join(project_root, "audit_logs")

        # 2. FORCE FOLDER CREATION
        if not os.path.exists(self.log_dir):
            try:
                os.makedirs(self.log_dir, exist_ok=True)
                logger.warning(f"!!! [AWP SYSTEM] FOLDER CREATED AT: {self.log_dir}")
            except Exception as e:
                logger.error(f"!!! [AWP SYSTEM] FOLDER FAILED: {str(e)}")

    def log_step(self, role, agent_id, action, output):
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "role": role,
            "agent_id": agent_id,
            "action": action,
            "output_preview": str(output)[:200]
        }
        self.logs.append(entry)
        logger.warning(f"[AWP AUDIT] {role} | {action}")

    def save_audit_log(self):
        """Finalizes and saves the log."""
        if not self.logs:
            return

        # Sanitize filename for Windows (remove special chars)
        safe_id = "".join(x for x in str(self.session_id) if x.isalnum())
        filename = os.path.join(self.log_dir, f"audit_{safe_id}.json")

        try:
            data = []
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                    except:
                        data = []

            data.append({
                "time": datetime.datetime.now().isoformat(),
                "steps": self.logs
            })

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            logger.warning(f"!!! [AWP SUCCESS] LOG SAVED: {filename}")
        except Exception as e:
            logger.error(f"!!! [AWP ERROR] SAVE FAILED: {str(e)}")