# AI Labs - Copilot Instructions

## Model Preferences

**Primary AI Assistant**: Use Claude 3.5 Sonnet for all coding tasks, analysis, and technical assistance. This model provides superior code understanding, architectural reasoning, and complex problem-solving capabilities for Azure infrastructure and AI projects.

**Fallback Models**: If Claude 3.5 Sonnet is unavailable, use GPT-4o or GPT-4 Turbo as alternatives.

## Architecture Overview

This repository demonstrates **Azure AI Foundry + RAG (Retrieval-Augmented Generation)** implementations using Infrastructure as Code. The primary pattern is:

**Azure AI Foundry Hub/Project** → **Azure OpenAI** (GPT-4o + embeddings) → **Azure AI Search** (vector search) → **Azure Storage** (document storage)

## Key Components & Relationships

### Core Infrastructure Pattern (`terraform/main.tf`)
- **AI Foundry Hub**: Central management using `azapi_resource` (not `azurerm_cognitive_account`)
- **AI Foundry Project**: Child resource of Hub, manages connections to AI services
- **Dual OpenAI Setup**: Separate `azapi_resource.ai_foundry` and `azurerm_cognitive_account.openai` for different use cases
- **Search Service**: Always uses `SystemAssigned` managed identity with RBAC authentication

### Critical RBAC Pattern (`role_assignments.tf`)
```terraform
# Pattern: Service → Service access using managed identities
resource "azurerm_role_assignment" "search_service_storage_blob_data_reader" {
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Blob Data Reader"
  principal_id         = azurerm_search_service.main.identity[0].principal_id
}
```
**Key**: AI Search needs multiple roles (Storage Blob Data Reader/Contributor, Cognitive Services OpenAI User). Current user gets administrative roles for portal access.

### Search Indexing Architecture (`search_indexing.tf`)
- **Commented Infrastructure**: Complete RAG setup exists but commented out - activate by uncommenting
- **Vectorization**: Uses `text-embedding-3-large` (not 3-small) - check `variables.tf` for current model
- **Skillset Pipeline**: Document extraction → Text splitting → OpenAI embedding → Vector storage
- **HNSW Algorithm**: Vector search using cosine similarity with specific parameters

## Development Workflows

### Terraform Deployment Pattern
```bash
cd labs/lab01-terraform-azure-ai-foundry/terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
terraform init
terraform plan
terraform apply
```

### Manual Search Setup (Alternative to Terraform)
Use `scripts/Setup-BlobImport.ps1` for portal-based configuration:
```powershell
.\Setup-BlobImport.ps1 -ResourceGroupName "rg-name" -SearchServiceName "search-name" -StorageAccountName "storage-name" -OpenAIResourceName "openai-name"
```

### Document Processing Workflow
1. **Upload**: Documents go to `documents` container in Storage Account
2. **Indexing**: AI Search indexer processes via skillset (extraction → chunking → embedding)
3. **RAG Integration**: Connect to AI Foundry Chat Playground via portal UI
4. **Testing**: Use Search Explorer or REST API for validation

## Project-Specific Conventions

### Resource Naming Pattern
```terraform
name = "${service_prefix}-${var.project_name}-${var.environment}-${random_string.suffix.result}"
```
Examples: `search-ailabs-dev-abc123`, `oai-ailabs-dev-abc123`

### Managed Identity First
- **Never use API keys** - everything uses managed identities
- **Storage Account**: `shared_access_key_enabled = false`
- **Search Service**: `local_authentication_enabled = true` but RBAC required for data operations
- **AI Foundry**: `disableLocalAuth = false` for compatibility but uses managed identity

### Documentation Structure
- **Main README**: Repository overview with architecture
- **Lab README**: Complete step-by-step instructions with screenshots
- **Images folder**: Sequential screenshots (`lab01_search_wizard_01.png`, `lab01_chat_playground_wizard_01.png`)

## Common Issues & Solutions

### Model Availability
```terraform
# Check region support before deployment
embedding_model_name = "text-embedding-3-large"  # More widely available than 3-small
gpt_model_version   = "2024-08-06"               # Use stable versions
```

### RBAC Dependencies
Always ensure role assignments complete before dependent resources:
```terraform
depends_on = [
  azurerm_role_assignment.search_service_storage_blob_data_reader,
  azurerm_role_assignment.ai_foundry_cognitive_services_openai_user
]
```

### Search Indexing Activation
The complete RAG setup in `search_indexing.tf` is commented out by design. Uncomment and apply when ready for full document processing pipeline.

## Critical File Locations

- **Infrastructure**: `labs/lab01-terraform-azure-ai-foundry/terraform/`
- **Helper Scripts**: `labs/lab01-terraform-azure-ai-foundry/scripts/`
- **Documentation Images**: `labs/lab01-terraform-azure-ai-foundry/images/`
- **Lab Instructions**: `labs/lab01-terraform-azure-ai-foundry/README.md`

## Testing Patterns

### Search Validation
```bash
# Test with RBAC authentication
curl -X POST "https://search-name.search.windows.net/indexes/documents-index/docs/search?api-version=2023-11-01" \
     -H "Authorization: Bearer $(az account get-access-token --resource https://search.azure.com --query accessToken -o tsv)" \
     -d '{"search": "*", "top": 5}'
```

### RAG Testing Queries
```text
"What documents do you have access to?"
"Summarize the main topics in the uploaded documents"  
"Tell me about [specific topic from your documents]"
```

Focus on **infrastructure patterns**, **RBAC relationships**, and **RAG implementation** when working with this codebase.