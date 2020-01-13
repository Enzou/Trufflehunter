import functools
from typing import Tuple, Optional, Callable, Dict
from pathlib import PurePath

import graphviz
from anytree import Node, RenderTree, ContRoundStyle, Resolver, ChildResolverError, PostOrderIter
from anytree.exporter import DotExporter, DictExporter
import streamlit as st
import pandas as pd
from anytree.importer import DictImporter
from tqdm import tqdm

import src.utils.io as io
from src.preprocessing import convert_weblog
from src.preprocessing.ruleset import Ruleset

aggregation_nodes = [
    "author",  # under blog
    "availability-and-performance",
    "blog",  # /wp-content/*  is resource
    "career",
    "configuration",
    "contact-support",
    "customers",  # TODO except archive/license-agreement
    # "news",
    "data-privacy",
    "diagnostics",  # under tools .. has several other intermed. paths
    "integrations",
    "javabook",
    "language",
    "partners",
    "perform-*",  # infos related to perform conferences
    "platform",  # TODO split between platform general and view of undercategory and 'comparison' and 'artificial-intelligence'
    "press-release",
    "release-notes",
    "resource-type",
    "security-alert",  # under news
    "services-support",
    "sla",  # under categories: saas and manager and each has sprint entries
    "solutions",  # TODO split between solutions in general and view of undercategory
    "sso",
    "support",
    "tag",
    "trial",
    "technologies",  # /* : resources
    "upgrade"
]


mappings = Ruleset([
    # if just string-rule is given, the resulting activity will be 'View <Page>'
    "blog/author",
    "blog",
    (r"perform-?\w*", "View Perform-Conference Details"),
])


# event_information: ['dynatrace-go', 'perform*' ]


# def get_node(root: Node, path: List) -> Node:
#     node = root
#     for f in path:
#         node = next(c for c in node.children if c.name == f)
#     return node
#


class tqdm:
    def __init__(self, iterable, title=None):
        if title:
            st.write(title)
        self.prog_bar = st.progress(0)
        self.iterable = iterable
        self.length = len(iterable)
        self.i = 0

    def __iter__(self):
        for obj in self.iterable:
            yield obj
            self.i += 1
            current_prog = self.i / self.length
            self.prog_bar.progress(current_prog)


@st.cache
def build_page_hierarchy(df: pd.DataFrame, update_fn: Callable = lambda x: x) -> Tuple[Dict, int]:
    root = Node('/', count=0)
    tree = {'/': root}
    max_count = 0  # for the color
    for ua_name in update_fn(df.ua_name):
        if "loading of page" in ua_name:
            url_path = ua_name.split(' ')[-1]
            frags = url_path.split("/")[1:-1]
            frags = ['/'] + ['-' if f == '' else f for f in frags]  # fix root-node and handle empty parts

            parent_node = root
            for i, (parent, node) in enumerate(zip(frags[:-1], frags[1:])):  # add missing in between nodes
                id = '/'.join([parent, node])
                if id not in tree:
                    # pre-pruning:
                    # page indicates pagination of previous site, so just repeat it
                    if (parent in aggregation_nodes and node != 'author') or node == "page":
                        drop_last_n = len(frags) - i - 1
                        frags = frags[:-drop_last_n]  # drop resource for aggregation # TODO fix dirty hack for pruned tree
                        break
                    parent_node = Node(node, parent_node, count=0)
                    tree[id] = parent_node
                else:
                    parent_node = tree[id]

            node_id = '/'.join(frags[-2:])  # use last two parts as id to avoid conflicts with other nodes with same name
            node = tree[node_id]
            node.count += 1
            if node.count > max_count:
                max_count = node.count

    exporter = DictExporter()
    d = exporter.export(root)

    return d, max_count


