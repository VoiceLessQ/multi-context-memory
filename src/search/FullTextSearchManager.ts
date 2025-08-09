import { CachedKnowledgeGraphManager } from '../graph/CachedKnowledgeGraphManager.js';
import { Entity } from '../types/graph.js';

interface SearchIndex {
  terms: Map<string, Set<string>>;
  entityTerms: Map<string, Set<string>>;
}

export class FullTextSearchManager {
  private searchIndex: SearchIndex | null = null;
  private memoryFilePath: string;

  constructor(memoryFilePath?: string) {
    this.memoryFilePath = memoryFilePath || '';
  }

  async buildSearchIndex(): Promise<SearchIndex> {
    const manager = new CachedKnowledgeGraphManager(this.memoryFilePath);
    const graph = await manager.readGraph();

    const index: SearchIndex = {
      terms: new Map(),
      entityTerms: new Map()
    };

    graph.entities.forEach((entity: Entity) => {
      const terms = this.extractTerms(entity);
      index.entityTerms.set(entity.name, new Set(terms));

      terms.forEach(term => {
        if (!index.terms.has(term)) {
          index.terms.set(term, new Set());
        }
        index.terms.get(term)!.add(entity.name);
      });
    });

    return index;
  }

  private extractTerms(entity: Entity): string[] {
    const text = [
      entity.name,
      entity.entityType,
      ...entity.observations
    ].join(' ').toLowerCase();

    return text.split(/\s+/).filter(term => term.length > 2);
  }

  async buildIndex(entities: Entity[]): Promise<void> {
    const index: SearchIndex = {
      terms: new Map(),
      entityTerms: new Map()
    };

    entities.forEach((entity: Entity) => {
      const terms = this.extractTerms(entity);
      index.entityTerms.set(entity.name, new Set(terms));

      terms.forEach(term => {
        if (!index.terms.has(term)) {
          index.terms.set(term, new Set());
        }
        index.terms.get(term)!.add(entity.name);
      });
    });

    this.searchIndex = index;
  }

  async search(query: string): Promise<Entity[]> {
    if (!this.searchIndex) {
      if (!this.memoryFilePath) {
        return [];
      }
      this.searchIndex = await this.buildSearchIndex();
    }

    const queryTerms = query.toLowerCase().split(/\s+/).filter(term => term.length > 2);
    const matchingEntities = new Set<string>();

    queryTerms.forEach(term => {
      const entities = this.searchIndex!.terms.get(term) || new Set<string>();
      entities.forEach(entity => matchingEntities.add(entity));
    });

    if (!this.memoryFilePath) {
      return [];
    }

    const manager = new CachedKnowledgeGraphManager(this.memoryFilePath);
    const graph = await manager.readGraph();

    return graph.entities.filter((e: Entity) => matchingEntities.has(e.name));
  }

  async clearIndex(): Promise<void> {
    this.searchIndex = null;
  }

  async getIndexSize(): Promise<number> {
    if (!this.searchIndex) {
      return 0;
    }
    return this.searchIndex.terms.size;
  }

  /**
   * Search with scoring and ranking
   */
  async searchWithScoring(query: string): Promise<{ entity: Entity; score: number }[]> {
    if (!this.searchIndex) {
      if (!this.memoryFilePath) {
        return [];
      }
      this.searchIndex = await this.buildSearchIndex();
    }

    const queryTerms = query.toLowerCase().split(/\s+/).filter(term => term.length > 2);
    const entityScores = new Map<string, number>();

    queryTerms.forEach(term => {
      const entities = this.searchIndex!.terms.get(term) || new Set<string>();
      entities.forEach(entityName => {
        const currentScore = entityScores.get(entityName) || 0;
        entityScores.set(entityName, currentScore + 1);
      });
    });

    if (!this.memoryFilePath) {
      return [];
    }

    const manager = new CachedKnowledgeGraphManager(this.memoryFilePath);
    const graph = await manager.readGraph();

    const results: { entity: Entity; score: number }[] = [];
    
    entityScores.forEach((score, entityName) => {
      const entity = graph.entities.find(e => e.name === entityName);
      if (entity) {
        results.push({ entity, score });
      }
    });

    // Sort by score descending
    return results.sort((a, b) => b.score - a.score);
  }
}
