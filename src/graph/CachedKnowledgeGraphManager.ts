import { LazyLoadingManager } from './LazyLoadingManager.js';
import { FullTextSearchManager } from '../search/FullTextSearchManager.js';
import { BatchOptimizedManager } from '../batch/BatchOptimizedManager.js';
import { MemoryOptimizedManager } from './MemoryOptimizedManager.js';
import { EnhancedKnowledgeGraphManager } from './EnhancedKnowledgeGraphManager.js';
import { Entity, Relation, KnowledgeGraph } from '../types/graph.js';
import { promises as fs } from 'fs';

interface CacheEntry {
  graph: KnowledgeGraph;
  lastModified: Date;
  filePath: string;
  indexes: GraphIndexes;
}

interface GraphIndexes {
  entityByName: Map<string, Entity>;
  entitiesByType: Map<string, Entity[]>;
  relationsByFrom: Map<string, Relation[]>;
  relationsByTo: Map<string, Relation[]>;
  relationsByType: Map<string, Relation[]>;
}

interface SearchOptions {
  limit?: number;
  offset?: number;
  sortBy?: 'name' | 'type' | 'createdAt' | 'updatedAt';
  sortOrder?: 'asc' | 'desc';
}

export class CachedKnowledgeGraphManager {
  private static cache = new Map<string, CacheEntry>();
  private static maxCacheSize = 100;
  private static cacheHits = 0;
  private static cacheMisses = 0;

  private memoryFilePath: string;
  private baseManager: EnhancedKnowledgeGraphManager;
  private lazyLoadingManager: LazyLoadingManager | null = null;
  private fullTextSearchManager: FullTextSearchManager | null = null;
  private batchOptimizedManager: BatchOptimizedManager | null = null;
  private memoryOptimizedManager: MemoryOptimizedManager | null = null;

  constructor(
    memoryFilePath: string,
    private readonly lazyLoadingEnabled: boolean = false,
    private readonly fullTextSearchEnabled: boolean = false,
    private readonly batchOperationsEnabled: boolean = false,
    private readonly memoryOptimizationEnabled: boolean = false
  ) {
    this.memoryFilePath = memoryFilePath;
    this.baseManager = new EnhancedKnowledgeGraphManager(memoryFilePath);

    if (lazyLoadingEnabled) {
      this.lazyLoadingManager = new LazyLoadingManager(memoryFilePath);
    }
    if (fullTextSearchEnabled) {
      this.fullTextSearchManager = new FullTextSearchManager(memoryFilePath);
    }
    if (batchOperationsEnabled) {
      this.batchOptimizedManager = new BatchOptimizedManager(memoryFilePath);
    }
    if (memoryOptimizationEnabled) {
      this.memoryOptimizedManager = new MemoryOptimizedManager(memoryFilePath);
    }
  }

  /**
   * Get cache statistics for monitoring
   */
  public static getCacheStats(): { hits: number; misses: number; hitRate: number; size: number } {
    const total = CachedKnowledgeGraphManager.cacheHits + CachedKnowledgeGraphManager.cacheMisses;
    const hitRate = total > 0 ? (CachedKnowledgeGraphManager.cacheHits / total) * 100 : 0;
    
    return {
      hits: CachedKnowledgeGraphManager.cacheHits,
      misses: CachedKnowledgeGraphManager.cacheMisses,
      hitRate,
      size: CachedKnowledgeGraphManager.cache.size
    };
  }

  /**
   * Clear the entire cache
   */
  public static clearCache(): void {
    MemoryOptimizedManager.clearCache();
    CachedKnowledgeGraphManager.cache.clear();
    CachedKnowledgeGraphManager.cacheHits = 0;
    CachedKnowledgeGraphManager.cacheMisses = 0;
  }

  /**
   * Set maximum cache size
   */
  public static setMaxCacheSize(size: number): void {
    CachedKnowledgeGraphManager.maxCacheSize = Math.max(1, size);
    CachedKnowledgeGraphManager.enforceCacheLimit();
  }

  /**
   * Enforce cache size limit using LRU eviction
   */
  private static enforceCacheLimit(): void {
    if (CachedKnowledgeGraphManager.cache.size > CachedKnowledgeGraphManager.maxCacheSize) {
      const entries = Array.from(CachedKnowledgeGraphManager.cache.entries());
      const sortedEntries = entries.sort((a, b) => a[1].lastModified.getTime() - b[1].lastModified.getTime());

      const toRemove = sortedEntries.slice(0, CachedKnowledgeGraphManager.cache.size - CachedKnowledgeGraphManager.maxCacheSize);
      toRemove.forEach(([key]) => CachedKnowledgeGraphManager.cache.delete(key));
    }
  }

