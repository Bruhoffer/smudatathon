from pyvis.network import Network
import tempfile
import networkx as nx
import json
import streamlit.components.v1 as components
from graph_analysis import compute_pagerank, detect_communities

# 🎨 **Define Colors for Different Entity Types**
ENTITY_COLORS = {
    "PERSON": "#ff4c4c",    # 🔴 Red
    "ORG": "#4caf50",       # 🟢 Green
    "GPE": "#3498db",       # 🔵 Blue
    "LAW": "#f39c12",       # 🟠 Orange
    "DATE": "#8e44ad",      # 🟣 Purple
    "Unknown": "#95a5a6"    # ⚪ Gray (Default)
}

def create_network_graph(nodes, edges, search_query=None):
    """Creates an interactive network graph with PyVis, enhanced with better tooltips and search zoom."""
    net = Network(height="800px", width="100%", directed=True, notebook=False)
    net.barnes_hut(gravity=-2000, central_gravity=0.1, spring_length=100, spring_strength=0.05)

    # Compute PageRank & Community Detection
    pagerank_scores = compute_pagerank(nodes, edges)
    communities = detect_communities(nodes, edges)

    existing_nodes = set(nodes.keys())
    search_focus_node = None  # Store node ID to zoom in later

    for node_id, (node_name, node_type) in nodes.items():
        color = ENTITY_COLORS.get(node_type, "#95a5a6")  
        node_size = 10 + (pagerank_scores.get(node_id, 0) * 300)  
        community_id = communities.get(node_id, 0)  

        # Highlight search query
        if search_query and search_query.lower() in node_name.lower():
            color = "#FFD700"  # Bright Yellow
            search_focus_node = node_id  # Save node for zoom-in effect

        # **Better Tooltip with Styling**
        node_tooltip = f"""
            🔹 {node_name}
            📌 Type: {node_type}
            🔥 Influence: {pagerank_scores.get(node_id, 0):.3f}
            🌎 Community: {community_id}
            """


        net.add_node(
            node_id, 
            label=node_name, 
            title=node_tooltip.strip(),  # Ensure no extra spaces
            color=color, 
            size=node_size, 
            group=community_id
        )

    # Add edges only if both source and target exist
    for source, target, relationship, confidence in edges:
        if source in existing_nodes and target in existing_nodes:
            edge_width = 1 + confidence * 3  

            # **Better Tooltip for Edge**
            edge_tooltip = f"""
            🔗 Relationship: {relationship}
            ✅ Confidence: {confidence:.2f}
            """


            net.add_edge(
                source, target, 
                title=edge_tooltip.strip(),  # Ensure no extra spaces
                width=edge_width
            )

    # ✅ Auto-focus on searched entity (if found) with proper JSON formatting
    if search_focus_node:
        options_dict = {
            "physics": {
                "barnesHut": {
                    "gravitationalConstant": -5000,
                    "centralGravity": 0.3
                }
            },
            "interaction": {
                "hover": True,
                "zoomView": True
            },
            "manipulation": {
                "enabled": False
            },
            "nodes": {
                "borderWidth": 2,
                "borderWidthSelected": 4,
                "shape": "dot"
            },
            "edges": {
                "smooth": {
                    "enabled": True,
                    "type": "continuous"
                },
                "arrows": {
                    "to": {"enabled": True}
                }
            },
            "focus": {
                "node": search_focus_node,
                "scale": 2.0
            }
        }
        
        net.set_options(json.dumps(options_dict))  # ✅ Use json.dumps() to prevent formatting issues

    return net


def display_graph(net):
    """Render PyVis graph in Streamlit."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp_file:
        net.save_graph(tmp_file.name)
        components.html(open(tmp_file.name, "r").read(), height=800, scrolling=True)
