import csv
import ast
import spacy
from spacy.matcher import Matcher
from py2neo import Graph, Node, Relationship


# Define Matcher for relation patterns
def define_relationship_patterns(nlp):
    matcher = Matcher(nlp.vocab)

    # Pattern for "works for"
    works_for_pattern = [{"POS": "PROPN"}, {"LEMMA": "work"}, {"LOWER": "for"}, {"POS": "PROPN"}]
    matcher.add("WORKS_FOR", [works_for_pattern])

    # Pattern for "located in"
    located_in_pattern = [{"POS": "PROPN"}, {"LEMMA": "locate"}, {"LOWER": "in"}, {"POS": "PROPN"}]
    matcher.add("LOCATED_IN", [located_in_pattern])

    return matcher


# Extract relationships from text
def extract_relationships(text, nlp, matcher):
    """
    Extract relationships from text using dependency parsing and patterns.

    Args:
        text (str): Input text for relationship extraction.
        nlp (Language): spaCy language model.
        matcher (Matcher): Configured spaCy Matcher.

    Returns:
        list: List of extracted relationships.
    """
    doc = nlp(text)
    matches = matcher(doc)
    relationships = []

    for match_id, start, end in matches:
        span = doc[start:end]
        relation_type = nlp.vocab.strings[match_id]  # Get the type of relationship
        relationships.append({
            "relationship": relation_type,
            "start_entity": doc[start].text,
            "end_entity": doc[end - 1].text
        })
    
    return relationships


# Connect to Neo4j database
def connect_to_neo4j(uri, username, password):
    return Graph(uri, auth=(username, password))


# Store relationships in Neo4j
def store_relationships(graph, relationships):
    """
    Store extracted relationships in the Neo4j database.
    """
    for rel in relationships:
        start_node = Node("Entity", name=rel["start_entity"])
        end_node = Node("Entity", name=rel["end_entity"])
        relationship = Relationship(start_node, rel["relationship"], end_node)

        graph.merge(start_node, "Entity", "name")
        graph.merge(end_node, "Entity", "name")
        graph.merge(relationship)


# Process CSV file and extract relationships
def process_csv_and_store(file_path, graph, nlp, matcher):
    """
    Process a CSV file to extract relationships and store them in Neo4j.

    Args:
        file_path (str): Path to the CSV file.
        graph (Graph): Neo4j Graph instance.
        nlp (Language): spaCy language model.
        matcher (Matcher): Configured spaCy Matcher.
    """
    with open(file_path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            try:
                text = row["text"]  # Extract the 'text' column
                entities = ast.literal_eval(row["entities"])  # Convert string to Python list of dicts
                
                # Process the text for relationships
                relationships = extract_relationships(text, nlp, matcher)
                
                # Add relationships from entities
                for i, entity in enumerate(entities[:-1]):  # Pair adjacent entities for relationships
                    start_entity = entity.get("text", None)
                    end_entity = entities[i + 1].get("text", None)
                    if start_entity and end_entity:
                        relationships.append({
                            "relationship": "RELATED_TO",  # Default relationship
                            "start_entity": start_entity,
                            "end_entity": end_entity
                        })
                
                # Store relationships in Neo4j
                store_relationships(graph, relationships)
                print(f"Processed text: {text}")
                print(f"Extracted Relationships: {relationships}")
            
            except Exception as e:
                print(f"Error processing row: {row}, error: {e}")
                continue


if __name__ == "__main__":
    # Initialize NLP model and matcher
    nlp = spacy.load("en_core_web_md")
    matcher = define_relationship_patterns(nlp)

    # Connect to Neo4j
    graph = connect_to_neo4j(uri="bolt://localhost:7687", username="neo4j", password="smudatathon")

    # Process CSV and store relationships
    csv_file_path = "ner_output.csv"  # Replace with your CSV file path
    process_csv_and_store(csv_file_path, graph, nlp, matcher)

    print("All relationships from the CSV have been stored in Neo4j!")
