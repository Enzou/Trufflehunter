from functools import partial
from pathlib import Path
from typing import List
from collections import Counter

import markov_clustering as mcl
import pandas as pd
import streamlit as st

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


def find_clusters(traces: pd.Series) -> List:
    corpus = create_corpus(traces)
    trace2vec_fn = partial(vectorize_trace, corpus)
    mat = create_similarity_matrix(corpus, traces, trace2vec_fn)

    expansion = st.slider("Expansion", min_value=2, max_value=100)
    inflation = st.slider("inflation", min_value=2., max_value=100.)
    clusters = cluster_with_markov(mat, expansion, inflation)
    show_labels = st.checkbox("Show labels?")
    mcl.draw_graph(mat, clusters, node_size=50, with_labels=show_labels, edge_color="gainsboro")
    st.pyplot()
    st.write(f"{len(clusters)} clusters identified")
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
    pass


def inspect_clusters(clusters, traces) -> None:
    corpus = create_corpus(traces)

    clusters = sorted(clusters, key=len)  # smaller clusters are more suspicious
    hist = pd.DataFrame([len(c) for c in clusters])
    st.bar_chart(hist)

    cluster_id = st.number_input("Cluster ", min_value=0, value=0, max_value=len(clusters))
    st.write(f"Cluster {cluster_id} has {len(clusters[cluster_id])} traces associated")
    activities = Counter()
    for trace_id in clusters[cluster_id]:
        trace = traces[trace_id]
        activities.update(trace.activities)

    st.bar_chart()

    st.write(activities)


def main():
    file_name, df = select_file('interim', default='dt_sessions_1k.csv')
    attr_mapping = attribute_mapper.show(df.columns)
    log = EventLog(df, **attr_mapping)
    traces = log.get_traces(lambda t: t.str.len() > 1)

    clusters = find_clusters(traces)

    if st.checkbox("Inspect trace?"):
        inspect_traces(traces)

    inspect_clusters(clusters, traces)

    if st.button("Save clusters"):
        save_clusters(log, traces, clusters)
        fout = file_name.replace('.csv', '_clustered.csv')
        log._df.to_csv(Path('./data/processed') / fout)
