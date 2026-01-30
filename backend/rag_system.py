"""
SwiftVisa RAG System - FAISS + Ollama (Mistral)
Processes UK Visa policy PDFs and provides eligibility screening.
"""

import os
import json
import pickle
import faiss
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from PyPDF2 import PdfReader
import requests

# Configuration
DATA_DIR = "data"
DB_DIR = "visa_db"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "mistral:latest"

class SwiftVisaRAG:
    """RAG system for UK Visa Eligibility Screening"""

    def __init__(self, data_dir=DATA_DIR, db_path=DB_DIR):
        self.data_dir = data_dir
        self.db_path = db_path
        self.chunks_file = f"{db_path}/chunks.pkl"
        self.index_file = f"{db_path}/faiss.index"
        self.metadata_file = f"{db_path}/metadata.json"

        os.makedirs(db_path, exist_ok=True)

        print(f"Loading embedding model ({EMBEDDING_MODEL}) on CPU...")
        self.embedder = SentenceTransformer(EMBEDDING_MODEL, device='cpu')
        print("Embedding model loaded.\n")

        self.index = None
        self.chunks = []
        self.metadata = []

    def load_from_disk(self):
        """Load existing index from disk"""
        if os.path.exists(self.index_file) and os.path.exists(self.chunks_file):
            print("Loading existing visa database...")
            self.index = faiss.read_index(self.index_file)
            with open(self.chunks_file, 'rb') as f:
                self.chunks = pickle.load(f)
            with open(self.metadata_file, 'r') as f:
                self.metadata = json.load(f)
            print(f"Loaded {len(self.chunks)} chunks from disk.\n")
            return True
        return False

    def extract_pdf(self, pdf_path):
        """Extract text from a single PDF"""
        if not os.path.exists(pdf_path):
            print(f"File not found: {pdf_path}")
            return []

        print(f"Extracting: {Path(pdf_path).name}")
        pages_text = []
        try:
            reader = PdfReader(pdf_path)
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text and text.strip():
                    pages_text.append({
                        'page': page_num + 1,
                        'text': text,
                        'source': Path(pdf_path).name
                    })
            print(f"  Extracted {len(pages_text)} pages.\n")
        except Exception as e:
            print(f"  Error: {e}\n")
        return pages_text

    def extract_all_pdfs(self):
        """Extract text from all PDFs in the data directory"""
        print("=" * 60)
        print("Extracting UK Visa Policy PDFs")
        print("=" * 60 + "\n")

        all_pages = []
        for pdf_file in Path(self.data_dir).glob("*.pdf"):
            pages = self.extract_pdf(str(pdf_file))
            all_pages.extend(pages)

        print(f"Total pages extracted: {len(all_pages)}\n")
        return all_pages

    def chunk_text(self, pages, chunk_size=500, overlap=100):
        """Chunk text with sliding window approach"""
        print("=" * 60)
        print(f"Chunking: size={chunk_size}, overlap={overlap}")
        print("=" * 60 + "\n")

        uk_keywords = {
            'visa_type': [
                'Student Visa', 'Skilled Worker', 'Health and Care Worker',
                'Graduate Visa', 'Standard Visitor'
            ],
            'section': [
                'Eligibility', 'Requirements', 'Application', 'Fee', 'Validity',
                'Extensions', 'Conditions', 'Dependants', 'Income', 'Qualifications',
                'Sponsor', 'Points', 'CAS', 'CoS'
            ]
        }

        chunks_list = []
        chunk_id = 0

        for page_info in pages:
            full_text = page_info['text']
            source = page_info.get('source', 'Unknown')
            page_num = page_info.get('page', 0)

            step = chunk_size - overlap
            for i in range(0, len(full_text), step):
                chunk_text = full_text[i:i + chunk_size]

                if len(chunk_text.split()) < 15:
                    continue

                visa_type = 'General UK Visa'
                section = 'General'
                chunk_lower = chunk_text.lower()

                for vtype in uk_keywords['visa_type']:
                    if vtype.lower() in chunk_lower:
                        visa_type = vtype
                        break

                for sec in uk_keywords['section']:
                    if sec.lower() in chunk_lower:
                        section = sec
                        break

                metadata = {
                    'id': chunk_id,
                    'visa_type': visa_type,
                    'section': section,
                    'source': source,
                    'page': page_num,
                    'word_count': len(chunk_text.split())
                }

                chunks_list.append({
                    'id': chunk_id,
                    'content': chunk_text,
                    'metadata': metadata
                })
                chunk_id += 1

        print(f"Created {len(chunks_list)} chunks.\n")
        return chunks_list

    def store_chunks(self, chunks_data):
        """Store chunks and embeddings in FAISS"""
        print("=" * 60)
        print("Storing Chunks and Building FAISS Index")
        print("=" * 60 + "\n")

        chunk_texts = [c['content'] for c in chunks_data]

        print(f"Embedding {len(chunk_texts)} chunks...")
        batch_size = 32
        embeddings = []

        for i in range(0, len(chunk_texts), batch_size):
            batch = chunk_texts[i:i+batch_size]
            batch_emb = self.embedder.encode(batch, convert_to_numpy=True).astype('float32')
            embeddings.extend(batch_emb)
            if (i + batch_size) % (batch_size * 5) == 0:
                print(f"  Processed {min(i + batch_size, len(chunk_texts))}/{len(chunk_texts)} chunks")

        embeddings = np.array(embeddings).astype('float32')

        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings)

        self.chunks = chunk_texts
        self.metadata = [c['metadata'] for c in chunks_data]

        faiss.write_index(self.index, self.index_file)
        with open(self.chunks_file, 'wb') as f:
            pickle.dump(self.chunks, f)
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)

        print(f"\n✓ Stored in {self.db_path}/")
        print(f"  - faiss.index ({self.index.ntotal} vectors, {dimension}D)")
        print(f"  - chunks.pkl ({len(self.chunks)} texts)")
        print(f"  - metadata.json ({len(self.metadata)} entries)\n")

    def retrieve(self, question, k=5):
        """Retrieve top-k relevant chunks for a question"""
        if self.index is None:
            return [], []

        question_emb = self.embedder.encode([question]).astype('float32')
        distances, indices = self.index.search(question_emb, k)

        retrieved_chunks = []
        retrieved_meta = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.chunks):
                retrieved_chunks.append(self.chunks[idx])
                retrieved_meta.append(self.metadata[idx])
        
        return retrieved_chunks, retrieved_meta

    def query_ollama(self, prompt):
        """Query local Ollama server"""
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "temperature": 0.2
        }
        try:
            response = requests.post(OLLAMA_URL, json=payload, timeout=120)
            if response.status_code == 200:
                return response.json().get('response', 'No response from model.')
            else:
                return f"Ollama Error: {response.status_code}"
        except requests.exceptions.ConnectionError:
            return "Error: Cannot connect to Ollama. Please run 'ollama serve' in a terminal."
        except Exception as e:
            return f"Error: {e}"

    def check_eligibility(self, user_profile_str, visa_type):
        """Main eligibility check using RAG"""
        
        # Retrieve relevant policy chunks
        search_query = f"{visa_type} eligibility requirements"
        retrieved_chunks, retrieved_meta = self.retrieve(search_query, k=7)

        if not retrieved_chunks:
            return "Error: Database not initialized. Please run ingestion first."

        # Build context string
        context = ""
        for i, (chunk, meta) in enumerate(zip(retrieved_chunks, retrieved_meta)):
            context += f"[Source: {meta.get('source')} | Page: {meta.get('page')}]\n{chunk}\n\n"

        # Build the prompt
        prompt = f"""You are SwiftVisa, an expert AI Visa Eligibility Officer for UK visas. 
Your task is to evaluate whether the user is likely ELIGIBLE or NOT ELIGIBLE for the specified visa type based ONLY on the provided policy context and their profile.

**UK Visa Policy Context:**
{context}

**User Application Profile for {visa_type}:**
{user_profile_str}

**Instructions:**
1. Analyze each field in the user's profile against the official requirements in the context.
2. Clearly state the verdict: "LIKELY ELIGIBLE", "LIKELY NOT ELIGIBLE", or "REQUIRES FURTHER REVIEW".
3. List the key requirements that are MET.
4. List any requirements that are NOT MET, with a brief explanation.
5. If critical information is missing to make a determination, state what is missing.
6. Be professional, direct, and base your reasoning ONLY on the provided context. Do not invent rules.

**Assessment:**"""

        # Query the LLM
        return self.query_ollama(prompt)

    def setup(self):
        """Full setup pipeline: extract, chunk, store"""
        if self.load_from_disk():
            return True

        pages = self.extract_all_pdfs()
        if not pages:
            print("No pages extracted. Check PDF paths.")
            return False

        chunks_data = self.chunk_text(pages)
        self.store_chunks(chunks_data)
        return True


# --- Script Entry Point for Ingestion ---
if __name__ == "__main__":
    print("SwiftVisa RAG Ingestion Script")
    print("=" * 60 + "\n")

    # Determine correct paths
    if not os.path.exists(DATA_DIR):
        # If running from backend folder
        DATA_DIR = "../data"
        DB_DIR = "../visa_db"

    rag = SwiftVisaRAG(data_dir=DATA_DIR, db_path=DB_DIR)
    rag.setup()
    print("\nIngestion complete. You can now run the Streamlit app.")
