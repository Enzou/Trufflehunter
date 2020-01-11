from typing import Tuple
from pathlib import PurePath
from anytree import Node, RenderTree, ContRoundStyle, Resolver, ChildResolverError
from anytree.exporter import DotExporter
import streamlit as st
import pandas as pd
import tqdm

from src.utils.io import load_csv_data

FILE_NAME = 'dt_sessions_full.csv'

mappings = [
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


# def get_node(root: Node, path: List) -> Node:
#     node = root
#     for f in path:
#         node = next(c for c in node.children if c.name == f)
#     return node
#

def build_page_hierarchy(df: pd.DataFrame) -> Tuple[Node, int]:
    root = Node('/', count=0)
    tree = {'/': root}
    max_count = 0  # for the color
    for ua_name in tqdm.tqdm(df.ua_name):
        if "loading of page" in ua_name:
            url_path = ua_name.split(' ')[-1]
            frags = url_path.split("/")[1:-1]
            frags = ['/'] + ['-' if f == '' else f for f in frags]  # fix root-node and handle empty parts

            parent_node = root
            for i, (parent, node) in enumerate(zip(frags[:-1], frags[1:])):  # add missing in between nodes
                id = '/'.join([parent, node])
                if id not in tree:
                    if parent in mappings and node != 'author':
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

    return tree['/'], max_count


def build_page_hierarchy_slow(df: pd.DataFrame) -> Tuple[Node, int]:
    root = Node('.', count=0)
    r = Resolver("name")
    max_count = 0  # for the color

    for ua_name in tqdm.tqdm(df.ua_name):
        if "loading of page" in ua_name:
            p = PurePath('.' + ua_name.split(' ')[-1])

            try:
                # parent = r.get(root, str(p.parent))
                path = str(p)
                node = r.get(root, str(p))
            except ChildResolverError:
                parent = root
                # recursively create parent nows if missing
                for par in list(p.parents)[1::-1]:  # first two items are '.' and root node -> skip them
                    try:
                        parent = r.get(root, str(p))
                    except ChildResolverError:
                        parent = Node(par.name, parent, count=0)
                node = Node(p.name, parent, count=0)

            node.count += 1
            if node.count > max_count:
                max_count = node.count

    return root, max_count


def build_page_visit_graph(df: pd.DataFrame) -> None:
    tree = {'/': Node('/')}
    for ua_name in tqdm.tqdm(df.ua_name):
        if "loading of page" in ua_name:
            url_path = ua_name.split(' ')[-1]
            frags = url_path.split("/")[:-1]
            if len(frags) == 0:
                print(f"invalid ua_name: {ua_name}")
                continue
            frags[0] = '/'  # fix name of root node

            for parent, node in zip(frags[:-1], frags[1:]):  # add missing in between nodes
                tree[node] = Node(node, tree[parent])

    fig = DotExporter(tree['/'])
    with open(FILE_NAME.replace('.csv', '.dot'), 'w') as f:
        for l in fig:
            f.write(f"{l}\n")


def is_leaf_parent(node: Node) -> bool:
    pass


def prune_tree(node: Node, max_count: int) -> DotExporter:
    pass


def analyze_paths(df: pd.DataFrame) -> None:
    # start = timeit()
    # root, max_count = build_page_hierarchy(df)
    # mid = timeit()
    root, max_count = build_page_hierarchy(df)
    # end = timeit()

    # print(f"Timings: new: {mid-start} / old: {end - mid}")

    # TODO filter sessions with only 1 entry
    # TODO filter nodes in tree with at most 1 visit

    if st.checkbox("Show pagetree in ASCII?", value=False):
        st.text(RenderTree(root, style=ContRoundStyle()))
    if st.checkbox("Show pagetree as graph?", value=True):
        st.text(f"max count {max_count}")
        # color is HSV; saturation determines color intensity
        fig = DotExporter(root, options=["node [color=black, style=filled];"],
                          nodenamefunc=lambda n: f"{n.name}\ncount={n.count}",
                          nodeattrfunc=lambda node: f'fillcolor="0.6 {node.count / max_count} 1"')

        if st.checkbox("Prune?"):
            prune_tree(root, max_count)

        img_name = FILE_NAME.replace('.csv', '.svg')
        fig.to_picture(img_name)
        print(f"exported page tree image to '{img_name}'")
        st.graphviz_chart(''.join(fig))
        # for l in fig:
        #     print(l)


def main():
    st.title("Exploratory Data Analysis")
    df = load_csv_data(FILE_NAME)
    analyze_paths(df)
    # build_page_visit_graph(df)


if __name__ == "__main__":
    main()
