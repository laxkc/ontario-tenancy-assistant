"""Self-check evaluation node for quality assurance."""

from langchain_openai import ChatOpenAI
from rag import config


def evaluate_answer_quality(state: dict) -> dict:
    """Evaluate the quality of the generated answer."""
    question = state["question"]
    answer = state["answer"]
    has_citations = state.get("has_citations", False)

    print("🔍 Running quality self-check...")

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.0,
        api_key=config.OPENAI_API_KEY,
    )

    prompt = f"""Evaluate this legal assistant's response for quality.

Question: {question}

Answer: {answer}

Rate on a scale of 0-10 based on:
1. Correctness (cites proper RTA sections)
2. Completeness (addresses the question fully)
3. Clarity (easy to understand)
4. Empathy (human-like, not robotic)
5. Citations (includes section numbers)

Respond with ONLY a number from 0-10 representing overall quality.
If citations are missing but should be present, maximum score is 6.

Your score:"""

    response = llm.invoke(prompt)

    try:
        quality_score = float(response.content.strip())
        quality_score = max(0.0, min(10.0, quality_score))
    except:
        quality_score = 7.0

    state["quality_score"] = quality_score

    if quality_score < 6.0:
        print(f"⚠️  Quality score: {quality_score}/10 - Below threshold")
    else:
        print(f"✓ Quality score: {quality_score}/10")

    return state


def improve_answer_if_needed(state: dict) -> dict:
    """Improve answer if quality score is below threshold."""
    quality_score = state.get("quality_score", 10.0)

    if quality_score >= 7.0:
        print("✓ Quality acceptable, no improvement needed")
        return state

    print("🔧 Improving answer based on quality feedback...")

    question = state["question"]
    original_answer = state["answer"]
    context = state.get("summarized_context", state["context"])

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.1,
        api_key=config.OPENAI_API_KEY,
    )

    prompt = f"""The following answer needs improvement. Enhance it with:
1. Proper RTA section citations
2. Clearer explanations
3. More empathetic tone
4. Complete coverage of the question

Original Question: {question}

Original Answer (needs improvement):
{original_answer}

Legal Context:
{context}

Provide an improved answer:"""

    response = llm.invoke(prompt)

    state["answer"] = response.content
    state["has_citations"] = "Section" in response.content

    print("✓ Answer improved")

    return state
