import os
from dotenv import load_dotenv
from langchain_community.graphs import Neo4jGraph
from langchain_openai import ChatOpenAI
from langchain_community.chains.graph_qa.cypher import GraphCypherQAChain
from tenacity import retry, stop_after_attempt, wait_exponential

# Load environment variables
load_dotenv()
NEO4J_URL = os.getenv("NEO4J_URL2")
NEO4J_USER = os.getenv("NEO4J_USERNAME2")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD2")

# Establish Neo4j connection
graph = Neo4jGraph(url=NEO4J_URL, username=NEO4J_USER, password=NEO4J_PASSWORD)

# OpenAI model for query generation
llm = ChatOpenAI(model_name="gpt-3.5-turbo-16k", temperature=0)

# Retry mechanism for failed queries
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def safe_qa_chain_run(qa_chain, inputs):
    """Handles retries for Neo4j queries"""
    try:
        return qa_chain.run(inputs)
    except ValueError as e:
        return f"Query failed: {str(e)}"
def fetch_graph_data():
    """Fetch relationships from Neo4j and format for visualization."""
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

        # Ensure correct structure
        nodes[source_id] = (source_name, source_label)
        nodes[target_id] = (target_name, target_label)
        edges.append((source_id, target_id, relationship, confidence))

    return nodes, edges  # ✅ Ensure exactly two values are returned


def ask_question(query):
    """Run a natural language question using Neo4j and LangChain"""
    qa_chain = GraphCypherQAChain.from_llm(
        llm=llm, graph=graph, verbose=True, allow_dangerous_requests=True
    )
    return safe_qa_chain_run(qa_chain, {"query": query})

def get_entity_count():
    """Count number of nodes in Neo4j"""
    query = "MATCH (n) RETURN COUNT(n) AS count"
    result = graph.query(query)
    return result[0]["count"] if result else 0

def get_relationship_count():
    """Count number of relationships in Neo4j"""
    query = "MATCH ()-[r]->() RETURN COUNT(r) AS count"
    result = graph.query(query)
    return result[0]["count"] if result else 0
