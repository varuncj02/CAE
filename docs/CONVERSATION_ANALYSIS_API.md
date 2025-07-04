# Conversation Analysis API

This document describes the conversation analysis endpoints that use Monte Carlo Tree Search (MCTS) to find optimal conversation paths based on specified goals.

## Overview

The Conversation Analysis API uses an advanced MCTS algorithm to:
- Explore multiple conversation response paths
- Optimize for specific conversation goals (e.g., "feel better", "get constructive criticism", "bounce off ideas")
- Score paths based on both general conversation quality metrics and goal-specific metrics
- Provide detailed analysis of why certain responses are recommended

## Endpoints

### Analyze Conversation
Analyzes a conversation using MCTS to find the optimal response path.

**Endpoint:** `POST /analysis/`

**Request Body:**
```json
{
  "chat_id": "550e8400-e29b-41d4-a716-446655440000",
  "conversation_goal": "help the user feel better",  // Optional
  "num_branches": 5,                                 // Optional, default: 5
  "simulation_depth": 3,                              // Optional, default: 3
  "max_tokens": 250,                                  // Optional, default: 250
  "mcts_iterations": 10,                              // Optional, default: 10
  "exploration_constant": 1.414                       // Optional, default: sqrt(2)
}
```

**Parameters:**
- `chat_id` (required): UUID of the chat session to analyze
- `conversation_goal` (optional): The goal to optimize for (e.g., "feel better", "get constructive criticism", "bounce off ideas")
- `num_branches`: Number of initial response options to explore
- `simulation_depth`: How many conversation turns to simulate ahead
- `max_tokens`: Maximum tokens per LLM response
- `mcts_iterations`: Number of MCTS iterations to perform
- `exploration_constant`: UCB1 exploration parameter (higher = more exploration)

**Response:** `200 OK`
```json
{
  "id": "analysis-uuid",
  "chat_id": "chat-uuid",
  "created_at": "2025-06-16T12:00:00.000Z",
  "conversation_goal": "help the user feel better",
  "branches": [
    {
      "response": "I understand how you're feeling...",
      "simulated_user_reactions": ["Thank you for listening...", "I appreciate that..."],
      "score": 0.87,
      "sub_history": [
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."}
      ],
      "general_metrics": {
        "clarity": 0.85,
        "relevance": 0.9,
        "engagement": 0.8,
        "authenticity": 0.95,
        "coherence": 0.85,
        "respectfulness": 0.9
      },
      "goal_metrics": {
        "empathy": 0.9,
        "validation": 0.85,
        "mood_improvement": 0.8
      },
      "visits": 25,
      "parent_index": null,
      "children_indices": [1, 2]
    }
    // ... more branches
  ],
  "selected_branch_index": 0,
  "selected_response": "I understand how you're feeling...",
  "analysis": "This response was selected because it demonstrates high empathy and validation...",
  "overall_scores": {
    "best_score": 0.87,
    "average_score": 0.75,
    "score_variance": 0.04
  },
  "mcts_statistics": {
    "total_iterations": 10,
    "nodes_created": 45,
    "nodes_evaluated": 120,
    "pruned_branches": 8,
    "parallel_evaluations": 40,
    "average_depth_explored": 2.3
  }
}
```

### Get Conversation Analyses
Retrieves all analyses performed for a specific chat session.

**Endpoint:** `GET /analysis/{chat_id}`

**Response:** `200 OK`
```json
[
  {
    "id": "analysis-uuid",
    "chat_id": "chat-uuid",
    "created_at": "2025-06-16T12:00:00.000Z",
    "conversation_goal": "help the user feel better",
    "branches": [...],
    "selected_branch_index": 0,
    "selected_response": "...",
    "analysis": "...",
    "scores": {...},
    "mcts_statistics": {...}
  }
]
```

## Scoring Metrics

### General Metrics (Applied to All Conversations)
- **clarity**: How clear and understandable the communication is (0.0-1.0)
- **relevance**: How well responses address the conversation context (0.0-1.0)
- **engagement**: Likelihood to maintain user interest and participation (0.0-1.0)
- **authenticity**: How genuine and natural the responses feel (0.0-1.0)
- **coherence**: How well the conversation flows logically (0.0-1.0)
- **respectfulness**: How considerate and appropriate the tone is (0.0-1.0)

### Goal-Specific Metrics (Dynamic Based on Goal)
The system automatically determines 3-5 metrics relevant to the specified goal:

**Example: Goal = "feel better"**
- empathy: Understanding and sharing feelings
- validation: Acknowledging the user's experience
- mood_improvement: Potential to improve emotional state

**Example: Goal = "get constructive criticism"**
- honesty: Direct and truthful feedback
- specificity: Concrete, actionable points
- actionability: Clear steps for improvement
- balance: Mix of positive and critical feedback

**Example: Goal = "bounce off ideas"**
- creativity: Novel perspectives and suggestions
- engagement: Active participation in ideation
- thought_provocation: Stimulating deeper thinking
- build_upon: Expanding on user's ideas

## MCTS Algorithm Details

The system uses a proper Monte Carlo Tree Search implementation with:

1. **Selection**: Uses UCB1 formula to balance exploration vs exploitation
2. **Expansion**: Generates new response options for promising nodes
3. **Simulation**: Runs conversation simulations to estimate outcome quality
4. **Backpropagation**: Updates node statistics up the tree
5. **Pruning**: Removes underperforming branches to focus computation

### MCTS Statistics Explained
- `total_iterations`: Number of MCTS iterations performed
- `nodes_created`: Total nodes created in the search tree
- `nodes_evaluated`: Number of nodes that underwent simulation
- `pruned_branches`: Branches removed due to poor performance
- `parallel_evaluations`: Number of evaluations run in parallel
- `average_depth_explored`: Average depth of tree exploration

## Error Responses

- `400 Bad Request` - Invalid request parameters or chat not found
- `504 Gateway Timeout` - Analysis timed out (try reducing simulation depth or branches)
- `500 Internal Server Error` - Server-side errors

## Example Usage

```bash
# Analyze a conversation with a specific goal
curl -X POST http://localhost:8000/analysis/ \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "550e8400-e29b-41d4-a716-446655440000",
    "conversation_goal": "help the user feel better",
    "num_branches": 5,
    "simulation_depth": 3,
    "mcts_iterations": 15
  }'

# Analyze without a specific goal (general conversation quality)
curl -X POST http://localhost:8000/analysis/ \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "550e8400-e29b-41d4-a716-446655440000"
  }'

# Get all analyses for a chat
curl http://localhost:8000/analysis/550e8400-e29b-41d4-a716-446655440000
```

## Tips for Best Results

1. **Specific Goals**: More specific goals yield better optimization (e.g., "help process grief" vs "feel better")
2. **Iteration Count**: More MCTS iterations generally improve quality but take longer
3. **Simulation Depth**: Deeper simulations provide better long-term optimization
4. **Max Tokens**: Adjust based on expected response length needs
5. **Exploration Constant**: Increase for more diverse exploration, decrease for exploitation of good paths 