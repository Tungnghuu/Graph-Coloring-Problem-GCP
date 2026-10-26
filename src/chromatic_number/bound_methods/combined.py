from bound_methods.clique import Clique
from bound_methods.greedy import Greedy

class CombinedBounds:
    def __init__(self):
        self.lower_method = Clique()
        self.upper_method = Greedy()

    def find_bounds(self, graph):
        lower_bound = self.lower_method.find_lower_bound(graph)
        upper_bound = self.upper_method.find_upper_bound(graph)

        return lower_bound, upper_bound
