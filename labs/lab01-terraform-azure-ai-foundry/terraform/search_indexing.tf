# # Azure AI Search Indexing Configuration for Blob Storage Import
# # This file configures the indexer, data source, index, and skillset for importing blobs

# # Add a blob container specifically for documents to be indexed
# resource "azurerm_storage_container" "documents" {
#   name                  = "documents"
#   storage_account_id    = azurerm_storage_account.main.id
#   container_access_type = "private"
# }

# # Data source configuration for Azure Blob Storage
# resource "azapi_resource" "blob_data_source" {
#   type      = "Microsoft.Search/searchServices/datasources@2025-05-01"
#   name      = "blob-datasource"
#   parent_id = azurerm_search_service.main.id

#   body = {
#     type = "azureblob"
#     credentials = {
#       # Using managed identity for secure access
#       connectionString = "@{uri='${azurerm_storage_account.main.primary_blob_endpoint}',ResourceId='${azurerm_storage_account.main.id}'}"
#     }
#     container = {
#       name = azurerm_storage_container.documents.name
#       # Query parameter to include specific file types
#       query = "*.pdf;*.docx;*.txt;*.md;*.html"
#     }
#     dataChangeDetectionPolicy = {
#       "@odata.type" = "#Microsoft.Azure.Search.HighWaterMarkChangeDetectionPolicy"
#       highWaterMarkColumnName = "_ts"
#     }
#     dataDeletionDetectionPolicy = {
#       "@odata.type" = "#Microsoft.Azure.Search.SoftDeleteColumnDeletionDetectionPolicy"
#       softDeleteColumnName = "IsDeleted"
#       softDeleteMarkerValue = "true"
#     }
#   }

#   depends_on = [
#     azurerm_role_assignment.search_service_storage_blob_data_reader
#   ]
# }

# # Search index configuration with vector fields for modern AI search
# resource "azapi_resource" "blob_search_index" {
#   type      = "Microsoft.Search/searchServices/indexes@2025-05-01"
#   name      = "documents-index"
#   parent_id = azurerm_search_service.main.id

#   body = {
#     fields = [
#       {
#         name = "id"
#         type = "Edm.String"
#         key = true
#         searchable = false
#         filterable = true
#         retrievable = true
#       },
#       {
#         name = "content"
#         type = "Edm.String"
#         searchable = true
#         filterable = false
#         retrievable = true
#         analyzer = "standard.lucene"
#       },
#       {
#         name = "title"
#         type = "Edm.String"
#         searchable = true
#         filterable = true
#         retrievable = true
#         sortable = true
#       },
#       {
#         name = "metadata_storage_name"
#         type = "Edm.String"
#         searchable = true
#         filterable = true
#         retrievable = true
#         sortable = true
#       },
#       {
#         name = "metadata_storage_path"
#         type = "Edm.String"
#         searchable = false
#         filterable = true
#         retrievable = true
#       },
#       {
#         name = "metadata_storage_size"
#         type = "Edm.Int64"
#         searchable = false
#         filterable = true
#         retrievable = true
#         sortable = true
#       },
#       {
#         name = "metadata_storage_last_modified"
#         type = "Edm.DateTimeOffset"
#         searchable = false
#         filterable = true
#         retrievable = true
#         sortable = true
#       },
#       {
#         name = "metadata_content_type"
#         type = "Edm.String"
#         searchable = false
#         filterable = true
#         retrievable = true
#       },
#       # Vector field for semantic search using Azure OpenAI embeddings
#       {
#         name = "contentVector"
#         type = "Collection(Edm.Single)"
#         searchable = true
#         retrievable = false
#         dimensions = 1536
#         vectorSearchProfile = "vector-profile"
#       }
#     ]
    
#     # Vector search configuration
#     vectorSearch = {
#       algorithms = [
#         {
#           name = "vector-config"
#           kind = "hnsw"
#           hnswParameters = {
#             metric = "cosine"
#             m = 4
#             efConstruction = 400
#             efSearch = 500
#           }
#         }
#       ]
#       profiles = [
#         {
#           name = "vector-profile"
#           algorithm = "vector-config"
#           vectorizer = "openai-vectorizer"
#         }
#       ]
#       vectorizers = [
#         {
#           name = "openai-vectorizer"
#           kind = "azureOpenAI"
#           azureOpenAIParameters = {
#             resourceUri = azapi_resource.ai_foundry.output.properties.endpoint
#             deploymentId = azurerm_cognitive_deployment.text_embedding.name
#             modelName = "text-embedding-3-small"
#             authIdentity = {
#               "@odata.type" = "#Microsoft.Azure.Search.SearchIndexerDataIdentity"
#             }
#           }
#         }
#       ]
#     }

#     # Semantic search configuration
#     semantic = {
#       configurations = [
#         {
#           name = "semantic-config"
#           prioritizedFields = {
#             titleField = {
#               fieldName = "title"
#             }
#             contentFields = [
#               {
#                 fieldName = "content"
#               }
#             ]
#             keywordsFields = [
#               {
#                 fieldName = "metadata_storage_name"
#               }
#             ]
#           }
#         }
#       ]
#     }
#   }
# }

# # Skillset for AI enrichment with integrated vectorization
# resource "azapi_resource" "blob_skillset" {
#   type      = "Microsoft.Search/searchServices/skillsets@2025-05-01"
#   name      = "blob-skillset"
#   parent_id = azurerm_search_service.main.id

