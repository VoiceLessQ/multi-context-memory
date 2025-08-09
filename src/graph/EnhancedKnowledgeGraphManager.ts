import { promises as fs } from 'fs';
import { Entity, Relation, KnowledgeGraph } from '../types/graph.js';
import { recordToolUsage } from '../tools/telemetryTools.js';

interface ObservationInput {
  entityName: string;
  contents: string[];
}

interface DeletionInput {
  entityName: string;
  observations: string[];
}

interface EntitySummary {
  entity: Entity | null;
  relations: {
    outgoing: Relation[];
    incoming: Relation[];
  };
  relatedEntities: Entity[];
}

interface SearchOptions {
  limit?: number;
  offset?: number;
  sortBy?: 'name' | 'type' | 'createdAt' | 'updatedAt';
  sortOrder?: 'asc' | 'desc';
}

interface GraphStatistics {
  totalEntities: number;
  totalRelations: number;
  entityTypes: Record<string, number>;
  relationTypes: Record<string, number>;
  averageObservationsPerEntity: number;
  lastUpdated: string;
}

interface PathResult {
  path: string[];
  relations: Relation[];
  distance: number;
}

interface EnhancedSearchResult {
  entities: Entity[];
  relations: Relation[];
  total: number;
}

export class EnhancedKnowledgeGraphManager {
  private memoryFilePath: string;

  constructor(memoryFilePath: string) {
    this.memoryFilePath = memoryFilePath;
  }

  private async loadGraph(): Promise<KnowledgeGraph> {
    try {
      const data = await fs.readFile(this.memoryFilePath, "utf-8");
      const lines = data.split("\n").filter(line => line.trim() !== "");
      return lines.reduce((graph: KnowledgeGraph, line) => {
        try {
          const item = JSON.parse(line);
          if (item.type === "entity") graph.entities.push(item as Entity);
          if (item.type === "relation") graph.relations.push(item as Relation);
        } catch (parseError) {
          console.warn(`Skipping malformed line: ${line}`);
        }
        return graph;
      }, { entities: [], relations: [] });
    } catch (error: any) {
      // Handle file not found error gracefully
      if (error.code === "ENOENT") {
        return { entities: [], relations: [] };
      }
      // Handle any other file system errors gracefully
      console.warn(`File system error: ${error.code || error.message}, returning empty graph`);
      return { entities: [], relations: [] };
    }
  }

  private async saveGraph(graph: KnowledgeGraph): Promise<void> {
    const lines = [
      ...graph.entities.map(e => JSON.stringify({ type: "entity", ...e })),
      ...graph.relations.map(r => JSON.stringify({ type: "relation", ...r })),
    ];
    await fs.writeFile(this.memoryFilePath, lines.join("\n"));
  }

  // Enhanced search with filtering and pagination
  async searchNodesEnhanced(query: string, options: SearchOptions = {}): Promise<EnhancedSearchResult> {
    const startTime = Date.now();
    try {
      const graph = await this.loadGraph();
      
      const matchingEntities = graph.entities.filter(entity => 
        entity.name.toLowerCase().includes(query.toLowerCase()) ||
        entity.entityType.toLowerCase().includes(query.toLowerCase()) ||
        entity.observations.some(obs => obs.toLowerCase().includes(query.toLowerCase()))
      );

      // Apply sorting
      const sortedEntities = [...matchingEntities].sort((a, b) => {
        const sortBy = options.sortBy || 'name';
        const sortOrder = options.sortOrder || 'asc';
        
        let comparison = 0;
        switch (sortBy) {
          case 'name':
            comparison = a.name.localeCompare(b.name);
            break;
          case 'type':
            comparison = a.entityType.localeCompare(b.entityType);
            break;
          case 'createdAt':
            comparison = new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime();
            break;
          case 'updatedAt':
            comparison = new Date(a.updatedAt).getTime() - new Date(b.updatedAt).getTime();
            break;
        }
        
        return sortOrder === 'desc' ? -comparison : comparison;
      });

      // Apply pagination
      const limit = options.limit || 50;
      const offset = options.offset || 0;
      const paginatedEntities = sortedEntities.slice(offset, offset + limit);

      // Find related relations
      const entityNames = new Set(paginatedEntities.map(e => e.name));
      const relatedRelations = graph.relations.filter(r => 
        entityNames.has(r.from) || entityNames.has(r.to)
      );

      const result = {
        entities: paginatedEntities,
        relations: relatedRelations,
        total: matchingEntities.length
      };

      recordToolUsage('search_nodes_enhanced', Date.now() - startTime);
      return result;
    } catch (error) {
      recordToolUsage('search_nodes_enhanced', Date.now() - startTime, error as Error);
      throw error;
    }
  }

