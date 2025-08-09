import { ContextManager } from '../context/ContextManager.js';

export class ContextHandlers {
  constructor(private contextManager: ContextManager) {}

  async listContexts() {
    const contexts = await this.contextManager.listContexts();
    return contexts.map(context => ({
      name: context.name,
      path: context.path,
      description: context.description,
      isProjectBased: context.isProjectBased,
      lastAccessed: context.lastAccessed
    }));
  }

  async getActiveContext() {
    const activeContext = await this.contextManager.getActiveContext();
    return { activeContext };
  }

  async setActiveContext(contextName: string) {
    await this.contextManager.setActiveContext(contextName);
    return { message: `Active context set to '${contextName}'` };
  }

  async addContext(context: any) {
    await this.contextManager.addContext({
      name: context.name,
      path: context.path,
      description: context.description,
      isProjectBased: context.isProjectBased || false
    });
    return { message: `Context '${context.name}' added successfully` };
  }

  async removeContext(contextName: string) {
    await this.contextManager.removeContext(contextName);
    return { message: `Context '${contextName}' removed successfully` };
  }
}
