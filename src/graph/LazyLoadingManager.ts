import * as fs from 'fs/promises';
import { Entity, KnowledgeGraph } from '../types/graph.js';

export class LazyLoadingManager {
  private memoryFilePath: string;
  private entityCache = new Map<string, Entity>();

  constructor(memoryFilePath: string) {
    this.memoryFilePath = memoryFilePath;
  }

  async loadEntityObservations(entityName: string): Promise<string[]> {
    const data = await fs.readFile(this.memoryFilePath, 'utf-8');
    const lines = data.split('\n');

    for (const line of lines) {
      if (line.trim()) {
        const item = JSON.parse(line);
        if (item.type === 'entity' && item.name === entityName) {
          return item.observations || [];
        }
      }
    }
    return [];
  }

  async loadEntity(entityName: string): Promise<Entity | null> {
    // Check cache first
    if (this.entityCache.has(entityName)) {
      return this.entityCache.get(entityName)!;
    }

    try {
      const data = await fs.readFile(this.memoryFilePath, 'utf-8');
      const lines = data.split('\n');

      for (const line of lines) {
        if (line.trim()) {
          const item = JSON.parse(line);
          if (item.type === 'entity' && item.name === entityName) {
            const entity: Entity = {
              name: item.name,
              entityType: item.entityType,
              observations: item.observations || [],
              createdAt: item.createdAt,
              updatedAt: item.updatedAt,
              version: item.version || 1
            };
            
            // Cache the entity
            this.entityCache.set(entityName, entity);
            return entity;
          }
        }
      }
    } catch (error) {
      console.warn(`Error loading entity ${entityName}:`, error);
    }

    return null;
  }

  async loadGraphLazy(): Promise<KnowledgeGraph> {
    try {
      const data = await fs.readFile(this.memoryFilePath, 'utf-8');
      const lines = data.split('\n');

      const entities: Entity[] = [];
      const relations: any[] = [];

      for (const line of lines) {
        if (line.trim()) {
          const item = JSON.parse(line);
          
          if (item.type === 'entity') {
            // Load entity with minimal observations initially
            const entity: Entity = {
              name: item.name,
              entityType: item.entityType,
              observations: [], // Load lazily when needed
              createdAt: item.createdAt,
              updatedAt: item.updatedAt,
              version: item.version || 1
            };
            entities.push(entity);
            this.entityCache.set(entity.name, entity);
          } else if (item.type === 'relation') {
            relations.push({
              from: item.from,
              to: item.to,
              relationType: item.relationType,
              createdAt: item.createdAt,
              updatedAt: item.updatedAt,
              version: item.version || 1
            });
          }
        }
      }

      return { entities, relations };
    } catch (error) {
      console.warn('Error loading graph lazily:', error);
      return { entities: [], relations: [] };
    }
  }

  /**
   * Load observations for an entity on demand
   */
  async loadObservationsOnDemand(entityName: string): Promise<string[]> {
    const cachedEntity = this.entityCache.get(entityName);
    if (cachedEntity && cachedEntity.observations.length > 0) {
      return cachedEntity.observations;
    }

    const observations = await this.loadEntityObservations(entityName);
    
    // Update cache
    if (cachedEntity) {
      cachedEntity.observations = observations;
    }

    return observations;
  }

  /**
   * Clear the entity cache
   */
  clearCache(): void {
    this.entityCache.clear();
  }
}