  /**
   * Build indexes for fast lookups
   */
  private buildIndexes(graph: KnowledgeGraph): GraphIndexes {
    const indexes: GraphIndexes = {
      entityByName: new Map(),
      entitiesByType: new Map(),
      relationsByFrom: new Map(),
      relationsByTo: new Map(),
      relationsByType: new Map()
    };

    // Build entity indexes
    graph.entities.forEach(entity => {
      indexes.entityByName.set(entity.name, entity);

      if (!indexes.entitiesByType.has(entity.entityType)) {
        indexes.entitiesByType.set(entity.entityType, []);
      }
      indexes.entitiesByType.get(entity.entityType)!.push(entity);
    });

    // Build relation indexes
    graph.relations.forEach(relation => {
      // Index by source
      if (!indexes.relationsByFrom.has(relation.from)) {
        indexes.relationsByFrom.set(relation.from, []);
      }
      indexes.relationsByFrom.get(relation.from)!.push(relation);

      // Index by target
      if (!indexes.relationsByTo.has(relation.to)) {
        indexes.relationsByTo.set(relation.to, []);
      }
      indexes.relationsByTo.get(relation.to)!.push(relation);

      // Index by type
      if (!indexes.relationsByType.has(relation.relationType)) {
        indexes.relationsByType.set(relation.relationType, []);
      }
      indexes.relationsByType.get(relation.relationType)!.push(relation);
    });

    return indexes;
  }

  /**
   * Check if file has been modified since last cache
   */
  private async hasFileChanged(): Promise<boolean> {
    try {
      const stats = await fs.stat(this.memoryFilePath);
      const cachedEntry = CachedKnowledgeGraphManager.cache.get(this.memoryFilePath);

      if (!cachedEntry) {
        return true;
      }

      return stats.mtime > cachedEntry.lastModified;
    } catch (error: any) {
      if (error.code === 'ENOENT') {
        return true;
      }
      console.warn(`Error checking file modification: ${error.message}`);
      return false;
    }
  }

  /**
   * Get cached entry with indexes, loading if necessary
   */
  private async getCachedEntry(): Promise<CacheEntry> {
    const cacheKey = this.memoryFilePath;

    if (this.memoryOptimizedManager) {
      const cachedEntry = MemoryOptimizedManager.getFromCache(cacheKey);
      if (cachedEntry) {
        CachedKnowledgeGraphManager.cacheHits++;
        return cachedEntry;
      }
    }

    const hasChanged = await this.hasFileChanged();

    if (!hasChanged) {
      const cachedEntry = CachedKnowledgeGraphManager.cache.get(cacheKey);
      if (cachedEntry) {
        CachedKnowledgeGraphManager.cacheHits++;
        return cachedEntry;
      }
    }

    // Cache miss or file changed - load from disk
    CachedKnowledgeGraphManager.cacheMisses++;
    let graph = await this.baseManager.readGraph();

    if (this.lazyLoadingManager) {
      // Load observations lazily
      graph.entities.forEach(async (entity: any) => {
        entity.observations = await this.lazyLoadingManager!.loadEntityObservations(entity.name);
      });
    }

    const indexes = this.buildIndexes(graph);

    // Create cache entry
    const cacheEntry: CacheEntry = {
      graph: structuredClone(graph),
      lastModified: new Date(),
      filePath: this.memoryFilePath,
      indexes
    };

    // Update cache with file modification time
    try {
      const stats = await fs.stat(this.memoryFilePath);
      cacheEntry.lastModified = stats.mtime;
    } catch (error: any) {
      if (error.code !== 'ENOENT') {
        console.warn(`Error updating cache timestamp: ${error.message}`);
      }
    }

    if (this.memoryOptimizedManager) {
      MemoryOptimizedManager.addToCache(cacheKey, cacheEntry);
    } else {
      CachedKnowledgeGraphManager.cache.set(cacheKey, cacheEntry);
      CachedKnowledgeGraphManager.enforceCacheLimit();
    }

    return cacheEntry;
  }

  /**
   * Invalidate cache entry
   */
  private invalidateCache(): void {
    if (this.memoryOptimizedManager) {
      MemoryOptimizedManager.deleteFromCache(this.memoryFilePath);
    } else {
      CachedKnowledgeGraphManager.cache.delete(this.memoryFilePath);
    }
  }

  // OPTIMIZED PUBLIC API METHODS - These now use cached data and indexes

