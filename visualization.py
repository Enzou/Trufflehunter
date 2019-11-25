import itertools

import pandas as pd
from graphviz import Digraph


def create_directly_follows_graph(footprint_matrix: pd.DataFrame) -> Digraph:
    dot = Digraph(comment='Directly Follows Graph')

    nodes = footprint_matrix.columns
    for n in nodes:
        dot.node(n)

    for row, col in itertools.product(nodes, nodes):
        fwd_transition = footprint_matrix.loc[row, col]
        if fwd_transition > 0:
            dot.edge(row, col, label=f"{fwd_transition:.2f}")

    return dot
