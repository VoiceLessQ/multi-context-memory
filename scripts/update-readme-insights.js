#!/usr/bin/env node
/**
 * Safe README Insights Updater
 * Updates the main README.md with telemetry insights (local only)
 * 
 * Usage: node update-readme-insights.js --month YYYY-MM
 */

const fs = require('fs');
const path = require('path');

function loadInsightsReport(month) {
  const insightsDir = path.join(__dirname, '..', 'community-telemetry', 'insights');
  const filePath = path.join(insightsDir, `${month}-insights.md`);
  
  if (!fs.existsSync(filePath)) {
    console.error(`Error: Insights report not found for ${month}`);
    console.error(`Expected: ${filePath}`);
    process.exit(1);
  }

  return fs.readFileSync(filePath, 'utf8');
}

function updateReadmeWithInsights(month, insightsContent) {
  const readmePath = path.join(__dirname, '..', 'README.md');
  
  if (!fs.existsSync(readmePath)) {
    console.error('Error: README.md not found');
    process.exit(1);
  }

  let readme = fs.readFileSync(readmePath, 'utf8');
  
  // Extract summary statistics from insights
  const summaryMatch = insightsContent.match(/## 📈 Summary Statistics([\s\S]*?)(?=##|$)/);
  const toolUsageMatch = insightsContent.match(/## 🛠️ Tool Usage([\s\S]*?)(?=##|$)/);
  const performanceMatch = insightsContent.match(/## ⚡ Performance Metrics([\s\S]*?)(?=##|$)/);

  const summary = summaryMatch ? summaryMatch[1].trim() : '';
  const toolUsage = toolUsageMatch ? toolUsageMatch[1].trim() : '';
  const performance = performanceMatch ? performanceMatch[1].trim() : '';

  // Create telemetry section
  const telemetrySection = `## 📊 Community Telemetry Insights

*Last updated: ${new Date().toISOString()}*

> **Note:** This telemetry is collected anonymously and processed locally. No data is transmitted externally.

### ${month} Summary

${summary}

### Tool Usage

${toolUsage}

### Performance

${performance}

### Full Report
See [${month}-insights.md](./community-telemetry/insights/${month}-insights.md) for complete details.

---

`;

  // Check if telemetry section exists
  const telemetryStart = readme.indexOf('## 📊 Community Telemetry Insights');
  
  if (telemetryStart !== -1) {
    // Find end of telemetry section
    const nextSection = readme.indexOf('## ', telemetryStart + 1);
    const endPos = nextSection === -1 ? readme.length : nextSection;
    
    // Replace existing section
    readme = readme.substring(0, telemetryStart) + telemetrySection + readme.substring(endPos);
  } else {
    // Add telemetry section before the first ## section
    const firstSection = readme.indexOf('## ');
    if (firstSection !== -1) {
      readme = readme.substring(0, firstSection) + telemetrySection + readme.substring(firstSection);
    } else {
      // Add at the end
      readme += '\n\n' + telemetrySection;
    }
  }

  fs.writeFileSync(readmePath, readme);
  console.log(`✅ README.md updated with ${month} insights`);
}

function main() {
  const args = process.argv.slice(2);
  const monthIndex = args.indexOf('--month');
  
  if (monthIndex === -1 || monthIndex + 1 >= args.length) {
    console.error('Usage: node update-readme-insights.js --month YYYY-MM');
    process.exit(1);
  }

  const month = args[monthIndex + 1];
  if (!/^\d{4}-\d{2}$/.test(month)) {
    console.error('Error: Month must be in YYYY-MM format');
    process.exit(1);
  }

  console.log(`📝 Updating README.md with ${month} insights...`);
  const insights = loadInsightsReport(month);
  updateReadmeWithInsights(month, insights);
  
  console.log('\n✅ README.md updated successfully!');
  console.log('   Review the changes and commit if they look good');
}

if (require.main === module) {
  main();
}

module.exports = { updateReadmeWithInsights, loadInsightsReport };
