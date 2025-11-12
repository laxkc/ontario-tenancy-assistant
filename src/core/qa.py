"""Question-answering system for tenancy law queries using RAG."""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

import sys
from pathlib import Path

# Add root directory to path for config import
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from .retriever import get_retriever
from .llm import get_llm


# Prompt template for tenancy law QA
TENANCY_QA_PROMPT = """You are an expert legal assistant specializing in Ontario tenancy law, specifically the Residential Tenancies Act, 2006.

Use the following context from the Act to answer the question. Be precise, cite specific sections when relevant, and explain the legal implications clearly.

If the context doesn't contain enough information to answer the question fully, acknowledge this and provide what information is available.

Context from the Residential Tenancies Act:
{context}

Question: {question}

Answer:"""


def format_docs(docs):
    """Format retrieved documents into context string."""
    formatted = []
    for i, doc in enumerate(docs, 1):
        metadata = doc.metadata
        section_info = f"Section {metadata.get('section_number', 'N/A')}"
        if metadata.get('subsection_number'):
            section_info += f" - Subsection {metadata.get('subsection_number')}"

        formatted.append(
            f"[{i}] {section_info} - {metadata.get('section_title', '')}\n{doc.page_content}"
        )

    return "\n\n".join(formatted)


def is_tenancy_question(question: str) -> bool:
    """Simple check if question is about Ontario tenancy law."""
    question_lower = question.lower()
    tenancy_keywords = [
        "rent", "tenant", "landlord", "lease", "eviction", "deposit",
        "ontario", "rta", "residential tenancies", "rental", "housing"
    ]
    return any(keyword in question_lower for keyword in tenancy_keywords)


def get_answer(
    question: str,
    chat_history: list = None,
    model_name: str = None,
    temperature: float = None,
    k: int = 5,
) -> dict:
    """Simple RAG: retrieve → generate → return.
    
    Args:
        question: User's question
        chat_history: Optional conversation history
        model_name: Model name (uses config default if None)
        temperature: Temperature for generation (uses config default if None)
        k: Number of documents to retrieve
        
    Returns:
        Dictionary with answer and sources
    """
    # Simple relevance check
    if not is_tenancy_question(question):
        return {
            "answer": """I'm specialized in **Ontario tenancy law** and the **Residential Tenancies Act, 2006**. I can only help with questions about:

🏠 **Rental & Housing in Ontario:**
- Landlord-tenant rights and responsibilities
- Rent increases, deposits, and payments
- Lease agreements and terminations
- Evictions and disputes
- Maintenance and repairs
- Specific sections of the RTA 2006

**Please ask a question related to Ontario rental/tenancy law**, and I'll be happy to help!""",
            "sources": [],
            "is_relevant": False,
        }
    
    # Retrieve documents
    retriever = get_retriever(k=k, filter={"jurisdiction": "Ontario"})
    
    # Enhance query with chat history if available
    query = question
    if chat_history:
        last_messages = chat_history[-3:]
        history_context = "\n".join([
            f"{msg['role']}: {msg['content'][:100]}"
            for msg in last_messages
        ])
        query = f"Given this conversation:\n{history_context}\n\nCurrent question: {question}"
    
    docs = retriever.invoke(query)
    
    if not docs:
        return {
            "answer": f"""I couldn't find specific information in the Ontario Residential Tenancies Act, 2006 directly related to your question: "{question}"

Could you please:
1. Rephrase your question with more specific legal terms
2. Provide more context about your situation
3. Ask about a specific section or aspect of tenancy law""",
            "sources": [],
            "needs_clarification": True,
        }
    
    # Format context
    context = format_docs(docs)
    
    # Generate answer using LLM (uses global config from config.py)
    llm = get_llm(model_name=model_name, temperature=temperature)
    
    prompt = ChatPromptTemplate.from_template(TENANCY_QA_PROMPT)
    
    # Build chain
    chain = (
        {
            "context": RunnablePassthrough.assign(context=lambda x: context),
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    
    answer = chain.invoke({"question": question, "context": context})
    
    # Ensure answer is a string
    if not isinstance(answer, str):
        answer = str(answer)
    
    return {
        "answer": answer,
        "sources": docs,
        "is_relevant": True,
        "needs_clarification": False,
    }

