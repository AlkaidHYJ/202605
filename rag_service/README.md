# RAG Service (Local)

This service indexes the PDF and provides a simple search endpoint for the skill.

## 1) Install

```
pip install -r requirements.txt
```

## 2) Build index

Set the PDF path and run the indexer:

```
set RAG_PDF_PATH=C:\Users\ALKAID\Desktop\0517_2\2025学生手册.pdf
python indexer.py
```

## 3) Start server

```
uvicorn app:app --host 127.0.0.1 --port 9001
```

## Endpoint

`POST /rag/search`

Request:

```
{"query": "川农 宿舍", "top_k": 3}
```

Response:

```
{
  "content": "- ...\n- ...",
  "sources": [
    {"title": "2025学生手册.pdf", "page": 12, "score": 0.78}
  ]
}
```
