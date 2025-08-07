export interface MemoryContext {
  name: string;
  path: string;
  description?: string;
  isProjectBased: boolean;
  lastAccessed?: string; // ISO timestamp
  projectDetectionRules?: {
    markers: string[];
    maxDepth: number;
  };
}

export interface ContextsConfig {
  activeContext: string;
  contexts: MemoryContext[];
}

export interface ProjectInfo {
  directory: string;
  name: string;
  marker: string | null;
}
