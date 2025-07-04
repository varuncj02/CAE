from .node import MCTSNode


class TreeOperations:
    """Utilities for MCTS tree manipulation"""

    @staticmethod
    def backpropagate(node: MCTSNode, score: float) -> None:
        current = node
        while current:
            current.update(score)
            current = current.parent

    @staticmethod
    def prune_branches(
        root_nodes: list[MCTSNode],
        threshold_ratio: float = 0.7,
    ) -> int:
        pruned_count = 0

        for root in root_nodes:
            if root.visits < 5:
                continue

            threshold = root.avg_score * threshold_ratio
            pruned_count += TreeOperations._prune_node_children(root, threshold)

        return pruned_count

    @staticmethod
    def _prune_node_children(node: MCTSNode, threshold: float) -> int:
        if not node.children:
            return 0

        pruned = 0
        children_to_keep = []

        for child in node.children:
            if child.visits > 0 and child.avg_score < threshold:
                pruned += 1 + TreeOperations._count_descendants(child)
            else:
                children_to_keep.append(child)
                pruned += TreeOperations._prune_node_children(child, threshold)

        node.children = children_to_keep
        return pruned

    @staticmethod
    def _count_descendants(node: MCTSNode) -> int:
        count = len(node.children)
        for child in node.children:
            count += TreeOperations._count_descendants(child)
        return count

    @staticmethod
    def get_tree_depths(node: MCTSNode, depth: int = 0) -> list[int]:
        if not node.children:
            return [depth]

        depths = []
        for child in node.children:
            depths.extend(TreeOperations.get_tree_depths(child, depth + 1))
        return depths

    @staticmethod
    def calculate_average_depth(root_nodes: list[MCTSNode]) -> float:
        all_depths = []
        for root in root_nodes:
            all_depths.extend(TreeOperations.get_tree_depths(root))

        return sum(all_depths) / len(all_depths) if all_depths else 0.0
