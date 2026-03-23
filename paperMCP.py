from fastmcp import FastMCP

from langchain_community.vectorstores import FAISS

from utils import get_llm_instance

# Set up vector store
embeddings = get_llm_instance("main_embedding_model", embedding=True)

vector_store = FAISS.load_local("persistent_vector_store",
                                embeddings=embeddings,
                                allow_dangerous_deserialization=True)


# Set up MCP server
mcp = FastMCP("Papers")

@mcp.tool()
def search_articles(query: str) -> list[dict]:
    """Search for papers"""
    papers = []
    for vector, score in vector_store.similarity_search_with_relevance_scores(query, k=3):
        papers.append({
            "id": vector.id,
            "title": vector.metadata['title'],
            "area": vector.metadata['area'],
            "score": score,
            })
    return papers


@mcp.tool()
def get_article_content(id: str) -> dict:
    """Get a paper's content"""
    vector = vector_store.get_by_ids([id])[0]

    return {
        "id": vector.id,
        "title": vector.metadata['title'],
        "area": vector.metadata['area'],
        "content": vector.page_content,
        }

if __name__ == "__main__":
    mcp.run(transport="streamable-http")