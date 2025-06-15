import asyncio
import json
import random
import time
from typing import List, Dict, Tuple
from uuid import UUID
from textwrap import dedent

from ..db.chat import get_chat_history, create_conversation_analysis
from ..schema.llm.message import Message
from ..schema.conversation_analysis import (
    ConversationBranch,
    ConversationAnalysisRequest,
    ConversationAnalysisResponse,
)
from ..services.llm_service import LLMService
from ..utils.config import app_settings
from ..utils.logger import logger


class ConversationAnalysisService:
    """Service for analyzing conversations using MCTS to find high-EQ response paths"""

    def __init__(self):
        # Initialize LLM service with the llm_model variables
        self.llm_service = LLMService(
            base_url=app_settings.LLM_API_BASE_URL,
            api_key=app_settings.LLM_API_KEY,
            model_name=app_settings.LLM_MODEL_NAME,
        )

    async def analyze_conversation(
        self, request: ConversationAnalysisRequest
    ) -> ConversationAnalysisResponse:
        """
        Main entry point for conversation analysis using MCTS
        """
        start_time = time.time()
        logger.info(f"Starting conversation analysis for chat {request.chat_id}")

        # Get chat history
        history = await get_chat_history(request.chat_id)
        if not history:
            raise ValueError(f"No chat history found for chat_id {request.chat_id}")

        logger.info(
            "Chat history retrieved",
            extra={
                "chat_id": str(request.chat_id),
                "message_count": len(history),
                "last_message_role": history[-1].role.value if history else None,
            },
        )

        # Convert to LLM messages
        messages = [
            Message(role=msg.role.value, content=msg.content) for msg in history
        ]

        # Generate initial response branches
        logger.info("Step 1/4: Generating initial response branches")
        step_start = time.time()
        branches = await self._generate_initial_branches(messages, request.num_branches)
        logger.info(f"Step 1/4 completed in {time.time() - step_start:.2f} seconds")

        # Run MCTS to evaluate and score branches
        logger.info("Step 2/4: Running MCTS evaluation")
        step_start = time.time()
        scored_branches = await self._run_mcts(
            messages, branches, request.simulation_depth
        )
        logger.info(f"Step 2/4 completed in {time.time() - step_start:.2f} seconds")

        # Select best branch
        logger.info("Step 3/4: Selecting best branch and generating analysis")
        step_start = time.time()
        best_branch_idx, analysis = await self._select_best_branch(
            scored_branches, messages
        )
        logger.info(f"Step 3/4 completed in {time.time() - step_start:.2f} seconds")

        # Prepare response
        logger.info("Step 4/4: Preparing response and storing results")
        step_start = time.time()
        branch_dicts = [
            {
                "response": b.response,
                "simulated_user_reactions": b.simulated_user_reactions,
                "eq_score": b.eq_score,
                "sub_history": b.sub_history,
                "scoring_breakdown": b.scoring_breakdown,
            }
            for b in scored_branches
        ]

        # Store analysis in database
        db_result = await create_conversation_analysis(
            chat_id=request.chat_id,
            branches=branch_dicts,
            selected_branch_index=best_branch_idx,
            selected_response=scored_branches[best_branch_idx].response,
            analysis=analysis,
            scores={
                "overall_eq_score": max(b.eq_score for b in scored_branches),
                "average_eq_score": sum(b.eq_score for b in scored_branches)
                / len(scored_branches),
            },
        )

        total_time = time.time() - start_time
        logger.info(
            f"Conversation analysis completed in {total_time:.2f} seconds",
            extra={
                "chat_id": str(request.chat_id),
                "total_time_seconds": total_time,
                "selected_branch": best_branch_idx,
                "best_score": scored_branches[best_branch_idx].eq_score,
            },
        )

        return ConversationAnalysisResponse(
            id=db_result["id"],
            chat_id=db_result["chat_id"],
            created_at=db_result["created_at"],
            branches=scored_branches,
            selected_branch_index=best_branch_idx,
            selected_response=scored_branches[best_branch_idx].response,
            analysis=analysis,
            overall_scores=db_result["scores"],
        )

    async def _generate_initial_branches(
        self, messages: List[Message], num_branches: int
    ) -> List[str]:
        """Generate diverse initial response branches"""

        logger.info(
            "Generating initial response branches",
            extra={
                "num_branches": num_branches,
                "conversation_length": len(messages),
            },
        )

        prompt = Message(
            role="system",
            content=dedent("""
                <task>
                You are an expert conversationalist with high emotional intelligence.
                Generate diverse, emotionally intelligent responses to continue this conversation.
                </task>
                
                <requirements>
                - Generate exactly {num_branches} different response options
                - Each response should demonstrate different aspects of emotional intelligence:
                  1. Empathetic understanding
                  2. Active listening and validation
                  3. Thoughtful questioning
                  4. Supportive encouragement
                  5. Balanced perspective offering
                - Responses should be natural, warm, and engaging
                - Consider the emotional context and needs of the conversation
                - Vary the tone, approach, and focus of each response
                </requirements>
                
                <output_format>
                Return a JSON object with this structure:
                {{
                    "responses": [
                        "First response option...",
                        "Second response option...",
                        ...
                    ]
                }}
                </output_format>
            """).format(num_branches=num_branches),
        )

        result = await self.llm_service.query_llm(
            messages=[prompt] + messages, json_response=True
        )

        logger.info(
            "Initial branches generated successfully",
            extra={
                "branches_count": len(result.get("responses", [])),
                "branch_previews": [
                    resp[:50] + "..." for resp in result.get("responses", [])[:3]
                ],
            },
        )

        return result["responses"]

    async def _run_mcts(
        self,
        base_messages: List[Message],
        initial_branches: List[str],
        simulation_depth: int,
    ) -> List[ConversationBranch]:
        """Run MCTS to evaluate branches"""

        logger.info(
            "Starting MCTS evaluation of branches",
            extra={
                "num_branches": len(initial_branches),
                "simulation_depth": simulation_depth,
                "base_conversation_length": len(base_messages),
            },
        )

        # Process branches in parallel
        tasks = [
            self._evaluate_branch(base_messages, branch, simulation_depth, idx)
            for idx, branch in enumerate(initial_branches)
        ]

        scored_branches = await asyncio.gather(*tasks)

        logger.info(
            "MCTS evaluation completed",
            extra={
                "branches_evaluated": len(scored_branches),
                "scores": [b.eq_score for b in scored_branches],
                "best_score": max(b.eq_score for b in scored_branches),
                "average_score": sum(b.eq_score for b in scored_branches)
                / len(scored_branches),
            },
        )

        return scored_branches

    async def _evaluate_branch(
        self,
        base_messages: List[Message],
        response: str,
        simulation_depth: int,
        branch_idx: int = 0,
    ) -> ConversationBranch:
        """Evaluate a single branch by simulating conversation continuation"""

        logger.info(
            f"Evaluating branch {branch_idx + 1}",
            extra={
                "branch_index": branch_idx,
                "response_preview": response[:100] + "...",
                "simulation_depth": simulation_depth,
            },
        )

        # Add the potential response to messages
        extended_messages = base_messages + [
            Message(role="assistant", content=response)
        ]

        # Simulate user reactions and conversation continuation
        simulation_prompt = Message(
            role="system",
            content=dedent("""
                <task>
                Simulate how a conversation might continue after the assistant's response.
                Consider various realistic user reactions and emotional responses.
                </task>
                
                <simulation_depth>{depth}</simulation_depth>
                
                <requirements>
                - Generate 3 possible user reactions (varied emotional tones)
                - For each reaction, simulate {depth} back-and-forth exchanges
                - Consider emotional dynamics and conversation flow
                - Be realistic about human emotional responses
                </requirements>
                
                <output_format>
                {{
                    "user_reactions": [
                        "Possible user reaction 1",
                        "Possible user reaction 2", 
                        "Possible user reaction 3"
                    ],
                    "simulated_conversations": [
                        [
                            {{"role": "user", "content": "..."}},
                            {{"role": "assistant", "content": "..."}},
                            ...
                        ],
                        [...],
                        [...]
                    ]
                }}
                </output_format>
            """).format(depth=simulation_depth),
        )

        logger.debug(
            f"Branch {branch_idx + 1}: Simulating user reactions",
            extra={
                "branch_index": branch_idx,
                "extended_conversation_length": len(extended_messages),
            },
        )

        simulation_result = await self.llm_service.query_llm(
            messages=[simulation_prompt] + extended_messages, json_response=True
        )

        logger.debug(
            f"Branch {branch_idx + 1}: User reactions simulated",
            extra={
                "branch_index": branch_idx,
                "num_reactions": len(simulation_result.get("user_reactions", [])),
                "num_simulations": len(
                    simulation_result.get("simulated_conversations", [])
                ),
            },
        )

        # Score the branch
        logger.debug(
            f"Branch {branch_idx + 1}: Starting scoring",
            extra={"branch_index": branch_idx},
        )

        scoring_result = await self._score_conversation_branch(
            extended_messages, simulation_result, branch_idx
        )

        logger.info(
            f"Branch {branch_idx + 1}: Scoring completed",
            extra={
                "branch_index": branch_idx,
                "overall_score": scoring_result["overall_score"],
                "best_simulation": scoring_result["best_simulation_index"],
                "scoring_breakdown": scoring_result["breakdown"],
            },
        )

        # Take the best simulated path
        best_sim_idx = scoring_result["best_simulation_index"]
        sub_history = simulation_result["simulated_conversations"][best_sim_idx]

        return ConversationBranch(
            response=response,
            simulated_user_reactions=simulation_result["user_reactions"],
            eq_score=scoring_result["overall_score"],
            sub_history=sub_history,
            scoring_breakdown=scoring_result["breakdown"],
        )

    async def _score_conversation_branch(
        self, messages: List[Message], simulation_data: Dict, branch_idx: int = 0
    ) -> Dict:
        """Score a conversation branch based on EQ factors"""

        scoring_prompt = Message(
            role="system",
            content=dedent("""
                <task>
                Analyze and score this conversation branch for emotional intelligence quality.
                </task>
                
                <scoring_criteria>
                1. Empathy (0-1): How well does the response demonstrate understanding of emotions?
                2. Active_Listening (0-1): Does it show the speaker was heard and understood?
                3. Emotional_Awareness (0-1): Recognition and appropriate response to emotional cues
                4. Supportiveness (0-1): Providing appropriate emotional support
                5. Engagement_Quality (0-1): Likelihood of positive continued engagement
                6. Conflict_Resolution (0-1): Ability to navigate tensions constructively
                7. Authenticity (0-1): Genuine and natural communication style
                8. Growth_Facilitation (0-1): Helping the conversation partner develop/learn
                </scoring_criteria>
                
                <analysis_data>
                {simulation_data}
                </analysis_data>
                
                <output_format>
                {{
                    "breakdown": {{
                        "empathy": 0.85,
                        "active_listening": 0.9,
                        "emotional_awareness": 0.8,
                        "supportiveness": 0.75,
                        "engagement_quality": 0.85,
                        "conflict_resolution": 0.7,
                        "authenticity": 0.9,
                        "growth_facilitation": 0.8
                    }},
                    "overall_score": 0.83,
                    "best_simulation_index": 0,
                    "reasoning": "Brief explanation of the scoring..."
                }}
                </output_format>
            """).format(simulation_data=json.dumps(simulation_data)),
        )

        result = await self.llm_service.query_llm(
            messages=[scoring_prompt] + messages, json_response=True
        )

        return result

    async def _select_best_branch(
        self, branches: List[ConversationBranch], original_messages: List[Message]
    ) -> Tuple[int, str]:
        """Select the best branch and generate analysis"""

        logger.info(
            "Selecting best branch from MCTS results",
            extra={
                "num_branches": len(branches),
                "all_scores": [(i, b.eq_score) for i, b in enumerate(branches)],
            },
        )

        # Sort branches by score
        indexed_branches = [(i, b) for i, b in enumerate(branches)]
        indexed_branches.sort(key=lambda x: x[1].eq_score, reverse=True)

        best_idx = indexed_branches[0][0]

        logger.info(
            "Best branch selected",
            extra={
                "selected_index": best_idx,
                "selected_score": branches[best_idx].eq_score,
                "score_difference": branches[best_idx].eq_score
                - indexed_branches[1][1].eq_score
                if len(indexed_branches) > 1
                else 0,
            },
        )

        logger.debug("Generating detailed analysis for selected branch")

        # Generate detailed analysis
        analysis_prompt = Message(
            role="system",
            content=dedent("""
                <task>
                Provide a detailed analysis of why the selected response is the best choice
                for continuing this conversation with high emotional intelligence.
                </task>
                
                <selected_response>
                {selected}
                </selected_response>
                
                <all_options>
                {all_branches}
                </all_options>
                
                <requirements>
                - Explain the emotional dynamics at play
                - Highlight what makes the selected response superior
                - Discuss potential positive outcomes
                - Note any risks that were avoided
                - Be specific about EQ factors demonstrated
                - Keep analysis concise but insightful (2-3 paragraphs)
                </requirements>
            """).format(
                selected=branches[best_idx].response,
                all_branches=json.dumps(
                    [
                        {
                            "response": b.response,
                            "score": b.eq_score,
                            "key_strengths": max(
                                b.scoring_breakdown.items(), key=lambda x: x[1]
                            ),
                        }
                        for b in branches
                    ],
                    indent=2,
                ),
            ),
        )

        analysis_response = await self.llm_service.query_llm(
            messages=[analysis_prompt] + original_messages, json_response=False
        )

        return best_idx, analysis_response.content
