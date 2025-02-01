import streamlit as st
from graph_queries import fetch_graph_data, ask_question, get_entity_count, get_relationship_count
from graph_processing import filter_graph_data
from graph_visualization import create_network_graph, display_graph

# 🎯 **Set up page**
st.set_page_config(layout="wide", page_title="📊 Graph RAG Viewer", page_icon=":chart_with_upwards_trend:")
st.title("Intelligence Analysis System for the Internal Security Department (ISD)")

# ==============================
# 🔢 **Graph Statistics**
# ==============================
st.sidebar.subheader("📊 Graph Statistics")
st.sidebar.write(f"🔹 **Entities:** {get_entity_count()}")
st.sidebar.write(f"🔸 **Relationships:** {get_relationship_count()}")

# ==============================
# 🎤 **Q&A Section**
# ==============================
st.subheader("💬 Ask a Question")
question = st.text_input("Enter your question:")

if st.button("Get Answer"):
    with st.spinner("🔍 Fetching AI-generated answer..."):
        answer = ask_question(question)
        if answer:
            st.success("✅ Answer:")
            st.write(answer)
        else:
            st.warning("⚠️ No answer found. Try rephrasing your question.")

# ==============================
# 🎛️ **Graph Filters**
# ==============================
st.sidebar.subheader("🔍 Filter Graph")
min_degree = st.sidebar.slider("Minimum Node Degree (Influence)", 0.001, 1.00, 0.001)
min_confidence = st.sidebar.slider("Minimum Confidence Score", 0.1, 1.0, 0.5)

# ==============================
# 🎯 **Entity Search**
# ==============================
st.sidebar.subheader("🔎 Search for an Entity")
search_query = st.sidebar.text_input("Enter entity name (case-insensitive):").strip()

# ℹ️ **Search Behavior Explanation**
st.sidebar.markdown("""
📌 **How Search Works**
- 🔍 The searched entity will be **highlighted in yellow**.
- 🏷️ The graph will **not be filtered**, but the node will stand out.
- 🌍 If the entity is present, the graph **keeps the focus on it**.
""")

# ==============================
# 🌐 **Generate Graph**
# ==============================
st.subheader("🌐 Network Graph Visualization")

if st.button("Generate Graph"):
    with st.spinner("📡 Fetching data from Neo4j..."):
        raw_data = fetch_graph_data()

        if not raw_data:
            st.error("❌ Failed to fetch data. Check database connection.")
        else:
            with st.spinner("🛠️ Processing graph data..."):
                nodes, edges = filter_graph_data(
                    raw_data, min_degree=min_degree, min_confidence=min_confidence
                )

            if not nodes or not edges:
                st.warning("⚠️ No graph data available after filtering.")
            else:
                with st.spinner("🎨 Rendering graph..."):
                    net = create_network_graph(nodes, edges, search_query)
                    display_graph(net)
                st.success("🎉 Graph generated successfully!")
