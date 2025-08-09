import { promises as fs } from 'fs';
import path from 'path';
import { ContextsConfig, MemoryContext, ProjectInfo } from '../types/context.js';

export class ContextManager {
  private contextsFilePath: string;
  private config: ContextsConfig;

  constructor(contextsDirectory: string) {
    this.contextsFilePath = path.join(contextsDirectory, 'contexts.json');
    this.config = { activeContext: 'default', contexts: [] };
  }

  async loadContexts(): Promise<ContextsConfig> {
    try {
      const data = await fs.readFile(this.contextsFilePath, 'utf-8');
      this.config = JSON.parse(data);
      return this.config;
    } catch (error) {
      // Create default configuration
      this.config = this.createDefaultConfig();
      await this.saveContexts();
      return this.config;
    }
  }

  private createDefaultConfig(): ContextsConfig {
    return {
      activeContext: 'default',
      contexts: [{
        name: 'default',
        path: './memory.jsonl',
        isProjectBased: false,
        description: 'Default memory context'
      }]
    };
  }

  async saveContexts(): Promise<void> {
    await fs.mkdir(path.dirname(this.contextsFilePath), { recursive: true });
    await fs.writeFile(this.contextsFilePath, JSON.stringify(this.config, null, 2));
  }

  async resolveMemoryPath(contextName?: string): Promise<string> {
    await this.loadContexts();
    
    const contextToUse = contextName || this.config.activeContext || 'default';
    const context = this.config.contexts.find(c => c.name === contextToUse);

    if (!context) {
      // Fall back to default context
      const defaultContext = this.config.contexts.find(c => c.name === 'default');
      return defaultContext?.path || './memory.jsonl';
    }

    if (!context.isProjectBased) {
      return context.path;
    }

    const projectInfo = await this.detectProjectInfo();
    return this.resolvePathTemplate(context.path, projectInfo);
  }

  private async detectProjectInfo(): Promise<ProjectInfo> {
    let currentDir = process.cwd();
    const maxDepth = this.config.contexts.find(c => c.isProjectBased)?.projectDetectionRules?.maxDepth || 5;

    for (let i = 0; i < maxDepth; i++) {
      const markers = this.config.contexts.find(c => c.isProjectBased)?.projectDetectionRules?.markers || 
                     ['.git', 'package.json', 'pyproject.toml'];
      
      for (const marker of markers) {
        try {
          await fs.access(path.join(currentDir, marker));
          return {
            directory: currentDir,
            name: path.basename(currentDir),
            marker: marker
          };
        } catch {
          // Marker not found, continue
        }
      }

      const parentDir = path.dirname(currentDir);
      if (parentDir === currentDir) break;
      currentDir = parentDir;
    }

    return {
      directory: process.cwd(),
      name: path.basename(process.cwd()),
      marker: null
    };
  }

  private resolvePathTemplate(template: string, projectInfo: ProjectInfo): string {
    return template.replace('{projectDir}', projectInfo.directory);
  }

  // Context management methods
  async listContexts(): Promise<MemoryContext[]> {
    await this.loadContexts();
    return this.config.contexts;
  }

  async getActiveContext(): Promise<string> {
    await this.loadContexts();
    return this.config.activeContext;
  }

  async setActiveContext(contextName: string): Promise<void> {
    await this.loadContexts();
    const context = this.config.contexts.find(c => c.name === contextName);
    if (!context) {
      throw new Error(`Context '${contextName}' not found`);
    }
    this.config.activeContext = contextName;
    await this.saveContexts();
  }

  async addContext(context: MemoryContext): Promise<void> {
    await this.loadContexts();
    if (this.config.contexts.some(c => c.name === context.name)) {
      throw new Error(`Context '${context.name}' already exists`);
    }
    this.config.contexts.push(context);
    await this.saveContexts();
  }

  async removeContext(contextName: string): Promise<void> {
    await this.loadContexts();
    if (contextName === 'default') {
      throw new Error('Cannot remove default context');
    }
    this.config.contexts = this.config.contexts.filter(c => c.name !== contextName);
    if (this.config.activeContext === contextName) {
      this.config.activeContext = 'default';
    }
    await this.saveContexts();
  }
}
