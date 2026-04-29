from dataclasses import dataclass
import sys
import os

from fastmcp import FastMCP
from langchain_community.vectorstores import FAISS

sys.path.append('../common/')
from utils import get_embedding


DOC_DIR = "./vector_db/documents"
DEFAULT_WINDOW_SIZE = 20000

# Set up vector store
embeddings = get_embedding("main_embedding_model")

vector_store = FAISS.load_local("vector_db/FAISS_vector_store",
                                embeddings=embeddings,
                                allow_dangerous_deserialization=True)

# chace docs
MAX_LOADED_DOCS = 50
docs_cache = {}
for i, doc in enumerate(os.scandir(DOC_DIR)):
    doc = doc.name
    if not doc.endswith(".md"):
        continue
    if i >= MAX_LOADED_DOCS:
        break
    with open(f"{DOC_DIR}/{doc}") as in_file:
        docs_cache[doc.strip(".md")] = in_file.read()

# Set up MCP server
mcp = FastMCP("Papers")


def get_content_around_center(doc_id: str,
                              center: int,
                              window_size: int = DEFAULT_WINDOW_SIZE
                              ) -> str:
    
    if doc_id in docs_cache:
        doc = docs_cache[doc_id]
    else:
        with open(f"{DOC_DIR}/{doc_id}.md") as in_file:
            doc = in_file.read()

    start =  center - window_size//2

    # window flush to the left if goes it beyond the start of the doc
    if start < 0:
        end = center + window_size//2 - start + window_size%2
        start = 0
    else:
        end = center + window_size//2 + window_size%2
        offset = end - len(doc)

        # flush to the right
        start = start - offset if offset > 0 else start
    
    return doc[start:end]


@mcp.tool
def search_articles(query: str) -> list[dict]:
    """Search for papers. Papers are divided into chunks."""
    papers = []
    results = vector_store.similarity_search_with_relevance_scores(query[:2048], k=3)
    for vector, score in results:
        papers.append({
            "id": vector.id,
            "title": vector.metadata['title'],
            "area": vector.metadata['area'],
            "score": float(score)
            })
    return papers if papers else [{}]


@mcp.tool
def get_article_content(id: str) ->  dict | str:
    """Get a paper's content"""
    vector = vector_store.get_by_ids([id])
    if not vector:
        return "No papers with the provided ID."

    vector = vector[0]

    content = get_content_around_center(
        doc_id=vector.metadata['doc_id'],
        center=vector.metadata['center'])

    return {
        "id": vector.id,
        "title": vector.metadata['title'],
        "area": vector.metadata['area'],
        "content": content
        }



SERVER_IP = os.environ["SERVER_IP"]
SERVER_PORT = int(os.environ["SERVER_PORT"])
if __name__ == "__main__":
    mcp.run(transport="http", host=SERVER_IP, port=SERVER_PORT)