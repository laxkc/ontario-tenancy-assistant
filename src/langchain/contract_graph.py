"""LangGraph workflow for contract analysis and compliance checking."""

import sys
from pathlib import Path

# Add root directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import TypedDict, Annotated, Sequence, List, Dict
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from src.core.retriever import get_retriever
from src.core.llm import get_llm


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

    llm = get_llm()

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
    
    # Extract content from response
    if hasattr(response, 'content'):
        response_content = response.content
    elif isinstance(response, str):
        response_content = response
    else:
        response_content = str(response)

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
        AIMessage(content=response_content)
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

    llm = get_llm()

    prompt = f"""You are a legal expert in Ontario tenancy law. Analyze this contract for compliance issues.

Contract Text:
{contract_text[:3000]}...

Relevant Ontario Residential Tenancies Act Sections:
{laws_context}

Provide a clear, structured analysis in markdown format. Identify:

1. **Clauses that Violate Ontario Tenancy Law** - List specific violations with RTA section citations
2. **Missing Mandatory Clauses** - List what's required but missing
3. **Unfair or Illegal Terms** - Identify problematic terms
4. **Clauses that Favor One Party Excessively** - Point out imbalanced terms

Format your response as markdown with clear headings and bullet points. Be concise but thorough. For each issue, cite the specific RTA section violated.

Keep the response focused and well-organized."""

    response = llm.invoke(prompt)
    
    # Extract content from response
    if hasattr(response, 'content'):
        issue_description = response.content
    elif isinstance(response, str):
        issue_description = response
    else:
        issue_description = str(response)

    compliance_issues = [
        {
            "severity": "high",
            "description": issue_description
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

    llm = get_llm(temperature=0.2)

    prompt = f"""Based on the compliance issues found, provide actionable recommendations in a clear, structured markdown format.

Issues Found:
{issues[0]['description'] if issues else 'None'}

Relevant Laws:
{laws_context}

Provide recommendations organized as follows:

1. **Specific Changes Needed** - List the key changes required to comply with Ontario law
2. **Suggested Wording** - Provide improved wording for problematic clauses
3. **Additional Protections** - Suggest additional clauses or protections that should be added
4. **Implementation Timeline** - Provide a realistic timeline for making these changes

Format your response as markdown with clear headings and bullet points. Be practical and actionable. Keep it concise but comprehensive."""

    response = llm.invoke(prompt)
    
    # Extract content from response
    if hasattr(response, 'content'):
        recommendation_text = response.content
    elif isinstance(response, str):
        recommendation_text = response
    else:
        recommendation_text = str(response)

    state["recommendations"] = [recommendation_text]

    print("✓ Recommendations generated")

    return state


def generate_final_report(state: ContractAnalysisState) -> ContractAnalysisState:
    """Generate comprehensive analysis report."""
    contract_type = state.get("contract_type", "Residential Lease")
    issues = state.get("compliance_issues", [])
    recommendations = state.get("recommendations", [])
    laws = state.get("retrieved_laws", [])

    print("📄 Generating final report...")

    # Format issues
    issues_text = "No major compliance issues found."
    if issues and len(issues) > 0:
        if isinstance(issues[0], dict) and 'description' in issues[0]:
            issues_text = issues[0]['description']
        elif isinstance(issues[0], str):
            issues_text = issues[0]
        else:
            issues_text = str(issues[0])
    
    # Format recommendations
    recommendations_text = "Contract appears compliant with Ontario law."
    if recommendations and len(recommendations) > 0:
        if isinstance(recommendations[0], str):
            recommendations_text = recommendations[0]
        else:
            recommendations_text = str(recommendations[0])

    # Clean up and format the issues text
    if issues_text and issues_text.strip():
        # Ensure proper markdown formatting
        if not issues_text.startswith("#"):
            issues_text = issues_text.strip()
    else:
        issues_text = "✅ **No major compliance issues found.**\n\nThe contract appears to be generally compliant with Ontario Residential Tenancies Act, 2006."
    
    # Clean up and format the recommendations text
    if recommendations_text and recommendations_text.strip():
        recommendations_text = recommendations_text.strip()
    else:
        recommendations_text = "✅ **Contract appears compliant.**\n\nNo specific recommendations at this time."

    report = f"""# 📋 Contract Analysis Report

## Contract Type
{contract_type}

## Summary
This contract has been analyzed against the **Ontario Residential Tenancies Act, 2006** to identify compliance issues and provide recommendations.

---

## ⚖️ Compliance Issues Found

{issues_text}

---

## 💡 Recommendations

{recommendations_text}

---

## 📚 Referenced Laws
"""

    if laws and len(laws) > 0:
        # Filter out irrelevant sections (like care homes, etc.) and prioritize relevant ones
        relevant_laws = []
        excluded_keywords = ['care home', 'care service', 'superintendent', 'offence', 'harassment']
        
        # Common residential tenancy sections (prioritize these)
        priority_sections = {'5', '14', '20', '26', '33', '37', '48', '49', '50', '51', '58', '59', '60', '61', '62', '64', '67', '69', '83', '105', '106', '107', '108', '109', '110', '111', '112', '113', '114', '115', '116', '117', '118', '119', '120', '121', '122', '123', '124', '125', '126', '127', '128', '129', '130', '131', '132', '133', '134', '135', '136', '137', '138', '139', '140', '141', '142', '143', '144', '145', '146', '147', '148', '149', '150'}
        
        priority_docs = []
        other_docs = []
        
        for doc in laws:
            metadata = doc.metadata
            section_title = metadata.get('section_title', '').lower()
            section_number = str(metadata.get('section_number', ''))
            
            # Skip sections that are clearly not relevant to standard residential tenancies
            if any(keyword in section_title for keyword in excluded_keywords):
                continue
            
            # Prioritize common residential tenancy sections
            if section_number in priority_sections:
                priority_docs.append(doc)
            else:
                other_docs.append(doc)
        
        # Combine: priority first, then others, limit to 5
        relevant_laws = (priority_docs + other_docs)[:5]
        
        if relevant_laws:
            for i, doc in enumerate(relevant_laws, 1):
                metadata = doc.metadata
                section = f"Section {metadata.get('section_number', 'N/A')}"
                if metadata.get('subsection_number'):
                    section += f" - Subsection {metadata.get('subsection_number')}"

                section_title = metadata.get('section_title', '')
                report += f"\n{i}. **{section}** - {section_title}"
        else:
            report += "\nNo directly relevant sections found in the retrieved documents."
    else:
        report += "\nNo specific sections referenced."

    report += "\n\n---\n\n⚠️ **Disclaimer**: This analysis is for informational purposes only and does not constitute legal advice. Consult with a qualified legal professional for specific legal guidance."

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