  // Search entities by type
  async searchEntitiesByType(entityType: string, options: SearchOptions = {}): Promise<{
    entities: Entity[];
    total: number;
  }> {
    const startTime = Date.now();
    try {
      const graph = await this.loadGraph();
      
      const matchingEntities = graph.entities.filter(entity => 
        entity.entityType.toLowerCase() === entityType.toLowerCase()
      );

      // Apply sorting and pagination
      const sortedEntities = [...matchingEntities].sort((a, b) => {
        const sortBy = options.sortBy || 'name';
        const sortOrder = options.sortOrder || 'asc';
        
        let comparison = 0;
        switch (sortBy) {
          case 'name':
            comparison = a.name.localeCompare(b.name);
            break;
          case 'createdAt':
            comparison = new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime();
            break;
          case 'updatedAt':
            comparison = new Date(a.updatedAt).getTime() - new Date(b.updatedAt).getTime();
            break;
        }
        
        return sortOrder === 'desc' ? -comparison : comparison;
      });

      const limit = options.limit || 50;
      const offset = options.offset || 0;
      const paginatedEntities = sortedEntities.slice(offset, offset + limit);

      const result = {
        entities: paginatedEntities,
        total: matchingEntities.length
      };

      recordToolUsage('search_entities_by_type', Date.now() - startTime);
      return result;
    } catch (error) {
      recordToolUsage('search_entities_by_type', Date.now() - startTime, error as Error);
      throw error;
    }
  }

  // Get all entities of a specific type
  async getEntitiesByType(entityType: string): Promise<Entity[]> {
    const startTime = Date.now();
    try {
      const graph = await this.loadGraph();
      const entities = graph.entities.filter(entity => 
        entity.entityType.toLowerCase() === entityType.toLowerCase()
      );
      
      recordToolUsage('get_entities_by_type', Date.now() - startTime);
      return entities;
    } catch (error) {
      recordToolUsage('get_entities_by_type', Date.now() - startTime, error as Error);
      throw error;
    }
  }

  // Find shortest path between two entities
  async findPathBetweenEntities(fromEntity: string, toEntity: string): Promise<PathResult | null> {
    const startTime = Date.now();
    try {
      const graph = await this.loadGraph();
      
      // Check if both entities exist
      const fromExists = graph.entities.some(e => e.name === fromEntity);
      const toExists = graph.entities.some(e => e.name === toEntity);
      
      if (!fromExists || !toExists) {
        return null;
      }

      // Build bidirectional adjacency list
      const adjacency = new Map<string, string[]>();
      graph.relations.forEach(relation => {
        // Forward direction
        if (!adjacency.has(relation.from)) {
          adjacency.set(relation.from, []);
        }
        adjacency.get(relation.from)!.push(relation.to);
        
        // Backward direction (treat as undirected for pathfinding)
        if (!adjacency.has(relation.to)) {
          adjacency.set(relation.to, []);
        }
        adjacency.get(relation.to)!.push(relation.from);
      });

      // BFS to find shortest path
      const queue: string[][] = [[fromEntity]];
      const visited = new Set<string>([fromEntity]);

      while (queue.length > 0) {
        const path = queue.shift()!;
        const current = path[path.length - 1];

        if (current === toEntity) {
          // Build relations for the path
          const relations: Relation[] = [];
          for (let i = 0; i < path.length - 1; i++) {
            const relation = graph.relations.find(r => 
              (r.from === path[i] && r.to === path[i + 1]) ||
              (r.from === path[i + 1] && r.to === path[i])
            );
            if (relation) {
              relations.push(relation);
            }
          }

          const result = {
            path,
            relations,
            distance: path.length - 1
          };

          recordToolUsage('find_path_between_entities', Date.now() - startTime);
          return result;
        }

        const neighbors = adjacency.get(current) || [];
        for (const neighbor of neighbors) {
          if (!visited.has(neighbor)) {
            visited.add(neighbor);
            queue.push([...path, neighbor]);
          }
        }
      }

      recordToolUsage('find_path_between_entities', Date.now() - startTime);
      return null;
    } catch (error) {
      recordToolUsage('find_path_between_entities', Date.now() - startTime, error as Error);
      throw error;
    }
  }

