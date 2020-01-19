import streamlit as st

import ui.eda
import ui.cluster
import ui.process_identification
import ui.trufflehunter
import ui.stats

PAGES = {
    "Weblog -> Eventlog": ui.eda,
    "Clustering": ui.cluster,
    "Process Identification": ui.process_identification,
    "TruffleHunt": ui.trufflehunter
    "Statistics": ui.stats
}


def main():
    st.sidebar.title("Navigation")
    pages = list(PAGES.keys())
    # default_page = pages.index('Exploratory Data Analysis')
    default_page = pages.index('Process Identification')
    # default_page = pages.index('TruffleHunt')
    selection = st.sidebar.radio("Go to", pages, index=default_page)

    with st.spinner(f"Loading {selection} ..."):
        page = PAGES[selection]
        st.title(selection)
        page.main()


if __name__ == "__main__":
    main()
