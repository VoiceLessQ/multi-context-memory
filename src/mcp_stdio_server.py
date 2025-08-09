#!/usr/bin/env python3
"""
Stdio-based MCP Server for MCP Multi-Context Memory System
This implements the proper MCP protocol over stdio transport.
"""

import asyncio
import json
import sys
import logging
import sqlite3
import os
from typing import Any, Dict, List, Optional
from datetime import datetime

# Database file path
DB_PATH = "/app/data/memory.db"

def init_database():
    """Initialize SQLite database with required tables"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            summary TEXT,
            tags TEXT,
            category TEXT,
            importance INTEGER DEFAULT 1,
            context_id INTEGER,
            access_level TEXT DEFAULT 'public',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contexts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS relations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            source_memory_id INTEGER NOT NULL,
            target_memory_id INTEGER NOT NULL,
            relation_type TEXT DEFAULT 'related_to',
            strength REAL DEFAULT 1.0,
            relation_metadata TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (source_memory_id) REFERENCES memories (id),
            FOREIGN KEY (target_memory_id) REFERENCES memories (id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory_clusters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            cluster_metadata TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory_cluster_members (
            cluster_id INTEGER NOT NULL,
            memory_id INTEGER NOT NULL,
            similarity_score REAL DEFAULT 1.0,
            PRIMARY KEY (cluster_id, memory_id),
            FOREIGN KEY (cluster_id) REFERENCES memory_clusters (id),
            FOREIGN KEY (memory_id) REFERENCES memories (id)
        )
    """)
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Get database connection"""
    return sqlite3.connect(DB_PATH)

# Set up logging to stderr (not stdout, which is used for MCP communication)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

class MCPStdioServer:
    def __init__(self):
        self.request_id = 0
        # Initialize database on startup
        init_database()

    async def handle_initialize(self, params: Dict) -> Dict:
        """Handle MCP initialize request"""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "resources": {},
                "tools": {}
            },
            "serverInfo": {
                "name": "mcp-multi-context-memory",
                "version": "1.0.0"
            }
        }

    async def handle_list_resources(self) -> Dict:
        """Handle list resources request"""
        resources = []
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM memories")
        memory_count = cursor.fetchone()[0]
        
        resources.append({
            "uri": "memory://summary",
            "name": f"Resources ({memory_count})",
            "description": f"Total number of memories stored in the system: {memory_count}.",
            "mimeType": "application/json"
        })
        
        conn.close()
        return {"resources": resources}

    async def handle_read_resource(self, uri: str) -> Dict:
        """Handle read resource request"""
        if uri == "memory://summary":
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get total memory count
            cursor.execute("SELECT COUNT(*) FROM memories")
            total_memories = cursor.fetchone()[0]
            
            # Get counts by category if available
            cursor.execute("SELECT category, COUNT(*) FROM memories GROUP BY category")
            category_counts = cursor.fetchall()
            
            # Get oldest and newest memory dates
            cursor.execute("SELECT MIN(created_at), MAX(created_at) FROM memories")
            date_range = cursor.fetchone()
            
            summary_data = {
                "total_memories": total_memories,
                "category_breakdown": {cat: count for cat, count in category_counts} if category_counts else {},
                "oldest_memory_date": date_range[0],
                "newest_memory_date": date_range[1]
            }
            
            conn.close()
            
            return {
                "contents": [{
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps(summary_data, indent=2)
                }]
            }
        elif uri.startswith("memory://"):
            # Existing logic for individual memory resources
            memory_id = int(uri.split("://")[1])
            
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, content, context_id, access_level, created_at FROM memories WHERE id = ?", (memory_id,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                memory = {
                    "id": result[0],
                    "title": result[1],
                    "content": result[2],
                    "context_id": result[3],
                    "access_level": result[4],
                    "created_at": result[5]
                }
                return {
                    "contents": [{
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(memory, indent=2)
                    }]
                }
            else:
                raise ValueError(f"Memory {memory_id} not found")
        else:
            raise ValueError(f"Unsupported resource URI: {uri}")

    async def handle_list_tools(self) -> Dict:
        """Handle list tools request"""
        return {
            "tools": [
                {
                    "name": "create_memory",
                    "description": "Create a new memory entry",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Title of the memory"},
                            "content": {"type": "string", "description": "Content of the memory"},
                            "context_id": {"type": "integer", "description": "ID of the context"},
                            "access_level": {"type": "string", "description": "Access level"}
                        },
                        "required": ["title", "content"]
                    }
                },
                {
                    "name": "search_memories",
                    "description": "Search for memories",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "limit": {"type": "integer", "description": "Maximum results", "default": 10}
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "create_context",
                    "description": "Create a new context",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Context name"},
                            "description": {"type": "string", "description": "Context description"}
                        },
                        "required": ["name", "description"]
                    }
                },
                {
                    "name": "create_relation",
                    "description": "Create a relation between two memories",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Name of the relation"},
                            "source_memory_id": {"type": "integer", "description": "Source memory ID"},
                            "target_memory_id": {"type": "integer", "description": "Target memory ID"},
                            "strength": {"type": "number", "description": "Relation strength (0-1)", "default": 1.0},
                            "relation_metadata": {"type": "object", "description": "Additional metadata"}
                        },
                        "required": ["name", "source_memory_id", "target_memory_id"]
                    }
                },
                {
                    "name": "get_memory_relations",
                    "description": "Get all relations for a specific memory",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "memory_id": {"type": "integer", "description": "Memory ID to get relations for"}
                        },
                        "required": ["memory_id"]
                    }
                },
                {
                    "name": "search_semantic",
                    "description": "Perform AI-powered semantic search across memories",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "limit": {"type": "integer", "description": "Maximum results", "default": 10},
                            "context_id": {"type": "integer", "description": "Filter by context ID"},
                            "similarity_threshold": {"type": "number", "description": "Minimum similarity score (0-1)", "default": 0.3}
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "analyze_knowledge_graph",
                    "description": "Analyze the knowledge graph and provide insights",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "analysis_type": {"type": "string", "description": "Type of analysis: 'overview', 'centrality', 'connections'", "default": "overview"},
                            "memory_id": {"type": "integer", "description": "Specific memory ID for focused analysis"}
                        },
                        "required": []
                    }
                },
                {
                    "name": "summarize_memory",
                    "description": "Generate or update summary for a memory",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "memory_id": {"type": "integer", "description": "Memory ID to summarize"},
                            "max_length": {"type": "integer", "description": "Maximum summary length in words", "default": 50}
                        },
                        "required": ["memory_id"]
                    }
                },
                {
                    "name": "update_memory",
                    "description": "Update an existing memory",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "memory_id": {"type": "integer", "description": "Memory ID to update"},
                            "title": {"type": "string", "description": "New title"},
                            "content": {"type": "string", "description": "New content"},
                            "tags": {"type": "string", "description": "Comma-separated tags"},
                            "category": {"type": "string", "description": "Memory category"},
                            "importance": {"type": "integer", "description": "Importance level (1-10)", "default": 1}
                        },
                        "required": ["memory_id"]
                    }
                },
                {
                    "name": "delete_memory",
                    "description": "Delete a memory and its relations",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "memory_id": {"type": "integer", "description": "Memory ID to delete"}
                        },
                        "required": ["memory_id"]
                    }
                },
                {
                    "name": "get_memory_statistics",
                    "description": "Get comprehensive statistics about memories",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "include_content_analysis": {"type": "boolean", "description": "Include content analysis", "default": True}
                        },
                        "required": []
                    }
                },
                {
                    "name": "bulk_create_memories",
                    "description": "Create multiple memories at once",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "memories": {
                                "type": "array",
                                "description": "Array of memory objects",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "title": {"type": "string"},
                                        "content": {"type": "string"},
                                        "tags": {"type": "string"},
                                        "category": {"type": "string"},
                                        "importance": {"type": "integer", "default": 1}
                                    },
                                    "required": ["title", "content"]
                                }
                            }
                        },
                        "required": ["memories"]
                    }
                },
                {
                    "name": "categorize_memories",
                    "description": "Automatically categorize and tag memories based on content analysis",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "context_id": {"type": "integer", "description": "Filter by context ID"},
                            "auto_generate_tags": {"type": "boolean", "description": "Auto-generate tags from content", "default": True}
                        },
                        "required": []
                    }
                },
                {
                    "name": "analyze_content",
                    "description": "Perform advanced content analysis on memories",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "memory_id": {"type": "integer", "description": "Specific memory to analyze"},
                            "analysis_type": {"type": "string", "description": "Type: 'keywords', 'sentiment', 'complexity', 'readability'", "default": "keywords"}
                        },
                        "required": []
                    }
                }
            ]
        }

    async def handle_call_tool(self, name: str, arguments: Dict) -> Dict:
        """Handle tool call request"""
        if name == "create_memory":
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO memories (title, content, context_id, access_level, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                arguments["title"],
                arguments["content"],
                arguments.get("context_id"),
                arguments.get("access_level", "public"),
                datetime.now().isoformat()
            ))
            
            memory_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {
                "content": [{
                    "type": "text",
                    "text": f"Created memory: {arguments['title']}"
                }]
            }
        
        elif name == "search_memories":
            query = arguments["query"].lower()
            limit = arguments.get("limit", 10)
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, title, content, context_id, access_level, created_at
                FROM memories
                WHERE LOWER(title) LIKE ? OR LOWER(content) LIKE ?
                LIMIT ?
            """, (f"%{query}%", f"%{query}%", limit))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    "id": row[0],
                    "title": row[1],
                    "content": row[2],
                    "context_id": row[3],
                    "access_level": row[4],
                    "created_at": row[5]
                })
            
            conn.close()
            
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps(results, indent=2)
                }]
            }
        
        elif name == "create_context":
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO contexts (name, description, created_at)
                VALUES (?, ?, ?)
            """, (
                arguments["name"],
                arguments["description"],
                datetime.now().isoformat()
            ))
            
            context_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {
                "content": [{
                    "type": "text",
                    "text": f"Created context: {arguments['name']}"
                }]
            }
        
        elif name == "create_relation":
            source_id = arguments["source_memory_id"]
            target_id = arguments["target_memory_id"]
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Validate that both memories exist
            cursor.execute("SELECT COUNT(*) FROM memories WHERE id = ?", (source_id,))
            source_exists = cursor.fetchone()[0] > 0
            cursor.execute("SELECT COUNT(*) FROM memories WHERE id = ?", (target_id,))
            target_exists = cursor.fetchone()[0] > 0
            
            if not source_exists or not target_exists:
                conn.close()
                raise ValueError("Source or target memory does not exist")
            
            cursor.execute("""
                INSERT INTO relations (name, source_memory_id, target_memory_id, strength, relation_metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                arguments["name"],
                source_id,
                target_id,
                arguments.get("strength", 1.0),
                json.dumps(arguments.get("relation_metadata", {})),
                datetime.now().isoformat()
            ))
            
            relation_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {
                "content": [{
                    "type": "text",
                    "text": f"Created relation '{arguments['name']}' between memory {source_id} and {target_id}"
                }]
            }
        
        elif name == "get_memory_relations":
            memory_id = arguments["memory_id"]
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check if memory exists
            cursor.execute("SELECT title FROM memories WHERE id = ?", (memory_id,))
            memory_result = cursor.fetchone()
            if not memory_result:
                conn.close()
                raise ValueError(f"Memory {memory_id} does not exist")
            
            memory_title = memory_result[0]
            
            # Find all relations involving this memory
            cursor.execute("""
                SELECT r.id, r.name, r.source_memory_id, r.target_memory_id, r.strength,
                       r.relation_metadata, r.created_at,
                       m1.title as source_title, m2.title as target_title
                FROM relations r
                LEFT JOIN memories m1 ON r.source_memory_id = m1.id
                LEFT JOIN memories m2 ON r.target_memory_id = m2.id
                WHERE r.source_memory_id = ? OR r.target_memory_id = ?
            """, (memory_id, memory_id))
            
            related_relations = []
            for row in cursor.fetchall():
                other_memory_id = row[3] if row[2] == memory_id else row[2]
                other_memory_title = row[8] if row[2] == memory_id else row[7]
                
                related_relations.append({
                    "id": row[0],
                    "name": row[1],
                    "source_memory_id": row[2],
                    "target_memory_id": row[3],
                    "strength": row[4],
                    "relation_metadata": json.loads(row[5]) if row[5] else {},
                    "created_at": row[6],
                    "related_memory": {
                        "id": other_memory_id,
                        "title": other_memory_title
                    }
                })
            
            conn.close()
            
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "memory_id": memory_id,
                        "memory_title": memory_title,
                        "relations": related_relations,
                        "total_relations": len(related_relations)
                    }, indent=2)
                }]
            }
        
        elif name == "search_semantic":
            # For now, implement enhanced text search with scoring
            # In a full implementation, this would use embeddings
            query = arguments["query"].lower()
            limit = arguments.get("limit", 10)
            context_id = arguments.get("context_id")
            threshold = arguments.get("similarity_threshold", 0.3)
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get memories, filtering by context if specified
            if context_id:
                cursor.execute("""
                    SELECT id, title, content, context_id, access_level, created_at
                    FROM memories WHERE context_id = ?
                """, (context_id,))
            else:
                cursor.execute("""
                    SELECT id, title, content, context_id, access_level, created_at
                    FROM memories
                """)
            
            results = []
            for row in cursor.fetchall():
                memory = {
                    "id": row[0],
                    "title": row[1],
                    "content": row[2],
                    "context_id": row[3],
                    "access_level": row[4],
                    "created_at": row[5]
                }
                
                title = memory["title"].lower()
                content = memory["content"].lower()
                
                # Calculate simple similarity score
                title_matches = sum(1 for word in query.split() if word in title)
                content_matches = sum(1 for word in query.split() if word in content)
                total_words = len(query.split())
                
                similarity = (title_matches * 2 + content_matches) / (total_words * 3)  # Weight title matches more
                
                if similarity >= threshold:
                    memory["similarity_score"] = round(similarity, 3)
                    memory["match_details"] = {
                        "title_matches": title_matches,
                        "content_matches": content_matches
                    }
                    results.append(memory)
            
            conn.close()
            
            # Sort by similarity score
            results.sort(key=lambda x: x["similarity_score"], reverse=True)
            results = results[:limit]
            
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "query": arguments["query"],
                        "results": results,
                        "total_found": len(results)
                    }, indent=2)
                }]
            }
        
        elif name == "analyze_knowledge_graph":
            analysis_type = arguments.get("analysis_type", "overview")
            memory_id = arguments.get("memory_id")
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if analysis_type == "overview":
                # General graph statistics
                cursor.execute("SELECT COUNT(*) FROM memories")
                total_memories = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM contexts")
                total_contexts = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM relations")
                total_relations = cursor.fetchone()[0]
                
                # Calculate memory connectivity
                cursor.execute("""
                    SELECT source_memory_id as memory_id FROM relations
                    UNION ALL
                    SELECT target_memory_id as memory_id FROM relations
                """)
                
                memory_connections = {}
                for row in cursor.fetchall():
                    mem_id = row[0]
                    memory_connections[mem_id] = memory_connections.get(mem_id, 0) + 1
                
                # Find most connected memories
                top_connected = sorted(memory_connections.items(), key=lambda x: x[1], reverse=True)[:5]
                top_connected_details = []
                for mem_id, conn_count in top_connected:
                    cursor.execute("SELECT title FROM memories WHERE id = ?", (mem_id,))
                    title_result = cursor.fetchone()
                    if title_result:
                        top_connected_details.append({
                            "memory_id": mem_id,
                            "title": title_result[0],
                            "connections": conn_count
                        })
                
                result = {
                    "analysis_type": "overview",
                    "graph_stats": {
                        "total_memories": total_memories,
                        "total_contexts": total_contexts,
                        "total_relations": total_relations,
                        "connectivity_ratio": round(total_relations / max(total_memories, 1), 2)
                    },
                    "top_connected_memories": top_connected_details
                }
            
            elif analysis_type == "centrality" and memory_id:
                cursor.execute("SELECT title FROM memories WHERE id = ?", (memory_id,))
                memory_result = cursor.fetchone()
                if not memory_result:
                    conn.close()
                    raise ValueError(f"Memory {memory_id} does not exist")
                
                memory_title = memory_result[0]
                
                # Analyze centrality of specific memory
                cursor.execute("""
                    SELECT COUNT(*) FROM relations
                    WHERE source_memory_id = ? OR target_memory_id = ?
                """, (memory_id, memory_id))
                direct_connections = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT DISTINCT
                        CASE
                            WHEN source_memory_id = ? THEN target_memory_id
                            ELSE source_memory_id
                        END as connected_id
                    FROM relations
                    WHERE source_memory_id = ? OR target_memory_id = ?
                """, (memory_id, memory_id, memory_id))
                
                connected_memories = [row[0] for row in cursor.fetchall()]
                
                cursor.execute("SELECT COUNT(*) FROM memories")
                total_memories = cursor.fetchone()[0]
                
                result = {
                    "analysis_type": "centrality",
                    "memory_id": memory_id,
                    "memory_title": memory_title,
                    "direct_connections": direct_connections,
                    "connected_memory_ids": connected_memories,
                    "centrality_score": round(direct_connections / max(total_memories - 1, 1), 3)
                }
            
            elif analysis_type == "connections":
                # Show all connections in the graph
                cursor.execute("""
                    SELECT r.name, r.source_memory_id, r.target_memory_id, r.strength,
                           m1.title as source_title, m2.title as target_title
                    FROM relations r
                    LEFT JOIN memories m1 ON r.source_memory_id = m1.id
                    LEFT JOIN memories m2 ON r.target_memory_id = m2.id
                """)
                
                connections = []
                for row in cursor.fetchall():
                    connections.append({
                        "relation_name": row[0],
                        "source": {
                            "id": row[1],
                            "title": row[4] if row[4] else ""
                        },
                        "target": {
                            "id": row[2],
                            "title": row[5] if row[5] else ""
                        },
                        "strength": row[3]
                    })
                
                result = {
                    "analysis_type": "connections",
                    "total_connections": len(connections),
                    "connections": connections
                }
            
            else:
                conn.close()
                raise ValueError(f"Unknown analysis type: {analysis_type}")
            
            conn.close()
            
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps(result, indent=2)
                }]
            }
        
        elif name == "summarize_memory":
            memory_id = arguments["memory_id"]
            max_length = arguments.get("max_length", 50)
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get memory content
            cursor.execute("SELECT title, content FROM memories WHERE id = ?", (memory_id,))
            result = cursor.fetchone()
            if not result:
                conn.close()
                raise ValueError(f"Memory {memory_id} does not exist")
            
            title, content = result
            
            # Generate simple extractive summary (first sentences up to word limit)
            sentences = content.replace('!', '.').replace('?', '.').split('.')
            summary_words = []
            for sentence in sentences:
                words = sentence.strip().split()
                if len(summary_words) + len(words) <= max_length:
                    summary_words.extend(words)
                else:
                    break
            
            summary = ' '.join(summary_words).strip()
            if not summary:
                summary = content[:min(len(content), max_length * 5)]  # Fallback
            
            # Update memory with summary
            cursor.execute("""
                UPDATE memories SET summary = ?, updated_at = ? WHERE id = ?
            """, (summary, datetime.now().isoformat(), memory_id))
            
            conn.commit()
            conn.close()
            
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "memory_id": memory_id,
                        "title": title,
                        "summary": summary,
                        "word_count": len(summary.split())
                    }, indent=2)
                }]
            }

        elif name == "update_memory":
            memory_id = arguments["memory_id"]
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check if memory exists
            cursor.execute("SELECT id FROM memories WHERE id = ?", (memory_id,))
            if not cursor.fetchone():
                conn.close()
                raise ValueError(f"Memory {memory_id} does not exist")
            
            # Build dynamic update query
            updates = []
            params = []
            
            for field in ["title", "content", "tags", "category", "importance"]:
                if field in arguments and arguments[field] is not None:
                    updates.append(f"{field} = ?")
                    params.append(arguments[field])
            
            if updates:
                updates.append("updated_at = ?")
                params.append(datetime.now().isoformat())
                params.append(memory_id)
                
                query = f"UPDATE memories SET {', '.join(updates)} WHERE id = ?"
                cursor.execute(query, params)
                conn.commit()
            
            conn.close()
            
            return {
                "content": [{
                    "type": "text",
                    "text": f"Updated memory {memory_id} with {len(updates)-1} fields"
                }]
            }

        elif name == "delete_memory":
            memory_id = arguments["memory_id"]
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check if memory exists
            cursor.execute("SELECT title FROM memories WHERE id = ?", (memory_id,))
            result = cursor.fetchone()
            if not result:
                conn.close()
                raise ValueError(f"Memory {memory_id} does not exist")
            
            title = result[0]
            
            # Delete relations first (foreign key constraints)
            cursor.execute("DELETE FROM relations WHERE source_memory_id = ? OR target_memory_id = ?",
                          (memory_id, memory_id))
            relations_deleted = cursor.rowcount
            
            # Delete from clusters
            cursor.execute("DELETE FROM memory_cluster_members WHERE memory_id = ?", (memory_id,))
            
            # Delete the memory
            cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            
            conn.commit()
            conn.close()
            
            return {
                "content": [{
                    "type": "text",
                    "text": f"Deleted memory '{title}' and {relations_deleted} associated relations"
                }]
            }

        elif name == "get_memory_statistics":
            include_content_analysis = arguments.get("include_content_analysis", True)
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Basic statistics
            cursor.execute("SELECT COUNT(*) FROM memories")
            total_memories = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM contexts")
            total_contexts = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM relations")
            total_relations = cursor.fetchone()[0]
            
            # Memory statistics by category
            cursor.execute("""
                SELECT category, COUNT(*) as count
                FROM memories
                WHERE category IS NOT NULL
                GROUP BY category
                ORDER BY count DESC
            """)
            categories = [{"category": row[0], "count": row[1]} for row in cursor.fetchall()]
            
            # Average content length
            cursor.execute("SELECT AVG(LENGTH(content)) FROM memories")
            avg_content_length = cursor.fetchone()[0] or 0
            
            stats = {
                "total_memories": total_memories,
                "total_contexts": total_contexts,
                "total_relations": total_relations,
                "categories": categories,
                "average_content_length": round(avg_content_length, 2),
                "connectivity_ratio": round(total_relations / max(total_memories, 1), 2)
            }
            
            if include_content_analysis:
                # Top keywords analysis (simple word frequency)
                cursor.execute("SELECT content FROM memories")
                all_content = ' '.join([row[0].lower() for row in cursor.fetchall()])
                words = all_content.split()
                
                # Filter common words and count
                common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'a', 'an'}
                word_freq = {}
                for word in words:
                    clean_word = ''.join(c for c in word if c.isalnum())
                    if len(clean_word) > 2 and clean_word not in common_words:
                        word_freq[clean_word] = word_freq.get(clean_word, 0) + 1
                
                top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
                stats["top_keywords"] = [{"word": word, "frequency": freq} for word, freq in top_keywords]
            
            conn.close()
            
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps(stats, indent=2)
                }]
            }

        elif name == "bulk_create_memories":
            memories_data = arguments["memories"]
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            created_memories = []
            for memory_data in memories_data:
                cursor.execute("""
                    INSERT INTO memories (title, content, tags, category, importance, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    memory_data["title"],
                    memory_data["content"],
                    memory_data.get("tags"),
                    memory_data.get("category"),
                    memory_data.get("importance", 1),
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                
                created_memories.append({
                    "id": cursor.lastrowid,
                    "title": memory_data["title"]
                })
            
            conn.commit()
            conn.close()
            
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "created_count": len(created_memories),
                        "memories": created_memories
                    }, indent=2)
                }]
            }

        elif name == "categorize_memories":
            context_id = arguments.get("context_id")
            auto_generate_tags = arguments.get("auto_generate_tags", True)
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get memories to categorize
            if context_id:
                cursor.execute("SELECT id, title, content FROM memories WHERE context_id = ?", (context_id,))
            else:
                cursor.execute("SELECT id, title, content FROM memories")
            
            memories = cursor.fetchall()
            categorized_count = 0
            
            for memory_id, title, content in memories:
                # Simple categorization based on content keywords
                category = "general"
                tags = []
                
                content_lower = content.lower()
                title_lower = title.lower()
                
                # Category detection
                if any(word in content_lower or word in title_lower for word in ["code", "programming", "function", "api", "database"]):
                    category = "technical"
                elif any(word in content_lower or word in title_lower for word in ["meeting", "discussion", "decision", "plan"]):
                    category = "planning"
                elif any(word in content_lower or word in title_lower for word in ["idea", "concept", "thought", "inspiration"]):
                    category = "ideas"
                elif any(word in content_lower or word in title_lower for word in ["research", "study", "analysis", "data"]):
                    category = "research"
                
                # Tag generation
                if auto_generate_tags:
                    potential_tags = []
                    if "important" in content_lower: potential_tags.append("important")
                    if "todo" in content_lower or "task" in content_lower: potential_tags.append("todo")
                    if "bug" in content_lower or "issue" in content_lower: potential_tags.append("bug")
                    if "feature" in content_lower: potential_tags.append("feature")
                    
                    tags = potential_tags[:3]  # Limit to 3 tags
                
                # Update memory
                cursor.execute("""
                    UPDATE memories
                    SET category = ?, tags = ?, updated_at = ?
                    WHERE id = ?
                """, (category, ','.join(tags) if tags else None, datetime.now().isoformat(), memory_id))
                
                categorized_count += 1
            
            conn.commit()
            conn.close()
            
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "categorized_count": categorized_count,
                        "auto_generated_tags": auto_generate_tags
                    }, indent=2)
                }]
            }

        elif name == "analyze_content":
            analysis_type = arguments.get("analysis_type", "keywords")
            memory_id = arguments.get("memory_id")
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if memory_id:
                cursor.execute("SELECT id, title, content FROM memories WHERE id = ?", (memory_id,))
                memories = cursor.fetchall()
                if not memories:
                    conn.close()
                    raise ValueError(f"Memory {memory_id} does not exist")
            else:
                cursor.execute("SELECT id, title, content FROM memories")
                memories = cursor.fetchall()
            
            results = []
            
            for mem_id, title, content in memories:
                if analysis_type == "keywords":
                    # Extract keywords
                    words = content.lower().split()
                    common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'a', 'an'}
                    keywords = [word for word in words if len(word) > 3 and word not in common_words]
                    word_freq = {word: keywords.count(word) for word in set(keywords)}
                    top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
                    
                    results.append({
                        "memory_id": mem_id,
                        "title": title,
                        "analysis_type": "keywords",
                        "keywords": [{"word": word, "frequency": freq} for word, freq in top_keywords]
                    })
                
                elif analysis_type == "sentiment":
                    # Simple sentiment analysis
                    positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'happy', 'success']
                    negative_words = ['bad', 'terrible', 'awful', 'sad', 'fail', 'problem', 'issue']
                    
                    content_lower = content.lower()
                    positive_count = sum(content_lower.count(word) for word in positive_words)
                    negative_count = sum(content_lower.count(word) for word in negative_words)
                    
                    sentiment = "neutral"
                    if positive_count > negative_count:
                        sentiment = "positive"
                    elif negative_count > positive_count:
                        sentiment = "negative"
                    
                    results.append({
                        "memory_id": mem_id,
                        "title": title,
                        "analysis_type": "sentiment",
                        "sentiment": sentiment,
                        "positive_indicators": positive_count,
                        "negative_indicators": negative_count
                    })
                
                elif analysis_type == "complexity":
                    # Simple complexity metrics
                    word_count = len(content.split())
                    sentence_count = len([s for s in content.replace('!', '.').replace('?', '.').split('.') if s.strip()])
                    avg_words_per_sentence = word_count / max(sentence_count, 1)
                    
                    complexity = "low"
                    if avg_words_per_sentence > 20:
                        complexity = "high"
                    elif avg_words_per_sentence > 10:
                        complexity = "medium"
                    
                    results.append({
                        "memory_id": mem_id,
                        "title": title,
                        "analysis_type": "complexity",
                        "complexity_level": complexity,
                        "word_count": word_count,
                        "sentence_count": sentence_count,
                        "avg_words_per_sentence": round(avg_words_per_sentence, 2)
                    })
                
                elif analysis_type == "readability":
                    # Simple readability score
                    word_count = len(content.split())
                    char_count = len(content)
                    avg_word_length = char_count / max(word_count, 1)
                    
                    readability = "easy"
                    if avg_word_length > 6:
                        readability = "difficult"
                    elif avg_word_length > 4:
                        readability = "medium"
                    
                    results.append({
                        "memory_id": mem_id,
                        "title": title,
                        "analysis_type": "readability",
                        "readability_level": readability,
                        "avg_word_length": round(avg_word_length, 2),
                        "total_words": word_count
                    })
            
            conn.close()
            
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "analysis_type": analysis_type,
                        "analyzed_memories": len(results),
                        "results": results
                    }, indent=2)
                }]
            }

        else:
            raise ValueError(f"Unknown tool: {name}")

    async def process_request(self, request: Dict) -> Dict:
        """Process an MCP request and return response"""
        try:
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")

            if method == "initialize":
                result = await self.handle_initialize(params)
            elif method == "resources/list":
                result = await self.handle_list_resources()
            elif method == "resources/read":
                result = await self.handle_read_resource(params["uri"])
            elif method == "tools/list":
                result = await self.handle_list_tools()
            elif method == "tools/call":
                result = await self.handle_call_tool(params["name"], params.get("arguments", {}))
            elif method == "resources/templates/list":
                result = {"resourceTemplates": []}
            else:
                raise ValueError(f"Unknown method: {method}")

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }

        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32000,
                    "message": str(e)
                }
            }

    async def run(self):
        """Main server loop - read from stdin, write to stdout"""
        logger.info("Starting MCP stdio server")
        
        while True:
            try:
                # Read a line from stdin
                line = sys.stdin.readline()
                if not line:
                    break
                
                line = line.strip()
                if not line:
                    continue

                # Parse JSON request
                request = json.loads(line)
                logger.info(f"Received request: {request.get('method')}")

                # Process request
                response = await self.process_request(request)
                
                # Send JSON response to stdout
                print(json.dumps(response), flush=True)
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "Parse error"
                    }
                }
                print(json.dumps(error_response), flush=True)
                
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32603,
                        "message": "Internal error"
                    }
                }
                print(json.dumps(error_response), flush=True)

async def main():
    """Main entry point"""
    server = MCPStdioServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())