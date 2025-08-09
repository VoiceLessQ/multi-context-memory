import { promises as fs } from 'fs';
import { createHash } from 'crypto';
import { join } from 'path';
import { homedir } from 'os';

/**
 * Anonymous usage telemetry for MCP Knowledge Graph
 * Privacy-first design with zero-knowledge principles
 */
export interface TelemetryConfig {
  enabled: boolean;
  sessionId: string;
  cachePath: string;
  maxCacheAge: number; // milliseconds
}

export interface SystemFingerprint {
  os: string;
  nodeVersion: string;
  architecture: string;
  hash: string;
}

export interface FeatureUsage {
  toolName: string;
  count: number;
  errorCount: number;
  avgResponseTime: number;
}

export interface ConfigurationMetrics {
  contextCount: number;
  memoryFileSize: number;
  featuresEnabled: string[];
}

export interface TelemetryData {
  sessionId: string;
  timestamp: number;
  systemFingerprint: SystemFingerprint;
  featureUsage: FeatureUsage[];
  configuration: ConfigurationMetrics;
  performance: {
    uptime: number;
    memoryUsage: number;
  };
}

export interface PrivacySettings {
  enabled: boolean;
  sessionId: string;
  dataPreview: any;
}

export class TelemetryManager {
  private config: TelemetryConfig;
  private cache: TelemetryData[] = [];
  private startTime: number = Date.now();
  private featureCounters = new Map<string, { count: number; errors: number; totalTime: number }>();
  private isDevEnvironment: boolean;
  private configuration: ConfigurationMetrics | undefined;

  constructor() {
    this.isDevEnvironment = this.detectDevEnvironment();
    this.config = this.loadConfigSync();
    
    if (this.isDevEnvironment) {
      console.error('Development environment detected - telemetry disabled');
      this.config.enabled = false;
    }
  }

  /**
   * Detect if running in development environment
   */
  private detectDevEnvironment(): boolean {
    return (
      process.env.NODE_ENV === 'development' ||
      process.env.MCP_KG_DEV === '1' ||
      process.argv.some(arg => arg.includes('ts-node')) ||
      process.argv.some(arg => arg.includes('typescript'))
    );
  }

  /**
   * Load configuration synchronously from multiple sources
   */
  private loadConfigSync(): TelemetryConfig {
    // Check environment variable first (highest priority)
    if (process.env.MCP_KG_NO_TELEMETRY === '1') {
      return {
        enabled: false,
        sessionId: this.generateSessionId(),
        cachePath: join(homedir(), '.mcp-knowledge-graph', 'telemetry-cache.json'),
        maxCacheAge: 30 * 24 * 60 * 60 * 1000, // 30 days
      };
    }

    // Check CLI flag
    if (process.argv.includes('--no-telemetry')) {
      return {
        enabled: false,
        sessionId: this.generateSessionId(),
        cachePath: join(homedir(), '.mcp-knowledge-graph', 'telemetry-cache.json'),
        maxCacheAge: 30 * 24 * 60 * 60 * 1000,
      };
    }

    // Check config file synchronously using require
    const configPath = join(homedir(), '.mcp-knowledge-graph', 'config.json');
    try {
      // Use dynamic import for sync loading
      const configData = require(configPath);
      if (configData.telemetry === false) {
        return {
          enabled: false,
          sessionId: this.generateSessionId(),
          cachePath: join(homedir(), '.mcp-knowledge-graph', 'telemetry-cache.json'),
          maxCacheAge: 30 * 24 * 60 * 60 * 1000,
        };
      }
    } catch (error) {
      // Config file doesn't exist or is invalid - proceed with defaults
    }

    // Default: enabled with privacy controls
    return {
      enabled: true,
      sessionId: this.generateSessionId(),
      cachePath: join(homedir(), '.mcp-knowledge-graph', 'telemetry-cache.json'),
      maxCacheAge: 30 * 24 * 60 * 60 * 1000,
    };
  }

  /**
   * Generate anonymous session ID
   */
  private generateSessionId(): string {
    return 'session_' + Math.random().toString(36).substring(2, 15) + 
           Math.random().toString(36).substring(2, 15);
  }

  /**
   * Generate system fingerprint (hashed, non-identifying)
   */
  private generateSystemFingerprint(): SystemFingerprint {
    const os = process.platform;
    const nodeVersion = process.version;
    const architecture = process.arch;
    
    // Create a hash that's consistent for this system but not reversible
    const hashInput = `${os}-${nodeVersion}-${architecture}`;
    const hash = createHash('sha256').update(hashInput).digest('hex').substring(0, 16);
    
    return { os, nodeVersion, architecture, hash };
  }

