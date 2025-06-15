import aiohttp
import asyncio
from typing import Any
from uuid import UUID
import json

from config import ui_config
from utils.logger import logger


class APIError(Exception):
    """Custom exception for API errors"""

    def __init__(self, message: str, status_code: int = None, details: Any = None):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


class APIClient:
    """Client for interacting with the FastAPI backend"""

    def __init__(self):
        self.base_url = ui_config.api_base_url
        self.timeout = aiohttp.ClientTimeout(total=ui_config.api_timeout)
        self._session = None
        logger.info(f"API Client initialized with base URL: {self.base_url}")

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=self.timeout, headers={"Content-Type": "application/json"}
            )
        return self._session

    async def close(self):
        """Close the aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.debug("API client session closed")

    async def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Make HTTP request to the API"""
        url = f"{self.base_url}{endpoint}"

        logger.debug(
            f"Making {method} request to {url}",
            extra={
                "method": method,
                "endpoint": endpoint,
                "params": kwargs.get("params"),
                "data": kwargs.get("json"),
            },
        )

        try:
            session = await self._get_session()
            async with session.request(method, url, **kwargs) as response:
                response_text = await response.text()

                if response.status >= 400:
                    logger.error(f"API error: {response.status} - {response_text}")
                    raise APIError(
                        f"API request failed: {response.status}",
                        status_code=response.status,
                        details=response_text,
                    )

                if response_text:
                    data = json.loads(response_text)
                    logger.debug(
                        f"API response: {response.status}", extra={"data": data}
                    )
                    return data

                return None

        except aiohttp.ClientError as e:
            logger.error(f"Network error during API request: {e}")
            raise APIError(f"Network error: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse API response: {e}")
            raise APIError(f"Invalid JSON response: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during API request: {e}", exc_info=True)
            raise APIError(f"Unexpected error: {str(e)}")

    # User endpoints

    async def create_user(self, name: str) -> dict:
        """Create a new user"""
        logger.info(f"Creating user: {name}")
        return await self._request("POST", "/users/", json={"name": name})

    async def list_users(self) -> list:
        """Get all users"""
        logger.info("Fetching all users")
        return await self._request("GET", "/users/")

    async def get_user(self, user_id: str) -> dict:
        """Get a specific user"""
        logger.info(f"Fetching user: {user_id}")
        return await self._request("GET", f"/users/{user_id}")

    async def delete_user(self, user_id: str):
        """Delete a user"""
        logger.info(f"Deleting user: {user_id}")
        await self._request("DELETE", f"/users/{user_id}")

    async def get_user_chats(self, user_id: str) -> list:
        """Get all chats for a user"""
        logger.info(f"Fetching chats for user: {user_id}")
        return await self._request("GET", f"/users/{user_id}/chats")

    # Chat endpoints

    async def send_message(
        self, user_id: str, message: str, chat_id: str = None
    ) -> list:
        """Send a message to the chat"""
        logger.info(
            f"Sending message for user {user_id}",
            extra={
                "chat_id": chat_id,
                "message_preview": message[:100] + "..."
                if len(message) > 100
                else message,
            },
        )

        return await self._request(
            "POST",
            "/chats/",
            json={"user_id": user_id, "message": message, "chat_id": chat_id},
        )

    async def get_chat_history(self, chat_id: str) -> list:
        """Get chat history"""
        logger.info(f"Fetching chat history: {chat_id}")
        return await self._request("GET", f"/chats/{chat_id}")

    async def delete_chat(self, chat_id: str):
        """Delete a chat session"""
        logger.info(f"Deleting chat: {chat_id}")
        await self._request("DELETE", f"/chats/{chat_id}")


# Global API client instance
api_client = APIClient()
