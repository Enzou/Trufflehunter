from pathlib import Path
from typing import Union, Dict
import numpy as np
import pandas as pd
import os

import utils
from eventlog import EventLog
from miner import AlphaMiner
from pm4py.objects.log.exporter.xes import factory as xes_exporter
from pm4py.visualization.petrinet import factory as pn_vis_factory

import streamlit as st
import altair as alt


def import_log_file(src_file: Union[str, Path]) -> EventLog:
    # event_stream = csv_importer.import_event_stream(str(src_file), parameters={'sep': ';'})
    # log = conversion_factory.apply(event_stream, parameters={PARAMETER_CONSTANT_CASEID_KEY: 'Case ID'})
    log = EventLog.read_from(src_file, datetime_fmt='%d-%m-%Y:%H.%M')
    return log


def export_log_file(log_file, file_path: Path):
    xes_file = file_path.with_suffix('.xes')
    xes_exporter.export_log(log_file, str(xes_file))


def create_dotted_chart(df: pd.DataFrame, color_attribute: str, x_attr: str, y_sort: str) -> alt.Chart:
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
        alt.Y('Case ID:O',  axis=alt.Axis(labelAngle=90)),# sort=alt.EncodingSortField(field=y_sort)),
        # alt.Size('Deaths:Q',
        #          scale=alt.Scale(range=[0, 4000]),
        #          legend=alt.Legend(title='Annual Global Deaths')
        #          ),
        color=alt.Color(color_attribute),
        tooltip=['Activity', 'Timestamp', 'Resource', 'Costs']
    ).properties(
        width=1000,
        height=800
        # ).transform_filter(
        #     alt.datum.Entity != 'All natural disasters'
    ).interactive()
    return c


def show_dotted_chart(log: EventLog) -> None:
    df = log._df.copy()
    start_times = df.sort_values(['Timestamp', 'Case ID']).groupby(by='Case ID').first()
    # add information about duration of case for every event
    df['Duration'] = (df['Timestamp'] - start_times.loc[df['Case ID']]['Timestamp'].values)/ np.timedelta64(1, 'm')

    # TODO x-axis attribute: trace start-time (-> investigate case duration time), timestamp
    # TODO sorting traces (by duration of trace, case id, etc.)
    # TODO zooming

    st.sidebar.title('Settings')
    col_attr = st.sidebar.selectbox('Color Attribute:', df.columns, 3)
    x_attr = st.sidebar.selectbox('X-Axis:', ['Timestamp', 'Duration'], 0)
    y_sort = st.sidebar.selectbox('Sort Y-Axis:', ['Case ID', 'Duration'])

    st.text(f"Loaded {len(df['Case ID'].unique())} cases with a total of {len(df)} events")
    st.altair_chart(create_dotted_chart(df, col_attr, x_attr, y_sort), width=-1)


def main():
    src_dir = Path('./data')
    st.header("It's a badger, Badger, BADGER!")
    datasets = [f for f in os.listdir(src_dir) if f.endswith('.csv')]
    # log_file = Path('./data/running-example.csv')
    log_file = st.selectbox('Dataset:', datasets, index=datasets.index('running-example.csv'))
    log_file = src_dir/log_file

    log = import_log_file(log_file)
    foot_mat = utils.create_heuristic_matrix(log)
    show_dotted_chart(log)

    if st.checkbox("Show footprint matrix?"):
        st.subheader('Footprint Matrix:')
        foot_mat = utils.create_footprint_matrix(log)
        st.table(foot_mat)

    if st.checkbox("Show heuristic matrix?"):
        st.subheader('Heuristic Matrix:')
        foot_mat = utils.create_heuristic_matrix(log)
        st.table(foot_mat)

    miner = AlphaMiner()
    net, start_mark, end_mark = miner.mine(log)

    if st.checkbox('Show details of Petri Net?'):
        st.markdown("#### Places:")
        for p in net.places:
            st.text(p)

        st.markdown("#### Transitions:")
        for t in net.transitions:
            st.text(t)

    if st.checkbox("Show Petri Net?"):
        st.subheader("Petri Net:")
        gviz = pn_vis_factory.apply(net, start_mark, end_mark)
        st.graphviz_chart(gviz)


if __name__ == "__main__":
    main()
