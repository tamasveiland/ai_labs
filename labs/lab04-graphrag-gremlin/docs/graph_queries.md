# Gremlin Query Examples for GraphRAG

This document provides example Gremlin queries for working with the GraphRAG knowledge graph in Cosmos DB.

## Basic Vertex Queries

### Count all vertices by label

```gremlin
g.V().hasLabel('document').count()
g.V().hasLabel('section').count()
g.V().hasLabel('chunk').count()
g.V().hasLabel('keyword').count()
```

### Get all vertices of a specific type

```gremlin
// Get all documents
g.V().hasLabel('document').valueMap()

// Get all keywords
g.V().hasLabel('keyword').valueMap()
```

### Find a specific vertex

```gremlin
// Find document by docId
g.V().hasLabel('document').has('docId', 'doc-001')

// Find chunk by chunkId
g.V().hasLabel('chunk').has('chunkId', 'chunk-001')

// Find keyword by term
g.V().hasLabel('keyword').has('term', 'azure')
```

## Traversal Queries

### Navigate the document hierarchy

```gremlin
// Get all sections of a document
g.V().hasLabel('document').has('docId', 'doc-001')
  .out('hasSection')
  .valueMap()

// Get all chunks of a document
g.V().hasLabel('document').has('docId', 'doc-001')
  .out('hasSection')
  .out('hasChunk')
  .valueMap()

// Get all chunks with their text
g.V().hasLabel('document').has('docId', 'doc-001')
  .out('hasSection')
  .out('hasChunk')
  .values('chunkId', 'text')
```

### Navigate from chunk to document

```gremlin
// Get parent section from chunk
g.V().hasLabel('chunk').has('chunkId', 'chunk-001')
  .in('hasChunk')
  .valueMap()

// Get parent document from chunk
g.V().hasLabel('chunk').has('chunkId', 'chunk-001')
  .in('hasChunk')
  .in('hasSection')
  .valueMap()
```

## Keyword-based Queries

### Find chunks by keyword

```gremlin
// Find all chunks with a specific keyword
g.V().hasLabel('keyword').has('term', 'azure')
  .out('hasKeyword')
  .values('chunkId', 'text')

// Count chunks for each keyword
g.V().hasLabel('keyword')
  .project('keyword', 'count')
  .by('term')
  .by(out('hasKeyword').count())
```

### Find keywords for a chunk

```gremlin
// Get all keywords for a specific chunk
g.V().hasLabel('chunk').has('chunkId', 'chunk-001')
  .in('hasKeyword')
  .values('term')
```

### Find documents by keyword

```gremlin
// Find all documents containing a specific keyword
g.V().hasLabel('keyword').has('term', 'graph')
  .out('hasKeyword')
  .in('hasChunk')
  .in('hasSection')
  .dedup()
  .values('docId', 'title')
```

## Relationship Queries

### Find related chunks

```gremlin
// Get chunks related to a specific chunk
g.V().hasLabel('chunk').has('chunkId', 'chunk-001')
  .both('relatedTo')
  .values('chunkId', 'text')

// Get chunks related within 2 hops
g.V().hasLabel('chunk').has('chunkId', 'chunk-001')
  .repeat(both('relatedTo')).times(2)
  .dedup()
  .values('chunkId')
```

## Context Expansion Queries

### Expand full context from a chunk

```gremlin
// Get comprehensive context for a chunk
g.V().hasLabel('chunk').has('chunkId', 'chunk-001')
  .project('chunk', 'keywords', 'relatedChunks', 'section', 'document')
  .by(valueMap())
  .by(in('hasKeyword').values('term').fold())
  .by(both('relatedTo').values('chunkId').fold())
  .by(in('hasChunk').valueMap())
  .by(in('hasChunk').in('hasSection').valueMap())
```

### Get neighboring chunks in document order

```gremlin
// Get chunks from the same section
g.V().hasLabel('chunk').has('chunkId', 'chunk-002')
  .in('hasChunk')
  .out('hasChunk')
  .order().by('position')
  .values('chunkId', 'position', 'text')
```

## Multi-tenancy Queries

### Query by tenant

