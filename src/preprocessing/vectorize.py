from collections import OrderedDict

import numpy as np


def create_corpus(traces) -> OrderedDict:
    unique_activities = set()
    for trace in traces:
        for event in trace._events:
            # print(f'ID: {event.get("visitId")}; Activity: {event.get("activity")} ')
            unique_activities.add(event.get("activity"))
    corpus = OrderedDict()
    for c, activity in enumerate(unique_activities):
        corpus[activity] = c
    return corpus


def vectorize_activities(traces, corpus):
    activity_list_ids = {}
    activity_list = {}
    max_len = 0
    for trace in traces:
        act = []
        act_name = []
        for events in trace._events:
            act.append(corpus.get(events.get("activity")))
            act_name.append(events.get("activity"))
        if len(act) > max_len:
            max_len = len(act)

        activity_list_ids[events.get("visitId")] = act
        activity_list[events.get("visitId")] = act_name
    return activity_list_ids, activity_list, max_len


def create_np_matrix(vectors, maxlen):
    names = []
    padded_vectors = []
    for _, vector in vectors.items():
        padded_vectors.append(np.pad(vector,
                                     (0, maxlen - len(vector)),
                                     'constant', constant_values=0))
    return np.array(padded_vectors)


def vectorize_trace(corpus, trace) -> np.array:
    """
    Create a vector of fixed length where each number donates number of occurrences of an activity in the trace
    :param corpus: collection of available activities. Size of corpus is size of resulting vector
    :param trace: trace which shall be vectorized
    :return: vectorized trace as array of numbers
    """
    vec = np.zeros(len(corpus), dtype=int)
    for a in trace:
        vec[corpus.get(a["activity"])] += 1
    return vec
