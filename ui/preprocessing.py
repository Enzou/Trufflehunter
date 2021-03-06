from typing import Tuple, Optional, Callable, Dict, List
from pathlib import PurePath, Path
from anytree import Node, RenderTree, ContRoundStyle, Resolver, ChildResolverError, PostOrderIter
from anytree.exporter import DotExporter, DictExporter
import streamlit as st
import pandas as pd
from anytree.importer import DictImporter
from tqdm import tqdm

import src.utils.io as io
from ui.components.data_selector import select_file
from src.preprocessing import convert_weblog, filter_by_session_length
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
    "perform-?.*",  # infos related to perform conferences
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

source_col = 'ua_name'

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
def build_page_hierarchy(df: pd.DataFrame, prepruning_nodes: Optional[List] = None, update_fn: Callable = lambda x: x) -> Tuple[Dict, int]:
    root = Node('/', count=0)
    tree = {'/': root}
    max_count = 0  # for the color
    for ua_name in update_fn(df[source_col]):
        if "loading of page" in ua_name:
            url_path = ua_name.split(' ')[-1]
            frags = url_path.split("/")[1:-1]
            frags = ['/'] + ['-' if f == '' else f for f in frags]  # fix root-node and handle empty parts

            parent_node = root
            for i, (parent, node) in enumerate(zip(frags[:-1], frags[1:])):  # add missing in between nodes
                id = '/'.join([parent, node])
                if id not in tree:
                    # page indicates pagination of previous site, so just repeat it
                    if prepruning_nodes is not None:
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


def prune_tree(root: Node, min_nodes: int = 2) -> Node:
    '''
    Post-Prune page tree after creation by removing nodes that occurred at most 1 time.
    Furthermore, intermediary nodes, that never have actually been visited and have only one child will be collapsed
    :param root:
    :param min_nodes:
    :return:
    '''
    if min_nodes > 0:
        for node in PostOrderIter(root):
            if node.count < min_nodes:
                node.parent = None
                del node

    return root


def analyze_paths(df: pd.DataFrame) -> Tuple[Node, int]:
    use_prepruning = st.checkbox("Use Pre-Pruning?")
    tree, max_count = build_page_hierarchy(df, aggregation_nodes if use_prepruning else None)
    root = DictImporter().import_(tree)

    # if st.checkbox("Show pagetree in ASCII?", value=False):
    #     st.text(RenderTree(root, style=ContRoundStyle()))
    # if st.checkbox("Show pagetree as graph?", value=True):
    min_counts = st.slider("Minimum number of counts:", value=2, min_value=0, max_value=50)
    root = prune_tree(root, min_counts)

    return root, max_count


def get_full_path(node: Node) -> str:
    return node.separator.join([str(n.name) for n in node.path])[1:]  # drop initial redundant / of root node


def mine_mapping_rules(root: Node, min_leaf_nodes: int = 2) -> Tuple[Node, Ruleset]:
    rules = []

    for n in PostOrderIter(root):
        # parents with > n leaf nodes should be activity
        n.is_activity = False
        if not n.is_leaf and len(n.children) > min_leaf_nodes:
            if n.parent is not None:
                if n.parent.name == "technologies" and n.name.endswith("-monitoring"):  # TODO hack to filter out specific potential activity nodes
                    continue
                elif n.parent.name == "/" and n.name.startswith("perform"):
                    continue  # manually added rule

            n.is_activity = True
            rules.append((rf"{get_full_path(n)}/*", f"Visit {n.name.title()}"))
            # remove non activity child nodes
            for child in n.children:
                if not child.is_activity:
                    child.parent = None
                    del child
        elif not n.is_root:
            n.parent.children += n.children

        # TODO siblings with similar names should be combined

    # no_leafs = len([True for n in PostOrderIter(root) if n.is_leaf])
    # print(f"Tree has {no_leafs} leaf-nodes")

    rules += [
        (r"perform-?\w*", "View Perform-Conference Details"),
        (r"/.*", "View homepage")
    ]

    rs = Ruleset(rules)
    return root, rs


def draw_page_tree(root: Node, max_count: int) -> DotExporter:
    # color is HSV; saturation determines color intensity
    fig = DotExporter(root, options=["rankdir = LR; node [color=black, style=filled];"],
                      nodenamefunc=lambda n: f"{n.name}\ncount={n.count}",
                      nodeattrfunc=lambda node: f'fillcolor="0.6 {node.count / max_count} 1"')

    st.graphviz_chart(''.join(fig))
    return fig


def draw_activity_tree(root: Node, rules) -> DotExporter:
    fig = DotExporter(root, options=["rankdir = LR;"],
                      nodenamefunc=lambda n: f"{n.name}\ncount={n.count}",
                      nodeattrfunc=lambda node: f'penwidth={5 if node.is_activity else 1}')

    st.graphviz_chart(''.join(fig))
    return fig


def export_page_tree(fig: DotExporter, file_name: str) -> None:
    img_name = file_name.replace('.csv', '.svg')
    fig.to_picture(img_name)
    st.write(f"exported page tree image to '{img_name}'")


def load_data(file_name: str) -> pd.DataFrame:
    st.spinner("Loading data " + file_name)
    df = io.load_csv_data(file_name)
    st.write(f"Loaded {len(df)} entries")
    return df


def convert_to_eventlog(df: pd.DataFrame, rules: Ruleset, file_name: str) -> None:
    # map `from column` -> `to column` using optional mapping function
    col_mapping = {
        'visitId': 'visitId',
        'ua_starttime': 'starttime',
        'ua_duration': 'duration',
        's_clientType': 'clientType'
    }
    col_transformations = [
        ('ua_name', 'activity', rules.entry_to_activity),
        ('ua_name', 'path', lambda v: v.split(' ')[-1]),
    ]
    elog = convert_weblog(df, col_mapping, col_transformations, activity_attr='activity',
                          case_id_attr='visitId', timestamp_attr='starttime',
                          ts_parse_params={'unit': 'ms'})
    dest_file = Path("./data/interim") / file_name
    elog.export_to_csv(dest_file)
    st.text(f"Saved event log to {dest_file} ✔️")


def main():
    cli_mode = not st._is_running_with_streamlit

    data_view_slot = st.empty()
    file_name, df = select_file('raw')

    # preprocess web log
    min_session_len = st.slider("Min. actions per session", min_value=1, max_value=10, value=2)
    df_filtered = filter_by_session_length(df, 'visitId', min_session_len)
    df_len = len(df_filtered)
    st.markdown(f"Filtered {len(df) - df_len} entries - **{df_len}** entries remaining")
    data_view_slot.dataframe(df_filtered.head(1000))

    st.header("Create activity tree")
    res = analyze_paths(df_filtered)

    # fig = draw_page_tree(*res)
    root, rules = mine_mapping_rules(res[0])
    if st.checkbox("Show activity tree", value=True):
        fig = draw_activity_tree(root, rules)
        if st.button("💾"):
            export_page_tree(fig, file_name)

    st.markdown('------')
    if st.button("Save as event log") or cli_mode:
        convert_to_eventlog(df_filtered, rules, file_name)


if __name__ == "__main__":
    main()
