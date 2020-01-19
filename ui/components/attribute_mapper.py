from typing import Dict, List

import streamlit as st


def get_case_default(features: List[str]) -> int:
    """
    Heuristic for selecting a sound attribute as default for case id
    :param features: list of available features
    :return: index of the suggested feature in the list
    """
    for idx, f in enumerate(features):
        if f.lower().endswith('id'):
            return idx
    return 0


def get_activity_default(features: List[str]) -> int:
    """
    Heuristic for selecting a sound attribute as default for activity
    :param features: list of available features
    :return: index of the suggested feature in the list
    """
    for idx, f in enumerate(features):
        if 'activity' in f.lower():
            return idx
    return 0


def get_starttime_default(features: List[str]) -> int:
    """
    Heuristic for selecting a sound attribute as default for start time
    :param features: list of available features
    :return: index of the suggested feature in the list
    """
    for idx, f in enumerate(features):
        if 'start' in f.lower():
            return idx
    return 0


def show(features: List[str], in_sidebar=True) -> Dict:
    s = st.sidebar if in_sidebar else st

    s.subheader("Map features to attributes")
    unmapped = features.copy()
    mapped = []
    case_attr = s.selectbox("Case:", unmapped, get_case_default(unmapped))
    mapped.append(case_attr)
    unmapped = [f for f in unmapped if f not in mapped]

    activity_attr = s.selectbox("Activity:", unmapped, get_activity_default(unmapped))
    # mapped += activity_attr
    mapped.append(activity_attr)
    unmapped = [f for f in unmapped if f not in mapped]

    starttime_attr = s.selectbox("Starttime:", unmapped, get_starttime_default(unmapped))
    mapped.append(starttime_attr)
    unmapped = [f for f in unmapped if f not in mapped]

    endime_attr = s.selectbox("Endtime:", unmapped)
    mapped.append(endime_attr)
    unmapped = [f for f in unmapped if f not in mapped]

    res_attrs = s.multiselect("Resources:", unmapped)
    mapped += res_attrs
    unmapped = [f for f in unmapped if f not in mapped]

    return {
        "case_id_attr": case_attr,
        "activity_attr": activity_attr,
        "timestamp_attr": starttime_attr,
        "resource_attrs": res_attrs
    }
