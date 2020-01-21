from pathlib import Path
from typing import Union
import numpy as np
import os
import sys
from functools import reduce
from itertools import combinations

import streamlit as st

from src.visualization import visualization as visu
from src.pmtools import matrices
from src.event_log.eventlog import EventLog
from src.miners import AlphaMiner
from src.utils import io
from pm4py.objects.log.exporter.xes import factory as xes_exporter
from pm4py.visualization.petrinet import factory as pn_vis_factory


# TODO:
# - show stats about paths in the log (i.e. # of different paths, counts per path)
# - separate query parameters from path (i.e. activity) -> query params = 'Resource'
# - try to group/cluster paths

# load weblog -> preprocessing/filtern -> transform 2 event log -> extract stats -> process mining
from src.visualization.visualization import create_dotted_chart
from ui.components import attribute_mapper
from ui.components.data_selector import select_file


# def import_log_file(src_file: Union[str, Path]) -> EventLog:
#     # event_stream = csv_importer.import_event_stream(str(src_file), parameters={'sep': ';'})
#     # log = conversion_factory.apply(event_stream, parameters={PARAMETER_CONSTANT_CASEID_KEY: 'Case ID'})
#     log = EventLog.read_from(src_file, case_id_attr='visitId', activity_attr='ua_name',
#                              timestamp_attr='ua_starttime', ts_parse_params={'unit': 'ms'})
#     return log


def export_log_file(log_file, file_path: Path):
    xes_file = file_path.with_suffix('.xes')
    xes_exporter.export_log(log_file, str(xes_file))


def show_dotted_chart(log: EventLog) -> None:
    df = log._df.copy()
    st.write(df)
    #start_times = df.sort_values([log.ts_attr, log.case_id_attr]).groupby(by=log.case_id_attr).first()
    # add information about duration of case for every event
    #df['Duration'] = (df[log.ts_attr] - start_times.loc[df[log.case_id_attr]][log.ts_attr].values) / np.timedelta64(1, 'm')

    # TODO x-axis attribute: trace start-time (-> investigate case duration time), timestamp
    # TODO sorting traces (by duration of trace, case id, etc.)

    st.sidebar.title('Settings')
    col_attr = st.sidebar.selectbox('Color Attribute:', df.columns, 5)
    x_attr = st.sidebar.selectbox('X-Axis:', [log.ts_attr, log.time_passed_attr], 0)
    y_attr = st.sidebar.selectbox('Y-Axis:', [log.case_id_attr])
    # y_sort = st.sidebar.selectbox('Sort Y-Axis:', [log.case_id_attr, log.ts_attr, 'Duration'])

    st.text(f"Loaded {len(df[log.case_id_attr].unique())} cases with a total of {len(df)} events")
    # tooltip = ['Activity', 'Timestamp', 'Resource', 'Costs']
    tooltip = [log.case_id_attr, log.activity_attr, log.ts_attr, 'path']
    st.altair_chart(create_dotted_chart(df, col_attr, x_attr, y_attr, x_attr, tooltip=tooltip), width=-1)


def load_all_processed_data():
    available_files = io.get_available_datasets(Path('processed'))

    data = []
    for av_file in available_files:
        df = io.load_csv_data(av_file, "processed")
        df["source"] = av_file
        data.append(df)

    datacol = [d["visitId"] for d in data]
    return datacol

def trace_in_all_detections():
    datacol = load_all_processed_data()
    test = reduce(set.intersection, map(set, datacol))

    st.markdown(f"### Detected the following trace(s) with all methods: ")
    st.write(list(test))
    return test, datacol

def detected_with_multible_methods():
    detected, datacol = trace_in_all_detections()
    combos = combinations(datacol, 2)
    st.markdown("### Detected the following trace(s) with atleast 2 methods:")
    found = []
    for c in combos:
        test = reduce(set.intersection, map(set, c))
        if detected not in test:
            found.extend(test)
    st.write(found)


def main():
    st.header("Let the hunt begin!")
    show_possible_anomalies = st.checkbox("Show possible anomalies?")
    if show_possible_anomalies:
        detected_with_multible_methods()

    file_name, df = select_file(Path('processed'), default='dt_sessions_1k.csv')
    attr_mapping = attribute_mapper.show(df.columns)
    log = EventLog(df, **attr_mapping, ts_parse_params={})

    st.write(file_name)
    #
    # log = import_log_file(DATA_DIR / log_file)
    # log = log[log._df['ua_type'] == 'Load']   # drop XHR requests to tracking/analytics sites

    show_dotted_chart(log)


    mat_map = {
        'Footprint Matrix': matrices.create_footprint_matrix,
        'Heuristic Matrix': matrices.create_heuristic_matrix
    }
    show_mats = st.multiselect("Show matrices: ", list(mat_map.keys()))
    for m in show_mats:
        st.subheader(f"{m}:")
        res_mat = mat_map[m](log)
        st.table(res_mat)

    miner = AlphaMiner()
    net, start_mark, end_mark = miner.mine(log)

    if st.checkbox('Show details of Petri Net?'):
        st.markdown("#### Places:")
        for p in net.places:
            st.text(p)

        st.markdown("#### Transitions:")
        for t in net.transitions:
            st.text(t)

    visu_type = st.selectbox("Select visualization:", ['None', 'Petri Net', 'Directly Follows Graph'], index=2)
    if visu_type != 'None':
        st.subheader(f"{visu_type}:")
        if visu_type == 'Petri Net':
            gviz = pn_vis_factory.apply(net, start_mark, end_mark)
            st.graphviz_chart(gviz)
        elif visu_type == 'Directly Follows Graph':
            mat = matrices.create_heuristic_matrix(log)
            gviz = visu.create_directly_follows_graph(mat)
            st.graphviz_chart(gviz)

    outliers()


if __name__ == "__main__":
    main()
