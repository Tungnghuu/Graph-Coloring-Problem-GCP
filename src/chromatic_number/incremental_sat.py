from src.chromatic_number.base import ChromaticNumberSolver

class IncrementalSAT(ChromaticNumberSolver):

    def find_chromatic_number(self, graph, encoding, bounds_method):
        lower_bound, upper_bound = bounds_method.find_bounds(graph)
        # Initialize one solver and reuse it.
        # The encoding must support incremental solving.
        pass