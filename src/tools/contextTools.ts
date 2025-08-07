export const CONTEXT_TOOLS = [
  {
    name: "list_contexts",
    description: "List all available memory contexts",
    inputSchema: {
      type: "object",
      properties: {},
    },
  },
  {
    name: "get_active_context",
    description: "Show which context is currently active",
    inputSchema: {
      type: "object",
      properties: {},
    },
  },
  {
    name: "set_active_context",
    description: "Change the active context",
    inputSchema: {
      type: "object",
      properties: {
        context: {
          type: "string",
          description: "Name of the context to activate"
        }
      },
      required: ["context"],
    },
  },
  {
    name: "add_context",
    description: "Add a new memory context",
    inputSchema: {
      type: "object",
      properties: {
        name: { type: "string", description: "Context name" },
        path: { type: "string", description: "Memory file path" },
        description: { type: "string", description: "Optional description" },
        isProjectBased: { 
          type: "boolean", 
          description: "Whether to use project detection",
          default: false
        }
      },
      required: ["name", "path"],
    },
  },
  {
    name: "remove_context",
    description: "Remove a memory context (doesn't delete the file)",
    inputSchema: {
      type: "object",
      properties: {
        name: { type: "string", description: "Context name to remove" }
      },
      required: ["name"],
    },
  },
];
