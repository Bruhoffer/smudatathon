import os
import spacy
import pandas as pd
import json
import torch
from tqdm import tqdm
from dotenv import load_dotenv
from py2neo import Graph, Node, Relationship
from sentence_transformers import SentenceTransformer, util
import opennre
import ast
from fuzzywuzzy import fuzz

# Load environment variables (Neo4j credentials)
load_dotenv()
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# ✅ Check if Neo4j Connection Works
try:
    graph = Graph(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    graph.run("RETURN 1")
    print("✅ Connected to Neo4j.")
except Exception as e:
    print(f"❌ Neo4j connection failed: {e}")
    exit()

# Load NLP models
nlp = spacy.load("en_core_web_md")  
device = "cuda" if torch.cuda.is_available() else "cpu"
embedding_model = SentenceTransformer('paraphrase-MiniLM-L6-v2', device=device)

# Load OpenNRE for Relationship Extraction
nre_model = opennre.get_model('wiki80_cnn_softmax', root_path="./OpenNRE")

# Relationship keywords for classification
relationship_keywords = [
    "threat to", "associated with", "collaborates with", "operates in", "funded by",
    "affiliated with", "connected to", "has conflict with", "leader of", "suspected member of",
    "targets", "linked to", "receives support from", "monitored by", "detained by",
    "interacts with", "opposes", "has influence over", "fined", "sentenced", "convicted", "banned",
    "elected", "resigned", "investigated", "charged", "partnered with", "owns", "merged with", "acquired"
]
rel_embeddings = embedding_model.encode(relationship_keywords, convert_to_tensor=True)

negation_words = {"not", "never", "no", "without"}

def detect_negation(dep_path):
    """ Detects negation in dependency path. """
    return any(neg in dep_path.lower() for neg in negation_words)

def extract_dependency_path(doc, ent1, ent2):
    """ Extracts dependency path with Spacy syntactic tree. """
    ent1_token = next((token for token in doc if ent1.lower() in token.text.lower()), None)
    ent2_token = next((token for token in doc if ent2.lower() in token.text.lower()), None)

    if not ent1_token or not ent2_token:
        return "UNKNOWN"

    path = []
    current = ent1_token
    while current != ent2_token and current.head != current:
        path.append(current.text)
        current = current.head
    path.append(ent2_token.text)

    return " -> ".join(path)

def classify_relationship(dep_path, negation_flag):
    """ Matches extracted dependency path to closest intelligence-related relationship. """
    dep_embedding = embedding_model.encode(dep_path, convert_to_tensor=True)

    similarities = util.pytorch_cos_sim(dep_embedding, rel_embeddings)[0]
    best_score, best_idx = torch.max(similarities, dim=0)
    best_score = float(best_score)
    best_idx = int(best_idx)

    best_match = relationship_keywords[best_idx] if best_score > 0.4 else "UNKNOWN"

    print(f"🧐 Matching: '{dep_path}' → '{best_match}' (Score: {best_score})")

    return best_match, best_score

def fuzzy_match_entity(doc, entity_text):
    """ Finds the best matching entity in the Spacy document if exact match fails. """
    for ent in doc.ents:
        if fuzz.partial_ratio(ent.text.lower(), entity_text.lower()) > 80:
            return ent.text
    return entity_text

def extract_relationships(text, entity_pairs, entity_info):
    """Extracts relationships while also preserving entity types for Neo4j storage."""
    doc = nlp(text)
    relations = []

    for ent1, ent2 in entity_pairs:
        ent1_matched = fuzzy_match_entity(doc, ent1)
        ent2_matched = fuzzy_match_entity(doc, ent2)

        dep_path = extract_dependency_path(doc, ent1_matched, ent2_matched)
        negation_flag = detect_negation(dep_path)
        best_rel, similarity_score = classify_relationship(dep_path, negation_flag)

        # Get entity types from entity_info dictionary
        ent1_type = entity_info.get(ent1, "Entity")  
        ent2_type = entity_info.get(ent2, "Entity")

        if best_rel != "UNKNOWN" and similarity_score > 0.4:
            relations.append({
                "entity1": ent1_matched, "entity2": ent2_matched,
                "relationship": best_rel, "confidence": similarity_score,
                "entity1_type": ent1_type, "entity2_type": ent2_type  
            })

    return relations

def store_relationships_in_neo4j(relationships):
    """Stores extracted relationships in Neo4j with correct entity type labels."""
    if not relationships:
        print("⚠️ No relationships to store.")
        return

    print(f"💾 Storing {len(relationships)} relationships in Neo4j...")

    for rel in relationships:
        try:
            entity1_type = rel.get("entity1_type", "Entity")
            entity2_type = rel.get("entity2_type", "Entity")

            start_node = Node(entity1_type, name=rel["entity1"])  
            end_node = Node(entity2_type, name=rel["entity2"])  
            relationship = Relationship(start_node, rel["relationship"], end_node, confidence=rel["confidence"])

            graph.merge(start_node, entity1_type, "name")  
            graph.merge(end_node, entity2_type, "name")  
            graph.merge(relationship)

            print(f"✅ Stored: {rel['entity1']} ({entity1_type}) -[{rel['relationship']}]-> {rel['entity2']} ({entity2_type})")

        except Exception as e:
            print(f"❌ Error storing relationship {rel}: {e}")

import ast

def process_text_data(input_file, output_file):
    """Process CSV file, extract relationships, and preserve entity types."""
    df = pd.read_csv(input_file)

    results = []
    for idx, row in tqdm(df.iterrows(), total=len(df)):
        print(f"\n📝 Processing row {idx+1}/{len(df)}")
        
        text = row["text"]

        try:
            entities = ast.literal_eval(row["entities"])
            if not isinstance(entities, list):
                continue
        except:
            continue

        entity_info = {ent["text"]: ent["label"] for ent in entities}  

        MAX_ENTITY_PAIRS = 15
        entity_pairs = [(entities[i]["text"], entities[j]["text"]) for i in range(len(entities)) for j in range(i + 1, len(entities))]
        entity_pairs = entity_pairs[:MAX_ENTITY_PAIRS]

        relations = extract_relationships(text, entity_pairs, entity_info)
        results.extend(relations)

    print(f"💾 Extracted {len(results)} relationships.")
    store_relationships_in_neo4j(results)

    with open(output_file, "w") as f:
        json.dump(results, f, indent=4)

    print(f"✅ Saved extracted relationships to {output_file}")

# Run pipeline
process_text_data("ner_output.csv", "finaloutput.csv")

# Debugging: Verify Neo4j Storage
print("🔎 Running Neo4j Debug Queries...")
print(graph.run("MATCH (n) RETURN DISTINCT labels(n);").data())  
print(graph.run("MATCH (n) RETURN COUNT(n);").data())  
print(graph.run("MATCH ()-[r]->() RETURN COUNT(r);").data())  
