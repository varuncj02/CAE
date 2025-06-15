import chainlit as cl
import asyncio
from typing import Any

from config import ui_config
from api_client import api_client
from utils.logger import logger
from components.user_selector import UserSelector
from components.chat_display import ChatDisplay
from components.side_panel import SidePanel


# Initialize components
user_selector = UserSelector()
chat_display = ChatDisplay()
side_panel = SidePanel()


@cl.on_chat_start
async def on_chat_start():
    """Initialize the chat session"""
    logger.info("New chat session started")

    try:
        # Set up the UI
        cl.user_session.set(
            "components",
            {
                "user_selector": user_selector,
                "chat_display": chat_display,
                "side_panel": side_panel,
            },
        )

        # Initialize side panel if enabled
        if ui_config.show_side_panel:
            await side_panel.setup_panel()

        # Show user selection interface
        await user_selector.show_user_selection()

    except Exception as e:
        logger.error(f"Error in chat start: {e}", exc_info=True)
        await cl.Message(
            content="❌ Failed to initialize chat. Please refresh the page and try again."
        ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming user messages"""
    try:
        # Get current user
        current_user = user_selector.get_current_user()

        if not current_user:
            logger.warning("Message received but no user selected")
            await cl.Message(
                content="⚠️ Please select a user first before sending messages."
            ).send()
            await user_selector.show_user_selection()
            return

        logger.info(
            f"Message received from user {current_user['id']}: {message.content[:50]}..."
        )

        # Process the message
        await chat_display.process_user_message(message.content, current_user)

        # Update analysis panel if enabled
        if ui_config.enable_analysis_panel:
            chat_id = cl.user_session.get("current_chat_id")
            if chat_id:
                # This is a placeholder - future implementation would update the analysis
                await side_panel.update_analysis(chat_id, [])

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        await cl.Message(
            content="❌ An error occurred while processing your message. Please try again."
        ).send()


@cl.action_callback()
async def on_action(action: cl.Action):
    """Handle action button clicks"""
    logger.info(f"Action triggered: {action.name} with value: {action.value}")

    try:
        # User selection actions
        if action.name.startswith("select_user_") or action.name == "create_new_user":
            await user_selector.handle_user_action(action)

        # User management actions
        elif action.name == "switch_user":
            await user_selector.show_user_selection()

        elif action.name == "view_chat_history":
            current_user = user_selector.get_current_user()
            if current_user:
                await chat_display.display_chat_history(current_user["id"])

        # Chat actions
        elif action.name.startswith("load_chat_"):
            chat_id = action.value
            await chat_display.load_chat_session(chat_id)

        elif action.name == "new_chat":
            await chat_display.start_new_chat()

        else:
            logger.warning(f"Unknown action: {action.name}")

        # Remove the action to clean up the UI
        await action.remove()

    except Exception as e:
        logger.error(f"Error handling action {action.name}: {e}", exc_info=True)
        await cl.Message(
            content="❌ An error occurred while processing your action. Please try again."
        ).send()


@cl.on_chat_end
async def on_chat_end():
    """Clean up when chat session ends"""
    logger.info("Chat session ending")

    try:
        # Close API client session
        await api_client.close()
        logger.info("Cleanup completed")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}", exc_info=True)


@cl.on_stop
async def on_stop():
    """Handle when user stops generation"""
    logger.info("User stopped generation")
    # In the future, this could cancel ongoing API requests


@cl.set_chat_profiles
async def chat_profiles():
    """Define chat profiles if needed"""
    # This is a placeholder for future multi-mode support
    return None


# Configure Chainlit settings
@cl.password_auth_callback
def auth_callback(username: str, password: str):
    """Authentication callback (disabled for now)"""
    # Authentication is not implemented in this version
    return None


if __name__ == "__main__":
    logger.info(f"Starting {ui_config.app_name}")
    # Chainlit will handle the server startup
