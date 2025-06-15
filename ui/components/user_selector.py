import chainlit as cl
from datetime import datetime

from ..api_client import api_client, APIError
from ..utils.logger import logger


class UserSelector:
    """Component for user selection and management"""

    def __init__(self):
        self.current_user = None
        self.users = []
        logger.info("UserSelector component initialized")

    async def show_user_selection(self):
        """Display user selection interface"""
        try:
            # Fetch current users
            self.users = await api_client.list_users()
            logger.info(f"Fetched {len(self.users)} users")

            # Create action buttons for existing users
            actions = []

            # Add create new user button
            actions.append(
                cl.Action(
                    name="create_new_user",
                    value="create_new",
                    label="➕ Create New User",
                    description="Create a new user account",
                )
            )

            # Add buttons for existing users
            for user in self.users:
                created_date = datetime.fromisoformat(
                    user["created_at"].replace("Z", "+00:00")
                )
                formatted_date = created_date.strftime("%b %d, %Y")

                actions.append(
                    cl.Action(
                        name=f"select_user_{user['id']}",
                        value=user["id"],
                        label=f"👤 {user['name']}",
                        description=f"Created on {formatted_date}",
                    )
                )

            # Send the actions to the user
            await cl.Message(
                content="👋 Welcome to AGI House Chat!\n\nPlease select a user or create a new one:",
                actions=actions,
            ).send()

            logger.info("User selection interface displayed")

        except APIError as e:
            logger.error(f"Failed to fetch users: {e}")
            await cl.Message(
                content=f"❌ Failed to load users: {e.message}\n\nPlease check if the backend is running."
            ).send()
        except Exception as e:
            logger.error(f"Unexpected error in user selection: {e}", exc_info=True)
            await cl.Message(
                content="❌ An unexpected error occurred. Please refresh the page."
            ).send()

    async def handle_user_action(self, action):
        """Handle user selection action"""
        try:
            if action.value == "create_new":
                await self.prompt_new_user()
            else:
                # User selected an existing user
                user_id = action.value
                user = next((u for u in self.users if u["id"] == user_id), None)

                if user:
                    await self.set_current_user(user)
                else:
                    logger.error(f"User not found: {user_id}")
                    await cl.Message(
                        content="❌ User not found. Please try again."
                    ).send()
                    await self.show_user_selection()

        except Exception as e:
            logger.error(f"Error handling user action: {e}", exc_info=True)
            await cl.Message(content="❌ An error occurred. Please try again.").send()

    async def prompt_new_user(self):
        """Prompt for new user creation"""
        res = await cl.AskUserMessage(content="What's your name?", timeout=60).send()

        if res:
            await self.create_user(res["output"])
        else:
            await cl.Message(
                content="⏰ User creation timed out. Please try again."
            ).send()
            await self.show_user_selection()

    async def create_user(self, name: str):
        """Create a new user"""
        try:
            if not name or not name.strip():
                await cl.Message(
                    content="❌ Name cannot be empty. Please try again."
                ).send()
                await self.prompt_new_user()
                return

            name = name.strip()
            logger.info(f"Creating new user: {name}")

            # Show loading message
            msg = cl.Message(content=f"Creating user '{name}'...")
            await msg.send()

            # Create user via API
            new_user = await api_client.create_user(name)
            logger.info(f"User created successfully: {new_user['id']}")

            # Update the message
            msg.content = f"✅ User '{name}' created successfully!"
            await msg.update()

            # Set as current user
            await self.set_current_user(new_user)

        except APIError as e:
            logger.error(f"Failed to create user: {e}")
            await cl.Message(content=f"❌ Failed to create user: {e.message}").send()
            await self.show_user_selection()
        except Exception as e:
            logger.error(f"Unexpected error creating user: {e}", exc_info=True)
            await cl.Message(
                content="❌ An unexpected error occurred. Please try again."
            ).send()
            await self.show_user_selection()

    async def set_current_user(self, user: dict):
        """Set the current user and update session"""
        self.current_user = user
        cl.user_session.set("current_user", user)
        cl.user_session.set("current_chat_id", None)

        logger.info(f"Current user set to: {user['id']} ({user['name']})")

        await cl.Message(
            content=f"✅ Logged in as **{user['name']}**\n\n💬 Start typing to begin a new conversation!",
            actions=[
                cl.Action(
                    name="switch_user",
                    value="switch",
                    label="🔄 Switch User",
                    description="Select a different user",
                ),
                cl.Action(
                    name="view_chat_history",
                    value="history",
                    label="📜 View Chat History",
                    description="View your previous conversations",
                ),
            ],
        ).send()

    def get_current_user(self) -> dict:
        """Get the current user from session"""
        return cl.user_session.get("current_user")
