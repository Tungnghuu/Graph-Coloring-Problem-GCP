from .clique import Clique
from .greedy import Greedy

class CombinedBounds:
    def __init__(self):
        # A clique gives a lower bound; greedy coloring gives an upper bound.
        self.lower_method = Clique()
        self.upper_method = Greedy()

    def find_bounds(self, graph):
        # Calculate both bounds for the same graph.
        lower_bound = self.lower_method.find_lower_bound(graph)
        upper_bound = self.upper_method.find_upper_bound(graph)
        return lower_bound, upper_bound