import os
from dotenv import load_dotenv
import streamlit as st
from langchain.prompts import PromptTemplate
from langchain_community.graphs import Neo4jGraph
from langchain_openai import ChatOpenAI
from langchain_community.chains.graph_qa.cypher import GraphCypherQAChain
from tenacity import retry, stop_after_attempt, wait_exponential
import networkx as nx
from pyvis.network import Network
import tempfile
import streamlit.components.v1 as components

# Load environment variables
load_dotenv()

# Define Colors for Different Entity Types
ENTITY_COLORS = {
    "PERSON": "#ff4c4c",    # 🔴 Red
    "ORG": "#4caf50",       # 🟢 Green
    "GPE": "#3498db",       # 🔵 Blue
    "LAW": "#f39c12",       # 🟠 Orange
    "DATE": "#8e44ad",      # 🟣 Purple
    "Unknown": "#95a5a6"    # ⚪ Gray (Default)
}

# Retry mechanism for handling ValueError
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def safe_qa_chain_run(qa_chain, inputs):
    try:
        return qa_chain.run(inputs)
    except ValueError as e:
        st.error(f"ValueError: {e}")
        raise

def fetch_graph_data(graph):
    """Fetch relationships from Neo4j and format for visualization with entity types."""
    query = """
    MATCH (n)-[r]->(m) 
    RETURN 
        elementId(n) AS source, 
        type(r) AS relationship, 
        elementId(m) AS target, 
        labels(n)[0] AS source_label, 
        labels(m)[0] AS target_label, 
        n.name AS source_name, 
        m.name AS target_name,
        r.confidence AS confidence
    LIMIT 200
    """
    results = graph.query(query)

    nodes = {}
    edges = []

    for record in results:
        source_id = record["source"]
        target_id = record["target"]
        relationship = record["relationship"]
        source_name = record["source_name"] or "Unknown"
        target_name = record["target_name"] or "Unknown"
        source_label = record["source_label"] or "Unknown"
        target_label = record["target_label"] or "Unknown"
        confidence = record["confidence"] if record["confidence"] else 0.5

        if source_name.startswith("https://") or target_name.startswith("https://"):
            continue

        nodes[source_id] = (source_name, source_label)
        nodes[target_id] = (target_name, target_label)
        edges.append((source_id, target_id, relationship, confidence))

    return nodes, edges


def create_network_graph(nodes, edges):
    """Create an interactive network graph with PyVis, using improved styles."""
    net = Network(height="800px", width="100%", directed=True, notebook=False)
    net.barnes_hut(gravity=-2000, central_gravity=0.1, spring_length=100, spring_strength=0.05)

    # Add nodes with colors and sizes based on entity type
    for node_id, (node_name, node_type) in nodes.items():
        color = ENTITY_COLORS.get(node_type, "#95a5a6")  # Default to gray if type is unknown
        node_size = 10 + len(node_name) * 0.5  # Scale size based on name length
        net.add_node(node_id, label=node_name, title=f"{node_name} ({node_type})", color=color, size=node_size)

    # Add edges with thickness based on confidence score
    for source, target, relationship, confidence in edges:
        edge_width = 1 + confidence * 3  # Scale edge thickness by confidence score
        net.add_edge(source, target, title=relationship, width=edge_width)

    return net

def display_graph(net):
    """Render PyVis graph in Streamlit"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp_file:
        net.save_graph(tmp_file.name)
        components.html(open(tmp_file.name, "r").read(), height=800, scrolling=True)

def main():
    st.set_page_config(layout="wide", page_title="Graph RAG Viewer", page_icon=":chart_with_upwards_trend:")
    st.title("📊 Graph RAG with Neo4j and LangChain")

    # Sidebar configurations
    st.sidebar.title("Configuration")
    openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")
    debug_mode = st.sidebar.checkbox("Enable Debug Mode")

    if openai_api_key:
        os.environ["OPENAI_API_KEY"] = openai_api_key

    # Neo4j Connection
    st.sidebar.subheader("Neo4j Connection")
    neo4j_url = st.sidebar.text_input("Neo4j URL", value="bolt://localhost:7687")
    neo4j_username = st.sidebar.text_input("Neo4j Username", value="neo4j")
    neo4j_password = st.sidebar.text_input("Neo4j Password", type="password")
    connect_button = st.sidebar.button("Connect to Neo4j")

    if "graph" not in st.session_state and connect_button:
        try:
            graph = Neo4jGraph(url=neo4j_url, username=neo4j_username, password=neo4j_password)
            st.session_state["graph"] = graph
            st.sidebar.success("✅ Connected to Neo4j database.")
        except Exception as e:
            st.sidebar.error(f"❌ Failed to connect to Neo4j: {e}")

    graph = st.session_state.get("graph", None)

    # Q&A Section
    if graph:
        st.subheader("💬 Ask a Question")
        question = st.text_input("Enter your question:")
        submit_button = st.button("Get Answer")

        if submit_button and question:
            with st.spinner("🔄 Generating answer..."):
                llm = ChatOpenAI(model_name="gpt-3.5-turbo-16k", temperature=0)
                qa_chain = GraphCypherQAChain.from_llm(
                    llm=llm, graph=graph, verbose=True, allow_dangerous_requests=True
                )
                result = safe_qa_chain_run(qa_chain, {"query": question})
                st.success("✅ Answer:")
                st.write(result)

        # Network Graph Visualization
        st.subheader("🌐 Network Graph Visualization")
        if st.button("Generate Graph"):
            with st.spinner("🔄 Fetching data from Neo4j..."):
                nodes, edges = fetch_graph_data(graph)
                if not nodes or not edges:
                    st.warning("⚠️ No graph data available.")
                else:
                    net = create_network_graph(nodes, edges)
                    display_graph(net)
                    st.success("🎉 Graph generated successfully!")

if __name__ == "__main__":
    main()