  async searchNodesEnhanced(query: string, options: SearchOptions = {}): Promise<{
    entities: Entity[];
    relations: Relation[];
    total: number;
  }> {
    const cacheEntry = await this.getCachedEntry();

    let matchingEntities: Entity[] = [];
    if (this.fullTextSearchManager) {
      matchingEntities = await this.fullTextSearchManager.search(query);
    } else {
      const queryLower = query.toLowerCase();
      matchingEntities = cacheEntry.graph.entities.filter(entity =>
        entity.name.toLowerCase().includes(queryLower) ||
        entity.entityType.toLowerCase().includes(queryLower) ||
        entity.observations.some(obs => obs.toLowerCase().includes(queryLower))
      );
    }

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

    // Find related relations using indexes
    const entityNames = new Set(paginatedEntities.map(e => e.name));
    const relatedRelations: Relation[] = [];

    entityNames.forEach(entityName => {
      const outgoing = cacheEntry.indexes.relationsByFrom.get(entityName) || [];
      const incoming = cacheEntry.indexes.relationsByTo.get(entityName) || [];
      relatedRelations.push(...outgoing, ...incoming);
    });

    // Remove duplicates
    const uniqueRelations = Array.from(new Set(relatedRelations.map(r =>
      `${r.from}-${r.to}-${r.relationType}`
    ))).map(key => {
      const [from, to, relationType] = key.split('-');
      return relatedRelations.find(r => r.from === from && r.to === to && r.relationType === relationType)!;
    });

    return {
      entities: paginatedEntities,
      relations: uniqueRelations,
      total: matchingEntities.length
    };
  }

  async searchEntitiesByType(entityType: string, options: SearchOptions = {}): Promise<{
    entities: Entity[];
    total: number;
  }> {
    const cacheEntry = await this.getCachedEntry();
    
    // Use index for O(1) lookup by type
    const matchingEntities = cacheEntry.indexes.entitiesByType.get(entityType.toLowerCase()) || [];

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

    return {
      entities: paginatedEntities,
      total: matchingEntities.length
    };
  }

  async getEntitiesByType(entityType: string): Promise<Entity[]> {
    const cacheEntry = await this.getCachedEntry();
    // Use index for O(1) lookup
    return cacheEntry.indexes.entitiesByType.get(entityType.toLowerCase()) || [];
  }

  async findPathBetweenEntities(fromEntity: string, toEntity: string): Promise<any> {
    const cacheEntry = await this.getCachedEntry();
    
    // Check if both entities exist using index
    const fromExists = cacheEntry.indexes.entityByName.has(fromEntity);
    const toExists = cacheEntry.indexes.entityByName.has(toEntity);
    
    if (!fromExists || !toExists) {
      return null;
    }

    // Build adjacency list from indexes (much faster)
    const adjacency = new Map<string, string[]>();
    
    cacheEntry.indexes.relationsByFrom.forEach((relations, from) => {
      if (!adjacency.has(from)) {
        adjacency.set(from, []);
      }
      relations.forEach(relation => {
        adjacency.get(from)!.push(relation.to);
      });
    });

    // Also add reverse direction for bidirectional search
    cacheEntry.indexes.relationsByTo.forEach((relations, to) => {
      relations.forEach(relation => {
        if (!adjacency.has(to)) {
          adjacency.set(to, []);
        }
        adjacency.get(to)!.push(relation.from);
      });
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
          const fromNode = path[i];
          const toNode = path[i + 1];
          
          const outgoingRelations = cacheEntry.indexes.relationsByFrom.get(fromNode) || [];
          const relation = outgoingRelations.find(r => r.to === toNode) ||
                          (cacheEntry.indexes.relationsByFrom.get(toNode) || []).find(r => r.to === fromNode);
          
          if (relation) {
            relations.push(relation);
          }
        }

        return {
          path,
          relations,
          distance: path.length - 1
        };
      }

      const neighbors = adjacency.get(current) || [];
      for (const neighbor of neighbors) {
        if (!visited.has(neighbor)) {
          visited.add(neighbor);
          queue.push([...path, neighbor]);
        }
      }
    }

