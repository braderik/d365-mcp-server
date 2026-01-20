from fastmcp import FastMCP
from openai import OpenAI
import os

# Initialize FastMCP server
mcp = FastMCP("D365 Documentation")

# OpenAI Vector Store ID (pre-indexed D365 docs)
VECTOR_STORE_ID = "vs_68f7bebdff78819195d043f09a740930"

def get_openai_client():
    return OpenAI()

@mcp.tool()
def query_d365_docs(query: str) -> str:
    """
    Search Microsoft Dynamics 365 documentation for relevant information.
    
    Args:
        query: Your question or topic to search for in D365 docs.
    
    Returns:
        Relevant excerpts from D365 documentation.
    """
    try:
        client = get_openai_client()
        
        # Create a thread with file search
        thread = client.beta.threads.create(
            messages=[{"role": "user", "content": query}],
            tool_resources={"file_search": {"vector_store_ids": [VECTOR_STORE_ID]}}
        )
        
        # Create assistant for search
        assistant = client.beta.assistants.create(
            name="D365 Documentation Search",
            instructions="Search the attached D365 documentation files and provide relevant information. Always cite the source file.",
            model="gpt-4o",
            tools=[{"type": "file_search"}]
        )
        
        try:
            # Run the assistant
            run = client.beta.threads.runs.create_and_poll(
                thread_id=thread.id,
                assistant_id=assistant.id
            )
            
            if run.status == 'completed':
                messages = client.beta.threads.messages.list(thread_id=thread.id)
                for msg in messages.data:
                    if msg.role == "assistant":
                        return msg.content[0].text.value
                return "No relevant D365 documentation found."
            else:
                return f"Search failed: {run.status}"
        finally:
            # Clean up assistant
            client.beta.assistants.delete(assistant.id)
            
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
