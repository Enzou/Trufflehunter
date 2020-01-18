import pandas as pd
import numpy as np
import streamlit as st
#import altair as alt
import hdbscan
import seaborn as sns
from pathlib import Path
import pickle
import re

from src.event_log.eventlog import EventLog
from src.event_log.trace import Trace
from src.preprocessing import filter_by_session_length
from src.preprocessing.vectorize import create_corpus, create_np_matrix,vectorize_activities
import src.utils.io as io

DATA_PATH = Path("data/processed")

def calc_distance(trace1, trace2) -> int:
    f"""
     trace1: {trace1}. 
    
     trace2: {trace2}"""

    f"length t1: {len(trace1)} - length t2: {len(trace2)}"

    distance = abs(len(trace1)- len(trace2))
    
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
    st.write(f"Distance : {calc_distance(t1,t2)}")

@st.cache(allow_output_mutation=True)
def read_processed_data(name):
    return EventLog.read_from(DATA_PATH / name)

def write_outliers_to_pickle(outliers, file_name):
    match = re.search("\w+", file_name)
    file_name = "outliers_" +match.group(0)+ ".pickle"
    with open(DATA_PATH/file_name, 'wb') as f:
        pickle.dump(outliers, f)


def main():
    st.sidebar.radio("Stage:", ['Clustering'])

    available_files = io.get_available_datasets("processed")
    file_name = st.sidebar.selectbox("Source web log: ",
                                     options=available_files,
                                     index=available_files.index('first30k.csv'))
   

    log = read_processed_data(file_name)

    traces = filter_by_session_length(log._df, 'visitId')
    traces = traces.groupby('visitId').apply(Trace)

    corpus = create_corpus(traces)
    show_corpus = st.checkbox("Show Corpus")
    if show_corpus:
        st.write("Activities in Traces:", corpus)
    # generate vectors from activities
    vectors_ids, vectors, vector_max_len = vectorize_activities(traces, corpus)
    matrix = create_np_matrix(vectors_ids, vector_max_len)
    
    # TODO write stuff to pickle 

    cluster = hdbscan.HDBSCAN(min_cluster_size=10, min_samples = 2).fit(matrix)
    """
        Outlierdetection: https://hdbscan.readthedocs.io/en/latest/outlier_detection.html
    """
    #"outlier_scores: ", cluster.outlier_scores_
    sns.distplot(cluster.outlier_scores_[np.isfinite(cluster.outlier_scores_)], rug=True)
    st.pyplot()
    outliers = {}
    for score, vector in zip(cluster.outlier_scores_, vectors.items()): 
        if score > 0.6:
            #st.write(vector)
            outliers[vector[0]] =vector[1]
    #print (outliers)
    write_outliers_to_pickle(outliers, file_name)
    outlier_trace_ids = [name for name in outliers.keys()]

    selected_outlier = st.selectbox("Select Outlier:",outlier_trace_ids)
    
    st.write(outliers[selected_outlier])
    #cluster_labels = cluster.fit_predict(matrix)
    # outliers = 0
    # st.markdown("## Outliers: ")
    # for  label, name in zip ( cluster_labels, tracenames):
    #     if label == -1: 
    #         st.write (f"{name}, Activities: {vectors.get(name)}")
    #         outliers = outliers +1
    # "number of outliers:", outliers

    #print("test", matrix)
    #db = dbscan(matrix)
    #core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
   
    #labels = db.labels_

    #print (labels)


if __name__ == "__main__":
    main()