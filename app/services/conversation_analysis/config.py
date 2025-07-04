from dataclasses import dataclass


@dataclass
class MCTSConfig:
    """Configuration for MCTS algorithm"""

    DEFAULT_MAX_CHILDREN = 3
    DEFAULT_EXPLORATION_CONSTANT = 1.414
    PRUNING_INTERVAL = 5
    PRUNING_THRESHOLD_RATIO = 0.7
    MIN_VISITS_FOR_PRUNING = 5


@dataclass
class ScoringConfig:
    """Configuration for scoring and evaluation"""

    SCORE_WEIGHT_QUALITY = 0.7
    SCORE_WEIGHT_VISITS = 0.3

    GENERAL_METRICS = [
        "clarity",
        "relevance",
        "engagement",
        "authenticity",
        "coherence",
        "respectfulness",
    ]


@dataclass
class ResponseConfig:
    """Configuration for response generation"""

    TOKEN_MULTIPLIER_INITIAL = 2
    TOKEN_MULTIPLIER_SIMULATION = 3
    TOKEN_MULTIPLIER_ANALYSIS = 2

    DEFAULT_RESPONSES = [
        "I understand you're going through a difficult time. Let's talk about what you're feeling.",
        "That sounds challenging. Can you tell me more about what happened?",
        "I'm here to listen and support you. What aspect of this situation is bothering you the most?",
    ]
