from typing import Any


class LLMException(Exception):
    """Exception raised for errors in LLM operations.

    Attributes:
        message: Explanation of the error
        details: Additional error details or context
    """

    def __init__(self, message: str, details: Any = None):
        self.message = message
        self.details = details
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class ConversationAnalysisException(Exception):
    """Base exception for conversation analysis errors"""

    pass


class ChatHistoryNotFoundError(ConversationAnalysisException):
    """Raised when chat history cannot be found"""

    def __init__(self, chat_id: str):
        self.chat_id = chat_id
        super().__init__(f"No chat history found for chat_id {chat_id}")


class MCTSException(ConversationAnalysisException):
    """Raised when MCTS algorithm encounters an error"""

    pass
