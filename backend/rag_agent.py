import os
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# Configuration
DB_DIR = "../chroma_db"
if not os.path.exists(DB_DIR):
    DB_DIR = "chroma_db" # Fallback if running from root

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# Use local server (LM Studio)
# User should ensure LM Studio is running on localhost:1234
LLM_BASE_URL = "http://localhost:1234/v1"
LLM_API_KEY = "lm-studio" # Placeholder key

class VisaEligibilityAgent:
    def __init__(self):
        print(f"Initializing VisaEligibilityAgent with DB at {DB_DIR}...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL_NAME,
            model_kwargs={'device': 'cpu'}
        )
        self.vector_store = Chroma(
            persist_directory=DB_DIR,
            embedding_function=self.embeddings
        )
        self.retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5}
        )
        
        self.llm = ChatOpenAI(
            base_url=LLM_BASE_URL,
            api_key=LLM_API_KEY,
            temperature=0.1,
            streaming=True
        )

        self.prompt_template = """You are SwiftVisa, an expert AI Visa Eligibility Officer. 
Your task is to evaluate the eligibility of a user for a specific visa type based ONLY on the provided Context and the User Profile.

Context (Immigration Policy):
{context}

User Profile:
{question}

Instructions:
1. Analyze the User Profile against the requirements found in the Context.
2. If the user meets all key requirements, state that they seem eligible.
3. If the user fails any requirement, clearly explain WHY, citing the specific policy rule.
4. If information is missing to make a decision, explicitly list what is missing.
5. Be professional, clear, and direct. Do not hallucinate rules not present in the context.

Response:"""

    def check_eligibility(self, user_profile_str):
        print("Checking eligibility...")
        
        # simple RAG chain
        prompt = ChatPromptTemplate.from_template(self.prompt_template)
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        chain = (
            {"context": self.retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
        return chain.stream(user_profile_str)
