import chainlit as cl
from datetime import datetime

from ..api_client import api_client, APIError
from ..utils.logger import logger
from ..config import ui_config


class ChatDisplay:
    """Component for displaying chat messages and managing chat history"""

    def __init__(self):
        logger.info("ChatDisplay component initialized")

    async def display_chat_history(self, user_id: str):
        """Display user's chat history"""
        try:
            logger.info(f"Fetching chat history for user: {user_id}")
            chats = await api_client.get_user_chats(user_id)

            if not chats:
                await cl.Message(
                    content="📭 You don't have any chat history yet. Start a new conversation!"
                ).send()
                return

            # Format chat list
            content = "📜 **Your Chat History**\n\n"
            actions = []

            for i, chat in enumerate(chats):
                created_date = datetime.fromisoformat(
                    chat["created_at"].replace("Z", "+00:00")
                )
                formatted_date = created_date.strftime("%b %d, %Y at %I:%M %p")

                content += f"{i + 1}. Chat from {formatted_date}\n"

                actions.append(
                    cl.Action(
                        name=f"load_chat_{chat['id']}",
                        value=chat["id"],
                        label=f"💬 Load Chat {i + 1}",
                        description=f"From {formatted_date}",
                    )
                )

            content += (
                "\nSelect a chat to load or start typing to begin a new conversation."
            )

            await cl.Message(content=content, actions=actions).send()

            logger.info(f"Displayed {len(chats)} chats for user")

        except APIError as e:
            logger.error(f"Failed to fetch chat history: {e}")
            await cl.Message(
                content=f"❌ Failed to load chat history: {e.message}"
            ).send()
        except Exception as e:
            logger.error(
                f"Unexpected error displaying chat history: {e}", exc_info=True
            )
            await cl.Message(
                content="❌ An unexpected error occurred while loading chat history."
            ).send()

    async def load_chat_session(self, chat_id: str):
        """Load and display a specific chat session"""
        try:
            logger.info(f"Loading chat session: {chat_id}")

            # Show loading message
            loading_msg = cl.Message(content="Loading chat history...")
            await loading_msg.send()

            # Fetch chat history
            messages = await api_client.get_chat_history(chat_id)

            # Remove loading message
            await loading_msg.remove()

            # Display header
            await cl.Message(
                content="📂 **Chat History Loaded**\n\n---", disable_feedback=True
            ).send()

            # Display messages
            for msg in messages:
                created_date = datetime.fromisoformat(
                    msg["created_at"].replace("Z", "+00:00")
                )

                if ui_config.show_timestamps:
                    timestamp = created_date.strftime("%I:%M %p")
                    author = "You" if msg["role"] == "user" else "Assistant"

                    await cl.Message(
                        content=msg["content"],
                        author=f"{author} • {timestamp}",
                        disable_feedback=(msg["role"] == "user"),
                    ).send()
                else:
                    await cl.Message(
                        content=msg["content"],
                        author="You" if msg["role"] == "user" else "Assistant",
                        disable_feedback=(msg["role"] == "user"),
                    ).send()

            # Set current chat in session
            cl.user_session.set("current_chat_id", chat_id)

            await cl.Message(
                content="---\n\n✅ Chat history loaded. You can continue this conversation or start a new one.",
                actions=[
                    cl.Action(
                        name="new_chat",
                        value="new",
                        label="🆕 Start New Chat",
                        description="Begin a fresh conversation",
                    )
                ],
                disable_feedback=True,
            ).send()

            logger.info(f"Loaded {len(messages)} messages from chat {chat_id}")

        except APIError as e:
            logger.error(f"Failed to load chat session: {e}")
            await loading_msg.remove()
            await cl.Message(content=f"❌ Failed to load chat: {e.message}").send()
        except Exception as e:
            logger.error(f"Unexpected error loading chat session: {e}", exc_info=True)
            await loading_msg.remove()
            await cl.Message(
                content="❌ An unexpected error occurred while loading the chat."
            ).send()

    async def process_user_message(self, message: str, user: dict):
        """Process and display user message with AI response"""
        try:
            # Validate message
            if not message or not message.strip():
                return

            if len(message) > ui_config.max_message_length:
                await cl.Message(
                    content=f"❌ Message too long. Maximum length is {ui_config.max_message_length} characters."
                ).send()
                return

            # Get current chat ID from session
            chat_id = cl.user_session.get("current_chat_id")

            logger.info(
                f"Processing message for user {user['id']}",
                extra={"chat_id": chat_id, "message_length": len(message)},
            )

            # Show thinking message
            thinking_msg = cl.Message(content="🤔 Thinking...")
            await thinking_msg.send()

            # Send message to API
            chat_messages = await api_client.send_message(
                user_id=user["id"], message=message, chat_id=chat_id
            )

            # Remove thinking message
            await thinking_msg.remove()

            # If this was a new chat, update the session
            if not chat_id and chat_messages:
                new_chat_id = chat_messages[0]["chat_id"]
                cl.user_session.set("current_chat_id", new_chat_id)
                logger.info(f"New chat created: {new_chat_id}")

            # Find and display the assistant's response
            # The API returns the full chat history, so we need the last assistant message
            assistant_messages = [
                msg for msg in chat_messages if msg["role"] == "assistant"
            ]
            if assistant_messages:
                last_assistant_msg = assistant_messages[-1]

                if ui_config.show_timestamps:
                    created_date = datetime.fromisoformat(
                        last_assistant_msg["created_at"].replace("Z", "+00:00")
                    )
                    timestamp = created_date.strftime("%I:%M %p")
                    author = f"Assistant • {timestamp}"
                else:
                    author = "Assistant"

                await cl.Message(
                    content=last_assistant_msg["content"], author=author
                ).send()
            else:
                logger.warning("No assistant response received")
                await cl.Message(
                    content="⚠️ No response received from the assistant. Please try again."
                ).send()

        except APIError as e:
            logger.error(f"API error processing message: {e}")
            await thinking_msg.remove()

            error_msg = "❌ Failed to send message"
            if e.status_code == 500:
                error_msg += ": Server error. Please try again."
            elif e.status_code == 422:
                error_msg += ": Invalid message format."
            else:
                error_msg += f": {e.message}"

            await cl.Message(content=error_msg).send()

        except Exception as e:
            logger.error(f"Unexpected error processing message: {e}", exc_info=True)
            try:
                await thinking_msg.remove()
            except:
                pass
            await cl.Message(
                content="❌ An unexpected error occurred. Please try again."
            ).send()

    async def start_new_chat(self):
        """Start a new chat session"""
        cl.user_session.set("current_chat_id", None)
        await cl.Message(
            content="🆕 Started a new chat session. Send a message to begin!",
            disable_feedback=True,
        ).send()
        logger.info("Started new chat session")