# def build_page_hierarchy_slow(df: pd.DataFrame) -> Tuple[Node, int]:
#     root = Node('.', count=0)
#     r = Resolver("name")
#     max_count = 0  # for the color
#
#     for ua_name in tqdm(df.ua_name):
#         if "loading of page" in ua_name:
#             p = PurePath('.' + ua_name.split(' ')[-1])
#
#             try:
#                 # parent = r.get(root, str(p.parent))
#                 path = str(p)
#                 node = r.get(root, str(p))
#             except ChildResolverError:
#                 parent = root
#                 # recursively create parent nows if missing
#                 for par in list(p.parents)[1::-1]:  # first two items are '.' and root node -> skip them
#                     try:
#                         parent = r.get(root, str(p))
#                     except ChildResolverError:
#                         parent = Node(par.name, parent, count=0)
#                 node = Node(p.name, parent, count=0)
#
#             node.count += 1
#             if node.count > max_count:
#                 max_count = node.count
#
#     return root, max_count


def build_page_visit_graph(df: pd.DataFrame) -> Node:
    tree = {'/': Node('/')}
    for ua_name in tqdm(df.ua_name):
        if "loading of page" in ua_name:
            url_path = ua_name.split(' ')[-1]
            frags = url_path.split("/")[:-1]
            if len(frags) == 0:
                print(f"invalid ua_name: {ua_name}")
                continue
            frags[0] = '/'  # fix name of root node

            for parent, node in zip(frags[:-1], frags[1:]):  # add missing in between nodes
                tree[node] = Node(node, tree[parent])

    return tree['/']


def prune_tree(root: Node, min_nodes: int = 2) -> Node:
    """
    Post-Prune page tree after creation by removing nodes that occured at most 1 time.
    Furthermore, intermediary nodes, that never have actually been visited and have only one child will be collapsed
    """
    if min_nodes > 0:
        for node in PostOrderIter(root):
            if node.count < min_nodes:
                node.parent = None
                del node

    return root


def analyze_paths(df: pd.DataFrame) -> Tuple[Node, int]:
    tree, max_count = build_page_hierarchy(df)
    root = DictImporter().import_(tree)

    # TODO filter sessions with only 1 entry
    available_rules = []
    selected_rules = st.multiselect("Mapping rules", options=available_rules)

    new_rule = st.text_input("New Rule: ")
    if st.button("+"):
        available_rules.append(new_rule)

    if st.checkbox("Show pagetree in ASCII?", value=False):
        st.text(RenderTree(root, style=ContRoundStyle()))
    if st.checkbox("Show pagetree as graph?", value=True):
        st.text(f"max count {max_count}")
        # color is HSV; saturation determines color intensity

        min_counts = st.slider("Minimum number of counts:", value=2)
        root = prune_tree(root, min_counts)

        no_leafs = len([True for n in PostOrderIter(root) if n.is_leaf])
        print(f"Tree has {no_leafs} leaf-nodes")

    return root, max_count


def draw_page_tree(root: Node, max_count: int) -> DotExporter:
    fig = DotExporter(root, options=["rankdir = LR; node [color=black, style=filled];"],
                      nodenamefunc=lambda n: f"{n.name}\ncount={n.count}",
                      nodeattrfunc=lambda node: f'fillcolor="0.6 {node.count / max_count} 1"')

    st.graphviz_chart(''.join(fig))
    # for l in fig:
    #     print(l)
    return fig


def export_page_tree(fig: DotExporter, file_name: str) -> None:
    img_name = file_name.replace('.csv', '.svg')
    fig.to_picture(img_name)
    print(f"exported page tree image to '{img_name}'")


def load_data(file_name: str) -> pd.DataFrame:
    st.spinner("Loading data " + file_name)
    df = io.load_csv_data(file_name)
    st.write(f"Loaded {len(df)} entries")
    return df


def main():
    if not st._is_running_with_streamlit:
        print("Not using streamlit - using fallback instead")
    st.title("Exploratory Data Analysis")

    st.sidebar.radio("Stage:", ['Exploratory Data Analysis'])

    available_files = io.get_available_datasets()
    file_name = st.sidebar.selectbox("Source web log: ",
                                     options=available_files,
                                     index=available_files.index('dt_sessions_70k.csv'))
    df = load_data(file_name)

    res = analyze_paths(df)
    fig = draw_page_tree(*res)
    if st.button("Export page tree"):
        export_page_tree(fig, file_name)
    # build_page_visit_graph(df)

    if st.button("Convert to weblog"):
        convert_weblog(df, mappings)


if __name__ == "__main__":
    main()
