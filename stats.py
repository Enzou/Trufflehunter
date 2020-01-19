import pandas as pd
import streamlit as st
import altair as alt

from trufflehunter import show_dotted_chart
from src.event_log.eventlog import EventLog
from src.utils.io import load_csv_data

# umbauen auf eventlog -> dottet chart with activities
def stats(df, threshold = 2):
    visit_id = df["visitId"].value_counts().sort_values(ascending = False)
    visit_id = visit_id.rename(columns = { "visitId" : "TraceId" } )
    
    df_trace_size_smaler_th = df[df.groupby('visitId')['visitId'].transform('count').lt(threshold)]

    st.markdown( '# Stats and stuff:' ) 
    
    f"""
    log contains {df.shape[0]} rows, this form {visit_id.shape[0]} different traces.

    {df_trace_size_smaler_th.shape[0]} lines are removed cause the Trace length is smaller than the Threshhold {threshold}.
    """
    
    df = df[df.groupby('visitId')['visitId'].transform('count').gt(threshold)]
    visit_id = df["visitId"].value_counts().sort_values(ascending = False)
    st.markdown('---')
    "Traces Summary(visitID):", visit_id.describe()
    
    "First 5 Lines:", df.head()
    
    # look at the longest traces
    "## Sessions with the most Requests:"

    visit_id_barplot = alt.Chart(visit_id.reset_index().head()) \
                        .mark_bar().encode(
        x = "visitId:Q",
        y = "index:N"
    )

    st.write(visit_id_barplot)

    longest_trace = visit_id.head().keys()
    options = st.selectbox("Select Trace to get Activities:", longest_trace)
    longest_trace_count = visit_id[options]
    st.write(f"Number of request in the Trace {longest_trace_count}")
    
    select_all = st.checkbox('All "longest Traces"? (only selected)')
    show_table = st.checkbox('Show Table with all Activities?')
    if select_all:
        selected_for_dotted_chart = df[ df.visitId.isin( list(longest_trace) )]
    else: 
        selected_for_dotted_chart = df[ df.visitId.str.contains( options )]
    dotted_log = EventLog(selected_for_dotted_chart, case_id_attr='visitId', activity_attr='ua_name',
                             timestamp_attr='ua_starttime', ts_parse_params={'unit': 'ms'})
    show_dotted_chart(dotted_log)
    
    if show_table:
        st.table( df[ df.visitId.str.contains( options )])

    st.markdown ("## Duration: ")
    "Traces Summary:", df.describe()

    duration_bp = alt.Chart(df).mark_boxplot().encode(
        y = alt.Y('visit_Id:N', axis = alt.Axis(format= '$', title = 'Traces' )),
        x = alt.X('ua_duration:T', axis = alt.Axis(format = '%', title = 'Duration'))
    )
    st.write(duration_bp)

    st.markdown ("## Longest Traces: ")
    
    
    st.markdown ("## Top Urls: ")

    url = 'ua_targetUrl'


    f"the log contains {df[url].nunique()} different Urls."
    
    "Count: ", df[url].value_counts()


    # TODO: stats only works with dataframe

def main():
    df = load_csv_data("first30k.csv")
    df = df.set_index("Unnamed: 0")
    stats(df)


if __name__ == "__main__":
    main()
