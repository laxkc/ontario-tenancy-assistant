# Refactoring Plan: Simplify & Restructure

## 🎯 Goal
**Single Responsibility, Clear Structure, Remove Unnecessary Complexity**

---

## 📊 Current Problems

### 1. **Too Many Abstraction Layers**
```
handlers → services → langchain → graph → chains → retriever → vectorstore → embeddings
```
**Problem**: 8 layers for a simple Q&A!

### 2. **Unused/Dead Code**
- `rag_service.py` - Service layer never used
- `web_chat.py` - Unused file
- `chat.py` - Wrong imports, not used
- `langchain_query.py` - Demo file, not needed
- `test_*.py` - Test files in wrong location
- Empty `utils/__init__.py`
- Empty `llm.py`

### 3. **Overcomplicated RAG Graph**
- 8 nodes: classify → retrieve → check → summarize → generate → evaluate → improve → end
- **Too complex** for simple Q&A
- Self-check/evaluation adds unnecessary complexity

### 4. **Unclear Structure**
- Multiple entry points
- Config files scattered
- Handlers split unnecessarily
- Documentation in wrong places

---

## ✅ Proposed Clean Structure

```
agent/
├── main.py                    # Single entry point
├── config.py                  # Single config file
│
├── core/                      # Core RAG functionality
│   ├── __init__.py
│   ├── embeddings.py          # BGE embeddings
│   ├── vectorstore.py         # Pinecone
│   ├── retriever.py           # Document retrieval
│   └── rag.py                 # Simple RAG chain (no graph complexity)
│
├── web/                       # Web interface
│   ├── __init__.py
│   ├── app.py                 # Chainlit app
│   └── handlers.py            # All handlers in one file
│
├── contract/                  # Contract analysis
│   ├── __init__.py
│   └── analyzer.py            # Contract analysis logic
│
├── data/                      # Data pipeline (keep as is)
│   ├── parse_document.py
│   ├── parsers/
│   └── config.py
│
└── scripts/                   # Utility scripts
    ├── flatten_for_rag.py
    └── upsert_to_pinecone.py
```

---

## 🔧 Refactoring Steps

### **Phase 1: Remove Dead Code** ✅

#### Delete Files:
```bash
# Unused files
rm rag/langchain/llm.py
rm src/web/web_chat.py
rm src/web/services/rag_service.py
rm rag/chat.py
rm rag/langchain_query.py
rm rag/test_embeddings.py
rm rag/test_langchain.py
rm data/utils/__init__.py
rm src/web/config.py  # Merge into main config
rm src/web/CONTRACT_ANALYSIS.md  # Move to docs/
rm rag/langchain/README.md  # Move to docs/
rm UNUSED_CODE_ANALYSIS.md
```

#### Remove Unused Functions:
- `get_simple_retrieval_chain()` from `chains.py`
- `create_contract_analysis_graph()` export (keep internal use)

#### Clean Imports:
- Remove `HTTPException` from `routes.py`
- Fix wrong imports in test files (or delete them)

---

### **Phase 2: Simplify RAG System** 🔄

#### Current (Complex):
```
graph.py: 8 nodes, routing, evaluation, improvement
self_check.py: Quality evaluation
chains.py: Multiple chain types
```

#### Proposed (Simple):
```python
# core/rag.py - Simple, direct RAG
def get_answer(question: str, chat_history: list = None) -> dict:
    """Simple RAG: retrieve → generate → return"""
    # 1. Retrieve relevant docs
    docs = retriever.get_relevant(question, k=5)
    
    # 2. Format context
    context = format_context(docs)
    
    # 3. Generate answer
    answer = llm.generate(question, context, chat_history)
    
    # 4. Return
    return {
        "answer": answer,
        "sources": docs
    }
```

**Remove:**
- ❌ `graph.py` - Overcomplicated workflow
- ❌ `self_check.py` - Unnecessary quality checks
- ❌ `classify_question` - Can be simple filter
- ❌ `summarize_context` - Not needed
- ❌ `evaluate_answer_quality` - Over-engineering
- ❌ `improve_answer_if_needed` - Over-engineering

**Keep:**
- ✅ `embeddings.py` - Core functionality
- ✅ `vectorstore.py` - Core functionality
- ✅ `retriever.py` - Core functionality
- ✅ Simple chain in `rag.py`

---

### **Phase 3: Consolidate Structure** 🔄

#### 3.1 Create `core/` Directory
```bash
mkdir core
mv rag/langchain/embeddings.py core/
mv rag/langchain/vectorstore.py core/
mv rag/langchain/retriever.py core/
# Create new simple core/rag.py
```

#### 3.2 Simplify Web Layer
```bash
# Merge handlers
mv src/web/handlers/chat_handlers.py web/handlers.py
mv src/web/handlers/file_handlers.py → merge into web/handlers.py
rm -rf src/web/handlers/
rm -rf src/web/services/
```

#### 3.3 Consolidate Contract Analysis
```bash
mkdir contract
# Move contract_graph.py → contract/analyzer.py
# Simplify: remove graph complexity, make it a simple function
```

#### 3.4 Single Config
```bash
# Create config.py at root
# Merge: rag/config.py + data/config.py + web config
```

---

### **Phase 4: Simplify Code** 🔄

