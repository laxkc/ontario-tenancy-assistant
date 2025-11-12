"""LangChain chains for RAG question answering."""

import sys
from pathlib import Path

# Add root directory to path for config import
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from src.core.retriever import get_retriever
from src.core.llm import get_llm


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


def get_qa_chain(
    model_name: str = None,
    temperature: float = None,
    k: int = 5,
    filter: dict = None,
):
    """Create a RAG question-answering chain using LangChain.

    Args:
        model_name: Model name (uses config default if None)
        temperature: Temperature for generation (uses config default if None)
        k: Number of documents to retrieve (default: 5)
        filter: Metadata filter for retrieval

    Returns:
        Configured LCEL chain
    """
    # Get LLM (uses global config from config.py)
    llm = get_llm(model_name=model_name, temperature=temperature)
    
    print(f"🔧 Setting up QA chain with {llm.__class__.__name__}")

    # Get retriever
    retriever = get_retriever(k=k, filter=filter)

    # Create prompt template
    prompt = ChatPromptTemplate.from_template(TENANCY_QA_PROMPT)

    # Build chain using LCEL
    chain = (
        {
            "context": retriever | format_docs,
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    print("✓ QA chain ready")

    return chain

