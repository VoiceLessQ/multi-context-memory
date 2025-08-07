import { Entity, Relation, KnowledgeGraph } from '../types/graph.js';
import { LazyLoadingManager } from './LazyLoadingManager.js';
import { FullTextSearchManager } from '../search/FullTextSearchManager.js';
import { MemoryOptimizedManager } from './MemoryOptimizedManager.js';
import { BatchOptimizedManager } from '../batch/BatchOptimizedManager.js';
import { CachedKnowledgeGraphManager } from './CachedKnowledgeGraphManager.js';
import { recordToolUsage } from '../tools/telemetryTools.js';
import * as fs from 'fs/promises';

/**
 * Optimized knowledge graph manager combining all Phase 2 improvements
 */
export class OptimizedKnowledgeGraphManager {
  private memoryFilePath: string;
  private lazyManager: LazyLoadingManager;
  private searchManager: FullTextSearchManager;
  private memoryManager: MemoryOptimizedManager;
  private batchManager: BatchOptimizedManager;
  private baseManager: CachedKnowledgeGraphManager;
  
  private options: {
    enableLazyLoading: boolean;
    enableFullTextSearch: boolean;
    enableMemoryOptimization: boolean;
    enableBatchOperations: boolean;
  };

  constructor(
    memoryFilePath: string,
    options: {
      enableLazyLoading?: boolean;
      enableFullTextSearch?: boolean;
      enableMemoryOptimization?: boolean;
      enableBatchOperations?: boolean;
    } = {}
  ) {
    this.memoryFilePath = memoryFilePath;
    this.options = {
      enableLazyLoading: options.enableLazyLoading ?? true,
      enableFullTextSearch: options.enableFullTextSearch ?? true,
      enableMemoryOptimization: options.enableMemoryOptimization ?? true,
      enableBatchOperations: options.enableBatchOperations ?? true,
    };

    this.baseManager = new CachedKnowledgeGraphManager(memoryFilePath);
    this.lazyManager = new LazyLoadingManager(memoryFilePath);
    this.searchManager = new FullTextSearchManager();
    this.memoryManager = new MemoryOptimizedManager(memoryFilePath);
    this.batchManager = new BatchOptimizedManager(memoryFilePath);
  }

  /**
   * Read graph with optimizations
   */
  async readGraph(): Promise<KnowledgeGraph> {
    const startTime = Date.now();
    try {
      const cacheKey = 'full_graph';
      
      // Check memory cache first
      if (this.options.enableMemoryOptimization) {
        const cached = await this.memoryManager.get(cacheKey);
        if (cached) {
          recordToolUsage('read_graph_cached', Date.now() - startTime);
          return cached;
        }
      }

      let graph: KnowledgeGraph;
      
      // Use lazy loading if enabled
      if (this.options.enableLazyLoading) {
        graph = await this.lazyManager.loadGraphLazy();
      } else {
        graph = await this.baseManager.readGraph();
      }

      // Build search index if enabled
      if (this.options.enableFullTextSearch) {
        await this.searchManager.buildIndex(graph.entities);
      }

      // Cache in memory if enabled
      if (this.options.enableMemoryOptimization) {
        await this.memoryManager.set(cacheKey, graph);
      }

      recordToolUsage('read_graph', Date.now() - startTime);
      return graph;
    } catch (error) {
      recordToolUsage('read_graph', Date.now() - startTime, error as Error);
      throw error;
    }
  }

  /**
   * Create entities with batch optimization
   */
  async createEntities(entities: Entity[]): Promise<void> {
    const startTime = Date.now();
    try {
      if (this.options.enableBatchOperations) {
        for (const entity of entities) {
          await this.batchManager.queueEntity(entity);
        }
      } else {
        await this.baseManager.createEntities(entities);
      }

      // Invalidate caches
      await this.invalidateCaches();

      recordToolUsage('create_entities', Date.now() - startTime);
    } catch (error) {
      recordToolUsage('create_entities', Date.now() - startTime, error as Error);
      throw error;
    }
  }

  /**
   * Create relations with batch optimization
   */
  async createRelations(relations: Relation[]): Promise<void> {
    const startTime = Date.now();
    try {
      if (this.options.enableBatchOperations) {
        for (const relation of relations) {
          await this.batchManager.queueRelation(relation);
        }
      } else {
        await this.baseManager.createRelations(relations);
      }

      // Invalidate caches
      await this.invalidateCaches();

      recordToolUsage('create_relations', Date.now() - startTime);
    } catch (error) {
      recordToolUsage('create_relations', Date.now() - startTime, error as Error);
      throw error;
    }
  }

