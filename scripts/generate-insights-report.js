#!/usr/bin/env node
/**
 * Safe Insights Report Generator
 * Generates human-readable insights from aggregated telemetry data
 * 
 * Usage: node generate-insights-report.js --month YYYY-MM
 */

const fs = require('fs');
const path = require('path');

function loadAggregatedData(month) {
  const analyticsDir = path.join(__dirname, '..', 'community-telemetry', 'analytics');
  const filePath = path.join(analyticsDir, `${month}-aggregated.json`);
  
  if (!fs.existsSync(filePath)) {
    console.error(`Error: Aggregated data not found for ${month}`);
    console.error(`Expected: ${filePath}`);
    process.exit(1);
  }

  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

function generateMarkdownReport(month, data) {
  const date = new Date(month + '-01');
  const monthName = date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  
  const report = `# 📊 MCP Knowledge Graph - Community Insights Report
**Month:** ${monthName} (${month})

## 📈 Summary Statistics

- **Total Submissions:** ${data.totalSubmissions}
- **Date Range:** ${data.dateRange.start?.split('T')[0]} to ${data.dateRange.end?.split('T')[0]}

## 🛠️ Tool Usage

| Tool | Usage Count |
|------|-------------|
${Object.entries(data.metrics.toolUsage)
  .sort(([,a], [,b]) => b - a)
  .map(([tool, count]) => `| ${tool} | ${count.toLocaleString()} |`)
  .join('\n')}

## ⚡ Performance Metrics

| Metric | Average | Unit |
|--------|---------|------|
| Response Time | ${data.metrics.performance.avgResponseTime.toFixed(2)} | ms |
| Error Rate | ${(data.metrics.performance.errorRate * 100).toFixed(2)} | % |

## ⚙️ Configuration Patterns

| Feature | Enabled | Percentage |
|---------|---------|------------|
| Contexts | ${data.metrics.configuration.contextsEnabled}/${data.totalSubmissions} | ${((data.metrics.configuration.contextsEnabled / data.totalSubmissions) * 100).toFixed(1)}% |
| Versioning | ${data.metrics.configuration.versioningEnabled}/${data.totalSubmissions} | ${((data.metrics.configuration.versioningEnabled / data.totalSubmissions) * 100).toFixed(1)}% |
| AI Summaries | ${data.metrics.configuration.aiSummariesEnabled}/${data.totalSubmissions} | ${((data.metrics.configuration.aiSummariesEnabled / data.totalSubmissions) * 100).toFixed(1)}% |

### Configuration Averages
- **Average Context Count:** ${data.metrics.configuration.contextCount.toFixed(1)}
- **Average Memory File Size:** ${(data.metrics.configuration.memoryFileSize / 1024 / 1024).toFixed(2)} MB

## 🖥️ System Distribution

### Operating Systems
${Object.entries(data.system.os)
  .sort(([,a], [,b]) => b - a)
  .map(([os, count]) => `- **${os}:** ${count} (${((count / data.totalSubmissions) * 100).toFixed(1)}%)`)
  .join('\n')}

### Node.js Versions
${Object.entries(data.system.nodeVersion)
  .sort(([,a], [,b]) => b - a)
  .map(([version, count]) => `- **${version}:** ${count} (${((count / data.totalSubmissions) * 100).toFixed(1)}%)`)
  .join('\n')}

### Architectures
${Object.entries(data.system.arch)
  .sort(([,a], [,b]) => b - a)
  .map(([arch, count]) => `- **${arch}:** ${count} (${((count / data.totalSubmissions) * 100).toFixed(1)}%)`)
  .join('\n')}

## 📊 Raw Data Summary

<details>
<summary>Click to expand submission details</summary>

| File | Timestamp | Session ID |
|------|-----------|------------|
${data.submissions.map(sub => `| ${sub.file} | ${sub.timestamp} | ${sub.sessionId.substring(0, 8)}... |`).join('\n')}

</details>

---

*Generated on ${new Date().toISOString()} using safe local processing only*
*No external API calls or data transmission occurred*
`;

  return report;
}

function saveReport(month, content) {
  const insightsDir = path.join(__dirname, '..', 'community-telemetry', 'insights');
  if (!fs.existsSync(insightsDir)) {
    fs.mkdirSync(insightsDir, { recursive: true });
  }

  const outputFile = path.join(insightsDir, `${month}-insights.md`);
  fs.writeFileSync(outputFile, content);
  
  console.log(`✅ Insights report saved to: ${outputFile}`);
  return outputFile;
}

function main() {
  const args = process.argv.slice(2);
  const monthIndex = args.indexOf('--month');
  
  if (monthIndex === -1 || monthIndex + 1 >= args.length) {
    console.error('Usage: node generate-insights-report.js --month YYYY-MM');
    process.exit(1);
  }

  const month = args[monthIndex + 1];
  if (!/^\d{4}-\d{2}$/.test(month)) {
    console.error('Error: Month must be in YYYY-MM format');
    process.exit(1);
  }

  console.log(`📊 Generating insights report for ${month}...`);
  const data = loadAggregatedData(month);
  const report = generateMarkdownReport(month, data);
  
  const outputFile = saveReport(month, report);
  
  console.log('\n🎉 Report generated successfully!');
  console.log(`   View: ${outputFile}`);
  console.log(`   Preview: Open ${outputFile} in your markdown viewer`);
}

if (require.main === module) {
  main();
}

module.exports = { generateMarkdownReport, loadAggregatedData };
