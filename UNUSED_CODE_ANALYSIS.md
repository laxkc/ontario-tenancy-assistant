# Unused Files and Code Analysis

## 🔴 Completely Unused Files

### 1. `rag/langchain/llm.py`
- **Status**: Empty file (0 bytes)
- **Issue**: File exists but has no content
- **Action**: Delete or implement if needed

### 2. `src/web/web_chat.py`
- **Status**: Defined but never imported
- **Content**: Simple Chainlit handler with "Hello World" message
- **Issue**: Not referenced in `main.py` or `src/web/app.py`
- **Action**: Delete if not needed, or integrate into main app

### 3. `src/web/services/rag_service.py`
- **Status**: Service class defined but never used
- **Issue**: `RAGService` class and `get_rag_service()` function are never imported or called
- **Current Usage**: The web handlers directly use `create_rag_graph()` from `rag.langchain`
- **Action**: Either use this service layer or remove it

### 4. `data/utils/__init__.py`
- **Status**: Empty utility module
- **Content**: Only has a docstring "Utility functions."
- **Issue**: No actual utilities defined or used
- **Action**: Delete if no utilities are planned

---

## ⚠️ Files with Incorrect Imports (Will Fail at Runtime)

### 5. `rag/chat.py`
- **Issue**: Line 8 has wrong import path
  ```python
  from langchain.chains import get_qa_chain  # ❌ WRONG
  ```
- **Should be**:
  ```python
  from rag.langchain.chains import get_qa_chain  # ✅ CORRECT
  ```
- **Status**: Will cause ImportError when run

### 6. `rag/langchain_query.py`
- **Issue**: Lines 16-18 have wrong import paths
  ```python
  from langchain.chains import get_qa_chain  # ❌ WRONG
  from langchain.retriever import get_retriever  # ❌ WRONG
  from langchain.graph import query_with_graph  # ❌ WRONG
  ```
- **Should be**:
  ```python
  from rag.langchain.chains import get_qa_chain  # ✅ CORRECT
  from rag.langchain.retriever import get_retriever  # ✅ CORRECT
  from rag.langchain.graph import query_with_graph  # ✅ CORRECT
  ```
- **Status**: Will cause ImportError when run

### 7. `rag/test_langchain.py`
- **Issue**: Lines 13, 33, 52 have wrong import paths
  ```python
  from langchain.retriever import get_retriever  # ❌ WRONG
  from langchain.chains import get_qa_chain  # ❌ WRONG
  from langchain.graph import query_with_graph  # ❌ WRONG
  ```
- **Should be**:
  ```python
  from rag.langchain.retriever import get_retriever  # ✅ CORRECT
  from rag.langchain.chains import get_qa_chain  # ✅ CORRECT
  from rag.langchain.graph import query_with_graph  # ✅ CORRECT
  ```
- **Status**: Will cause ImportError when run

---

## 🟡 Unused Functions/Classes

### 8. `rag/langchain/chains.py` - `get_simple_retrieval_chain()`
- **Status**: Function defined (lines 91-106) but never called
- **Usage**: Only mentioned in README.md as example
- **Action**: Remove if not needed, or add usage example

### 9. `rag/langchain/contract_graph.py` - `create_contract_analysis_graph()`
- **Status**: Function exported in `__init__.py` but never directly used
- **Usage**: Only `analyze_contract()` is used (which calls it internally)
- **Action**: Can keep for advanced usage, or remove from exports if not needed

### 10. `src/api/routes.py` - `HTTPException`
- **Status**: Imported but never used
- **Line 2**: `from fastapi import APIRouter, HTTPException`
- **Action**: Remove unused import

### 11. `src/web/config.py` - Configuration Variables
- **Status**: Variables defined but never imported/used
  - `WEB_APP_TITLE`
  - `WEB_APP_DESCRIPTION`
  - `THEME_SETTINGS`
  - `ENABLE_AUTHENTICATION`
  - `ENABLE_DATA_PERSISTENCE`
- **Action**: Either use these in the app or remove them

---

## 🟢 Test/Demo Files (Intentionally Standalone)

These files are meant to be run standalone, not imported:

- ✅ `rag/test_embeddings.py` - Test script
- ✅ `rag/test_langchain.py` - Test script (but has wrong imports)
- ✅ `rag/scripts/query_example.py` - Example script
- ✅ `rag/scripts/flatten_for_rag.py` - Ingestion script
- ✅ `rag/scripts/upsert_to_pinecone.py` - Ingestion script
- ✅ `data/parse_document.py` - Parsing script

---

## 📊 Summary

### Files to Delete:
1. `rag/langchain/llm.py` (empty)
2. `src/web/web_chat.py` (unused)
3. `data/utils/__init__.py` (empty)

### Files to Fix (Import Errors):
1. `rag/chat.py` - Fix import path
2. `rag/langchain_query.py` - Fix import paths
3. `rag/test_langchain.py` - Fix import paths

### Code to Clean:
1. `src/web/services/rag_service.py` - Use or remove
2. `rag/langchain/chains.py` - Remove `get_simple_retrieval_chain()` if unused
3. `src/api/routes.py` - Remove unused `HTTPException` import
4. `src/web/config.py` - Use config vars or remove

---

## 🔧 Recommended Actions

### Priority 1: Fix Import Errors
```bash
# Fix these files to prevent runtime errors:
- rag/chat.py
- rag/langchain_query.py  
- rag/test_langchain.py
```

### Priority 2: Remove Unused Files
```bash
# Safe to delete:
rm rag/langchain/llm.py
rm src/web/web_chat.py
rm data/utils/__init__.py
```

### Priority 3: Clean Up Unused Code
- Remove unused imports
- Decide on `rag_service.py` - use it or remove it
- Remove or use config variables in `src/web/config.py`

