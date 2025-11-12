# Contract Analysis Feature

## Overview

The Contract Analysis feature uses LangGraph to analyze rental/tenancy contracts for compliance with Ontario's Residential Tenancies Act, 2006.

## Features

### 🔍 Automated Analysis
- **Clause Extraction**: Identifies key contract clauses
- **Legal Compliance Check**: Compares against Ontario RTA
- **Issue Detection**: Flags illegal or unfair terms
- **Recommendations**: Suggests specific improvements

### 📄 Supported File Types
- PDF (`.pdf`)
- Word Documents (`.docx`, `.doc`)
- Text Files (`.txt`)

## How It Works

### LangGraph Workflow

```
Contract Upload
    ↓
Extract Clauses (GPT-4o-mini)
    ↓
Retrieve Relevant Laws (Vector Search)
    ↓
Check Compliance (GPT-4o-mini + RTA)
    ↓
Generate Recommendations (GPT-4o-mini)
    ↓
Final Report
```

### Analysis Steps

1. **Extract Contract Clauses**
   - Identifies rent, lease terms, deposits, etc.
   - Uses GPT-4o-mini for structured extraction

2. **Retrieve Relevant Laws**
   - Searches 678 RTA sections via vector database
   - Finds 3 most relevant sections per clause type
   - Deduplicates to top 10 unique sections

3. **Check Compliance**
   - Compares contract terms against RTA requirements
   - Identifies violations with severity levels
   - Cites specific sections violated

4. **Generate Recommendations**
   - Provides actionable fix suggestions
   - Includes suggested wording
   - Prioritizes by severity

5. **Final Report**
   - Comprehensive analysis document
   - Includes all issues and recommendations
   - Lists referenced law sections

## Usage

### Via Chainlit UI

1. Navigate to http://localhost:8000/chainlit
2. Click the file upload button
3. Select a contract (PDF, DOCX, or TXT)
4. Wait for automatic analysis
5. Review the compliance report

### Via Python API

```python
from rag.langchain import analyze_contract

# Analyze a contract
result = analyze_contract(
    contract_text="Full contract text here...",
    contract_type="Residential Lease"
)

# Access results
print(result["analysis_result"])  # Full report
print(result["compliance_issues"])  # Issues found
print(result["recommendations"])  # Suggestions
```

## Output Format

```markdown
# Contract Analysis Report

## Contract Type
Residential Lease

## Summary
Analyzed contract against Ontario Residential Tenancies Act, 2006.

## Compliance Issues Found
[Detailed issues with RTA citations]

## Recommendations
[Specific actionable fixes]

## Referenced Laws
1. **Section 12 - Subsection 1** - Rent Increase Rules
2. **Section 37** - Security Deposits
[...]

---

⚠️ Disclaimer: This analysis is for informational purposes only
and does not constitute legal advice.
```

## Integration Points

### Chat Mode + Contract Analysis

Users can:
1. Upload a contract for analysis
2. Then ask follow-up questions about specific clauses
3. Get instant answers with RTA references

Example:
```
User: [Uploads contract]
Assistant: [Provides compliance report]
User: "What does Section 12 say about rent increases?"
Assistant: [Answers using RAG]
```

## Configuration

### Customization Options

Edit `rag/langchain/contract_graph.py`:

```python
# Adjust LLM model
llm = ChatOpenAI(
    model="gpt-4o-mini",  # Change model
    temperature=0.0,       # Adjust creativity
)

# Modify retrieval count
retriever = get_retriever(k=3)  # Change k

# Filter contract types
if contract_type == "Commercial Lease":
    # Handle differently
```

## Best Practices

### For Accurate Analysis

1. **Upload complete contracts** (not excerpts)
2. **Use clear scans** (for PDFs)
3. **Proper formatting** (for DOCX files)
4. **Include all pages** (complete document)

### Performance Tips

- Contracts < 5000 chars: ~10 seconds
- Contracts 5000-15000 chars: ~20 seconds
- Contracts > 15000 chars: ~30+ seconds

## Limitations

- ⚠️ **Not legal advice** - Always consult a lawyer
- 📄 **Ontario-specific** - Only covers Ontario RTA
- 🔍 **AI-powered** - May miss nuanced issues
- 📊 **Best effort** - Not a substitute for legal review

## Future Enhancements

- [ ] Multi-jurisdiction support
- [ ] Export analysis as PDF
- [ ] Compare multiple contracts
- [ ] Track amendments over time
- [ ] Integration with e-signature platforms