```gremlin
// Get all chunks for a specific tenant
g.V().hasLabel('chunk').has('tenant', 'default')
  .values('chunkId', 'text')

// Count documents per tenant
g.V().hasLabel('document')
  .group()
  .by('tenant')
  .by(count())
```

## Advanced Queries

### Find chunks with multiple keywords

```gremlin
// Find chunks that have both 'azure' and 'search' keywords
g.V().hasLabel('keyword').has('term', 'azure')
  .out('hasKeyword')
  .as('chunk')
  .where(
    __.in('hasKeyword').has('keyword', 'term', 'search')
  )
  .select('chunk')
  .values('chunkId', 'text')
```

### Find most connected chunks

```gremlin
// Find chunks with most keyword connections
g.V().hasLabel('chunk')
  .project('chunkId', 'keywordCount')
  .by('chunkId')
  .by(in('hasKeyword').count())
  .order().by(select('keywordCount'), desc)
  .limit(10)
```

### Similarity-based retrieval

```gremlin
// Find chunks similar to a given chunk (via shared keywords)
g.V().hasLabel('chunk').has('chunkId', 'chunk-001')
  .in('hasKeyword')
  .out('hasKeyword')
  .where(__.not(has('chunkId', 'chunk-001')))
  .dedup()
  .values('chunkId', 'text')
```

## Edge Queries

### Count edges by type

```gremlin
g.E().hasLabel('hasSection').count()
g.E().hasLabel('hasChunk').count()
g.E().hasLabel('hasKeyword').count()
g.E().hasLabel('relatedTo').count()
```

### Find all edges for a vertex

```gremlin
// Get all outgoing edges from a document
g.V().hasLabel('document').has('docId', 'doc-001')
  .outE()
  .label()
  .dedup()

// Get all edges (both directions) for a chunk
g.V().hasLabel('chunk').has('chunkId', 'chunk-001')
  .bothE()
  .project('direction', 'label', 'target')
  .by(__.constant('out'))
  .by(label())
  .by(inV().values('id'))
```

## Graph Statistics

### Get graph overview

```gremlin
// Count all vertices and edges
g.V().count()
g.E().count()

// Count by vertex label
g.V().groupCount().by(label())

// Count by edge label
g.E().groupCount().by(label())
```

### Get graph degree distribution

```gremlin
// Find vertices with highest degree (most connections)
g.V()
  .project('id', 'label', 'degree')
  .by(id())
  .by(label())
  .by(bothE().count())
  .order().by(select('degree'), desc)
  .limit(10)
```

## Data Validation Queries

### Verify graph structure

```gremlin
// Find chunks without parent sections
g.V().hasLabel('chunk')
  .where(__.not(in('hasChunk')))
  .values('chunkId')

// Find sections without parent documents
g.V().hasLabel('section')
  .where(__.not(in('hasSection')))
  .values('sectionId')

// Find orphaned keywords (no connections to chunks)
g.V().hasLabel('keyword')
  .where(__.not(out('hasKeyword')))
  .values('term')
```

### Check tenant consistency

```gremlin
// Verify chunk tenant matches document tenant
g.V().hasLabel('chunk')
  .as('chunk')
  .select('chunk').by('tenant')
  .as('chunkTenant')
  .select('chunk')
  .in('hasChunk').in('hasSection')
  .as('doc')
  .select('doc').by('tenant')
  .as('docTenant')
  .where('chunkTenant', neq('docTenant'))
```

## Tips for Optimal Queries

1. **Use partition key filtering**: Always filter by `tenant` when querying in a multi-tenant setup
2. **Limit results**: Use `.limit(N)` to avoid large result sets
3. **Index properties**: Ensure frequently queried properties are indexed
4. **Avoid full scans**: Use specific vertex/edge lookups when possible
5. **Use `.valueMap()` sparingly**: Only retrieve needed properties to reduce RU consumption
6. **Dedup results**: Use `.dedup()` when traversing bidirectional edges
7. **Profile queries**: Use `.profile()` to analyze query performance

## Testing Queries

You can test these queries using:

1. **Azure Portal**: Navigate to your Cosmos DB account → Data Explorer → Select graph
2. **Gremlin Console**: Use the Apache TinkerPop Gremlin console
3. **Python script**: Use the `initialize_graph.py` script's `execute_query` function
