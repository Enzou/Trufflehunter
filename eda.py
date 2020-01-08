from typing import Tuple

import streamlit as st
import pandas as pd
from pathlib import Path
from anytree import Node, RenderTree, ContRoundStyle
from anytree.exporter import DotExporter


def build_page_hierarchy(df: pd.DataFrame) -> Tuple[Node, int]:
    tree = {'/': Node('/', count=0)}
    max_count = 0
    for ua_name in df.ua_name:
        if "loading of page" in ua_name:
            url_path = ua_name.split(' ')[-1]
            frags = url_path.split("/")[:-1]
            frags[0] = '/'  # fix name of root node

            for parent, node in zip(frags[:-1], frags[1:]):  # add missing in between nodes
                if node not in tree:
                    tree[node] = Node(node, tree[parent], count=0)
            tree[frags[-1]].count += 1
            if tree[frags[-1]].count > max_count:
                max_count = tree[frags[-1]].count

    return tree['/'], max_count


def analyze_paths(df: pd.DataFrame) -> None:
    root, max_count = build_page_hierarchy(df)
    if st.checkbox("Show pagetree in ASCII?", value=False):
        st.text(RenderTree(root, style=ContRoundStyle()))
    if st.checkbox("Show pagetree as graph?"):
        st.text(f"max count {max_count}")
        # color is HSV; saturation determines color intensity
        fig = DotExporter(root, options=["node [color=black, style=filled];"],
                          nodenamefunc=lambda n: f"{n.name}\ncount={n.count}",
                          nodeattrfunc=lambda node: f'fillcolor="0.6 {node.count/max_count} 1"')
        # for l in fig:
        #     print(l)
        fig.to_picture('page_tree.png')
        st.graphviz_chart(''.join(fig))


def main():
    st.title("Exploratory Data Analysis")
    DATA_DIR = Path('data/raw')
    df = pd.read_csv(DATA_DIR / 'dt_sessions_1k.csv')

    analyze_paths(df)


if __name__ == "__main__":
    main()
