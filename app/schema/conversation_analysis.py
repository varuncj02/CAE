from datetime import datetime
from typing import Dict, List
from uuid import UUID
from pydantic import BaseModel, Field


class ConversationBranch(BaseModel):
    """Represents a single conversation branch explored by MCTS"""

    response: str = Field(..., description="The potential response for this branch")
    simulated_user_reactions: List[str] = Field(
        ..., description="Possible user reactions to this response"
    )
    eq_score: float = Field(
        ..., description="Emotional intelligence score for this branch"
    )
    sub_history: List[Dict[str, str]] = Field(
        ..., description="Simulated conversation continuation"
    )
    scoring_breakdown: Dict[str, float] = Field(
        ..., description="Detailed scoring breakdown"
    )


class ConversationAnalysisRequest(BaseModel):
    """Request model for conversation analysis"""

    chat_id: UUID = Field(..., description="The chat session to analyze")
    num_branches: int = Field(default=5, description="Number of branches to explore")
    simulation_depth: int = Field(
        default=3, description="How many turns to simulate ahead"
    )


class ConversationAnalysisResponse(BaseModel):
    """Response model for conversation analysis"""

    id: UUID = Field(..., description="Analysis ID")
    chat_id: UUID = Field(..., description="Chat session ID")
    created_at: datetime = Field(..., description="When the analysis was created")
    branches: List[ConversationBranch] = Field(..., description="All explored branches")
    selected_branch_index: int = Field(..., description="Index of the selected branch")
    selected_response: str = Field(..., description="The chosen response")
    analysis: str = Field(
        ..., description="Detailed analysis of why this path was chosen"
    )
    overall_scores: Dict[str, float] = Field(
        ..., description="Aggregated scoring metrics"
    )
