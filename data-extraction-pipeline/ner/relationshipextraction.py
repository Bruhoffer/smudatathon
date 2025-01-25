import ast
import csv
from py2neo import Graph, Node, Relationship
import opennre
from dotenv import load_dotenv
import os

load_dotenv()

# Retrieve Neo4j credentials
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Set the correct path for GloVe files

def store_relationships(graph, relationships, source, page, confidence_threshold=0.5):
    """
    Store extracted relationships in the Neo4j database with labels derived from entity labels.
    Includes source and page metadata as relationship properties.
    Only stores relationships with confidence above the specified threshold.
    """
    if not relationships:
        print("No relationships to store.")
        return

    for rel in relationships:
        try:
            # Filter by confidence threshold
            if rel.get("confidence", 0) < confidence_threshold:
                print(f"Skipping relationship with low confidence: {rel}")
                continue

            # Use the existing entity labels as node labels
            start_label = rel.get("start_label", "Entity")  # Default to 'Entity' if label is missing
            end_label = rel.get("end_label", "Entity")

            # Create nodes
            start_node = Node(start_label, name=rel["start_entity"])
            end_node = Node(end_label, name=rel["end_entity"])

            # Create relationship with metadata
            relationship = Relationship(
                start_node,
                rel["relationship"],
                end_node,
                confidence=rel.get("confidence", 0),  # Add confidence as a property
                source=source,
                page=page
            )

            # Merge nodes and relationship
            graph.merge(start_node, start_label, "name")
            graph.merge(end_node, end_label, "name")
            graph.merge(relationship)
        except Exception as e:
            print(f"Error storing relationship {rel}: {e}")
            
def extract_relationships_with_opennre(text, entities, model):
    """
    Extract relationships using OpenNRE between entities in the text.
    """
    relationships = []

    # Check if at least two entities are present
    if len(entities) < 2:
        print("Less than two entities in text, skipping.")
        return relationships

    # Iterate over entity pairs
    for i, entity1 in enumerate(entities):
        for j, entity2 in enumerate(entities):
            if i >= j:  # Avoid duplicate and self-pairing
                continue

            try:
                # Check if entity spans are valid
                h_pos_start = text.find(entity1["text"])
                t_pos_start = text.find(entity2["text"])
                if h_pos_start == -1 or t_pos_start == -1:
                    print(f"Entity span not found in text: {entity1['text']}, {entity2['text']}")
                    continue

                # Use OpenNRE to infer the relationship
                try:
                    relation = model.infer({
                        'text': text,
                        'h': {'pos': [h_pos_start, h_pos_start + len(entity1["text"])]},
                        't': {'pos': [t_pos_start, t_pos_start + len(entity2["text"])]}
                    })
                except Exception as e:
                    print(f"Error during model inference: {e}")
                    continue

                # Handle tuple structure of relation
                if isinstance(relation, tuple) and len(relation) == 2:
                    relation_type, confidence = relation
                    if confidence > 0.5:  # Confidence threshold
                        relationships.append({
                            "start_entity": entity1["text"],
                            "start_label": entity1["label"],
                            "relationship": relation_type,
                            "end_entity": entity2["text"],
                            "end_label": entity2["label"],
                            "confidence": confidence
                        })
                else:
                    print(f"Invalid or unexpected relation object: {relation}")

            except Exception as e:
                print(f"Error inferring relationship for entities {entity1['text']} and {entity2['text']}: {e}")

    return relationships


def process_csv_and_store(file_path, graph, model):
    """
    Process the CSV file, extract relationships, and store them in Neo4j.
    Includes source and page metadata.
    """
    try:
        with open(file_path, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:
                try:
                    # Extract required columns
                    source = row.get("source", "Unknown")
                    page = row.get("page", "Unknown")
                    text = row.get("text", "")
                    entities_raw = row.get("entities", "")

                    # Skip rows with missing text or entities
                    if not text or not entities_raw:
                        print(f"Skipping row with missing text or entities. Source: {source}, Page: {page}")
                        continue

                    # Convert stringified list of dictionaries to Python objects
                    try:
                        entities = ast.literal_eval(entities_raw)
                    except Exception as e:
                        print(f"Failed to parse entities: {entities_raw}. Skipping row. Source: {source}, Page: {page}. Error: {e}")
                        continue

                    # Validate entities structure
                    if not isinstance(entities, list):
                        print(f"Invalid entities format: {entities}. Skipping row. Source: {source}, Page: {page}")
                        continue

                    # Filter valid entities
                    valid_entities = [
                        entity for entity in entities
                        if isinstance(entity, dict) and "text" in entity and "label" in entity
                    ]

                    if len(valid_entities) < 2:
                        print(f"Not enough valid entities in row: {valid_entities}. Skipping row. Source: {source}, Page: {page}")
                        continue

                    # Extract relationships using OpenNRE
                    relationships = extract_relationships_with_opennre(text, valid_entities, model)

                    # Store relationships in Neo4j with source and page metadata
                    store_relationships(graph, relationships, source, page)
                    print(f"Processed text from Source: {source}, Page: {page}")
                    print(f"Extracted Relationships: {relationships}")
                except Exception as e:
                    print(f"Error processing row: {row}, error: {e}")
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except Exception as e:
        print(f"Unexpected error reading the file {file_path}: {e}")



if __name__ == "__main__":
    try:
        # Connect to Neo4j
        print("Connecting to Neo4j...")
        graph = Graph(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        print("Connected to Neo4j.")

        # Load OpenNRE pre-trained model
        print("Loading OpenNRE pre-trained model...")
        model = opennre.get_model('wiki80_cnn_softmax', root_path="/Users/justiny/Projects/smudatathon/data-extraction-pipeline/ner/OpenNRE")

        print("Model loaded successfully.")

        # Process CSV file and store data in Neo4j
        csv_file_path = "ner_output_original.csv"
        print(f"Processing CSV file: {csv_file_path}")
        process_csv_and_store(csv_file_path, graph, model)
        print("Processing complete.")
    except Exception as e:
        print(f"Critical error in the main pipeline: {e}")