  // Get comprehensive graph statistics
  async getGraphStatistics(): Promise<GraphStatistics> {
    const startTime = Date.now();
    try {
      const graph = await this.loadGraph();
      
      const entityTypes: Record<string, number> = {};
      const relationTypes: Record<string, number> = {};
      
      graph.entities.forEach(entity => {
        entityTypes[entity.entityType] = (entityTypes[entity.entityType] || 0) + 1;
      });
      
      graph.relations.forEach(relation => {
        relationTypes[relation.relationType] = (relationTypes[relation.relationType] || 0) + 1;
      });
      
      const totalObservations = graph.entities.reduce((sum, entity) => 
        sum + entity.observations.length, 0
      );
      
      const lastUpdated = graph.entities.length > 0 
        ? graph.entities.reduce((latest, entity) => 
            new Date(entity.updatedAt) > new Date(latest) ? entity.updatedAt : latest
          , graph.entities[0].updatedAt)
        : new Date().toISOString();
      
      const result = {
        totalEntities: graph.entities.length,
        totalRelations: graph.relations.length,
        entityTypes,
        relationTypes,
        averageObservationsPerEntity: graph.entities.length > 0 
          ? totalObservations / graph.entities.length 
          : 0,
        lastUpdated
      };

      recordToolUsage('get_graph_statistics', Date.now() - startTime);
      return result;
    } catch (error) {
      recordToolUsage('get_graph_statistics', Date.now() - startTime, error as Error);
      throw error;
    }
  }

  // Export graph to JSON
  async exportGraph(): Promise<string> {
    const startTime = Date.now();
    try {
      const graph = await this.loadGraph();
      const exportData = {
        exportedAt: new Date().toISOString(),
        version: "1.0",
        graph
      };
      
      recordToolUsage('export_graph', Date.now() - startTime);
      return JSON.stringify(exportData, null, 2);
    } catch (error) {
      recordToolUsage('export_graph', Date.now() - startTime, error as Error);
      throw error;
    }
  }

  // Import graph from JSON with validation
  async importGraph(jsonData: string): Promise<void> {
    const startTime = Date.now();
    try {
      let importData;
      try {
        importData = JSON.parse(jsonData);
      } catch (parseError) {
        throw new Error('Invalid JSON format');
      }
      
      if (!importData.graph || !Array.isArray(importData.graph.entities) || !Array.isArray(importData.graph.relations)) {
        throw new Error('Invalid import format: missing graph structure');
      }
      
      // Validate entities
      const validEntities = importData.graph.entities.filter((entity: any) => {
        return entity.name && entity.entityType && Array.isArray(entity.observations);
      });
      
      // Validate relations
      const validRelations = importData.graph.relations.filter((relation: any) => {
        return relation.from && relation.to && relation.relationType;
      });
      
      if (validEntities.length !== importData.graph.entities.length) {
        console.warn(`Filtered out ${importData.graph.entities.length - validEntities.length} invalid entities`);
      }
      
      if (validRelations.length !== importData.graph.relations.length) {
        console.warn(`Filtered out ${importData.graph.relations.length - validRelations.length} invalid relations`);
      }
      
      const graph: KnowledgeGraph = {
        entities: validEntities,
        relations: validRelations
      };
      
      await this.saveGraph(graph);
      
      recordToolUsage('import_graph', Date.now() - startTime);
    } catch (error) {
      recordToolUsage('import_graph', Date.now() - startTime, error as Error);
      throw error;
    }
  }

  // Backward compatibility methods
  async createEntities(entities: Entity[]): Promise<Entity[]> {
    const startTime = Date.now();
    try {
      const graph = await this.loadGraph();
      const timestamp = new Date().toISOString();
      const newEntities = entities
        .filter(e => !graph.entities.some(existing => existing.name === e.name))
        .map(e => ({
          ...e,
          createdAt: e.createdAt || timestamp,
          updatedAt: e.updatedAt || timestamp,
          version: e.version || 1
        }));
      graph.entities.push(...newEntities);
      await this.saveGraph(graph);
      
      recordToolUsage('create_entities', Date.now() - startTime);
      return newEntities;
    } catch (error) {
      recordToolUsage('create_entities', Date.now() - startTime, error as Error);
      throw error;
    }
  }

  async createRelations(relations: Relation[]): Promise<Relation[]> {
    const startTime = Date.now();
    try {
      const graph = await this.loadGraph();
      const timestamp = new Date().toISOString();
      const newRelations = relations
        .filter(r => 
          !graph.relations.some(existing => 
            existing.from === r.from && 
            existing.to === r.to && 
            existing.relationType === r.relationType
          )
        )
        .map(r => ({
          ...r,
          createdAt: r.createdAt || timestamp,
          updatedAt: r.updatedAt || timestamp,
          version: r.version || 1
        }));
      graph.relations.push(...newRelations);
      await this.saveGraph(graph);
      
      recordToolUsage('create_relations', Date.now() - startTime);
      return newRelations;
    } catch (error) {
      recordToolUsage('create_relations', Date.now() - startTime, error as Error);
      throw error;
    }
  }

