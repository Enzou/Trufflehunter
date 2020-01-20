from collections import Counter
from functools import partial
from typing import List, Tuple, Dict

import altair as alt
import markov_clustering as mcl
import networkx as nx
import nx_altair as nxa
import pandas as pd
import streamlit as st

from src.event_log.eventlog import EventLog
from src.pmtools.matrices import create_similarity_matrix
from src.preprocessing.vectorize import create_corpus, vectorize_trace
from ui.components import attribute_mapper
from ui.components.data_selector import select_file


@st.cache(show_spinner=False)
def cluster_with_markov(mat: pd.DataFrame, expansion: int, inflation: float) -> List:
    result = mcl.run_mcl(mat, expansion=expansion, inflation=inflation, loop_value=0)
    clusters = mcl.get_clusters(result)  # get clusters

    return clusters


@st.cache(show_spinner=False)
def create_cluster_histogram(cluster_map: Dict) -> alt.Chart:
    df = pd.Series(cluster_map).value_counts().reset_index()
    df.columns = ['Cluster', 'Size']
    chart = alt.Chart(df).mark_bar().encode(
        alt.X("Cluster:O", axis=alt.Axis(labelAngle=0)),
        alt.Y("Size:Q"),
        alt.Color('Cluster:O', scale=alt.Scale(scheme='Paired')),
        tooltip=['Cluster', 'Size']
    ).properties(
        height=500
    )
    return chart


@st.cache(show_spinner=False)
def draw_cluster(matrix, cluster_map: Dict) -> alt.Chart:
    g = nx.Graph(matrix)
    # map node to cluster id for colors
    for tid in g.nodes():
        node = g.nodes[tid]
        node['cluster'] = cluster_map[tid]
        node['id'] = tid

    # Compute positions for viz.
    pos = nx.spring_layout(g, seed=42)
    # Draw the graph using Altair
    graph_viz = nxa.draw_networkx(g, pos=pos, node_color='cluster',
                                  cmap='Paired',  # category20 colormap = `tab20`
                                  edge_color='gainsboro',
                                  node_tooltip=['cluster', 'id'])
    return graph_viz


@st.cache(show_spinner=False)
def find_clusters(traces: pd.Series, expansion: int, inflation: float) -> Tuple[Dict, alt.Chart]:
    corpus = create_corpus(traces)
    trace2vec_fn = partial(vectorize_trace, corpus)
    mat = create_similarity_matrix(corpus, traces, trace2vec_fn)

    clusters = cluster_with_markov(mat, expansion, inflation)
    cluster_map = {traces.index[node]: i + 1 for i, cluster in enumerate(clusters) for node in cluster}
    graph_viz = draw_cluster(mat, cluster_map)
    return cluster_map, graph_viz


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


@st.cache(show_spinner=False)
def create_cluster_activities_graph(selected_cluster: List) -> alt.Chart:
    act_count = Counter()
    for activities in selected_cluster:
        # trace = traces[trace_id]
        act_count.update(activities)

    df = pd.DataFrame({"Activity": list(act_count.keys()), "Count": list(act_count.values())})
    chart = alt.Chart(df, padding={"top": 5}, height=500).mark_bar().encode(
        alt.X("Activity", axis=alt.Axis(labelAngle=0)),
        alt.Y("Count"),
        tooltip=['Count']
    ).properties(
        # width=450,
        height=500
    )
    return chart


def inspect_clusters(clusters: Dict, traces) -> None:
    # analyze number of different activities in selected cluster
    no_clusters = len(set(clusters.values()))
    cluster_id = st.number_input("Cluster ", min_value=1, value=1, max_value=no_clusters)
    selected_cluster = [traces[tid].activities for tid, cid in clusters.items() if cid == cluster_id]
    st.write(f"Cluster {cluster_id} has {len(selected_cluster)} traces associated")
    chart = create_cluster_activities_graph(selected_cluster)
    st.altair_chart(chart)


def save_clusters(log: EventLog, cluster_map: Dict, file_name: str) -> None:
    """
    Add column to event log with information of the cluster
    :param log: the event log that will be updated
    :param cluster_map: dict mapping trace ids to cluster id
    :param file_name:
    """
    log.set_clusters(cluster_map)
    fout = file_name.replace('.csv', '_clustered.csv')
    log.export_to_csv(f"./data/processed/{fout}")
    st.text(f"Saved log file with cluster info to {fout}")


def main():
    file_name, df = select_file('interim', default='dt_sessions_1k.csv')
    attr_mapping = attribute_mapper.show(df.columns)
    log = EventLog(df, **attr_mapping)
    traces = log.get_traces(lambda t: t.str.len() > 1)

    st.header("Cluster traces")
    expansion = st.slider("Expansion", min_value=2, max_value=100)
    inflation = st.slider("inflation", min_value=2., max_value=100.)
    with st.spinner("Traces are being clusters - please be patient 😴 ..."):
        clusters, graph_viz = find_clusters(traces, expansion, inflation)
        st.altair_chart(graph_viz)
        chart = create_cluster_histogram(clusters)
        st.altair_chart(chart)
    st.write(f"{len(set(clusters.values()))} clusters identified")

    if st.checkbox("Inspect trace?"):
        inspect_traces(traces)

    st.header("Inspect cluster")
    inspect_clusters(clusters, traces)

    st.markdown('------')
    cli_mode = not st._is_running_with_streamlit
    if st.button("Save clusters") or cli_mode:
        save_clusters(log, clusters, file_name)
