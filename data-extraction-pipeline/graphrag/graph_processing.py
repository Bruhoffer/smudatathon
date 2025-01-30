def filter_graph_data(raw_data, show_persons=True, show_orgs=True, show_gpe=True, show_laws=True, min_degree=1, min_confidence=0.5):
    """Filters graph data based on node type, degree, and confidence threshold."""
    if not isinstance(raw_data, tuple) or len(raw_data) != 2:
        raise ValueError(f"Expected raw_data to be (nodes, edges), got {type(raw_data)} with length {len(raw_data)}")

    nodes, edges = raw_data
    filtered_nodes = {}
    degree_count = {}

    # Compute node degrees
    for source, target, _, confidence in edges:
        if confidence >= min_confidence:  # 🔥 NEW: Confidence-based filtering
            degree_count[source] = degree_count.get(source, 0) + 1
            degree_count[target] = degree_count.get(target, 0) + 1

    # Filter nodes based on type and degree
    for node_id, (name, entity_type) in nodes.items():
        if (
            (show_persons and entity_type == "PERSON") or
            (show_orgs and entity_type == "ORG") or
            (show_gpe and entity_type == "GPE") or
            (show_laws and entity_type == "LAW")
        ) and degree_count.get(node_id, 0) >= min_degree:
            filtered_nodes[node_id] = (name, entity_type)

    # Filter edges to remove orphaned nodes
    filtered_edges = [
        (source, target, rel, conf) for source, target, rel, conf in edges
        if source in filtered_nodes and target in filtered_nodes
    ]

    return filtered_nodes, filtered_edges
