from functools import partial
from pathlib import Path
from typing import List
from collections import Counter

import markov_clustering as mcl
import pandas as pd
import streamlit as st
import altair as alt
import networkx as nx
import nx_altair as nxa

from src.event_log.eventlog import EventLog
from src.pmtools.matrices import create_similarity_matrix
from src.preprocessing.vectorize import create_corpus, vectorize_trace
from ui.components import attribute_mapper
from ui.components.data_selector import select_file


@st.cache
def cluster_with_markov(mat: pd.DataFrame, expansion: int, inflation: float) -> List:
    result = mcl.run_mcl(mat, expansion=expansion, inflation=inflation, loop_value=0)
    clusters = mcl.get_clusters(result)  # get clusters

    return clusters


def draw_cluster(matrix, clusters, traces) -> None:
    g = nx.Graph(matrix)
    # map node to cluster id for colors
    cluster_map = {node: i + 1 for i, cluster in enumerate(clusters) for node in cluster}
    for n_id in g.nodes():
        node = g.nodes[n_id]
        node['cluster'] = cluster_map[n_id]
        node['id'] = traces.index[n_id]

    # Compute positions for viz.
    pos = nx.spring_layout(g, seed=42)
    # Draw the graph using Altair
    graph_viz = nxa.draw_networkx(g, pos=pos, node_color='cluster',
                                  cmap='Paired',  # category20 colormap = `tab20`
                                  edge_color='gainsboro',
                                  node_tooltip=['cluster', 'id'])
    st.altair_chart(graph_viz)
    chart = create_cluster_histogram(clusters)
    st.altair_chart(chart)


def find_clusters(traces: pd.Series) -> List:
    corpus = create_corpus(traces)
    trace2vec_fn = partial(vectorize_trace, corpus)
    mat = create_similarity_matrix(corpus, traces, trace2vec_fn)

    expansion = st.slider("Expansion", min_value=2, max_value=100)
    inflation = st.slider("inflation", min_value=2., max_value=100.)
    with st.spinner("Traces are being clusters - pleace be patient 😴 ..."):
        clusters = cluster_with_markov(mat, expansion, inflation)
        draw_cluster(mat, clusters, traces)
    return clusters


def inspect_traces(traces: pd.Series) -> None:
    st.subheader("Inspect trace")

    if st.checkbox("Search by cluster index", value=True):
        trace_idx = st.number_input("Trace number: ", min_value=0, value=0, max_value=len(traces))
        st.write(traces[trace_idx])
    else:
        trace_id = st.selectbox("Trace Id:", sorted([t.id for t in traces]))
        st.text("searching for " + trace_id)
        # trace = log.get_trace(trace_id)
        trace = next(t for t in traces if t.id == trace_id)
        st.write(trace)

        for i, t in enumerate(traces):
            if t.id == trace.id:
                st.text(f"Index of selected trace: {i}")


def save_clusters(log: EventLog, traces: pd.Series, clusters: List) -> None:
    """
    Add column to event log with information of the cluster
    :param log: the eventlog that will be updated
    :param traces: filtered subset of traces used for clustering. Needed to map the clusters back to the eventlog
    :param clusters: list of tuples with traces indices grouped together
    """
    st.balloons()


def create_cluster_histogram(clusters) -> alt.Chart:
    cluster_dict = [{"Cluster": i + 1, "Size": len(c)} for i, c in enumerate(clusters)]
    hist = pd.DataFrame(cluster_dict)
    chart = alt.Chart(hist).mark_bar().encode(
        alt.X("Cluster:O"),
        alt.Y("Size:Q"),
        alt.Color('Cluster:O', scale=alt.Scale(scheme='Paired')),
        tooltip=['Cluster', 'Size']
    ).properties(
        height=500
    )
    return chart


def inspect_clusters(clusters, traces) -> None:
    # analyze number of different activities in selected cluster
    cluster_id = st.number_input("Cluster ", min_value=1, value=1, max_value=len(clusters))
    selected_cluster = clusters[cluster_id - 1]
    st.write(f"Cluster {cluster_id} has {len(selected_cluster)} traces associated")
    activities = Counter()
    for trace_id in selected_cluster:
        trace = traces[trace_id]
        activities.update(trace.activities)

    df = pd.DataFrame({"Activity": list(activities.keys()), "Count": list(activities.values())})
    chart = alt.Chart(df, padding={"top": 5}, height=500).mark_bar().encode(
        alt.X("Activity", axis=alt.Axis(labelAngle=0)),
        alt.Y("Count"),
        tooltip=['Count']
    ).properties(
        # width=450,
        height=500
    )
    st.altair_chart(chart)


def main():
    file_name, df = select_file('interim', default='dt_sessions_1k.csv')
    attr_mapping = attribute_mapper.show(df.columns)
    log = EventLog(df, **attr_mapping)
    traces = log.get_traces(lambda t: t.str.len() > 1)

    st.header("Cluster traces")
    clusters = find_clusters(traces)
    st.write(f"{len(clusters)} clusters identified")

    if st.checkbox("Inspect trace?"):
        inspect_traces(traces)

    inspect_clusters(clusters, traces)

    st.markdown('------')
    if st.button("Save clusters"):
        save_clusters(log, traces, clusters)
        fout = file_name.replace('.csv', '_clustered.csv')
        log._df.to_csv(Path('./data/processed') / fout)
