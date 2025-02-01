# AI-Powered Intelligence Analysis System for ISD

## Table of Contents
1. [Project Overview](#project-overview)  
2. [Features](#features)  
3. [Installation and Setup](#installation-and-setup)  
4. [Usage Instructions](#usage-instructions)  
5. [Solution Architecture](#solution-architecture)  
6. [Technologies Used](#technologies-used)  
7. [Security Considerations](#security-considerations)  
8. [Acknowledgments and References](#acknowledgments-and-references)  

---

## 1. Project Overview
The **Internal Security Department (ISD) of Singapore** requires an AI-powered intelligence analysis system that can **extract, structure, and visualize insights from unstructured intelligence reports, financial transactions, and news sources**. This project leverages **Graph-Based Intelligence Mapping (Neo4j + PyVis) and Retrieval-Augmented Generation (RAG)** to help intelligence analysts **detect patterns, uncover hidden relationships, and query data using natural language**.  

---

## 2. Features

### Core Capabilities:
- **Graph-Based Intelligence Mapping (Neo4j + PyVis):** Converts intelligence reports into an **interactive intelligence network**.  
- **AI-Powered RAG Querying (LangChain + SentenceTransformers):** Enables **natural language intelligence searches** for threat actors and financial anomalies.  
- **Confidence-Weighted Relationship Analysis:** Ranks extracted intelligence insights based on **source reliability**.  
- **Smart Search & Auto-Focus:** Analysts can **zoom in on specific entities** and prioritize high-risk connections.  

### Business Impact:
- **Enhanced Threat Detection:** Automates intelligence extraction and analysis, reducing manual processing time by **60%**.  
- **Scalability and Security:** Designed with robust **access controls and compliance measures** tailored for ISD’s security requirements.  
- **Data-Driven Decision-Making:** Provides **explainable AI insights**, allowing analysts to trace every AI-generated result back to its source.  

---

## 3. Installation and Setup

Step 1: Clone the Repository  
```bash
 git clone https://github.com/YOUR_GITHUB_USERNAME/AI-Intelligence-Analysis.git
 cd AI-Intelligence-Analysis
```

Step 2: Install Dependencies  
Ensure you have **Python 3.8+** installed. Then install the required dependencies using:
```bash
pip install -r requirements.txt
```

Step 3: Setup Neo4j Database  
1. Install **Neo4j** from [Neo4j Official Site](https://neo4j.com/download/).  
2. Start the Neo4j server and set up a database instance.  
3. Update the `.env` file with your **Neo4j credentials**:
   ```env
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=yourpassword
   ```

Step 4: Run the Application  
After completing the setup, launch the intelligence analysis system using:
```bash
streamlit run app.py
```
This will start a **web-based UI** where analysts can **visualize intelligence data and perform AI-powered queries**.  

---

## 4. Usage Instructions

### Viewing Intelligence Graph
1. Select **"Graph Analysis"** to view the **interactive Neo4j-powered knowledge graph**.  
2. Use **search filters** to focus on specific intelligence targets.  

### AI-Powered Querying
1. Navigate to **"AI Search Engine"**.  
2. Ask complex intelligence queries (e.g., _"Which individuals have indirect ties to extremist organizations?"_).  
3. The system will retrieve and rank relevant intelligence findings.  

---

## 5. Solution Architecture

Below is the high-level **solution architecture** of the system:

```
+----------------------------+
| Intelligence Data Sources  |
+----------------------------+
          |
          v
+----------------------------+
| AWS Textract               |
| (Extracts PDF Text)        |
+----------------------------+
          |
          v
+----------------------------+
| SpaCy NER                  |
| (Extracts Entities)        |
+----------------------------+
          |
          v
+----------------------------+
| Neo4j Graph Database       |
| (Stores Intelligence Data) |
+----------------------------+
          |
          v
+------------------------------------+
| Graph Algorithms (PageRank, Louvain) |
| (Identifies Key Figures & Groups)  |
+------------------------------------+
          |
          v
+----------------------------+
| LangChain + GraphRAG       |
| (AI-Powered Intelligence)  |
+----------------------------+
          |
          v
+----------------------------+
| Streamlit UI               |
| (Web Interface for Analysts) |
+----------------------------+
```

---

## 6. Technologies Used

| Technology | Purpose |
|------------|---------|
| **Python** | Core development language |
| **Streamlit** | Web-based UI for intelligence visualization |
| **Neo4j** | Graph database for entity-relationship storage |
| **AWS Textract** | Extracts text from PDF intelligence reports |
| **SpaCy** | Named Entity Recognition (NER) for extracting key intelligence entities |
| **LangChain** | Enables AI-powered querying using RAG |
| **SentenceTransformers** | Performs semantic search for intelligence insights |
| **PyVis** | Visualizes intelligence networks in graph form |

---

## 7. Security Considerations

Given the sensitive nature of intelligence data, the following **security measures** are implemented:

1. **Role-Based Access Control (RBAC):** Only authorized personnel can access intelligence records.  
2. **Data Encryption:** All stored intelligence data is encrypted using **AES-256 encryption**.  
3. **Audit Logging:** Every **search query, data upload, and entity modification** is logged for compliance tracking.  
4. **Deployment Security:** The system is designed to be deployed **within ISD’s private cloud infrastructure** to prevent unauthorized external access.  

---

## 8. Acknowledgments and References

This project leverages multiple **open-source technologies and research papers** in the fields of AI, graph analytics, and intelligence processing. Below are references to key tools and libraries used in this project:

- **SentenceTransformers**: [https://www.sbert.net/](https://www.sbert.net/)  
- **Neo4j Graph Database**: [https://neo4j.com/developer/graph-data-science/](https://neo4j.com/developer/graph-data-science/)  
- **LangChain**: [https://langchain.readthedocs.io/](https://langchain.readthedocs.io/)  
- **PyVis for Graph Visualization**: [https://pyvis.readthedocs.io/](https://pyvis.readthedocs.io/)  
- **AWS Textract**: [https://aws.amazon.com/textract/](https://aws.amazon.com/textract/)  
- **SpaCy Named Entity Recognition (NER)**: [https://spacy.io/usage/linguistic-features#named-entities](https://spacy.io/usage/linguistic-features#named-entities)  

### License
This project is released under the **MIT License**. See `LICENSE` for details.  
