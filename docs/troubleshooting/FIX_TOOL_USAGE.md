# Fix Tool Usage Guide

## 🚨 Immediate Fixes Needed

### 1. Replace `batch_create_entities` with `batch_operations`

**❌ Incorrect:**
```json
{
  "tool": "batch_create_entities",
  "arguments": {
    "entities": [...]
  }
}
```

**✅ Correct:**
```json
{
  "tool": "batch_operations",
  "arguments": {
    "entities": [...],
    "relations": [...],
    "observations": [...]
  }
}
```

### 2. Remove `list_tools` calls

**❌ Incorrect:**
```json
{
  "tool": "list_tools"
}
```

**✅ Correct:**
- Use your MCP client's built-in tool listing feature
- Or refer to `AVAILABLE_TOOLS.md` for complete tool reference

## 🔧 Quick Migration Script

Here's a simple migration pattern for existing code:

```javascript
// OLD CODE (broken)
const result = await use_mcp_tool({
  server_name: "mcp-knowledge-graph",
  tool_name: "batch_create_entities",
  arguments: { entities: [...] }
});

// NEW CODE (working)
const result = await use_mcp_tool({
  server_name: "mcp-knowledge-graph", 
  tool_name: "batch_operations",
  arguments: { 
    entities: [...],
    relations: [], // optional
    observations: [] // optional
  }
});
```

## ✅ Verification Steps

1. **Test the corrected tools:**
   ```bash
   # Test batch_operations
   use_mcp_tool mcp-knowledge-graph batch_operations '{"entities": [{"name": "Test", "entityType": "test"}]}'
   
   # Test get_graph_stats
   use_mcp_tool mcp-knowledge-graph get_graph_stats '{}'
   ```

2. **Check your active context:**
   ```bash
   use_mcp_tool mcp-knowledge-graph get_active_context '{}'
   ```

3. **Verify tool availability:**
   - Your MCP client should show all available tools when connected
   - No need for `list_tools` - it's handled by the protocol

## 🎯 Common Patterns

### Creating a Project with Team
```json
{
  "tool": "batch_operations",
  "arguments": {
    "entities": [
      {"name": "My Project", "entityType": "project", "observations": ["New project"]},
      {"name": "Alice", "entityType": "person", "observations": ["Developer"]},
      {"name": "Bob", "entityType": "person", "observations": ["Designer"]}
    ],
    "relations": [
      {"from": "Alice", "to": "My Project", "relationType": "works_on"},
      {"from": "Bob", "to": "My Project", "relationType": "works_on"}
    ]
  }
}
```

### Adding Observations Later
```json
{
  "tool": "add_observations",
  "arguments": {
    "observations": [
      {"entityName": "My Project", "contents": ["Completed milestone 1", "On track for release"]}
    ]
  }
}
```

## 🆘 Still Having Issues?

1. **Check your MCP client version** - ensure it supports the latest MCP protocol
2. **Verify server connection** - the server should be running and accessible
3. **Review AVAILABLE_TOOLS.md** for complete tool documentation
4. **Test with simple examples** before complex operations
