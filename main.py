from pathlib import Path
from typing import Union
import numpy as np
import pandas as pd
import os

from pm4py.objects.log.importer.csv import factory as csv_importer
from pm4py.objects.log.exporter.xes import factory as xes_exporter
from pm4py.objects.conversion.log import factory as conversion_factory
from pm4py.objects.log.log import EventStream
from pm4py.util.constants import PARAMETER_CONSTANT_CASEID_KEY
from pm4py.algo.discovery.alpha import factory as alpha_miner

import streamlit as st
import altair as alt


@st.cache
def import_log_file(src_file: Union[str, Path]) -> EventStream:
    event_stream = csv_importer.import_event_stream(str(src_file), parameters={'sep': ';'})
    log = conversion_factory.apply(event_stream, parameters={PARAMETER_CONSTANT_CASEID_KEY: 'Case ID'})
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


def create_footprint_matrix():
    pass


def main():
    src_dir = Path('./data')
    st.header("It's a badger, Badger, BADGER!")
    datasets = [f for f in os.listdir(src_dir) if f.endswith('.csv')]
    # log_file = Path('./data/running-example.csv')
    log_file = st.selectbox('Dataset:', datasets, index=datasets.index('running-example.csv'))
    log_file = src_dir/log_file

    log = import_log_file(log_file)

    df = csv_importer.import_dataframe_from_path(log_file, parameters={'sep': ';'})
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='%d-%m-%Y:%H.%M')
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

    st.text(f"Loaded {len(log)} entries from '{log_file}'")

    st.altair_chart(create_dotted_chart(df, col_attr, x_attr, y_sort), width=-1)


if __name__ == "__main__":
    main()
