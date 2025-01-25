import os
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_community.graphs import Neo4jGraph
from langchain_openai import ChatOpenAI
from langchain_community.chains.graph_qa.cypher import GraphCypherQAChain
import streamlit as st
from tenacity import retry, stop_after_attempt, wait_exponential
from langchain_core.callbacks import CallbackManager, StdOutCallbackHandler

@retry(
    stop=stop_after_attempt(3),  # Max 3 retries
    wait=wait_exponential(multiplier=1, min=4, max=10)  # Wait 4s, 8s, 16s...
)
def safe_qa_chain_run(qa_chain, inputs):
    try:
        return qa_chain.run(inputs)
    except ValueError as e:
        st.error(f"ValueError: {e}")
        raise

# Load environment variables
load_dotenv()

def main():
    st.set_page_config(layout="wide", page_title="Graph RAG Viewer", page_icon=":chart_with_upwards_trend:")
    st.title("Graph RAG with Neo4j and LangChain")

    # Sidebar configurations
    st.sidebar.title("Configuration")
    openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")
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
            st.sidebar.success("Connected to Neo4j database.")
        except Exception as e:
            st.sidebar.error(f"Failed to connect to Neo4j: {e}")

    graph = st.session_state.get("graph", None)

    # Q&A Section
    if graph:
        st.subheader("Ask a Question")
        question = st.text_input("Enter your question:")
        submit_button = st.button("Get Answer")

        if submit_button and question:
            with st.spinner("Generating answer..."):
                llm = ChatOpenAI(model_name="gpt-3.5-turbo-16k", temperature=0)  # Larger token window
                
                try:
                    # Get raw schema string
                    schema_str = graph.schema
                    
                    # Parse node labels
                    node_labels = list(set(
                        line.split(")-")[0].strip("(:") 
                        for line in schema_str.split("\n") 
                        if line.startswith("(:")
                    ))
                    
                    # Parse relationship types
                    relationships = list(set(
                        line.split("-[:")[1].split("]->")[0].strip()  # Extract text inside "[:...]"
                        for line in schema_str.split("\n") 
                        if "-[:" in line and "]->" in line  # Check for relationship pattern
                    ))

                    # Handle empty relationships
                    if not relationships:
                        st.warning("No relationships detected in the graph. Queries will be limited to node labels.")
                    # st.write("Node Labels:", node_labels)
                    # st.write("Relationships:", relationships)
                    
                    simplified_schema = (
                        f"Node Labels: {', '.join(node_labels)}\n"
                        f"Relationship Types: {', '.join(relationships)}"
                    )
                    st.write("Simplified Schema:", simplified_schema)  # Debug
                    
                except Exception as e:
                    st.error(f"Failed to retrieve schema: {e}")
                    return

                # Shorter prompt template
                prompt = PromptTemplate(
                    template="""Generate a VALID Cypher query to answer this question. Follow these rules:
                - Use ONLY node labels: {node_labels}
                - Use ONLY relationship types: {relationship_types}
                - Do not include properties (e.g., `Person {{name: 'Alice'}}` is invalid)
                - Use `MATCH` and `RETURN` clauses

                Question: {question}

                Cypher Query:""",
                    input_variables=["node_labels", "relationship_types", "query"]
                )

                try:
                    callback_manager = CallbackManager([StdOutCallbackHandler()])

                    qa_chain = GraphCypherQAChain.from_llm(
                        llm=llm,
                        graph=graph,
                        cypher_prompt=prompt,
                        verbose=True,
                        allow_dangerous_requests=True,
                        callback_manager=callback_manager
                    )
                    
                    # Pass schema components along with the question
                    result = safe_qa_chain_run(qa_chain, {
                        "query": question,
                        "node_labels": node_labels,
                        "relationship_types": relationships
                    })
                    
                    # # Debug: Print the full result object
                    # st.write("Full Result Object:", result)
                    
                    # If the result is "I don't know the answer," manually generate and execute the query
                    if result == "I don't know the answer.":
                        st.warning("The QA chain could not generate an answer. Manually generating and executing the query...")
                        
                        # Generate the Cypher query using the prompt template
                        cypher_query = llm.predict(
                            f"""Generate a VALID Cypher query to answer this question. Follow these rules:
                            - Use ONLY node labels: {node_labels}
                            - Use ONLY relationship types: {relationships}
                            - Do not include properties (e.g., `Person {{name: 'Alice'}}` is invalid)
                            - Use `MATCH` and `RETURN` clauses

                            Question: {question}

                            Cypher Query:"""
                        )
                        st.write("Generated Cypher Query:", cypher_query)
                        
                        # Execute the query manually
                        query_result = graph.query(cypher_query)
                        
                        if not query_result:
                            st.warning("No results found for the manually generated query.")
                        else:
                            # Extract the "name" values from the query results
                            answer = [item["d"]["name"] for item in query_result if "d" in item and "name" in item["d"]]
                            
                            if not answer:
                                st.warning("No valid answer found in the query results.")
                            else:
                                st.success("Answer:")
                                st.write(answer)
                    else:
                        st.success("Answer:")
                        st.write(result)
                        
                except Exception as e:
                    st.error(f"Failed after retries: {e}")
                                        

if __name__ == "__main__":
    main()