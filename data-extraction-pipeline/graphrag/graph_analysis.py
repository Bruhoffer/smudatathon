import networkx as nx
from community import community_louvain

def compute_pagerank(nodes, edges):
    """Computes PageRank for each node in the graph."""
    G = nx.DiGraph()
    
    if not nodes or not edges:
        return {}

    for node_id in nodes.keys():
        G.add_node(node_id)

    for source, target, _, _ in edges:
        G.add_edge(source, target)

    return nx.pagerank(G)

def detect_communities(nodes, edges):
    """Detects communities using Louvain Modularity"""
    G = nx.Graph()

    if not nodes or not edges:
        return {}

    for node_id in nodes.keys():
        G.add_node(node_id)

    for source, target, _, _ in edges:
        G.add_edge(source, target)

    return community_louvain.best_partition(G)
