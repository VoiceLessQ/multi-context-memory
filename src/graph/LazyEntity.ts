import { Entity } from '../types/graph.js';

export interface LazyEntity extends Entity {
  _observations?: string[]; // Optional cached observations
  getObservations(): Promise<string[]>;
}
