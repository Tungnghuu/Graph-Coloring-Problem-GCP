from .base import LowerBoundMethod
from .greedy import _build_adjacency, _sort_vertices_by_degree

class Clique(LowerBoundMethod):
    def find_lower_bound(self, graph) -> int:
        n, adjacency = _build_adjacency(graph)
        if n == 0:
            return 0

        # Try vertices with many neighbors before vertices with fewer neighbors.
        vertices = _sort_vertices_by_degree(adjacency)
        largest_clique = []

        # Start a possible clique at each vertex.
        for start in vertices:
            clique = [start]
            candidates = []
            for vertex in vertices:
                is_start = vertex == start
                is_neighbor = vertex in adjacency[start]
                if not is_start and is_neighbor:
                    candidates.append(vertex)

            # Consider candidates with more neighbors first.
            candidates = _sort_vertices_by_degree(adjacency, candidates)

            # Add a candidate only if it connects to every current clique member.
            for vertex in candidates:
                connects_to_clique = True
                for member in clique:
                    if vertex not in adjacency[member]:
                        connects_to_clique = False
                        break

                if connects_to_clique:
                    clique.append(vertex)

            if len(clique) > len(largest_clique):
                largest_clique = clique

        return len(largest_clique)