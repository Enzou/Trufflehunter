import itertools
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import paired_distances
from sklearn.metrics.pairwise import cosine_similarity
from typing import Callable
from src.event_log.eventlog import EventLog


def create_footprint_matrix(log: EventLog) -> pd.DataFrame:
    unique_activities = log.get_unique_activities()
    trans_mat = create_transition_matrix(log, unique_activities)

    # convert to footprint matrix
    foot_mat = pd.DataFrame(index=unique_activities, columns=unique_activities, data='#')
    for row, col in itertools.product(unique_activities, unique_activities):
        fwd_transition = trans_mat.loc[row, col]
        back_transition = trans_mat.loc[col, row]
        if fwd_transition > 0:
            if back_transition > 0:
                foot_mat.loc[row, col] = '||'
            else:
                foot_mat.loc[row, col] = '→'
        elif back_transition > 0:
            foot_mat.loc[row, col] = '←'
    return foot_mat


def create_transition_matrix(log, unique_activities):
    # create transition matrix
    trans_mat = pd.DataFrame(index=unique_activities, columns=unique_activities, data=0)
    for trace in log:
        activities = trace.activities
        for ai, aj in zip(activities, activities[1:]):
            trans_mat.loc[ai, aj] += 1
    return trans_mat


def create_heuristic_matrix(log: EventLog) -> pd.DataFrame:
    unique_activities = log.get_unique_activities()
    trans_mat = create_transition_matrix(log, unique_activities)

    mat = pd.DataFrame(index=unique_activities, columns=unique_activities, data=0.)
    for row, col in itertools.product(unique_activities, unique_activities):
        fwd_transition = trans_mat.loc[row, col]
        back_transition = trans_mat.loc[col, row]
        mat.loc[row, col] = (fwd_transition - back_transition) / (fwd_transition + back_transition + 1)

    return mat


def create_similarity_matrix(corpus, traces, vectorizer_fn: Callable) -> pd.DataFrame:
    # vfunc = np.vectorize(vectorizer_fn, otypes=[int] * len(corpus))
    # mat = vfunc(traces)
    # mat = np.fromiter((vectorizer_fn(t) for t in traces), dtype=int)

    # return mat
    m = [vectorizer_fn(t) for t in traces]
    mat = pd.DataFrame(cosine_similarity(m), columns=traces.index, index=traces.index)

    return mat