    return null;
  }

  async getGraphStatistics(): Promise<any> {
    const cacheEntry = await this.getCachedEntry();
    const graph = cacheEntry.graph;
    
    // Use indexes for faster statistics
    const entityTypes: Record<string, number> = {};
    const relationTypes: Record<string, number> = {};
    
    cacheEntry.indexes.entitiesByType.forEach((entities, type) => {
      entityTypes[type] = entities.length;
    });
    
    cacheEntry.indexes.relationsByType.forEach((relations, type) => {
      relationTypes[type] = relations.length;
    });
    
    const totalObservations = graph.entities.reduce((sum, entity) => 
      sum + entity.observations.length, 0
    );
    
    const lastUpdated = graph.entities.length > 0 
      ? graph.entities.reduce((latest, entity) => 
          new Date(entity.updatedAt) > new Date(latest) ? entity.updatedAt : latest
        , graph.entities[0].updatedAt)
      : new Date().toISOString();
    
    return {
      totalEntities: graph.entities.length,
      totalRelations: graph.relations.length,
      entityTypes,
      relationTypes,
      averageObservationsPerEntity: graph.entities.length > 0 
        ? totalObservations / graph.entities.length 
        : 0,
      lastUpdated
    };
  }

  async exportGraph(): Promise<string> {
    const cacheEntry = await this.getCachedEntry();
    const exportData = {
      exportedAt: new Date().toISOString(),
      version: "1.0",
      graph: cacheEntry.graph
    };
    
    return JSON.stringify(exportData, null, 2);
  }

  async importGraph(jsonData: string): Promise<void> {
    await this.baseManager.importGraph(jsonData);
    this.invalidateCache();
  }

  async createEntities(entities: Entity[]): Promise<Entity[]> {
    if (this.batchOptimizedManager) {
      entities.forEach(entity => this.batchOptimizedManager!.queueEntity(entity));
      return entities; // Return immediately, batch will be flushed later
    }
    const result = await this.baseManager.createEntities(entities);
    this.invalidateCache();
    return result;
  }

  async createRelations(relations: Relation[]): Promise<Relation[]> {
    if (this.batchOptimizedManager) {
      relations.forEach(relation => this.batchOptimizedManager!.queueRelation(relation));
      return relations; // Return immediately, batch will be flushed later
    }
    const result = await this.baseManager.createRelations(relations);
    this.invalidateCache();
    return result;
  }

  async readGraph(): Promise<KnowledgeGraph> {
    const cacheEntry = await this.getCachedEntry();
    return structuredClone(cacheEntry.graph);
  }

  async searchNodes(query: string): Promise<Entity[]> {
    const result = await this.searchNodesEnhanced(query, { limit: 50 });
    return result.entities;
  }

  async openNodes(names: string[]): Promise<Entity[]> {
    const cacheEntry = await this.getCachedEntry();
    // Use index for O(1) lookups
    return names.map(name => cacheEntry.indexes.entityByName.get(name))
                .filter((entity): entity is Entity => entity !== undefined);
  }

  async getEntitySummary(entityName: string): Promise<any> {
    const cacheEntry = await this.getCachedEntry();
    
    // Use index for O(1) entity lookup
    const entity = cacheEntry.indexes.entityByName.get(entityName);
    if (!entity) {
      return {
        entity: null,
        relations: { outgoing: [], incoming: [] },
        relatedEntities: []
      };
    }

    // Use indexes for O(1) relation lookups
    const outgoing = cacheEntry.indexes.relationsByFrom.get(entityName) || [];
    const incoming = cacheEntry.indexes.relationsByTo.get(entityName) || [];
    
    const relatedEntityNames = new Set([
      ...outgoing.map(r => r.to),
      ...incoming.map(r => r.from)
    ]);
    
    // Use index for O(1) entity lookups
    const relatedEntities = Array.from(relatedEntityNames)
      .map(name => cacheEntry.indexes.entityByName.get(name))
      .filter((entity): entity is Entity => entity !== undefined && entity.name !== entityName);

    return {
      entity,
      relations: { outgoing, incoming },
      relatedEntities
    };
  }

  /**
   * Force refresh cache for this file
   */
  public async refreshCache(): Promise<void> {
    this.invalidateCache();
  }

  async deleteEntity(entityName: string): Promise<void> {
    const graph = await this.readGraph();
    
    // Remove entity
    const entityIndex = graph.entities.findIndex(e => e.name === entityName);
    if (entityIndex >= 0) {
      graph.entities.splice(entityIndex, 1);
    }
    
    // Remove related relations
    graph.relations = graph.relations.filter(r =>
      r.from !== entityName && r.to !== entityName
    );
    
    // Update storage
    await this.baseManager.createEntities(graph.entities);
    await this.baseManager.createRelations(graph.relations);
    
    // Invalidate cache
    this.invalidateCache();
  }

  /**
   * Get current cache entry for monitoring
   */
  public getCacheEntry(): CacheEntry | undefined {
    return CachedKnowledgeGraphManager.cache.get(this.memoryFilePath);
  }
}