#### 4.1 Simplify RAG Graph → Simple Function

**Before (Complex):**
```python
# 8 nodes, routing, evaluation
create_rag_graph() → classify → retrieve → check → summarize → generate → evaluate → improve
```

**After (Simple):**
```python
# core/rag.py
def get_answer(question: str, history: list = None) -> dict:
    # Check if relevant (simple)
    if not is_tenancy_question(question):
        return {"answer": "I only answer Ontario tenancy questions..."}
    
    # Retrieve
    docs = retriever.get(question, k=5)
    if not docs:
        return {"answer": "Couldn't find relevant information..."}
    
    # Generate
    context = format_docs(docs)
    answer = llm.generate(question, context, history)
    
    return {"answer": answer, "sources": docs}
```

#### 4.2 Simplify Contract Analysis

**Before:**
```python
# 5-node graph: extract → retrieve → check → recommend → report
```

**After:**
```python
# contract/analyzer.py
def analyze_contract(text: str) -> dict:
    # 1. Extract clauses
    clauses = extract_clauses(text)
    
    # 2. Get relevant laws
    laws = retriever.get_relevant_for_clauses(clauses)
    
    # 3. Check compliance
    issues = check_compliance(clauses, laws)
    
    # 4. Generate report
    return generate_report(issues, laws)
```

#### 4.3 Merge Handlers

**Before:**
- `chat_handlers.py` (150 lines)
- `file_handlers.py` (154 lines)

**After:**
- `web/handlers.py` (single file, ~200 lines)

---

## 📁 Final Clean Structure

```
agent/
├── main.py                    # Entry point
├── config.py                  # All configuration
├── requirements.txt           # Dependencies
│
├── core/                      # Core RAG (4 files)
│   ├── __init__.py
│   ├── embeddings.py          # BGE embeddings wrapper
│   ├── vectorstore.py         # Pinecone integration
│   ├── retriever.py           # Document retrieval
│   └── rag.py                 # Simple RAG function
│
├── web/                       # Web interface (2 files)
│   ├── __init__.py
│   ├── app.py                 # Chainlit entry
│   └── handlers.py            # All handlers
│
├── contract/                  # Contract analysis (1 file)
│   ├── __init__.py
│   └── analyzer.py            # Contract analysis
│
├── data/                      # Data pipeline (keep as is)
│   ├── parse_document.py
│   ├── config.py
│   └── parsers/
│
└── scripts/                   # Utility scripts
    ├── flatten_for_rag.py
    └── upsert_to_pinecone.py
```

**Total Files: ~15 core files** (vs current ~40+)

---

## 🎯 Key Simplifications

### 1. **Remove Graph Complexity**
- ❌ LangGraph workflow with 8 nodes
- ✅ Simple function: retrieve → generate → return

### 2. **Remove Unnecessary Layers**
- ❌ Service layer (`rag_service.py`)
- ❌ Multiple handler files
- ❌ Over-abstracted chains

### 3. **Single Responsibility**
- `core/` = RAG functionality only
- `web/` = Web interface only
- `contract/` = Contract analysis only
- `data/` = Data parsing only

### 4. **Remove Dead Code**
- All test files in wrong locations
- All demo files
- All unused abstractions
- All empty files

---

## 📋 Implementation Checklist

### Phase 1: Cleanup (30 min)
- [ ] Delete all unused files
- [ ] Remove unused functions
- [ ] Clean imports

### Phase 2: Restructure (1 hour)
- [ ] Create `core/` directory
- [ ] Move and simplify RAG code
- [ ] Create `web/` directory
- [ ] Merge handlers
- [ ] Create `contract/` directory
- [ ] Simplify contract analysis

### Phase 3: Consolidate Config (15 min)
- [ ] Create single `config.py`
- [ ] Update all imports

### Phase 4: Test & Verify (30 min)
- [ ] Test web interface
- [ ] Test RAG queries
- [ ] Test contract analysis
- [ ] Verify all imports work

---

## 🚀 Benefits

1. **50% Less Code** - Remove unnecessary complexity
2. **Clear Structure** - Each directory has single purpose
3. **Easier to Understand** - No over-engineering
4. **Faster Development** - Less layers to navigate
5. **Better Maintainability** - Simple, direct code

---

## ⚠️ What We're Keeping

✅ **Data Pipeline** - Keep as is (it's separate, works well)
✅ **Core RAG Components** - Embeddings, vectorstore, retriever
✅ **Web Interface** - Chainlit handlers
✅ **Contract Analysis** - Simplified version
✅ **Scripts** - Utility scripts for ingestion

---

## ❌ What We're Removing

❌ **LangGraph Complexity** - Replace with simple function
❌ **Service Layer** - Unused abstraction
❌ **Quality Evaluation** - Over-engineering
❌ **Multiple Test Files** - Should be in `tests/` or deleted
❌ **Demo Files** - Not needed in production
❌ **Multiple Configs** - Consolidate to one
❌ **Unused Handlers** - Merge into one file

---

## 📝 Next Steps

1. **Review this plan** - Confirm approach
2. **Start Phase 1** - Delete dead code
3. **Implement Phase 2** - Restructure
4. **Test** - Verify everything works
5. **Document** - Update README

---

**Ready to proceed?** This will make the codebase **much simpler and cleaner** while keeping all functionality.