  /**
   * Search entities with full-text search
   */
  async searchEntities(query: string, options: {
    limit?: number;
    offset?: number;
    entityType?: string;
    minObservations?: number;
    maxObservations?: number;
  } = {}): Promise<{
    entities: Entity[];
    total: number;
    searchTime: number;
  }> {
    const startTime = Date.now();
    try {
      if (!this.options.enableFullTextSearch) {
        // Use basic search from base manager
        const entities = await this.baseManager.searchNodes(query);
        return {
          entities: entities.slice(options.offset || 0, (options.offset || 0) + (options.limit || 50)),
          total: entities.length,
          searchTime: Date.now() - startTime
        };
      }

      // Use full-text search
      const entities = await this.searchManager.search(query);
      
      // Apply filters
      let filteredEntities = entities;
      
      if (options.entityType) {
        filteredEntities = filteredEntities.filter(e => e.entityType === options.entityType);
      }
      
      if (options.minObservations !== undefined) {
        filteredEntities = filteredEntities.filter(e => e.observations.length >= options.minObservations!);
      }
      
      if (options.maxObservations !== undefined) {
        filteredEntities = filteredEntities.filter(e => e.observations.length <= options.maxObservations!);
      }

      // Apply pagination
      const offset = options.offset || 0;
      const limit = options.limit || 50;
      const paginatedEntities = filteredEntities.slice(offset, offset + limit);

      recordToolUsage('search_entities', Date.now() - startTime);
      return {
        entities: paginatedEntities,
        total: filteredEntities.length,
        searchTime: Date.now() - startTime
      };
    } catch (error) {
      recordToolUsage('search_entities', Date.now() - startTime, error as Error);
      throw error;
    }
  }

  /**
   * Delete entities with batch optimization
   */
  async deleteEntities(entityNames: string[]): Promise<void> {
    const startTime = Date.now();
    try {
      if (this.options.enableBatchOperations) {
        for (const entityName of entityNames) {
          await this.batchManager.queueDeletion(entityName);
        }
      } else {
        // Use base manager for individual deletions
        for (const entityName of entityNames) {
          await this.baseManager.deleteEntity(entityName);
        }
      }

      // Invalidate caches
      await this.invalidateCaches();

      recordToolUsage('delete_entities', Date.now() - startTime);
    } catch (error) {
      recordToolUsage('delete_entities', Date.now() - startTime, error as Error);
      throw error;
    }
  }

  /**
   * Get entity with lazy loading
   */
  async getEntity(entityName: string): Promise<Entity | null> {
    const startTime = Date.now();
    try {
      if (this.options.enableLazyLoading) {
        return await this.lazyManager.loadEntity(entityName);
      } else {
        const graph = await this.baseManager.readGraph();
        return graph.entities.find(e => e.name === entityName) || null;
      }
    } catch (error) {
      recordToolUsage('get_entity', Date.now() - startTime, error as Error);
      throw error;
    }
  }

  /**
   * Invalidate all caches
   */
  private async invalidateCaches(): Promise<void> {
    if (this.options.enableMemoryOptimization) {
      await this.memoryManager.clear();
    }
    
    if (this.options.enableFullTextSearch) {
      await this.searchManager.clearIndex();
    }
  }

  /**
   * Get optimization statistics
   */
  async getOptimizationStats(): Promise<{
    memoryUsage?: any;
    cacheStats?: any;
    searchIndexSize?: number;
    batchQueueSize?: number;
  }> {
    const stats: any = {};

    if (this.options.enableMemoryOptimization) {
      stats.memoryUsage = await this.memoryManager.getStats();
    }

    if (this.options.enableFullTextSearch) {
      stats.searchIndexSize = await this.searchManager.getIndexSize();
    }

    if (this.options.enableBatchOperations) {
      stats.batchQueueSize = await this.batchManager.getQueueSize();
    }

    return stats;
  }

  /**
   * Flush all pending batch operations
   */
  async flushAll(): Promise<void> {
    if (this.options.enableBatchOperations) {
      await this.batchManager.flushBatchNow();
    }
  }

  /**
   * Get memory statistics
   */
  async getMemoryStats(): Promise<any> {
    if (this.options.enableMemoryOptimization) {
      return await this.memoryManager.getStats();
    }
    return null;
  }

  /**
   * Get current configuration
   */
  getConfiguration(): {
    enableLazyLoading: boolean;
    enableFullTextSearch: boolean;
    enableMemoryOptimization: boolean;
    enableBatchOperations: boolean;
  } {
    return { ...this.options };
  }

  /**
   * Update configuration
   */
  async updateConfiguration(newOptions: {
    enableLazyLoading?: boolean;
    enableFullTextSearch?: boolean;
    enableMemoryOptimization?: boolean;
    enableBatchOperations?: boolean;
  }): Promise<void> {
    this.options = {
      ...this.options,
      ...newOptions
    };

    // Reinitialize managers if needed
    if (newOptions.enableLazyLoading !== undefined) {
      if (newOptions.enableLazyLoading && !this.lazyManager) {
        this.lazyManager = new LazyLoadingManager(this.memoryFilePath);
      }
    }

    if (newOptions.enableFullTextSearch !== undefined) {
      if (newOptions.enableFullTextSearch && !this.searchManager) {
        this.searchManager = new FullTextSearchManager(this.memoryFilePath);
      }
    }

    if (newOptions.enableMemoryOptimization !== undefined) {
      if (newOptions.enableMemoryOptimization && !this.memoryManager) {
        this.memoryManager = new MemoryOptimizedManager(this.memoryFilePath);
      }
    }

    if (newOptions.enableBatchOperations !== undefined) {
      if (newOptions.enableBatchOperations && !this.batchManager) {
        this.batchManager = new BatchOptimizedManager(this.memoryFilePath);
      }
    }
  }
}
