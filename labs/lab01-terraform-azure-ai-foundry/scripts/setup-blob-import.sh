#!/bin/bash

# Azure AI Search Blob Import Script
# This script creates indexing resources for importing blobs from Azure Storage to Azure AI Search
# Prerequisites: Azure CLI logged in with appropriate permissions

# Set variables (update these with your actual values)
RESOURCE_GROUP="your-resource-group-name"
SEARCH_SERVICE="your-search-service-name"
STORAGE_ACCOUNT="your-storage-account-name"
CONTAINER_NAME="documents"
INDEX_NAME="documents-index"
INDEXER_NAME="blob-indexer"
DATASOURCE_NAME="blob-datasource"
SKILLSET_NAME="blob-skillset"
OPENAI_RESOURCE="your-openai-resource-name"
EMBEDDING_DEPLOYMENT="text-embedding-3-small-deployment"

echo "🚀 Starting Azure AI Search blob import setup..."

# Step 1: Create storage container for documents
echo "📁 Creating storage container for documents..."
az storage container create \
    --name $CONTAINER_NAME \
    --account-name $STORAGE_ACCOUNT \
    --auth-mode login

# Step 2: Create data source
echo "🔗 Creating data source for blob storage..."
cat > datasource.json << EOF
{
    "name": "$DATASOURCE_NAME",
    "type": "azureblob",
    "credentials": {
        "connectionString": "@{uri='https://$STORAGE_ACCOUNT.blob.core.windows.net/',ResourceId='/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Storage/storageAccounts/$STORAGE_ACCOUNT'}"
    },
    "container": {
        "name": "$CONTAINER_NAME",
        "query": "*.pdf;*.docx;*.txt;*.md;*.html"
    },
    "dataChangeDetectionPolicy": {
        "@odata.type": "#Microsoft.Azure.Search.HighWaterMarkChangeDetectionPolicy",
        "highWaterMarkColumnName": "_ts"
    }
}
EOF

az rest \
    --method POST \
    --url "https://$SEARCH_SERVICE.search.windows.net/datasources?api-version=2025-05-01" \
    --body @datasource.json \
    --headers "Content-Type=application/json"

# Step 3: Create search index with vector support
echo "📊 Creating search index with vector fields..."
cat > index.json << EOF
{
    "name": "$INDEX_NAME",
    "fields": [
        {
            "name": "id",
            "type": "Edm.String",
            "key": true,
            "searchable": false,
            "filterable": true,
            "retrievable": true
        },
        {
            "name": "content",
            "type": "Edm.String",
            "searchable": true,
            "filterable": false,
            "retrievable": true,
            "analyzer": "standard.lucene"
        },
        {
            "name": "title",
            "type": "Edm.String",
            "searchable": true,
            "filterable": true,
            "retrievable": true,
            "sortable": true
        },
        {
            "name": "metadata_storage_name",
            "type": "Edm.String",
            "searchable": true,
            "filterable": true,
            "retrievable": true,
            "sortable": true
        },
        {
            "name": "metadata_storage_path",
            "type": "Edm.String",
            "searchable": false,
            "filterable": true,
            "retrievable": true
        },
        {
            "name": "metadata_storage_size",
            "type": "Edm.Int64",
            "searchable": false,
            "filterable": true,
            "retrievable": true,
            "sortable": true
        },
        {
            "name": "metadata_storage_last_modified",
            "type": "Edm.DateTimeOffset",
            "searchable": false,
            "filterable": true,
            "retrievable": true,
            "sortable": true
        },
        {
            "name": "contentVector",
            "type": "Collection(Edm.Single)",
            "searchable": true,
            "retrievable": false,
            "dimensions": 1536,
            "vectorSearchProfile": "vector-profile"
        }
    ],
    "vectorSearch": {
        "algorithms": [
            {
                "name": "vector-config",
                "kind": "hnsw",
                "hnswParameters": {
                    "metric": "cosine",
                    "m": 4,
                    "efConstruction": 400,
                    "efSearch": 500
                }
            }
        ],
        "profiles": [
            {
                "name": "vector-profile",
                "algorithm": "vector-config",
                "vectorizer": "openai-vectorizer"
            }
        ],
        "vectorizers": [
            {
                "name": "openai-vectorizer",
                "kind": "azureOpenAI",
                "azureOpenAIParameters": {
                    "resourceUri": "https://$OPENAI_RESOURCE.openai.azure.com",
                    "deploymentId": "$EMBEDDING_DEPLOYMENT",
                    "modelName": "text-embedding-3-small",
                    "authIdentity": {
                        "@odata.type": "#Microsoft.Azure.Search.SearchIndexerDataIdentity"
                    }
                }
            }
        ]
    },
    "semantic": {
        "configurations": [
            {
                "name": "semantic-config",
                "prioritizedFields": {
                    "titleField": {
                        "fieldName": "title"
                    },
                    "contentFields": [
                        {
                            "fieldName": "content"
                        }
                    ],
                    "keywordsFields": [
                        {
                            "fieldName": "metadata_storage_name"
                        }
                    ]
                }
            }
        ]
    }
}
EOF

az rest \
    --method POST \
    --url "https://$SEARCH_SERVICE.search.windows.net/indexes?api-version=2025-05-01" \
    --body @index.json \
    --headers "Content-Type=application/json"

