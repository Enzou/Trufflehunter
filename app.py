import streamlit as st

import ui.eda
import ui.cluster
import ui.trufflehunter
import ui.stats

PAGES = {
    "Exploratory Data Analysis": ui.eda,
    "Clustering": ui.cluster,
    "TrufflesHunt": ui.trufflehunter,
    "Statistics": ui.stats
}


def main():
    st.sidebar.title("Navigation")
    selection = st.sidebar.radio("Go to", list(PAGES.keys()))

    with st.spinner(f"Loading {selection} ..."):
        page = PAGES[selection]
        page.main()


if __name__ == "__main__":
    main()
