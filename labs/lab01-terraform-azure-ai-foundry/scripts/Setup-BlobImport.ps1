# Azure AI Search Blob Import PowerShell Script
# This script creates indexing resources for importing blobs from Azure Storage to Azure AI Search
# Prerequisites: Azure CLI or PowerShell modules installed and authenticated

param(
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroupName,
    
    [Parameter(Mandatory=$true)]
    [string]$SearchServiceName,
    
    [Parameter(Mandatory=$true)]
    [string]$StorageAccountName,
    
    [Parameter(Mandatory=$true)]
    [string]$OpenAIResourceName,
    
    [string]$ContainerName = "documents",
    [string]$IndexName = "documents-index",
    [string]$IndexerName = "blob-indexer",
    [string]$DataSourceName = "blob-datasource",
    [string]$SkillsetName = "blob-skillset",
    [string]$EmbeddingDeployment = "text-embedding-3-small-deployment"
)

Write-Host "🚀 Starting Azure AI Search blob import setup..." -ForegroundColor Green

# Get subscription ID
$subscriptionId = (az account show --query id -o tsv)

# Step 1: Create storage container for documents
Write-Host "📁 Creating storage container for documents..." -ForegroundColor Yellow
az storage container create `
    --name $ContainerName `
    --account-name $StorageAccountName `
    --auth-mode login

# Step 2: Create data source
Write-Host "🔗 Creating data source for blob storage..." -ForegroundColor Yellow
$dataSourceJson = @{
    name = $DataSourceName
    type = "azureblob"
    credentials = @{
        connectionString = "@{uri='https://$StorageAccountName.blob.core.windows.net/',ResourceId='/subscriptions/$subscriptionId/resourceGroups/$ResourceGroupName/providers/Microsoft.Storage/storageAccounts/$StorageAccountName'}"
    }
    container = @{
        name = $ContainerName
        query = "*.pdf;*.docx;*.txt;*.md;*.html"
    }
    dataChangeDetectionPolicy = @{
        "@odata.type" = "#Microsoft.Azure.Search.HighWaterMarkChangeDetectionPolicy"
        highWaterMarkColumnName = "_ts"
    }
} | ConvertTo-Json -Depth 10

$dataSourceJson | Out-File -FilePath "datasource.json" -Encoding UTF8

az rest `
    --method POST `
    --url "https://$SearchServiceName.search.windows.net/datasources?api-version=2025-05-01" `
    --body '@datasource.json' `
    --headers "Content-Type=application/json"

# Step 3: Create search index with vector support
Write-Host "📊 Creating search index with vector fields..." -ForegroundColor Yellow
$indexJson = @{
    name = $IndexName
    fields = @(
        @{
            name = "id"
            type = "Edm.String"
            key = $true
            searchable = $false
            filterable = $true
            retrievable = $true
        },
        @{
            name = "content"
            type = "Edm.String"
            searchable = $true
            filterable = $false
            retrievable = $true
            analyzer = "standard.lucene"
        },
        @{
            name = "title"
            type = "Edm.String"
            searchable = $true
            filterable = $true
            retrievable = $true
            sortable = $true
        },
        @{
            name = "metadata_storage_name"
            type = "Edm.String"
            searchable = $true
            filterable = $true
            retrievable = $true
            sortable = $true
        },
        @{
            name = "metadata_storage_path"
            type = "Edm.String"
            searchable = $false
            filterable = $true
            retrievable = $true
        },
        @{
            name = "metadata_storage_size"
            type = "Edm.Int64"
            searchable = $false
            filterable = $true
            retrievable = $true
            sortable = $true
        },
        @{
            name = "metadata_storage_last_modified"
            type = "Edm.DateTimeOffset"
            searchable = $false
            filterable = $true
            retrievable = $true
            sortable = $true
        },
        @{
            name = "contentVector"
            type = "Collection(Edm.Single)"
            searchable = $true
            retrievable = $false
            dimensions = 1536
            vectorSearchProfile = "vector-profile"
        }
    )
    vectorSearch = @{
        algorithms = @(
            @{
                name = "vector-config"
                kind = "hnsw"
                hnswParameters = @{
                    metric = "cosine"
                    m = 4
                    efConstruction = 400
                    efSearch = 500
                }
            }
        )
        profiles = @(
            @{
                name = "vector-profile"
                algorithm = "vector-config"
                vectorizer = "openai-vectorizer"
            }
        )
        vectorizers = @(
            @{
                name = "openai-vectorizer"
                kind = "azureOpenAI"
                azureOpenAIParameters = @{
                    resourceUri = "https://$OpenAIResourceName.openai.azure.com"
                    deploymentId = $EmbeddingDeployment
                    modelName = "text-embedding-3-small"
                    authIdentity = @{
                        "@odata.type" = "#Microsoft.Azure.Search.SearchIndexerDataIdentity"
                    }
                }
            }
        )
    }
    semantic = @{
        configurations = @(
            @{
                name = "semantic-config"
                prioritizedFields = @{
                    titleField = @{
                        fieldName = "title"
                    }
                    contentFields = @(
                        @{
                            fieldName = "content"
                        }
                    )
                    keywordsFields = @(
                        @{
                            fieldName = "metadata_storage_name"
                        }
                    )
                }
            }
        )
    }
} | ConvertTo-Json -Depth 10

$indexJson | Out-File -FilePath "index.json" -Encoding UTF8

az rest `
    --method POST `
    --url "https://$SearchServiceName.search.windows.net/indexes?api-version=2025-05-01" `
    --body '@index.json' `
    --headers "Content-Type=application/json"

# Step 4: Create skillset for AI enrichment
Write-Host "🧠 Creating AI enrichment skillset..." -ForegroundColor Yellow
$skillsetJson = @{
    name = $SkillsetName
    description = "Skillset for blob processing with AI enrichment and vectorization"
    skills = @(
        @{
            "@odata.type" = "#Microsoft.Skills.Util.DocumentExtractionSkill"
            name = "document-extraction"
            description = "Extract text from documents"
            context = "/document"
            inputs = @(
                @{
                    name = "file_data"
                    source = "/document/file_data"
                }
            )
            outputs = @(
                @{
                    name = "content"
                    targetName = "extracted_content"
                }
            )
            configuration = @{
                dataToExtract = "contentAndMetadata"
                parsingMode = "default"
            }
        },
        @{
            "@odata.type" = "#Microsoft.Skills.Text.SplitSkill"
            name = "text-splitter"
            description = "Split text into smaller chunks"
            context = "/document"
            inputs = @(
                @{
                    name = "text"
                    source = "/document/extracted_content"
                }
            )
            outputs = @(
                @{
                    name = "textItems"
                    targetName = "pages"
                }
            )
            defaultLanguageCode = "en"
            textSplitMode = "pages"
            maximumPageLength = 2000
            pageOverlapLength = 200
        },
        @{
            "@odata.type" = "#Microsoft.Skills.Text.AzureOpenAIEmbeddingSkill"
            name = "openai-embedding"
            description = "Generate embeddings using Azure OpenAI"
            context = "/document/pages/*"
            resourceUri = "https://$OpenAIResourceName.openai.azure.com"
            deploymentId = $EmbeddingDeployment
            modelName = "text-embedding-3-small"
            authIdentity = @{
                "@odata.type" = "#Microsoft.Azure.Search.SearchIndexerDataUserAssignedIdentity"
            }
            inputs = @(
                @{
                    name = "text"
                    source = "/document/pages/*"
                }
            )
            outputs = @(
                @{
                    name = "embedding"
                    targetName = "vector"
                }
            )
        }
    )
} | ConvertTo-Json -Depth 10

$skillsetJson | Out-File -FilePath "skillset.json" -Encoding UTF8

az rest `
    --method POST `
    --url "https://$SearchServiceName.search.windows.net/skillsets?api-version=2025-05-01" `
    --body '@skillset.json' `
    --headers "Content-Type=application/json"

# Step 5: Create indexer
Write-Host "⚙️ Creating indexer..." -ForegroundColor Yellow
$indexerJson = @{
    name = $IndexerName
    description = "Indexer for blob storage with AI enrichment"
    dataSourceName = $DataSourceName
    targetIndexName = $IndexName
    skillsetName = $SkillsetName
    schedule = @{
        interval = "PT1H"
        startTime = "2024-01-01T00:00:00Z"
    }
    parameters = @{
        batchSize = 10
        maxFailedItems = 5
        maxFailedItemsPerBatch = 5
        configuration = @{
            dataToExtract = "contentAndMetadata"
            parsingMode = "default"
            indexedFileNameExtensions = ".pdf,.docx,.doc,.txt,.html,.md"
            excludedFileNameExtensions = ".png,.jpg,.jpeg,.gif,.bmp"
            failOnUnsupportedContentType = $false
            failOnUnprocessableDocument = $false
            indexStorageMetadata = $true
            allowSkillsetToReadFileData = $true
        }
    }
    fieldMappings = @(
        @{
            sourceFieldName = "metadata_storage_path"
            targetFieldName = "id"
            mappingFunction = @{
                name = "base64Encode"
            }
        },
        @{
            sourceFieldName = "metadata_storage_name"  
            targetFieldName = "title"
        }
    )
    outputFieldMappings = @(
        @{
            sourceFieldName = "/document/extracted_content"
            targetFieldName = "content"
        },
        @{
            sourceFieldName = "/document/pages/*/vector"
            targetFieldName = "contentVector"
        }
    )
} | ConvertTo-Json -Depth 10

$indexerJson | Out-File -FilePath "indexer.json" -Encoding UTF8

az rest `
    --method POST `
    --url "https://$SearchServiceName.search.windows.net/indexers?api-version=2025-05-01" `
    --body '@indexer.json' `
    --headers "Content-Type=application/json"

# Step 6: Run the indexer
Write-Host "🏃 Running the indexer..." -ForegroundColor Yellow
az rest `
    --method POST `
    --url "https://$SearchServiceName.search.windows.net/indexers/$IndexerName/run?api-version=2025-05-01"

# Step 7: Check indexer status
Write-Host "📊 Checking indexer status..." -ForegroundColor Yellow
az rest `
    --method GET `
    --url "https://$SearchServiceName.search.windows.net/indexers/$IndexerName/status?api-version=2025-05-01"

# Clean up temporary files
Remove-Item -Path "datasource.json", "index.json", "skillset.json", "indexer.json" -ErrorAction SilentlyContinue

Write-Host "✅ Azure AI Search blob import setup completed!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Next steps:" -ForegroundColor Cyan
Write-Host "1. Upload documents to the '$ContainerName' container in your storage account"
Write-Host "2. The indexer will automatically process new documents every hour"
Write-Host "3. Use the Azure portal or REST API to search your indexed content"
Write-Host "4. Try vector search queries using the contentVector field for semantic search"
Write-Host ""
Write-Host "🔍 Test your search index:" -ForegroundColor Cyan
Write-Host "Invoke-RestMethod -Uri 'https://$SearchServiceName.search.windows.net/indexes/$IndexName/docs/search?api-version=2025-05-01' ``" -ForegroundColor Gray
Write-Host "     -Method POST ``" -ForegroundColor Gray
Write-Host "     -Headers @{'Content-Type'='application/json'; 'api-key'='YOUR_ADMIN_KEY'} ``" -ForegroundColor Gray
Write-Host "     -Body '{\"search\": \"your search query\", \"select\": \"title,content\", \"top\": 10}'" -ForegroundColor Gray