#   body = {
#     description = "Skillset for blob processing with AI enrichment and vectorization"
#     skills = [
#       # Text extraction skill
#       {
#         "@odata.type" = "#Microsoft.Skills.Util.DocumentExtractionSkill"
#         name = "document-extraction"
#         description = "Extract text from documents"
#         context = "/document"
#         inputs = [
#           {
#             name = "file_data"
#             source = "/document/file_data"
#           }
#         ]
#         outputs = [
#           {
#             name = "content"
#             targetName = "extracted_content"
#           }
#         ]
#         configuration = {
#           dataToExtract = "contentAndMetadata"
#           parsingMode = "default"
#         }
#       },
      
#       # Text splitting skill for chunking
#       {
#         "@odata.type" = "#Microsoft.Skills.Text.SplitSkill"
#         name = "text-splitter"
#         description = "Split text into smaller chunks"
#         context = "/document"
#         inputs = [
#           {
#             name = "text"
#             source = "/document/extracted_content"
#           }
#         ]
#         outputs = [
#           {
#             name = "textItems"
#             targetName = "pages"
#           }
#         ]
#         defaultLanguageCode = "en"
#         textSplitMode = "pages"
#         maximumPageLength = 2000
#         pageOverlapLength = 200
#       },

#       # Azure OpenAI Embedding skill for vectorization
#       {
#         "@odata.type" = "#Microsoft.Skills.Text.AzureOpenAIEmbeddingSkill"
#         name = "openai-embedding"
#         description = "Generate embeddings using Azure OpenAI"
#         context = "/document/pages/*"
#         resourceUri = azapi_resource.ai_foundry.output.properties.endpoint
#         deploymentId = azurerm_cognitive_deployment.text_embedding.name
#         modelName = "text-embedding-3-small"
#         authIdentity = {
#           "@odata.type" = "#Microsoft.Azure.Search.SearchIndexerDataUserAssignedIdentity"
#           userAssignedIdentity = azurerm_search_service.main.identity[0].principal_id
#         }
#         inputs = [
#           {
#             name = "text"
#             source = "/document/pages/*"
#           }
#         ]
#         outputs = [
#           {
#             name = "embedding"
#             targetName = "vector"
#           }
#         ]
#       }
#     ]

#     # Knowledge store configuration (optional)
#     knowledgeStore = {
#       storageConnectionString = "@{uri='${azurerm_storage_account.main.primary_blob_endpoint}',ResourceId='${azurerm_storage_account.main.id}'}"
#       projections = [
#         {
#           tables = [
#             {
#               tableName = "documentsTable"
#               generatedKeyName = "DocumentId"
#               source = "/document"
#               sourceContext = "/document/pages/*"
#               inputs = [
#                 {
#                   name = "title"
#                   source = "/document/metadata_storage_name"
#                 },
#                 {
#                   name = "content"
#                   source = "/document/pages/*"
#                 },
#                 {
#                   name = "vector"
#                   source = "/document/pages/*/vector"
#                 }
#               ]
#             }
#           ]
#         }
#       ]
#     }
#   }

#   depends_on = [
#     azurerm_role_assignment.ai_foundry_cognitive_services_openai_user
#   ]
# }

# # Indexer configuration with AI enrichment
# resource "azapi_resource" "blob_indexer" {
#   type      = "Microsoft.Search/searchServices/indexers@2025-05-01"
#   name      = "blob-indexer"
#   parent_id = azurerm_search_service.main.id

#   body = {
#     description = "Indexer for blob storage with AI enrichment"
#     dataSourceName = azapi_resource.blob_data_source.name
#     targetIndexName = azapi_resource.blob_search_index.name
#     skillsetName = azapi_resource.blob_skillset.name
    
#     schedule = {
#       interval = "PT1H" # Run every hour
#       startTime = "2024-01-01T00:00:00Z"
#     }

#     parameters = {
#       batchSize = 10
#       maxFailedItems = 5
#       maxFailedItemsPerBatch = 5
#       configuration = {
#         dataToExtract = "contentAndMetadata"
#         parsingMode = "default"
#         indexedFileNameExtensions = ".pdf,.docx,.doc,.txt,.html,.md"
#         excludedFileNameExtensions = ".png,.jpg,.jpeg,.gif,.bmp"
#         failOnUnsupportedContentType = false
#         failOnUnprocessableDocument = false
#         indexStorageMetadata = true
#         allowSkillsetToReadFileData = true
#       }
#     }

#     # Field mappings from data source to index
#     fieldMappings = [
#       {
#         sourceFieldName = "metadata_storage_path"
#         targetFieldName = "id"
#         mappingFunction = {
#           name = "base64Encode"
#         }
#       },
#       {
#         sourceFieldName = "metadata_storage_name"
#         targetFieldName = "title"
#       }
#     ]

#     # Output field mappings from skillset to index
#     outputFieldMappings = [
#       {
#         sourceFieldName = "/document/extracted_content"
#         targetFieldName = "content"
#       },
#       {
#         sourceFieldName = "/document/pages/*/vector"
#         targetFieldName = "contentVector"
#       }
#     ]
#   }

#   depends_on = [
#     azapi_resource.blob_data_source,
#     azapi_resource.blob_search_index,
#     azapi_resource.blob_skillset
#   ]
# }