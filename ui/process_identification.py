from functools import partial
from pathlib import Path
from typing import Dict, List

import markov_clustering as mcl
import pandas as pd
import streamlit as st

from src.event_log.eventlog import EventLog
from src.event_log.trace import Trace
from src.pmtools.matrices import create_similarity_matrix
from src.preprocessing import filter_by_session_length
from src.preprocessing.vectorize import create_corpus, vectorize_trace
from ui.components import attribute_mapper
from ui.components.data_selector import select_file


@st.cache
def cluster_with_markov(mat: pd.DataFrame, expansion: int, inflation: float) -> List:
    result = mcl.run_mcl(mat, expansion=expansion, inflation=inflation, loop_value=0)
    clusters = mcl.get_clusters(result)  # get clusters

    return clusters


# @st.cache(allow_output_mutation=True)
# def get_traces(df: pd.DataFrame, attr_mapping: Dict) -> pd.DataFrame:
#     case_attr = attr_mapping['case_id_attr']
#     traces = filter_by_session_length(df, case_attr)
#     traces = traces.groupby(case_attr).apply(Trace, attrs=attr_mapping)
#     return traces


def cluster_traces(traces: pd.Series) -> None:
    corpus = create_corpus(traces)
    trace2vec_fn = partial(vectorize_trace, corpus)

    # activity_ids, activities, max_len = vectorize_activities(traces, corpus)
    mat = create_similarity_matrix(corpus, traces, trace2vec_fn)

    expansion = st.slider("Expansion", min_value=2, max_value=100)
    inflation = st.slider("inflation", min_value=2., max_value=100.)
    clusters = cluster_with_markov(mat, expansion, inflation)
    mcl.draw_graph(mat, clusters, node_size=50, with_labels=True, edge_color="silver")
    st.pyplot()
    st.write(f"{len(clusters)} clusters identified")


def inspect_traces(traces: pd.Series) -> None:
    st.subheader("Inspect trace")

    trace_idx = st.number_input("Trace number: ", min_value=0, value=0, max_value=len(traces))
    st.write(traces[trace_idx])

    trace_id = st.selectbox("Trace Id:", sorted([t.id for t in traces]))
    st.text("searching for " + trace_id)
    # trace = log.get_trace(trace_id)
    trace = next(t for t in traces if t.id == trace_id)
    st.write(trace)

    for i, t in enumerate(traces):
        if t.id == trace.id:
            st.text(f"Index of selected trace: {i}")


def main():
    file_name, df = select_file(Path('./data/raw'), default='dt_sessions_1k.csv')
    attr_mapping = attribute_mapper.show(df.columns)
    log = EventLog(df, **attr_mapping)
    traces = log.get_traces(lambda t: t.str.len() > 1)

    cluster_traces(traces)

    if st.checkbox("Inspect trace?"):
        inspect_traces(traces)

    # log = read_processed_data(file_name)
