from functools import partial

import pandas as pd
import markov_clustering as mcl

from src.pmtools.matrices import create_similarity_matrix
from src.preprocessing.vectorize import create_corpus, vectorize_trace


def cluster_traces(traces: pd.Series, expansion: int, inflation: float) -> None:
    corpus = create_corpus(traces)
    trace2vec_fn = partial(vectorize_trace, corpus)

    # activity_ids, activities, max_len = vectorize_activities(traces, corpus)
    mat = create_similarity_matrix(corpus, traces, trace2vec_fn)

    result = mcl.run_mcl(mat, expansion=expansion, inflation=inflation, loop_value=0)
    clusters = mcl.get_clusters(result)  # get clusters
    return clusters