  async readGraph(): Promise<KnowledgeGraph> {
    return this.loadGraph();
  }

  // Simple search method for backward compatibility (renamed to avoid conflict)
  async searchNodes(query: string): Promise<Entity[]> {
    const startTime = Date.now();
    try {
      const result = await this.searchNodesEnhanced(query, { limit: 50 });
      recordToolUsage('search_nodes_simple', Date.now() - startTime);
      return result.entities;
    } catch (error) {
      recordToolUsage('search_nodes_simple', Date.now() - startTime, error as Error);
      throw error;
    }
  }

  async openNodes(names: string[]): Promise<Entity[]> {
    const startTime = Date.now();
    try {
      const graph = await this.loadGraph();
      const entities = graph.entities.filter(e => names.includes(e.name));
      
      recordToolUsage('open_nodes', Date.now() - startTime);
      return entities;
    } catch (error) {
      recordToolUsage('open_nodes', Date.now() - startTime, error as Error);
      throw error;
    }
  }

  async getEntitySummary(entityName: string): Promise<EntitySummary> {
    const startTime = Date.now();
    try {
      const graph = await this.loadGraph();
      
      const entity = graph.entities.find(e => e.name === entityName);
      if (!entity) {
        return {
          entity: null,
          relations: { outgoing: [], incoming: [] },
          relatedEntities: []
        };
      }

      const outgoing = graph.relations.filter(r => r.from === entityName);
      const incoming = graph.relations.filter(r => r.to === entityName);
      
      const relatedEntityNames = new Set([
        ...outgoing.map(r => r.to),
        ...incoming.map(r => r.from)
      ]);
      
      const relatedEntities = graph.entities.filter(e => 
        relatedEntityNames.has(e.name) && e.name !== entityName
      );

      const result = {
        entity,
        relations: { outgoing, incoming },
        relatedEntities
      };

      recordToolUsage('get_entity_summary', Date.now() - startTime);
      return result;
    } catch (error) {
      recordToolUsage('get_entity_summary', Date.now() - startTime, error as Error);
      throw error;
    }
  }
async updateEntity(entities: Entity[]): Promise<void> {
  const startTime = Date.now();
  try {
    const graph = await this.loadGraph();
    entities.forEach(entity => {
      const index = graph.entities.findIndex(e => e.name === entity.name);
      if (index !== -1) {
        graph.entities[index] = entity;
      }
    });
    await this.saveGraph(graph);
    recordToolUsage('update_entity', Date.now() - startTime);
  } catch (error) {
    recordToolUsage('update_entity', Date.now() - startTime, error as Error);
    throw error;
  }
}

async deleteEntity(entityNames: string[]): Promise<void> {
  const startTime = Date.now();
  try {
    const graph = await this.loadGraph();
    graph.entities = graph.entities.filter(e => !entityNames.includes(e.name));
    graph.relations = graph.relations.filter(r => !entityNames.includes(r.from) && !entityNames.includes(r.to));
    await this.saveGraph(graph);
    recordToolUsage('delete_entity', Date.now() - startTime);
  } catch (error) {
    recordToolUsage('delete_entity', Date.now() - startTime, error as Error);
    throw error;
  }
}

async deleteRelation(relationIds: string[]): Promise<void> {
  const startTime = Date.now();
  try {
    const graph = await this.loadGraph();
    graph.relations = graph.relations.filter(r => !relationIds.includes(`${r.from}-${r.to}-${r.relationType}`));
    await this.saveGraph(graph);
    recordToolUsage('delete_relation', Date.now() - startTime);
  } catch (error) {
    recordToolUsage('delete_relation', Date.now() - startTime, error as Error);
    throw error;
  }
}

async updateRelation(relations: Relation[]): Promise<void> {
  const startTime = Date.now();
  try {
    const graph = await this.loadGraph();
    relations.forEach(relation => {
      const index = graph.relations.findIndex(r => r.from === relation.from && r.to === relation.to && r.relationType === relation.relationType);
      if (index !== -1) {
        graph.relations[index] = relation;
      }
    });
    await this.saveGraph(graph);
    recordToolUsage('update_relation', Date.now() - startTime);
  } catch (error) {
    recordToolUsage('update_relation', Date.now() - startTime, error as Error);
    throw error;
  }
}
}
