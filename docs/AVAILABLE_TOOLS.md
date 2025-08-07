# MCP Knowledge Graph - Available Tools Guide

## 🎯 Overview
This document provides a complete and accurate reference for all available tools in the MCP Knowledge Graph server. All tool names have been verified against the actual server implementation in `index.ts`.

## ✅ Available Tools by Category

### 🔍 **Knowledge Graph Core Tools**

#### `create_entities`
Create multiple new entities in the knowledge graph.
```json
{
  "entities": [
    {
      "name": "Entity Name",
      "entityType": "Type",
      "observations": ["Observation 1", "Observation 2"]
    }
  ]
}
```

#### `create_relations`
Create multiple new relations between entities in the knowledge graph. Relations should be in active voice.
```json
{
  "relations": [
    {
      "from": "Source Entity",
      "to": "Target Entity",
      "relationType": "relates to"
    }
  ]
}
```

#### `add_observations`
Add new observations to existing entities in the knowledge graph.
```json
{
  "observations": [
    {
      "entityName": "Entity Name",
      "contents": ["New observation 1", "New observation 2"]
    }
  ]
}
```

#### `read_graph`
Read the entire knowledge graph.
```json
{}
```

#### `search_nodes`
Search for nodes in the knowledge graph based on a query.
```json
{
  "query": "search term"
}
```

#### `open_nodes`
Open specific nodes in the knowledge graph by their names.
```json
{
  "names": ["Entity1", "Entity2"]
}
```

#### `get_entity_summary`
Get a comprehensive summary of a specific entity including its relations and related entities.
```json
{
  "entityName": "Entity Name"
}
```

#### `update_entities`
Update multiple existing entities in the knowledge graph.
```json
{
  "entities": [
    {
      "name": "Entity Name",
      "entityType": "New Type",
      "observations": ["Updated observations"]
    }
  ]
}
```

#### `update_relations`
Update multiple existing relations in the knowledge graph.
```json
{
  "relations": [
    {
      "from": "Source",
      "to": "Target",
      "relationType": "old type",
      "newRelationType": "new type"
    }
  ]
}
```

#### `delete_entities`
Delete multiple entities and their associated relations from the knowledge graph.
```json
{
  "entityNames": ["Entity1", "Entity2"]
}
```

#### `delete_observations`
Delete specific observations from entities in the knowledge graph.
```json
{
  "deletions": [
    {
      "entityName": "Entity Name",
      "observations": ["Observation to delete"]
    }
  ]
}
```

#### `delete_relations`
Delete multiple relations from the knowledge graph.
```json
{
  "relations": [
    {
      "from": "Source",
      "to": "Target",
      "relationType": "relation type"
    }
  ]
}
```

### 🚀 **Enhanced Features**

#### `batch_operations`
Perform multiple operations (create entities, relations, and add observations) in a single transaction.
```json
{
  "entities": [...],
  "relations": [...],
  "observations": [...]
}
```

#### `find_path`
Find the shortest path between two entities in the knowledge graph.
```json
{
  "from": "Start Entity",
  "to": "End Entity",
  "maxDepth": 10
}
```

#### `get_graph_stats`
Get comprehensive statistics about the knowledge graph.
```json
{}
```

#### `export_graph`
Export the knowledge graph in various formats (JSON, CSV, GraphML).
```json
{
  "format": "json",
  "includeMetadata": true
}
```

#### `import_graph`
Import knowledge graph data from JSON format.
```json
{
  "data": {...},
  "mergeStrategy": "merge"
}
```

#### `get_similar_entities`
Find entities similar to a given entity based on type and observations.
```json
{
  "entityName": "Entity Name",
  "limit": 5
}
```

### 🗂️ **Context Management Tools**

#### `list_contexts`
List all available memory contexts.
```json
{}
```

#### `get_active_context`
Show which context is currently active.
```json
{}
```

#### `set_active_context`
Change the active context.
```json
{
  "context": "context-name"
}
```

#### `add_context`
Add a new memory context.
```json
{
  "name": "context-name",
  "path": "path/to/memory.jsonl",
  "description": "Optional description"
}
```

#### `remove_context`
Remove a memory context (doesn't delete the file).
```json
{
  "name": "context-name"
}
```

### 📊 **Telemetry Tools**

#### `get_telemetry_status`
Get current telemetry status and configuration.
```json
{}
```

#### `disable_telemetry`
Disable telemetry data collection.
```json
{}
```

#### `enable_telemetry`
Enable telemetry data collection.
```json
{}
```

#### `export_telemetry_data`
Export telemetry data for analysis.
```json
{}
```

#### `reset_telemetry_id`
Reset the telemetry identifier.
```json
{}
```

#### `clear_telemetry_data`
Clear all collected telemetry data.
```json
{}
```

## 📝 **Usage Notes**

- All tools return JSON responses
- Tool names are case-sensitive and must match exactly
- Required parameters are marked in the JSON schemas
- Optional parameters have default values when not specified
- Context can be specified for memory tools using the `context` parameter

## 🔧 **Common Parameters**

- `context`: Optional parameter for memory tools to specify which memory file to use
- `format`: Used in export tools to specify output format (json, csv, graphml)
- `mergeStrategy`: Used in import tools (replace, merge, skip)

## ⚠️ **Tool Verification Status**
- **Total Verified Tools**: 29 tools confirmed working
- **Missing Tools**: `list_tools` - This tool does **NOT** exist in the MCP Knowledge Graph server
- **All Other Tools**: Successfully tested and verified against `index.ts`

## 📋 **Source Verification**
All tools have been cross-referenced with the actual server implementation in `index.ts` lines 150-450, confirming the exact tool names and schemas used by the MCP server.
