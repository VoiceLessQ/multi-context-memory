import { promises as fs } from 'fs';
import { join } from 'path';
import { homedir } from 'os';

interface TelemetryEvent {
  timestamp: string;
  toolName: string;
  duration: number;
  error?: string;
  memoryUsage?: {
    heapUsed: number;
    heapTotal: number;
    external: number;
  };
}

interface PerformanceMetrics {
  totalOperations: number;
  averageDuration: number;
  errorRate: number;
  memoryTrend: number;
}

class TelemetryManager {
  private events: TelemetryEvent[] = [];
  private maxEvents: number = 1000;
  private logFile: string;
  private isEnabled: boolean = true;

  constructor() {
    this.logFile = join(homedir(), '.mcp-knowledge-graph', 'telemetry.json');
    this.loadEvents();
  }

  /**
   * Record a tool usage event
   */
  recordToolUsage(toolName: string, duration: number, error?: Error): void {
    if (!this.isEnabled) return;

    const event: TelemetryEvent = {
      timestamp: new Date().toISOString(),
      toolName,
      duration,
      error: error?.message,
      memoryUsage: process.memoryUsage()
    };

    this.events.push(event);
    
    // Keep only recent events
    if (this.events.length > this.maxEvents) {
      this.events = this.events.slice(-this.maxEvents);
    }

    // Save to file asynchronously
    this.saveEvents().catch(console.error);
  }

  /**
   * Get performance metrics
   */
  getPerformanceMetrics(): PerformanceMetrics {
    const recentEvents = this.events.slice(-100); // Last 100 events
    
    if (recentEvents.length === 0) {
      return {
        totalOperations: 0,
        averageDuration: 0,
        errorRate: 0,
        memoryTrend: 0
      };
    }

    const totalOperations = recentEvents.length;
    const totalDuration = recentEvents.reduce((sum, event) => sum + event.duration, 0);
    const errorCount = recentEvents.filter(event => event.error).length;
    
    // Calculate memory trend
    const memoryEvents = recentEvents.filter(e => e.memoryUsage);
    let memoryTrend = 0;
    if (memoryEvents.length > 1) {
      const first = memoryEvents[0].memoryUsage!.heapUsed;
      const last = memoryEvents[memoryEvents.length - 1].memoryUsage!.heapUsed;
      memoryTrend = ((last - first) / first) * 100;
    }

    return {
      totalOperations,
      averageDuration: totalDuration / totalOperations,
      errorRate: (errorCount / totalOperations) * 100,
      memoryTrend
    };
  }

  /**
   * Get tool usage statistics
   */
  getToolStats(): Record<string, {
    count: number;
    averageDuration: number;
    errorCount: number;
    lastUsed: string;
  }> {
    const stats: Record<string, any> = {};
    
    for (const event of this.events) {
      if (!stats[event.toolName]) {
        stats[event.toolName] = {
          count: 0,
          totalDuration: 0,
          errorCount: 0,
          lastUsed: event.timestamp
        };
      }
      
      stats[event.toolName].count++;
      stats[event.toolName].totalDuration += event.duration;
      if (event.error) {
        stats[event.toolName].errorCount++;
      }
      stats[event.toolName].lastUsed = event.timestamp;
    }

    // Calculate averages
    for (const toolName in stats) {
      const tool = stats[toolName];
      tool.averageDuration = tool.totalDuration / tool.count;
      delete tool.totalDuration;
    }

    return stats;
  }

  /**
   * Get memory usage trends
   */
  getMemoryTrends(): {
    timestamps: string[];
    heapUsed: number[];
    heapTotal: number[];
    external: number[];
  } {
    const memoryEvents = this.events.filter(e => e.memoryUsage);
    
    return {
      timestamps: memoryEvents.map(e => e.timestamp),
      heapUsed: memoryEvents.map(e => e.memoryUsage!.heapUsed),
      heapTotal: memoryEvents.map(e => e.memoryUsage!.heapTotal),
      external: memoryEvents.map(e => e.memoryUsage!.external)
    };
  }

  /**
   * Export telemetry data
   */
  exportData(): {
    events: TelemetryEvent[];
    metrics: PerformanceMetrics;
    toolStats: Record<string, any>;
    memoryTrends: any;
  } {
    return {
      events: this.events,
      metrics: this.getPerformanceMetrics(),
      toolStats: this.getToolStats(),
      memoryTrends: this.getMemoryTrends()
    };
  }

  /**
   * Clear all telemetry data
   */
  clear(): void {
    this.events = [];
    this.saveEvents().catch(console.error);
  }

  /**
   * Enable/disable telemetry
   */
  setEnabled(enabled: boolean): void {
    this.isEnabled = enabled;
  }

  /**
   * Load events from file
   */
  private async loadEvents(): Promise<void> {
    try {
      const data = await fs.readFile(this.logFile, 'utf8');
      this.events = JSON.parse(data);
    } catch (error) {
      // File doesn't exist or is invalid, start fresh
      this.events = [];
    }
  }

  /**
   * Save events to file
   */
  private async saveEvents(): Promise<void> {
    try {
      const dir = this.logFile.split('/').slice(0, -1).join('/');
      await fs.mkdir(dir, { recursive: true });
      await fs.writeFile(this.logFile, JSON.stringify(this.events, null, 2));
    } catch (error) {
      console.error('Failed to save telemetry:', error);
    }
  }
}

// Global telemetry instance
const telemetry = new TelemetryManager();

/**
 * Record tool usage with performance metrics
 */
export function recordToolUsage(toolName: string, duration: number, error?: Error): void {
  telemetry.recordToolUsage(toolName, duration, error);
}

/**
 * Get performance metrics
 */
export function getPerformanceMetrics(): PerformanceMetrics {
  return telemetry.getPerformanceMetrics();
}

/**
 * Get tool usage statistics
 */
export function getToolStats(): Record<string, any> {
  return telemetry.getToolStats();
}

/**
 * Get memory usage trends
 */
export function getMemoryTrends(): any {
  return telemetry.getMemoryTrends();
}

/**
 * Export all telemetry data
 */
export function exportTelemetryData(): any {
  return telemetry.exportData();
}

/**
 * Clear telemetry data
 */
export function clearTelemetry(): void {
  telemetry.clear();
}

/**
 * Enable/disable telemetry
 */
export function setTelemetryEnabled(enabled: boolean): void {
  telemetry.setEnabled(enabled);
}