  /**
   * Check if telemetry is enabled
   */
  public isEnabled(): boolean {
    return this.config.enabled;
  }

  /**
   * Disable telemetry
   */
  public disable(): void {
    this.config.enabled = false;
    console.error('Telemetry disabled');
  }

  /**
   * Enable telemetry
   */
  public enable(): void {
    if (this.isDevEnvironment) {
      console.error('Cannot enable telemetry in development environment');
      return;
    }
    this.config.enabled = true;
    console.error('Telemetry enabled');
  }

  /**
   * Record tool usage
   */
  public recordToolUsage(toolName: string, responseTime: number, error?: Error): void {
    if (!this.config.enabled) return;

    const counter = this.featureCounters.get(toolName) || { count: 0, errors: 0, totalTime: 0 };
    counter.count++;
    if (error) counter.errors++;
    counter.totalTime += responseTime;
    this.featureCounters.set(toolName, counter);
  }

  /**
   * Record configuration metrics
   */
  public recordConfiguration(contextCount: number, memoryFileSize: number, featuresEnabled: string[]): void {
    if (!this.config.enabled) return;

    this.configuration = {
      contextCount,
      memoryFileSize,
      featuresEnabled,
    };
  }

  /**
   * Collect current telemetry data
   */
  public collectTelemetryData(): TelemetryData {
    const featureUsage: FeatureUsage[] = Array.from(this.featureCounters.entries()).map(([toolName, counter]) => ({
      toolName,
      count: counter.count,
      errorCount: counter.errors,
      avgResponseTime: counter.count > 0 ? counter.totalTime / counter.count : 0,
    }));

    return {
      sessionId: this.config.sessionId,
      timestamp: Date.now(),
      systemFingerprint: this.generateSystemFingerprint(),
      featureUsage,
      configuration: this.configuration || {
        contextCount: 0,
        memoryFileSize: 0,
        featuresEnabled: [],
      },
      performance: {
        uptime: Date.now() - this.startTime,
        memoryUsage: process.memoryUsage().heapUsed,
      },
    };
  }

  /**
   * Save telemetry data to cache
   */
  public async saveTelemetryData(): Promise<void> {
    if (!this.config.enabled) return;

    try {
      const data = this.collectTelemetryData();
      
      // Ensure directory exists
      const dir = this.config.cachePath.split('/').slice(0, -1).join('/');
      try {
        await fs.mkdir(dir, { recursive: true });
      } catch (error) {
        // Directory might already exist
      }

      // Load existing cache
      let cache: TelemetryData[] = [];
      try {
        const existingData = await fs.readFile(this.config.cachePath, 'utf-8');
        cache = JSON.parse(existingData);
      } catch (error) {
        // File doesn't exist or is invalid
      }

      // Add new data and clean old entries
      cache.push(data);
      const cutoffTime = Date.now() - this.config.maxCacheAge;
      cache = cache.filter(entry => entry.timestamp > cutoffTime);

      // Save updated cache
      await fs.writeFile(this.config.cachePath, JSON.stringify(cache, null, 2));
    } catch (error) {
      console.error('Failed to save telemetry data:', error);
    }
  }

  /**
   * Get telemetry status
   */
  public getStatus(): PrivacySettings {
    return {
      enabled: this.config.enabled,
      sessionId: this.config.sessionId,
      dataPreview: this.config.enabled ? this.collectTelemetryData() : null,
    };
  }

  /**
   * Export telemetry data for user transparency
   */
  public async exportTelemetryData(): Promise<string> {
    try {
      const cache = await this.loadCache();
      return JSON.stringify({
        sessionId: this.config.sessionId,
        totalEntries: cache.length,
        data: cache,
        privacyNote: 'This data contains only anonymous usage statistics. No personal information, file paths, or knowledge graph content is included.',
      }, null, 2);
    } catch (error) {
      return JSON.stringify({ error: 'Failed to load telemetry data' });
    }
  }

  /**
   * Reset telemetry session ID
   */
  public resetSessionId(): void {
    this.config.sessionId = this.generateSessionId();
    console.error('Telemetry session ID reset');
  }

  /**
   * Load cache from file
   */
  private async loadCache(): Promise<TelemetryData[]> {
    try {
      const data = await fs.readFile(this.config.cachePath, 'utf-8');
      return JSON.parse(data);
    } catch (error) {
      return [];
    }
  }

  /**
   * Clear all telemetry data
   */
  public async clearTelemetryData(): Promise<void> {
    try {
      await fs.unlink(this.config.cachePath);
      this.featureCounters.clear();
      console.error('Telemetry data cleared');
    } catch (error) {
      console.error('Failed to clear telemetry data:', error);
    }
  }
}
