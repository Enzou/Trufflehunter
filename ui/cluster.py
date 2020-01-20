import pandas as pd
import numpy as np
import streamlit as st
# import altair as alt
import hdbscan
import seaborn as sns
from pathlib import Path
import pickle
import re

from src.event_log.eventlog import EventLog
from src.event_log.trace import Trace
from src.preprocessing import filter_by_session_length
from src.preprocessing.vectorize import create_corpus, create_np_matrix, vectorize_activities
import src.utils.io as io
from ui.components import attribute_mapper

DATA_PATH = Path("data/interim")
DATA_PATH_Processed = Path("data/processed")


def calc_distance(trace1, trace2) -> int:
    f"""
     trace1: {trace1}. 
    
     trace2: {trace2}"""

    f"length t1: {len(trace1)} - length t2: {len(trace2)}"

    distance = abs(len(trace1) - len(trace2))

    for t1, t2 in zip(trace1, trace2):
        if t1 != t2:
            distance = distance + 1

    return distance


# write all activities of a trace
# calculate levenshtein distance between activitiy vectors
# Next Steps Clustering

# dbscan clustering

def test_calc_distance():
    t1 = ["a", "a", "c", "a", "a", "a"]
    t2 = ["a", "b", "c"]
    st.write(f"Distance : {calc_distance(t1, t2)}")


@st.cache(allow_output_mutation=True)
def read_processed_data(name):
    return EventLog.read_from(DATA_PATH / name)


def write_outliers_to_pickle(outliers, file_name):

    match = re.search("\w+", file_name)
    file_name = "outliers_" + match.group(0) + ".pickle"
    with open(DATA_PATH_Processed / file_name, 'wb') as f:
        pickle.dump(outliers, f)


def main():
    available_files = io.get_available_datasets("interim")
    file_name = st.sidebar.selectbox("Source web log: ",
                                     options=available_files)

    log = read_processed_data(file_name)

    attr_mapping = attribute_mapper.show(log._df.columns)
    case_attr = attr_mapping['case_id_attr']
    traces = filter_by_session_length(log._df, case_attr)
    traces = traces.groupby(case_attr).apply(Trace, attrs=attr_mapping)
   

    corpus = create_corpus(traces)
    show_corpus = st.checkbox("Show Corpus")
    if show_corpus:
        st.write("Activities in Traces:", corpus)
    # generate vectors from activities
    vectors_ids, vectors, vector_max_len = vectorize_activities(traces, corpus)
    matrix = create_np_matrix(vectors_ids, vector_max_len)

    min_cluster_size = 4
    min_sample = 1

    change_parameters = st.checkbox("Change Parameters")
    if change_parameters:
        min_cluster_size = st.slider("Min Cluster size: ", 2, 20, 4)
        min_sample = st.slider("min samples per cluster: ", 1, 5, 1)
    
    st.write(f"""\nDBSCAN with the parameters:\n
    min_cluster_size = {min_cluster_size}\n
    min_samples per cluster = {min_sample}""")
    

    cluster = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size, min_samples=min_sample,
    cluster_selection_epsilon=0.5).fit(matrix)
    """
        Outlierdetection: https://hdbscan.readthedocs.io/en/latest/outlier_detection.html
    """
    # "outlier_scores: ", cluster.outlier_scores_
    #sns.distplot(cluster.outlier_scores_[np.isfinite(cluster.outlier_scores_)], rug=True)
    #st.pyplot()
    outliers = {}
    for score, vector in zip(cluster.outlier_scores_, vectors.items()):
        if score > 0.6:
            outliers[vector[0]] = vector[1]
    write_outliers_to_pickle(outliers, file_name)
    outlier_trace_ids = [name for name in outliers.keys()]

    st.write(f"{len(outlier_trace_ids)} outliers found in {len(traces)} Traces.")
    show_outliers = st.checkbox("show a list of all outliers?")
    if show_outliers:
        st.write(outlier_trace_ids)

    selected_outlier = st.selectbox("Select Outlier to get trace:", outlier_trace_ids)

    st.write(outliers[selected_outlier])
    # cluster_labels = cluster.fit_predict(matrix)
    # outliers = 0
    # st.markdown("## Outliers: ")
    # for  label, name in zip ( cluster_labels, tracenames):
    #     if label == -1: 
    #         st.write (f"{name}, Activities: {vectors.get(name)}")
    #         outliers = outliers +1
    # "number of outliers:", outliers

    # print("test", matrix)
    # db = dbscan(matrix)
    # core_samples_mask = np.zeros_like(db.labels_, dtype=bool)

    # labels = db.labels_

    # print (labels)


if __name__ == "__main__":
    main()
