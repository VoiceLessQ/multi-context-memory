#!/usr/bin/env node
/**
 * Safe Telemetry Aggregator
 * Aggregates telemetry data locally without external dependencies
 * 
 * Usage: node aggregate-telemetry.js --month YYYY-MM
 */

const fs = require('fs');
const path = require('path');

function findTelemetryFiles(month) {
  const submissionsDir = path.join(__dirname, '..', 'community-telemetry', 'submissions');
  const files = [];
  
  if (!fs.existsSync(submissionsDir)) {
    return files;
  }

  const yearMonth = month.replace('-', path.sep);
  const monthDir = path.join(submissionsDir, yearMonth);
  
  if (fs.existsSync(monthDir)) {
    const entries = fs.readdirSync(monthDir, { withFileTypes: true });
    for (const entry of entries) {
      if (entry.isFile() && entry.name.endsWith('.json')) {
        files.push(path.join(monthDir, entry.name));
      }
    }
  }

  return files;
}

function aggregateTelemetry(files) {
  const aggregated = {
    totalSubmissions: 0,
    dateRange: { start: null, end: null },
    metrics: {
      toolUsage: {},
      performance: {
        avgResponseTime: [],
        errorRate: []
      },
      configuration: {
        contextsEnabled: 0,
        versioningEnabled: 0,
        aiSummariesEnabled: 0,
        contextCount: [],
        memoryFileSize: []
      }
    },
    system: {
      os: {},
      nodeVersion: {},
      arch: {}
    },
    submissions: []
  };

  for (const file of files) {
    try {
      const data = JSON.parse(fs.readFileSync(file, 'utf8'));
      
      // Basic validation
      if (!data.version || !data.timestamp || !data.metrics) {
        console.warn(`Skipping invalid file: ${file}`);
        continue;
      }

      aggregated.totalSubmissions++;
      aggregated.submissions.push({
        file: path.basename(file),
        timestamp: data.timestamp,
        sessionId: data.sessionId
      });

      // Update date range
      const timestamp = new Date(data.timestamp);
      if (!aggregated.dateRange.start || timestamp < new Date(aggregated.dateRange.start)) {
        aggregated.dateRange.start = data.timestamp;
      }
      if (!aggregated.dateRange.end || timestamp > new Date(aggregated.dateRange.end)) {
        aggregated.dateRange.end = data.timestamp;
      }

      // Aggregate tool usage
      if (data.metrics.toolUsage) {
        for (const [tool, count] of Object.entries(data.metrics.toolUsage)) {
          aggregated.metrics.toolUsage[tool] = (aggregated.metrics.toolUsage[tool] || 0) + count;
        }
      }

      // Aggregate performance
      if (data.metrics.performance) {
        if (typeof data.metrics.performance.avgResponseTime === 'number') {
          aggregated.metrics.performance.avgResponseTime.push(data.metrics.performance.avgResponseTime);
        }
        if (typeof data.metrics.performance.errorRate === 'number') {
          aggregated.metrics.performance.errorRate.push(data.metrics.performance.errorRate);
        }
      }

      // Aggregate configuration
      if (data.metrics.configuration) {
        const config = data.metrics.configuration;
        if (config.contextsEnabled) aggregated.metrics.configuration.contextsEnabled++;
        if (config.versioningEnabled) aggregated.metrics.configuration.versioningEnabled++;
        if (config.aiSummariesEnabled) aggregated.metrics.configuration.aiSummariesEnabled++;
        if (typeof config.contextCount === 'number') {
          aggregated.metrics.configuration.contextCount.push(config.contextCount);
        }
        if (typeof config.memoryFileSize === 'number') {
          aggregated.metrics.configuration.memoryFileSize.push(config.memoryFileSize);
        }
      }

      // Aggregate system info
      if (data.system) {
        const system = data.system;
        aggregated.system.os[system.os] = (aggregated.system.os[system.os] || 0) + 1;
        aggregated.system.nodeVersion[system.nodeVersion] = (aggregated.system.nodeVersion[system.nodeVersion] || 0) + 1;
        aggregated.system.arch[system.arch] = (aggregated.system.arch[system.arch] || 0) + 1;
      }

    } catch (error) {
      console.warn(`Error processing ${file}: ${error.message}`);
    }
  }

  // Calculate averages
  const calculateAverage = (arr) => arr.length > 0 ? arr.reduce((a, b) => a + b, 0) / arr.length : 0;
  
  aggregated.metrics.performance.avgResponseTime = calculateAverage(aggregated.metrics.performance.avgResponseTime);
  aggregated.metrics.performance.errorRate = calculateAverage(aggregated.metrics.performance.errorRate);
  aggregated.metrics.configuration.contextCount = calculateAverage(aggregated.metrics.configuration.contextCount);
  aggregated.metrics.configuration.memoryFileSize = calculateAverage(aggregated.metrics.configuration.memoryFileSize);

  return aggregated;
}

function saveAggregatedData(month, data) {
  const analyticsDir = path.join(__dirname, '..', 'community-telemetry', 'analytics');
  if (!fs.existsSync(analyticsDir)) {
    fs.mkdirSync(analyticsDir, { recursive: true });
  }

  const outputFile = path.join(analyticsDir, `${month}-aggregated.json`);
  fs.writeFileSync(outputFile, JSON.stringify(data, null, 2));
  
  console.log(`✅ Aggregated data saved to: ${outputFile}`);
  return outputFile;
}

function main() {
  const args = process.argv.slice(2);
  const monthIndex = args.indexOf('--month');
  
  if (monthIndex === -1 || monthIndex + 1 >= args.length) {
    console.error('Usage: node aggregate-telemetry.js --month YYYY-MM');
    process.exit(1);
  }

  const month = args[monthIndex + 1];
  if (!/^\d{4}-\d{2}$/.test(month)) {
    console.error('Error: Month must be in YYYY-MM format');
    process.exit(1);
  }

  console.log(`🔍 Finding telemetry files for ${month}...`);
  const files = findTelemetryFiles(month);
  
  if (files.length === 0) {
    console.log(`No telemetry files found for ${month}`);
    return;
  }

  console.log(`📊 Processing ${files.length} files...`);
  const aggregated = aggregateTelemetry(files);
  
  saveAggregatedData(month, aggregated);
  
  console.log('\n📈 Summary:');
  console.log(`   Total submissions: ${aggregated.totalSubmissions}`);
  console.log(`   Date range: ${aggregated.dateRange.start} to ${aggregated.dateRange.end}`);
  console.log(`   Average response time: ${aggregated.metrics.performance.avgResponseTime.toFixed(2)}ms`);
  console.log(`   Average error rate: ${(aggregated.metrics.performance.errorRate * 100).toFixed(2)}%`);
}

if (require.main === module) {
  main();
}

module.exports = { findTelemetryFiles, aggregateTelemetry, saveAggregatedData };
