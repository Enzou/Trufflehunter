import itertools
from typing import Optional, List

import altair as alt
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


def create_dotted_chart(df: pd.DataFrame, color_attribute: str, x_attr: str, y_attr: str, y_sort: str, tooltip: Optional[List] = None) -> alt.Chart:
    # c = alt.Chart(df).mark_line().encode(
    #     alt.X(f"{x_attr}:T",  axis=alt.Axis(labelAngle=-45)),
    #     alt.Y('Case ID:O'),# sort=alt.EncodingSortField(field=y_sort)),
    #     detail='Duration',
    #     color=alt.Color(color_attribute))

    c = alt.Chart(df).mark_circle(
        opacity=0.8,
        size=100,
        # stroke='black',
        # strokeWidth=1
    ).encode(
        alt.X(f"{x_attr}:T"),
        alt.Y(f"{y_attr}:O", axis=alt.Axis(labelAngle=90)),  # sort=alt.EncodingSortField(field=y_sort)),
        # alt.Size('Deaths:Q',
        #          scale=alt.Scale(range=[0, 4000]),
        #          legend=alt.Legend(title='Annual Global Deaths')
        #          ),
        color=alt.Color(color_attribute, legend=alt.Legend(orient='top')),
        tooltip=tooltip
    ).properties(
        width=1000,
        height=800
        # ).transform_filter(
        #     alt.datum.Entity != 'All natural disasters'
    ).interactive()
    return c