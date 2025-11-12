"""LangGraph workflow for contract analysis and compliance checking."""

from typing import TypedDict, Annotated, Sequence, List, Dict
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

from rag import config
from .retriever import get_retriever
from .chains import format_docs


class ContractAnalysisState(TypedDict):
    """State for the contract analysis graph."""
    contract_text: str
    contract_type: str
    analysis_questions: List[str]
    retrieved_laws: list
    compliance_issues: List[Dict]
    recommendations: List[str]
    analysis_result: str
    messages: Annotated[Sequence[BaseMessage], "Chat history"]


def extract_contract_clauses(state: ContractAnalysisState) -> ContractAnalysisState:
    """Extract and categorize key clauses from the contract."""
    contract_text = state["contract_text"]

    print("🔍 Extracting contract clauses...")

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.0,
        api_key=config.OPENAI_API_KEY,
    )

    prompt = f"""Analyze this tenancy contract and extract key clauses.

Contract:
{contract_text[:3000]}...

Identify and list:
1. Rent amount and payment terms
2. Lease duration and renewal terms
3. Security deposit details
4. Maintenance and repair responsibilities
5. Termination and eviction clauses
6. Any unusual or concerning clauses

Format as a bulleted list."""

    response = llm.invoke(prompt)

    analysis_questions = [
        "rent increases and notice requirements",
        "tenant rights regarding maintenance",
        "landlord's right to enter the property",
        "security deposit return conditions",
        "lease termination procedures"
    ]

    state["analysis_questions"] = analysis_questions
    state["messages"] = [
        HumanMessage(content=prompt),
        AIMessage(content=response.content)
    ]

    print(f"✓ Extracted {len(analysis_questions)} key areas for analysis")

    return state


def retrieve_relevant_laws(state: ContractAnalysisState) -> ContractAnalysisState:
    """Retrieve relevant laws for each contract clause."""
    questions = state["analysis_questions"]

    print("📚 Retrieving relevant tenancy laws...")

    retriever = get_retriever(k=3)

    all_docs = []
    for question in questions:
        docs = retriever.invoke(question)
        all_docs.extend(docs)

    unique_docs = []
    seen_sections = set()
    for doc in all_docs:
        section = doc.metadata.get('section_number')
        if section not in seen_sections:
            unique_docs.append(doc)
            seen_sections.add(section)

    state["retrieved_laws"] = unique_docs[:10]

    print(f"✓ Retrieved {len(unique_docs)} unique law sections")

    return state


def check_compliance(state: ContractAnalysisState) -> ContractAnalysisState:
    """Check contract compliance against Ontario tenancy laws."""
    contract_text = state["contract_text"]
    laws_context = format_docs(state["retrieved_laws"])

    print("⚖️ Checking compliance...")

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.0,
        api_key=config.OPENAI_API_KEY,
    )

    prompt = f"""You are a legal expert in Ontario tenancy law. Analyze this contract for compliance issues.

Contract Text:
{contract_text[:3000]}...

Relevant Ontario Residential Tenancies Act Sections:
{laws_context}

Identify:
1. Any clauses that violate Ontario tenancy law
2. Missing mandatory clauses
3. Unfair or illegal terms
4. Clauses that favor one party excessively

For each issue, cite the specific RTA section violated."""

    response = llm.invoke(prompt)

    compliance_issues = [
        {
            "severity": "high",
            "description": response.content
        }
    ]

    state["compliance_issues"] = compliance_issues

    print(f"✓ Compliance check complete")

    return state


def generate_recommendations(state: ContractAnalysisState) -> ContractAnalysisState:
    """Generate recommendations for contract improvements."""
    issues = state["compliance_issues"]
    laws_context = format_docs(state["retrieved_laws"])

    print("💡 Generating recommendations...")

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2,
        api_key=config.OPENAI_API_KEY,
    )

    prompt = f"""Based on the compliance issues found, provide actionable recommendations.

Issues Found:
{issues[0]['description'] if issues else 'None'}

Relevant Laws:
{laws_context}

Provide:
1. Specific changes needed to comply with Ontario law
2. Suggested wording for problematic clauses
3. Additional protections that should be added
4. Timeline for when changes should be implemented"""

    response = llm.invoke(prompt)

    state["recommendations"] = [response.content]

    print("✓ Recommendations generated")

    return state


def generate_final_report(state: ContractAnalysisState) -> ContractAnalysisState:
    """Generate comprehensive analysis report."""
    contract_type = state.get("contract_type", "Residential Lease")
    issues = state["compliance_issues"]
    recommendations = state["recommendations"]
    laws = state["retrieved_laws"]

    print("📄 Generating final report...")

    report = f"""# Contract Analysis Report

## Contract Type
{contract_type}

## Summary
Analyzed contract against Ontario Residential Tenancies Act, 2006.

## Compliance Issues Found
{issues[0]['description'] if issues else 'No major issues found.'}

## Recommendations
{recommendations[0] if recommendations else 'Contract appears compliant.'}

## Referenced Laws
"""

    for i, doc in enumerate(laws[:5], 1):
        metadata = doc.metadata
        section = f"Section {metadata.get('section_number', 'N/A')}"
        if metadata.get('subsection_number'):
            section += f" - Subsection {metadata.get('subsection_number')}"

        report += f"\n{i}. **{section}** - {metadata.get('section_title', '')}"

    report += "\n\n---\n\n⚠️ **Disclaimer**: This analysis is for informational purposes only and does not constitute legal advice."

    state["analysis_result"] = report

    print("✓ Report generated")

    return state


def create_contract_analysis_graph():
    """Create the contract analysis workflow graph.

    Returns:
        Compiled LangGraph workflow
    """
    workflow = StateGraph(ContractAnalysisState)

    workflow.add_node("extract_clauses", extract_contract_clauses)
    workflow.add_node("retrieve_laws", retrieve_relevant_laws)
    workflow.add_node("check_compliance", check_compliance)
    workflow.add_node("generate_recommendations", generate_recommendations)
    workflow.add_node("generate_report", generate_final_report)

    workflow.set_entry_point("extract_clauses")
    workflow.add_edge("extract_clauses", "retrieve_laws")
    workflow.add_edge("retrieve_laws", "check_compliance")
    workflow.add_edge("check_compliance", "generate_recommendations")
    workflow.add_edge("generate_recommendations", "generate_report")
    workflow.add_edge("generate_report", END)

    app = workflow.compile()

    print("✓ Contract analysis graph compiled")

    return app


def analyze_contract(contract_text: str, contract_type: str = "Residential Lease") -> dict:
    """Analyze a contract for compliance with Ontario tenancy laws.

    Args:
        contract_text: Full text of the contract
        contract_type: Type of contract (default: Residential Lease)

    Returns:
        Analysis results with compliance issues and recommendations
    """
    print("=" * 70)
    print("📋 CONTRACT ANALYSIS")
    print("=" * 70)
    print(f"\nContract Type: {contract_type}")
    print(f"Contract Length: {len(contract_text)} characters\n")

    graph = create_contract_analysis_graph()

    initial_state = {
        "contract_text": contract_text,
        "contract_type": contract_type,
        "analysis_questions": [],
        "retrieved_laws": [],
        "compliance_issues": [],
        "recommendations": [],
        "analysis_result": "",
        "messages": [],
    }

    result = graph.invoke(initial_state)

    print("\n" + "=" * 70)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 70)

    return result
