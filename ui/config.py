import os
from dataclasses import dataclass


@dataclass
class UIConfig:
    """Configuration for the Chainlit UI application"""

    # API Configuration
    api_base_url: str = os.getenv("API_BASE_URL", "http://localhost:8000")
    api_timeout: int = int(os.getenv("API_TIMEOUT", "30"))

    # UI Configuration
    app_name: str = "AGI House Chat"
    welcome_message: str = (
        "Welcome to AGI House Chat! Please select or create a user to start chatting."
    )

    # Layout Configuration
    show_side_panel: bool = True
    side_panel_width: int = 300

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = "logs/chainlit_ui.log"

    # Chat Configuration
    max_message_length: int = 10000
    show_timestamps: bool = True

    # Feature Flags
    enable_chat_history: bool = True
    enable_user_switching: bool = True
    enable_analysis_panel: bool = True


ui_config = UIConfig()
