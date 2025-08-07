#!/usr/bin/env node
/**
 * Safe Telemetry Schema Validator
 * Validates telemetry data files without any external dependencies
 * 
 * Usage: node validate-telemetry-schema.js <file>
 */

const fs = require('fs');
const path = require('path');

// Telemetry schema definition
const TELEMETRY_SCHEMA = {
  type: 'object',
  required: ['version', 'timestamp', 'sessionId', 'metrics'],
  properties: {
    version: { type: 'string', pattern: '^\\d+\\.\\d+\\.\\d+$' },
    timestamp: { type: 'string', format: 'date-time' },
    sessionId: { type: 'string', pattern: '^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$' },
    metrics: {
      type: 'object',
      required: ['toolUsage', 'performance', 'configuration'],
      properties: {
        toolUsage: {
          type: 'object',
          patternProperties: {
            '^[a-zA-Z]+$': { type: 'number', minimum: 0 }
          }
        },
        performance: {
          type: 'object',
          required: ['avgResponseTime', 'errorRate'],
          properties: {
            avgResponseTime: { type: 'number', minimum: 0 },
            errorRate: { type: 'number', minimum: 0, maximum: 1 }
          }
        },
        configuration: {
          type: 'object',
          required: ['contextsEnabled', 'versioningEnabled', 'aiSummariesEnabled'],
          properties: {
            contextsEnabled: { type: 'boolean' },
            versioningEnabled: { type: 'boolean' },
            aiSummariesEnabled: { type: 'boolean' },
            contextCount: { type: 'number', minimum: 0 },
            memoryFileSize: { type: 'number', minimum: 0 }
          }
        }
      }
    },
    system: {
      type: 'object',
      required: ['os', 'nodeVersion', 'arch'],
      properties: {
        os: { type: 'string' },
        nodeVersion: { type: 'string' },
        arch: { type: 'string' }
      }
    }
  }
};

function validateSchema(data, schema, path = '') {
  const errors = [];

  if (schema.required) {
    for (const field of schema.required) {
      if (!(field in data)) {
        errors.push(`Missing required field: ${path}${field}`);
      }
    }
  }

  if (schema.properties) {
    for (const [key, value] of Object.entries(data)) {
      if (key in schema.properties) {
        const propSchema = schema.properties[key];
        const propPath = path ? `${path}.${key}` : key;
        
        if (propSchema.type && typeof value !== propSchema.type) {
          errors.push(`Type mismatch at ${propPath}: expected ${propSchema.type}, got ${typeof value}`);
        }

        if (propSchema.pattern && typeof value === 'string' && !new RegExp(propSchema.pattern).test(value)) {
          errors.push(`Pattern mismatch at ${propPath}: ${value}`);
        }

        if (propSchema.format === 'date-time' && isNaN(Date.parse(value))) {
          errors.push(`Invalid date-time format at ${propPath}: ${value}`);
        }

        if (propSchema.minimum !== undefined && value < propSchema.minimum) {
          errors.push(`Value too small at ${propPath}: ${value} < ${propSchema.minimum}`);
        }

        if (propSchema.maximum !== undefined && value > propSchema.maximum) {
          errors.push(`Value too large at ${propPath}: ${value} > ${propSchema.maximum}`);
        }

        if (propSchema.type === 'object' && typeof value === 'object' && value !== null) {
          errors.push(...validateSchema(value, propSchema, propPath + '.'));
        }
      }
    }
  }

  if (schema.patternProperties && typeof data === 'object' && data !== null) {
    for (const [key, value] of Object.entries(data)) {
      for (const [pattern, propSchema] of Object.entries(schema.patternProperties)) {
        if (new RegExp(pattern).test(key)) {
          const propPath = path ? `${path}.${key}` : key;
          errors.push(...validateSchema(value, propSchema, propPath));
        }
      }
    }
  }

  return errors;
}

function main() {
  const args = process.argv.slice(2);
  
  if (args.length === 0 || args.includes('--help') || args.includes('-h')) {
    console.log(`
Safe Telemetry Schema Validator
Usage: node validate-telemetry-schema.js <file>
       node validate-telemetry-schema.js --help

Validates telemetry JSON files against the schema without external dependencies.
    `.trim());
    process.exit(0);
  }

  const filePath = args[0];
  
  if (!fs.existsSync(filePath)) {
    console.error(`Error: File not found: ${filePath}`);
    process.exit(1);
  }

  try {
    const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
    const errors = validateSchema(data, TELEMETRY_SCHEMA);

    if (errors.length === 0) {
      console.log(`✅ Valid: ${filePath}`);
      process.exit(0);
    } else {
      console.error(`❌ Invalid: ${filePath}`);
      errors.forEach(error => console.error(`  - ${error}`));
      process.exit(1);
    }
  } catch (error) {
    console.error(`Error: Failed to parse JSON: ${error.message}`);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = { validateSchema, TELEMETRY_SCHEMA };
