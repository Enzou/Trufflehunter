import streamlit as st

import ui.preprocessing
import ui.cluster
import ui.process_identification
import ui.trufflehunter
import ui.stats

PAGES = {
    "Preprocessing": ui.preprocessing,
    "Statistics": ui.stats,
    "Clustering": ui.cluster,
    "Process Identification": ui.process_identification,
    "TruffleHunt": ui.trufflehunter   
}


def main():
    st.sidebar.title("Navigation")
    pages = list(PAGES.keys())
    # default_page = pages.index('Preprocessing')
    default_page = pages.index('Process Identification')
    # default_page = pages.index('TruffleHunt')
    selection = st.sidebar.radio("Go to", pages, index=default_page)

    with st.spinner(f"Loading {selection} ..."):
        page = PAGES[selection]
        st.title(selection)
        page.main()


if __name__ == "__main__":
    main()
