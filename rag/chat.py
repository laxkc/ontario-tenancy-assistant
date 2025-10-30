#!/usr/bin/env python3
"""
Terminal Chat Interface for Ontario Tenancy Law

Simple, clean chat interface powered by LangChain + OpenAI
"""

from langchain.chains import get_qa_chain


def print_header():
    """Print chat header."""
    print("\n" + "=" * 70)
    print("🏠 ONTARIO TENANCY LAW - CHAT ASSISTANT")
    print("=" * 70)
    print("\nPowered by:")
    print("  • BGE-M3 (local embeddings)")
    print("  • OpenAI GPT-4o-mini")
    print("  • Pinecone (678 RTA sections)")
    print("\nCommands:")
    print("  - Type your question and press Enter")
    print("  - 'quit' or 'exit' to stop")
    print("  - 'clear' to clear screen")
    print("\n" + "=" * 70 + "\n")


def main():
    """Main chat loop."""
    print_header()

    # Initialize QA chain once
    print("🔧 Loading system...")
    chain = get_qa_chain(model_name="gpt-4o-mini", k=5)
    print("✓ Ready!\n")

    # Chat loop
    while True:
        try:
            # Get user input
            question = input("You: ").strip()

            # Handle commands
            if not question:
                continue

            if question.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!\n")
                break

            if question.lower() == 'clear':
                import os
                os.system('clear' if os.name != 'nt' else 'cls')
                print_header()
                continue

            # Generate answer
            print("\n💭 Thinking...\n")
            answer = chain.invoke(question)

            # Display answer
            print("Assistant:")
            print("-" * 70)
            print(answer)
            print("-" * 70)
            print()

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    main()
