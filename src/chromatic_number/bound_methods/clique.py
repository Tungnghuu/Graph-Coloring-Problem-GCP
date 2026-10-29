from .base import LowerBoundMethod
from .greedy import _build_adjacency

class Clique(LowerBoundMethod):
    def find_lower_bound(self, graph) -> int:
        n, adjacency = _build_adjacency(graph)
        if n == 0:
            return 0

        vertices = sorted(
            range(n),
            key=lambda vertex: (-len(adjacency[vertex]), vertex),
        )
        largest_clique = []

        for start in vertices:
            clique = [start]
            candidates = [
                vertex
                for vertex in vertices
                if vertex != start and vertex in adjacency[start]
            ]
            candidates.sort(key=lambda vertex: (-len(adjacency[vertex]), vertex))

            for vertex in candidates:
                if all(vertex in adjacency[member] for member in clique):
                    clique.append(vertex)

            if len(clique) > len(largest_clique):
                largest_clique = clique

        return len(largest_clique)