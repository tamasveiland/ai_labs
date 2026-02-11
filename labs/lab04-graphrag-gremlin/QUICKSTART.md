# GraphRAG Quick Start Guide

This guide will help you get started with the GraphRAG lab quickly.

## Prerequisites

- Azure subscription with appropriate permissions
- Python 3.9 or later
- Azure CLI installed and authenticated

## Step 1: Clone and Setup (5 minutes)

```bash
# Clone the repository
git clone https://github.com/tamasveiland/ai_labs.git
cd ai_labs/labs/lab04-graphrag-gremlin

# Copy environment template
cp .env.example .env

# Edit .env file with your Azure subscription ID
# Required: AZURE_SUBSCRIPTION_ID
nano .env  # or use your preferred editor
```

## Step 2: Install Dependencies (2 minutes)

```bash
# Install infrastructure dependencies
cd infra
pip install -r requirements.txt

# Install script dependencies
cd ../scripts
pip install -r requirements.txt

# Install application dependencies
cd ../src
pip install -r requirements.txt

cd ..
```

## Step 3: Deploy Infrastructure (15-20 minutes)

```bash
# Authenticate with Azure
az login

# Set your subscription
export AZURE_SUBSCRIPTION_ID="your-subscription-id"

# Deploy all resources
python infra/deploy_infrastructure.py
```

This creates:
- ✅ Cosmos DB account with Gremlin API
- ✅ Gremlin database and graph
- ✅ Azure AI Search service
- ✅ Azure OpenAI with embedding model
- ✅ Storage account

## Step 4: Initialize Graph (2 minutes)

```bash
# Create graph schema and sample data
python scripts/initialize_graph.py
```

This creates:
- 📊 2 Document vertices
- 📊 3 Section vertices
- 📊 4 Chunk vertices
- 📊 5 Keyword vertices
- 🔗 All necessary edges (hasSection, hasChunk, hasKeyword, relatedTo)

## Step 5: Setup Search Index (2 minutes)

```bash
# Create Azure AI Search index with vector search
python scripts/setup_search_index.py
```

This creates:
- 🔍 Chunks index with 6 fields
- 🎯 Vector search configuration (3072 dimensions for text-embedding-3-large)
- 📈 Semantic search configuration

## Step 6: Setup Search Indexer (2 minutes)

```bash
# Create indexer to automatically sync Cosmos DB chunks to AI Search
python scripts/setup_search_indexer.py
```

This creates:
- 💾 Data source connected to Cosmos DB Gremlin graph
- 🧠 Skillset for Azure OpenAI embedding generation
- 🔄 Indexer that automatically pulls and indexes chunk data

The indexer will:
- Pull chunk vertices from Cosmos DB Gremlin
- Generate embeddings using Azure OpenAI
- Index documents to Azure AI Search
- Run automatically every hour

## Step 7: Test Queries (1 minute)

```bash
# Run a sample query
python src/query_graphrag.py --query "azure ai services"

# Run with verbose output
python src/query_graphrag.py --query "graph database" --verbose

# Get top 3 results
python src/query_graphrag.py --query "search and rag" --top 3

# Enable semantic ranking (requires Standard tier)
python src/query_graphrag.py --query "azure openai" --semantic
```

## Example Query Output

```
🔍 Processing query: 'azure ai services'

[Step 1/5] Extracting keywords...
  Keywords: ['azure', 'services']

[Step 2/5] Generating query embedding...
  Embedding dimensions: 3072

[Step 3/5] Performing hybrid search...
  Found 50 candidates

[Step 4/5] Validating with graph (keyword edges)...
  Validated 2 chunks with keyword edges

[Step 5/5] Expanding context via graph...
  Enriched 2 results with graph context

================================================================================
QUERY RESULTS
================================================================================

Query: azure ai services
Extracted Keywords: azure, services
Total Candidates: 50
Top Results: 2

Result #1
Chunk ID:    chunk-001
Document ID: doc-001
Score:       0.8542
Validated:   ✓ (keyword edge verified)

Text:
Azure AI Services provides comprehensive AI capabilities including OpenAI models.

Keywords: azure, ai, openai, services
```

## Common Commands

### Query Operations

```bash
# Basic query
python src/query_graphrag.py -q "your query here"

# Get more results
python src/query_graphrag.py -q "your query" --top 10

# Disable graph validation
python src/query_graphrag.py -q "your query" --no-graph-validation

# Output as JSON
python src/query_graphrag.py -q "your query" --json

# Multi-tenant query
python src/query_graphrag.py -q "your query" --tenant "tenant-id"
```

### Graph Operations

```bash
# Re-initialize graph with new data
python scripts/initialize_graph.py

# Reload search index
python scripts/load_sample_data.py
```

### Infrastructure Operations

```bash
# View resources in Azure Portal
az group show --name rg-graphrag-lab

# Cleanup all resources
python infra/cleanup_resources.py
```

## Troubleshooting

### Issue: Authentication Failed

```bash
# Re-authenticate with Azure
az login
az account set --subscription "your-subscription-id"
```

### Issue: Deployment Model Not Available

The embedding model may not be available in all regions. Try:
1. Change `AZURE_LOCATION` in `.env` to `eastus` or `westeurope`
2. Check [Azure OpenAI model availability](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models)

### Issue: Quota Exceeded

If you hit quota limits:
1. Request quota increase in Azure Portal
2. Or use existing OpenAI resources by updating `.env`

### Issue: Import Errors

```bash
# Ensure you're in the correct directory
cd /path/to/ai_labs/labs/lab04-graphrag-gremlin

# Reinstall dependencies
pip install -r infra/requirements.txt
pip install -r scripts/requirements.txt
pip install -r src/requirements.txt
```

## Next Steps

1. **Explore Graph Queries**: Check `docs/graph_queries.md` for example Gremlin queries
2. **Add Your Own Documents**: Modify sample documents in `data/sample_documents/`
3. **Customize the Model**: Edit graph schema in `scripts/initialize_graph.py`
4. **Integrate with Applications**: Use `src/graphrag_client.py` as a library
5. **Scale Up**: Increase Cosmos DB throughput and Search service tier

## Environment Variables

Key environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `AZURE_SUBSCRIPTION_ID` | *required* | Your Azure subscription ID |
| `RESOURCE_GROUP_NAME` | `rg-graphrag-lab` | Resource group name |
| `AZURE_LOCATION` | `eastus` | Azure region |
| `COSMOS_ACCOUNT_NAME` | `cosmos-graphrag-dev` | Cosmos DB account name |
| `SEARCH_SERVICE_NAME` | `search-graphrag-dev` | Search service name |
| `OPENAI_ACCOUNT_NAME` | `oai-graphrag-dev` | OpenAI account name |

## Cost Estimation

Approximate monthly costs (as of 2024, may vary by region):

- Cosmos DB Gremlin (400 RU/s): ~$24/month
- Azure AI Search (Basic tier): ~$75/month
- Azure OpenAI (pay-per-use): ~$1-10/month (light usage)
- Storage Account: <$1/month

**Total: ~$100-110/month**

💡 **Tip**: Run `python infra/cleanup_resources.py` when not in use to avoid charges.

## Support

- **Issues**: Open an issue on GitHub
- **Documentation**: See `README.md` and `docs/graph_queries.md`
- **Azure Support**: [Azure Portal Support](https://portal.azure.com/#blade/Microsoft_Azure_Support/HelpAndSupportBlade)

## License

MIT License - See [LICENSE](../../LICENSE) for details.
