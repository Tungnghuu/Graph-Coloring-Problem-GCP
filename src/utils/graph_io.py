from dataclasses import dataclass

@dataclass
class Graph:
    n: int
    edges: list
    colors: list

    def get_vertices(self):
        return list(range(self.n))

def read_col(filepath):
    n = 0
    edges = []
    seen_edges = set()

    with open(filepath, "r") as f:
        for line in f:
            parts = line.split()

            if not parts or parts[0] == "c":
                continue

            if parts[0] == "p":
                n = int(parts[2])

            elif parts[0] == "e":
                u = int(parts[1]) - 1
                v = int(parts[2]) - 1

                edge = (min(u, v), max(u, v))

                if edge not in seen_edges:
                    seen_edges.add(edge)
                    edges.append(edge)

    colors = [None] * n

    return Graph(n, edges, colors)

if __name__ == "__main__":
    graph = read_col("data/instances/anna.col")

    print("Number of vertices:", graph.n)
    print("Number of edges:", len(graph.edges))
    print("First 5 edges:", graph.edges[:5])
    print("Vertices:", graph.get_vertices())
    print("Colors:", graph.colors)