# Step 4: Create skillset for AI enrichment
echo "🧠 Creating AI enrichment skillset..."
cat > skillset.json << EOF
{
    "name": "$SKILLSET_NAME",
    "description": "Skillset for blob processing with AI enrichment and vectorization",
    "skills": [
        {
            "@odata.type": "#Microsoft.Skills.Util.DocumentExtractionSkill",
            "name": "document-extraction",
            "description": "Extract text from documents",
            "context": "/document",
            "inputs": [
                {
                    "name": "file_data",
                    "source": "/document/file_data"
                }
            ],
            "outputs": [
                {
                    "name": "content",
                    "targetName": "extracted_content"
                }
            ],
            "configuration": {
                "dataToExtract": "contentAndMetadata",
                "parsingMode": "default"
            }
        },
        {
            "@odata.type": "#Microsoft.Skills.Text.SplitSkill",
            "name": "text-splitter",
            "description": "Split text into smaller chunks",
            "context": "/document",
            "inputs": [
                {
                    "name": "text",
                    "source": "/document/extracted_content"
                }
            ],
            "outputs": [
                {
                    "name": "textItems",
                    "targetName": "pages"
                }
            ],
            "defaultLanguageCode": "en",
            "textSplitMode": "pages",
            "maximumPageLength": 2000,
            "pageOverlapLength": 200
        },
        {
            "@odata.type": "#Microsoft.Skills.Text.AzureOpenAIEmbeddingSkill",
            "name": "openai-embedding",
            "description": "Generate embeddings using Azure OpenAI",
            "context": "/document/pages/*",
            "resourceUri": "https://$OPENAI_RESOURCE.openai.azure.com",
            "deploymentId": "$EMBEDDING_DEPLOYMENT",
            "modelName": "text-embedding-3-small",
            "authIdentity": {
                "@odata.type": "#Microsoft.Azure.Search.SearchIndexerDataUserAssignedIdentity"
            },
            "inputs": [
                {
                    "name": "text",
                    "source": "/document/pages/*"
                }
            ],
            "outputs": [
                {
                    "name": "embedding",
                    "targetName": "vector"
                }
            ]
        }
    ]
}
EOF

az rest \
    --method POST \
    --url "https://$SEARCH_SERVICE.search.windows.net/skillsets?api-version=2025-05-01" \
    --body @skillset.json \
    --headers "Content-Type=application/json"

# Step 5: Create indexer
echo "⚙️ Creating indexer..."
cat > indexer.json << EOF
{
    "name": "$INDEXER_NAME",
    "description": "Indexer for blob storage with AI enrichment",
    "dataSourceName": "$DATASOURCE_NAME",
    "targetIndexName": "$INDEX_NAME",
    "skillsetName": "$SKILLSET_NAME",
    "schedule": {
        "interval": "PT1H",
        "startTime": "2024-01-01T00:00:00Z"
    },
    "parameters": {
        "batchSize": 10,
        "maxFailedItems": 5,
        "maxFailedItemsPerBatch": 5,
        "configuration": {
            "dataToExtract": "contentAndMetadata",
            "parsingMode": "default",
            "indexedFileNameExtensions": ".pdf,.docx,.doc,.txt,.html,.md",
            "excludedFileNameExtensions": ".png,.jpg,.jpeg,.gif,.bmp",
            "failOnUnsupportedContentType": false,
            "failOnUnprocessableDocument": false,
            "indexStorageMetadata": true,
            "allowSkillsetToReadFileData": true
        }
    },
    "fieldMappings": [
        {
            "sourceFieldName": "metadata_storage_path",
            "targetFieldName": "id",
            "mappingFunction": {
                "name": "base64Encode"
            }
        },
        {
            "sourceFieldName": "metadata_storage_name",
            "targetFieldName": "title"
        }
    ],
    "outputFieldMappings": [
        {
            "sourceFieldName": "/document/extracted_content",
            "targetFieldName": "content"
        },
        {
            "sourceFieldName": "/document/pages/*/vector",
            "targetFieldName": "contentVector"
        }
    ]
}
EOF

az rest \
    --method POST \
    --url "https://$SEARCH_SERVICE.search.windows.net/indexers?api-version=2025-05-01" \
    --body @indexer.json \
    --headers "Content-Type=application/json"

# Step 6: Run the indexer
echo "🏃 Running the indexer..."
az rest \
    --method POST \
    --url "https://$SEARCH_SERVICE.search.windows.net/indexers/$INDEXER_NAME/run?api-version=2025-05-01"

# Step 7: Check indexer status
echo "📊 Checking indexer status..."
az rest \
    --method GET \
    --url "https://$SEARCH_SERVICE.search.windows.net/indexers/$INDEXER_NAME/status?api-version=2025-05-01"

# Clean up temporary files
rm -f datasource.json index.json skillset.json indexer.json

echo "✅ Azure AI Search blob import setup completed!"
echo ""
echo "📝 Next steps:"
echo "1. Upload documents to the '$CONTAINER_NAME' container in your storage account"
echo "2. The indexer will automatically process new documents every hour"
echo "3. Use the Azure portal or REST API to search your indexed content"
echo "4. Try vector search queries using the contentVector field for semantic search"
echo ""
echo "🔍 Test your search index:"
echo "curl -X POST 'https://$SEARCH_SERVICE.search.windows.net/indexes/$INDEX_NAME/docs/search?api-version=2025-05-01' \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -H 'api-key: YOUR_ADMIN_KEY' \\"
echo "     -d '{\"search\": \"your search query\", \"select\": \"title,content\", \"top\": 10}'"