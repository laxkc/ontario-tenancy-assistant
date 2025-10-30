#!/usr/bin/env python3
"""Quick test of LangChain components."""

import sys
from pathlib import Path

# Test 1: Simple retrieval
print("=" * 70)
print("TEST 1: Simple Retrieval")
print("=" * 70)

try:
    from langchain.retriever import get_retriever

    retriever = get_retriever(k=2)
    docs = retriever.invoke("rent increase")

    print(f"✓ Retrieved {len(docs)} documents")
    if docs:
        print(f"  First doc metadata: {docs[0].metadata.get('section_number')}")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 2: QA Chain
print("\n" + "=" * 70)
print("TEST 2: QA Chain")
print("=" * 70)

try:
    from langchain.chains import get_qa_chain

    chain = get_qa_chain(model_name="gpt-4o-mini", k=2)
    answer = chain.invoke("Can landlords charge for keys?")

    print(f"✓ Generated answer ({len(answer)} chars)")
    print(f"  Preview: {answer[:100]}...")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 3: LangGraph
print("\n" + "=" * 70)
print("TEST 3: LangGraph Workflow")
print("=" * 70)

try:
    from langchain.graph import query_with_graph

    result = query_with_graph("What is a tenancy agreement?")

    print(f"✓ Workflow completed")
    print(f"  Retrieved: {len(result.get('retrieved_docs', []))} docs")
    print(f"  Answer length: {len(result.get('answer', ''))} chars")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("✅ ALL TESTS COMPLETE")
print("=" * 70)
