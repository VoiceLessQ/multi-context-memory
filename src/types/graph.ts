export interface Entity {
  name: string;
  entityType: string;
  observations: string[];
  createdAt: string;  // ISO timestamp of creation
  updatedAt: string;  // ISO timestamp of last update
  version: number;    // Incremented with each update
}

export interface Relation {
  from: string;
  to: string;
  relationType: string;
  createdAt: string;  // ISO timestamp of creation
  updatedAt: string;  // ISO timestamp of last update
  version: number;    // Incremented with each update
}

export interface KnowledgeGraph {
  entities: Entity[];
  relations: Relation[];
}
