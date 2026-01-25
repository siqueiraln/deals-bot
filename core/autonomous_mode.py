import json
import os
from datetime import datetime

class AutonomousMode:
    def __init__(self, config_path="data/bot_config.json"):
        self.config_path = config_path
        # Ensure data dir exists
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        self.is_autonomous = self._load_config()

    def toggle(self) -> bool:
        """Alterna entre modo manual e autônomo. Retorna novo estado."""
        self.is_autonomous = not self.is_autonomous
        self._save_config()
        return self.is_autonomous
    
    def set_mode(self, autonomous: bool):
        """Define modo explicitamente."""
        self.is_autonomous = autonomous
        self._save_config()
    
    def get_status(self) -> dict:
        """Retorna status atual."""
        return {
            "mode": "Autônomo" if self.is_autonomous else "Manual",
            "description": self._get_mode_description()
        }

    def _get_mode_description(self) -> str:
        if self.is_autonomous:
            return "O bot postará automaticamente ofertas com score alto."
        return "Todas as ofertas requerem aprovação manual."

    def _load_config(self) -> bool:
        if not os.path.exists(self.config_path):
            return False
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get("autonomous_mode", False)
        except Exception:
            return False

    def _save_config(self):
        try:
            data = {
                "autonomous_mode": self.is_autonomous,
                "last_updated": datetime.now().isoformat()
            }
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
