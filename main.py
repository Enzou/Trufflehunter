from pathlib import Path
from typing import Union, Dict, Optional, List
import numpy as np
import pandas as pd
import os

import utils
import visualization as visu
from eventlog import EventLog
from miner import AlphaMiner
from pm4py.objects.log.exporter.xes import factory as xes_exporter
from pm4py.visualization.petrinet import factory as pn_vis_factory

import streamlit as st
import altair as alt


# TODO:
# - show stats about paths in the log (i.e. # of different paths, counts per path)
# - separate query parameters from path (i.e. activity) -> query params = 'Resource'
# - filter entries for different domains (e.g. Google Analytics, etc.)
# - try to group/cluster paths


def import_log_file(src_file: Union[str, Path]) -> EventLog:
    # event_stream = csv_importer.import_event_stream(str(src_file), parameters={'sep': ';'})
    # log = conversion_factory.apply(event_stream, parameters={PARAMETER_CONSTANT_CASEID_KEY: 'Case ID'})
    log = EventLog.read_from(src_file, case_id_attr='visitId', activity_attr='ua_name', timestamp_attr='ua_starttime', ts_parse_params={
        # 'format':'%d-%m-%Y:%H.%M'
        'unit': 'ms'
    })
    return log


def export_log_file(log_file, file_path: Path):
    xes_file = file_path.with_suffix('.xes')
    xes_exporter.export_log(log_file, str(xes_file))


def create_dotted_chart(df: pd.DataFrame, color_attribute: str, x_attr: str, y_attr: str, y_sort: str, tooltip: Optional[List] = None) -> alt.Chart:
    # c = alt.Chart(df).mark_line().encode(
    #     alt.X(f"{x_attr}:T",  axis=alt.Axis(labelAngle=-45)),
    #     alt.Y('Case ID:O'),# sort=alt.EncodingSortField(field=y_sort)),
    #     detail='Duration',
    #     color=alt.Color(color_attribute))

    c = alt.Chart(df).mark_circle(
        opacity=0.8,
        size=100,
        # stroke='black',
        # strokeWidth=1
    ).encode(
        alt.X(f"{x_attr}:T"),
        alt.Y(f"{y_attr}:O", axis=alt.Axis(labelAngle=90)),  # sort=alt.EncodingSortField(field=y_sort)),
        # alt.Size('Deaths:Q',
        #          scale=alt.Scale(range=[0, 4000]),
        #          legend=alt.Legend(title='Annual Global Deaths')
        #          ),
        color=alt.Color(color_attribute),
        tooltip=tooltip
    ).properties(
        width=1000,
        height=800
        # ).transform_filter(
        #     alt.datum.Entity != 'All natural disasters'
    ).interactive()
    return c


def show_dotted_chart(log: EventLog) -> None:
    df = log._df.copy()
    start_times = df.sort_values([log.ts_attr, log.case_id_attr]).groupby(by=log.case_id_attr).first()
    # add information about duration of case for every event
    df['Duration'] = (df[log.ts_attr] - start_times.loc[df[log.case_id_attr]][log.ts_attr].values) / np.timedelta64(1, 'm')

    # TODO x-axis attribute: trace start-time (-> investigate case duration time), timestamp
    # TODO sorting traces (by duration of trace, case id, etc.)
    # TODO zooming

    st.sidebar.title('Settings')
    col_attr = st.sidebar.selectbox('Color Attribute:', df.columns, 3)
    x_attr = st.sidebar.selectbox('X-Axis:', [log.ts_attr, 'Duration'], 0)
    y_attr = st.sidebar.selectbox('Y-Axis:', [log.case_id_attr])
    y_sort = st.sidebar.selectbox('Sort Y-Axis:', [log.case_id_attr, 'Duration'])

    st.text(f"Loaded {len(df[log.case_id_attr].unique())} cases with a total of {len(df)} events")
    # tooltip = ['Activity', 'Timestamp', 'Resource', 'Costs']
    tooltip = [log.activity_attr, log.ts_attr]
    st.altair_chart(create_dotted_chart(df, col_attr, x_attr, y_attr, y_sort, tooltip=tooltip), width=-1)


def main():
    src_dir = Path('./data')
    st.header("Let the hunt begin!")
    datasets = [f for f in os.listdir(src_dir) if f.endswith('.csv')]
    # log_file = Path('./data/running-example.csv')
    log_file = st.selectbox('Dataset:', datasets, index=datasets.index('dt_sessions_1k.csv'))
    # log_file = st.selectbox('Dataset:', datasets, index=0)

    log = import_log_file(src_dir/log_file)
    show_dotted_chart(log)

    mat_map = {
        'Footprint Matrix': utils.create_footprint_matrix,
        'Heuristic Matrix': utils.create_heuristic_matrix
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
            mat = utils.create_heuristic_matrix(log)
            gviz = visu.create_directly_follows_graph(mat)
            st.graphviz_chart(gviz)


if __name__ == "__main__":
    main()
