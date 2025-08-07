import { CachedKnowledgeGraphManager } from '../graph/CachedKnowledgeGraphManager.js';
import { Entity, Relation } from '../types/graph.js';

export class BatchOptimizedManager {
  private pendingOperations: {
    entities: Entity[];
    relations: Relation[];
    deletions: string[];
  } = { entities: [], relations: [], deletions: [] };

  private batchTimeout: NodeJS.Timeout | null = null;
  private memoryFilePath: string;

  constructor(memoryFilePath: string) {
    this.memoryFilePath = memoryFilePath;
  }

  async queueEntity(entity: Entity): Promise<void> {
    this.pendingOperations.entities.push(entity);
    this.scheduleBatch();
  }

  async queueRelation(relation: Relation): Promise<void> {
    this.pendingOperations.relations.push(relation);
    this.scheduleBatch();
  }

  private scheduleBatch(): void {
    if (this.batchTimeout) {
      clearTimeout(this.batchTimeout);
    }

    this.batchTimeout = setTimeout(() => {
      this.flushBatch();
    }, 100); // 100ms batch window
  }

  private async flushBatch(): Promise<void> {
    if (this.hasPendingOperations()) {
      const manager = new CachedKnowledgeGraphManager(this.memoryFilePath);
      const graph = await manager.readGraph();

      // Apply deletions first
      this.pendingOperations.deletions.forEach((entityName: string) => {
        const entityIndex = graph.entities.findIndex((e: Entity) => e.name === entityName);
        if (entityIndex >= 0) {
          graph.entities.splice(entityIndex, 1);
        }
        
        // Remove related relations
        graph.relations = graph.relations.filter((r: Relation) =>
          r.from !== entityName && r.to !== entityName
        );
      });

      // Apply entity updates/creations
      this.pendingOperations.entities.forEach((entity: Entity) => {
        const existingIndex = graph.entities.findIndex((e: Entity) => e.name === entity.name);
        if (existingIndex >= 0) {
          graph.entities[existingIndex] = entity;
        } else {
          graph.entities.push(entity);
        }
      });

      // Apply relation updates/creations
      this.pendingOperations.relations.forEach((relation: Relation) => {
        const existingIndex = graph.relations.findIndex((r: Relation) =>
          r.from === relation.from && r.to === relation.to && r.relationType === relation.relationType
        );
        if (existingIndex >= 0) {
          graph.relations[existingIndex] = relation;
        } else {
          graph.relations.push(relation);
        }
      });

      // Write back to storage
      await manager.createEntities(graph.entities);
      await manager.createRelations(graph.relations);

      this.clearPendingOperations();
    }
  }

  private hasPendingOperations(): boolean {
    return this.pendingOperations.entities.length > 0 ||
           this.pendingOperations.relations.length > 0 ||
           this.pendingOperations.deletions.length > 0;
  }

  async queueDeletion(entityName: string): Promise<void> {
    this.pendingOperations.deletions.push(entityName);
    this.scheduleBatch();
  }

  async getQueueSize(): Promise<number> {
    return this.pendingOperations.entities.length +
           this.pendingOperations.relations.length +
           this.pendingOperations.deletions.length;
  }

  /**
   * Force flush the current batch immediately
   */
  async flushBatchNow(): Promise<void> {
    if (this.batchTimeout) {
      clearTimeout(this.batchTimeout);
      this.batchTimeout = null;
    }
    await this.flushBatch();
  }

  /**
   * Get pending operations count by type
   */
  async getPendingOperationsStats(): Promise<{
    entities: number;
    relations: number;
    deletions: number;
    total: number;
  }> {
    return {
      entities: this.pendingOperations.entities.length,
      relations: this.pendingOperations.relations.length,
      deletions: this.pendingOperations.deletions.length,
      total: this.pendingOperations.entities.length +
             this.pendingOperations.relations.length +
             this.pendingOperations.deletions.length
    };
  }

  private clearPendingOperations(): void {
    this.pendingOperations = { entities: [], relations: [], deletions: [] };
  }
}
