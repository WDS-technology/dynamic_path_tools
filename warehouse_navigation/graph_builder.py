import json
from pathlib import Path
from typing import Union, List, Dict, Tuple, Optional
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict
from math import sqrt
import glob
from pathlib import Path

def load_warehouse_map(path: Union[str, Path]) -> List[Dict]:
    """Load warehouse map from JSON file (flat list of passage points)."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Warehouse map not found: {path}")
    with path.open("r") as f:
        return json.load(f)["passages"]

def build_graph(passages: List[Dict]):
    """
    Build a directed graph from warehouse map passages and return:
      - G: networkx.DiGraph with nodes storing positions
      - pos_to_node: dict mapping (x, y, z) positions to node IDs
    """
    G = nx.DiGraph()
    pos_to_node = {}

    # Group passages by passage_id
    passages_by_id = defaultdict(list)
    for p in passages:
        passages_by_id[p["passage_id"]].append(p)

    # Sort each passage by 'order' and add nodes
    for pid, points in passages_by_id.items():
        points.sort(key=lambda x: x["order"])
        for wp in points:
            node_id = f"P{pid}_W{wp['order']}"
            pos = (wp["position_x"], wp["position_y"], wp.get("position_z", 0))

            # Add node with attributes
            G.add_node(node_id, pos=pos,
                       passage_id=wp["passage_id"],
                       order=wp["order"],
                       is_intersection=wp["is_intersection"],
                       is_entrance=wp["is_entrance"])

            # Maintain pos -> node dictionary
            pos_to_node[pos] = node_id

    # Add edges within each passage
    for pid, points in passages_by_id.items():
        n = len(points)
        for i, wp in enumerate(points):
            node_id = f"P{pid}_W{wp['order']}"
            if i > 0:
                G.add_edge(node_id, f"P{pid}_W{points[i-1]['order']}")  # backward
            if i < n-1:
                G.add_edge(node_id, f"P{pid}_W{points[i+1]['order']}")  # forward

    # Add edges between passages (intersection jumps)
    sorted_passage_ids = sorted(passages_by_id.keys(), key=int)
    for i in range(len(sorted_passage_ids) - 1):
        curr_points = passages_by_id[sorted_passage_ids[i]]
        next_points = passages_by_id[sorted_passage_ids[i+1]]

        wp_curr = next(p for p in curr_points if p["is_intersection"])
        wp_next = next(p for p in next_points if p["is_intersection"])
        node_curr = f"P{wp_curr['passage_id']}_W{wp_curr['order']}"
        node_next = f"P{wp_next['passage_id']}_W{wp_next['order']}"
        G.add_edge(node_curr, node_next) # forward
        G.add_edge(node_next, node_curr) # backward

    return G, pos_to_node

def shortest_path(G: nx.DiGraph, start: str, end: str, return_coords: bool = False) -> Tuple[List, Optional[str]]:
    """
    Compute shortest path between start and end nodes.
    Also attempts to load a relevant YAML config file based on passage IDs.

    Args:
        G: networkx DiGraph.
        start: starting node ID.
        end: ending node ID.
        return_coords: if True, return list of coordinates instead of node IDs.

    Returns:
        Tuple[List, Optional[str]]: A tuple containing:
            - List of node IDs or list of coordinates along the path.
            - The content of the loaded YAML file as a string, or None if not found.
    """
    path_nodes = nx.shortest_path(G, source=start, target=end)
    start_passage = path_nodes[0].split('_W')[0][1:]
    end_passage = path_nodes[-1].split('_W')[0][1:]

    print(f"Start passage: {start_passage}")
    print(f"End passage: {end_passage}")

    loaded_yaml_content = None
    # Adjust path for glob to be relative to the submodule root
    yaml_files = glob.glob(str(Path(__file__).parent.parent / "warehouse_navigation" / "data" / "*.yaml"))

    print("yaml_files", yaml_files)

    passage_version_1 = start_passage + "_" + end_passage
    passage_version_2 = end_passage + "_" + start_passage

    print("Looking for passage versions:", passage_version_1, passage_version_2)
    
    for yaml_file_path in yaml_files:
        filename = Path(yaml_file_path).name
        if passage_version_1 in filename or passage_version_2 in filename:
            with open(yaml_file_path, 'r') as f:
                loaded_yaml_content = f.read()
            break

    
    if return_coords:
        return [G.nodes[node]["pos"] for node in path_nodes], loaded_yaml_content
    else:
        return path_nodes, loaded_yaml_content


def plot_path(G: nx.DiGraph, path: List[str], title: str = ""):
    """
    Plot graph with highlighted path, ignoring Z.
    (Requires matplotlib and networkx to be installed)
    """
    # Extract only x, y for plotting
    pos = {node: (coords[0], coords[1]) for node, coords in nx.get_node_attributes(G, 'pos').items()}

    nx.draw_networkx_nodes(G, pos, node_size=50)
    nx.draw_networkx_edges(G, pos, alpha=0.3)
    path_edges = list(zip(path[:-1], path[1:]))
    nx.draw_networkx_edges(G, pos, edgelist=path_edges, edge_color='orange', width=2)
    nx.draw_networkx_labels(G, pos, font_size=6)
    plt.title(title)
    plt.axis('equal')
    plt.show()


def find_closest_node(G: nx.DiGraph, target_pos: Tuple[float, float, float]) -> Dict:
    """
    Find the closest node in the graph to a given position.

    Args:
        G: networkx DiGraph with node attribute 'pos' as (x, y, z).
        target_pos: tuple (x, y, z) representing the position to check.

    Returns:
        Dictionary with:
            - node_id: closest node ID
            - pos: coordinates of the closest node
            - distance: Euclidean distance to target_pos
    """
    closest_node = None
    min_dist = float('inf')
    closest_pos = None

    tx, ty, tz = target_pos

    for node_id, data in G.nodes(data=True):
        x, y, z = data['pos']
        dist = sqrt((x - tx)**2 + (y - ty)**2 + (z - tz)**2)
        if dist < min_dist:
            min_dist = dist
            closest_node = node_id
            closest_pos = (x, y, z)

    return {"node_id": closest_node, "pos": closest_pos, "distance": min_dist}
