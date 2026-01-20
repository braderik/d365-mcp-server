from fastmcp import FastMCP
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from openai import OpenAI
import os
import json

# Initialize FastMCP server
mcp = FastMCP("D365 Documentation")

# Configuration
QDRANT_PATH = os.environ.get("QDRANT_PATH", "./qdrant_storage")
COLLECTION_NAME = "d365_docs"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536

def get_qdrant_client():
    """Get Qdrant client."""
    return QdrantClient(path=QDRANT_PATH)

def get_embedding(text: str) -> list:
    """Generate embedding using OpenAI."""
    client = OpenAI()
    response = client.embeddings.create(
        input=text,
        model=EMBEDDING_MODEL
    )
    return response.data[0].embedding

@mcp.tool()
def query_d365_docs(query: str, limit: int = 5) -> str:
    """
    Search Microsoft Dynamics 365 documentation for relevant information.
    
    Args:
        query: Your question or topic to search for in D365 docs.
        limit: Maximum number of results to return (default: 5).
    
    Returns:
        Relevant excerpts from D365 documentation.
    """
    try:
        # Generate embedding for query
        query_vector = get_embedding(query)
        
        # Search Qdrant
        client = get_qdrant_client()
        results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=limit
        )
        
        if not results:
            return "No relevant D365 documentation found for your query."
        
        # Format results
        formatted = []
        for i, point in enumerate(results, 1):
            payload = point.payload or {}
            source = payload.get("source", "Unknown")
            content = payload.get("content", "")[:500]
            score = point.score
            formatted.append(f"**[{i}] {source}** (relevance: {score:.2f})\n{content}...")
        
        return "\n\n---\n\n".join(formatted)
    
    except Exception as e:
        return f"Error searching D365 documentation: {str(e)}"

@mcp.tool()
def list_d365_topics() -> str:
    """
    List available D365 documentation topics/modules.
    
    Returns:
        List of available D365 modules and topics.
    """
    topics = [
        "Commerce - E-commerce, POS, retail operations",
        "Finance - General ledger, AP/AR, fixed assets, budgeting",
        "Supply Chain - Inventory, warehousing, manufacturing, procurement",
        "Human Resources - Employee management, benefits, leave, payroll",
        "Finance & Operations Core - Administration, data management, security"
    ]
    return "**Available D365 Documentation Topics:**\n\n" + "\n".join(f"- {t}" for t in topics)

if __name__ == "__main__":
    # Run with HTTP transport for ChatGPT compatibility
    mcp.run(transport="http", host="0.0.0.0", port=8000, path="/mcp")
