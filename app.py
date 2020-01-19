import streamlit as st

import ui.eda
import ui.cluster
import ui.process_identification
import ui.trufflehunter


PAGES = {
    "Exploratory Data Analysis": ui.eda,
    "Clustering": ui.cluster,
    "Process Identification": ui.process_identification,
    "TrufflesHunt": ui.trufflehunter
}


def main():
    st.sidebar.title("Navigation")
    pages = list(PAGES.keys())
    # default_page = pages.index('Exploratory Data Analysis')
    default_page = pages.index('Process Identification')
    selection = st.sidebar.radio("Go to", pages, index=default_page)

    with st.spinner(f"Loading {selection} ..."):
        page = PAGES[selection]
        st.title(selection)
        page.main()


if __name__ == "__main__":
    main()
