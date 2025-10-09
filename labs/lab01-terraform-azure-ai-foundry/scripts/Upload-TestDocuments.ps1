# Upload Test Documents Script
# This script uploads sample documents to test the Azure AI Search blob import

param(
    [Parameter(Mandatory=$true)]
    [string]$StorageAccountName,
    
    [string]$ContainerName = "documents"
)

Write-Host "📄 Creating and uploading test documents..." -ForegroundColor Green

# Create a temp directory for test documents
$tempDir = Join-Path $env:TEMP "test-documents"
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

# Create sample documents
$documents = @{
    "azure-ai-overview.txt" = @"
Azure AI Services Overview

Azure AI services provide developers with AI capabilities to build intelligent applications without requiring deep machine learning expertise. These services include:

1. Azure OpenAI Service
   - GPT models for text generation and completion
   - DALL-E for image generation
   - Embeddings for semantic search

2. Azure AI Search (formerly Azure Cognitive Search)
   - Full-text search capabilities
   - Vector search for semantic similarity
   - AI-powered content enrichment

3. Azure AI Vision
   - Image analysis and recognition
   - OCR for text extraction from images
   - Face detection and recognition

4. Azure AI Language
   - Sentiment analysis
   - Key phrase extraction
   - Named entity recognition
   - Language detection

Key Benefits:
- Easy integration with existing applications
- Scalable and reliable cloud infrastructure
- Pre-trained models ready to use
- Support for custom model training
"@

    "search-best-practices.md" = @"
# Azure AI Search Best Practices

## Index Design
- Plan your index schema carefully
- Use appropriate field types for your data
- Enable vector search for semantic capabilities
- Implement proper field mappings

## Performance Optimization
- Use batch operations for bulk data ingestion
- Implement proper caching strategies
- Monitor query performance and optimize
- Use search filters to reduce result sets

## Security Considerations
- Enable RBAC for secure access control
- Use managed identities for authentication
- Implement network security restrictions
- Monitor access patterns and usage

## AI Enrichment
- Use skillsets for content processing
- Implement custom skills for specific needs
- Cache enriched content for performance
- Monitor AI service usage and costs

## Monitoring and Maintenance
- Set up proper logging and alerting
- Monitor indexer performance
- Implement change detection policies
- Regular index maintenance and optimization
"@

    "data-integration-guide.html" = @"
<!DOCTYPE html>
<html>
<head>
    <title>Data Integration with Azure AI Search</title>
</head>
<body>
    <h1>Data Integration Guide</h1>
    
    <h2>Supported Data Sources</h2>
    <ul>
        <li>Azure Blob Storage</li>
        <li>Azure SQL Database</li>
        <li>Azure Cosmos DB</li>
        <li>Azure Table Storage</li>
        <li>SharePoint Online</li>
        <li>Microsoft OneLake</li>
    </ul>
    
    <h2>Indexing Strategies</h2>
    <p>Choose the right indexing approach based on your data characteristics:</p>
    
    <h3>Push Model</h3>
    <p>Use when you have full control over data updates and need real-time indexing.</p>
    
    <h3>Pull Model (Indexers)</h3>
    <p>Ideal for automated data ingestion from supported data sources with built-in change detection.</p>
    
    <h2>Vector Search Integration</h2>
    <p>Modern applications benefit from vector search capabilities for semantic understanding and similarity matching.</p>
    
    <h3>Embedding Models</h3>
    <ul>
        <li>Azure OpenAI text-embedding-ada-002</li>
        <li>Azure OpenAI text-embedding-3-small</li>
        <li>Azure AI Vision for image embeddings</li>
    </ul>
</body>
</html>
"@
}

# Create and upload documents
foreach ($fileName in $documents.Keys) {
    $filePath = Join-Path $tempDir $fileName
    $documents[$fileName] | Out-File -FilePath $filePath -Encoding UTF8
    
    Write-Host "📤 Uploading $fileName..." -ForegroundColor Yellow
    
    az storage blob upload `
        --account-name $StorageAccountName `
        --container-name $ContainerName `
        --name $fileName `
        --file $filePath `
        --auth-mode login `
        --overwrite
}

# Create a PDF simulation (text file with .pdf extension for demo)
$pdfContent = @"
Enterprise Search Solutions with Azure AI Search

Executive Summary
This document outlines the implementation of enterprise search solutions using Azure AI Search, focusing on modern AI-powered capabilities including vector search and semantic understanding.

Key Features
- Full-text search with advanced ranking
- Vector search for semantic similarity
- AI-powered content enrichment
- Multi-language support
- Faceted navigation and filtering

Architecture Overview
The solution leverages Azure AI Search as the core search engine, integrated with Azure OpenAI for embeddings generation and content understanding. Data sources include:
- Document repositories (SharePoint, file shares)
- Database systems (SQL, Cosmos DB)
- Web content and APIs
- Email and collaboration platforms

Implementation Phases
Phase 1: Data ingestion and basic search
Phase 2: AI enrichment and vector search
Phase 3: Advanced features and customization
Phase 4: Monitoring and optimization

ROI and Benefits
- Improved information discovery
- Reduced time to find relevant content
- Enhanced user experience
- Better decision-making through data insights
"@

$pdfPath = Join-Path $tempDir "enterprise-search-whitepaper.pdf"
$pdfContent | Out-File -FilePath $pdfPath -Encoding UTF8

Write-Host "📤 Uploading enterprise-search-whitepaper.pdf..." -ForegroundColor Yellow
az storage blob upload `
    --account-name $StorageAccountName `
    --container-name $ContainerName `
    --name "enterprise-search-whitepaper.pdf" `
    --file $pdfPath `
    --auth-mode login `
    --overwrite

# Clean up temp directory
Remove-Item -Path $tempDir -Recurse -Force

Write-Host "✅ Test documents uploaded successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Uploaded documents:" -ForegroundColor Cyan
Write-Host "- azure-ai-overview.txt (Text file with Azure AI overview)"
Write-Host "- search-best-practices.md (Markdown file with best practices)"
Write-Host "- data-integration-guide.html (HTML file with integration guide)"
Write-Host "- enterprise-search-whitepaper.pdf (PDF simulation)"
Write-Host ""
Write-Host "🔄 The indexer will process these documents automatically." -ForegroundColor Yellow
Write-Host "Check the indexer status in about 5-10 minutes to see the results."