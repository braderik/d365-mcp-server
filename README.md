# D365 Documentation MCP Server

An MCP server that provides semantic search over Microsoft Dynamics 365 documentation.

## Features

- **query_d365_docs**: Search D365 documentation by semantic similarity
- **list_d365_topics**: List available D365 modules

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set your OpenAI API key:
   ```bash
   export OPENAI_API_KEY=your_key_here
   ```

3. Index the D365 documentation:
   ```bash
   python index_documents.py  # Full indexing
   python index_documents.py --test-mode  # Test with 10 files
   ```

4. Run the server:
   ```bash
   python server.py
   ```

## Deployment

For ChatGPT integration, deploy to a public URL and add as a connector:
1. Deploy to FastMCP Cloud, Fly.io, or use ngrok for local testing
2. In ChatGPT: Settings → Apps & Connectors → Advanced → Enable Developer Mode
3. Settings → Connectors → Create → paste your `/mcp` URL

## Usage in ChatGPT

After adding as a connector:
- "How do I configure posting profiles in D365 Finance?"
- "Explain warehouse management in D365 Supply Chain"
- "What are the best practices for D365 Commerce POS?"
