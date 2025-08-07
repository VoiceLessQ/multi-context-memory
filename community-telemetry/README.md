# 📊 Community Telemetry Program

## 🎯 Overview

This directory contains **anonymous, privacy-first telemetry data** submitted by the MCP Knowledge Graph community to help improve the project. All data is **completely anonymized** and contains **no personal information**.

## 🔐 Privacy Promise

### ✅ What We Collect
- **Anonymous usage patterns** - Which features are used most
- **Performance metrics** - Response times and error rates
- **Configuration patterns** - How people configure the system
- **System information** - Generic OS/architecture info (anonymized)

### ❌ What We NEVER Collect
- **Personal information** - No names, emails, or identifiers
- **File paths** - All paths are anonymized
- **Entity content** - No knowledge graph data
- **API keys** - No credentials or secrets
- **User queries** - No actual user input

## 📁 Directory Structure

```
community-telemetry/
├── README.md              # This file
├── 2025-08/              # Monthly telemetry data
│   ├── telemetry-1234567890.json
│   └── telemetry-1234567891.json
└── analytics/            # Processed community insights
    ├── monthly-report-2025-08.md
    └── feature-usage-trends.json
```

## 🚀 How to Contribute

### Option 1: Automatic PR Creation (Recommended)
Use the MCP tool to automatically create a telemetry PR:
```bash
# Preview what would be shared
mcp-client: preview_telemetry_data

# Create telemetry PR
mcp-client: submit_telemetry_pr --consent true
```

### Option 2: Manual Submission
1. Run your local MCP Knowledge Graph
2. Enable telemetry in settings
3. Data is automatically anonymized
4. Submit via the MCP interface

## 📊 Data Format

Each telemetry file follows this anonymized schema:

```json
{
  "metadata": {
    "timestamp": "2025-08-02T16:45:00Z",
    "sessionId": "hashed-session-id",
    "version": "1.3.0",
    "os": "linux",
    "nodeVersion": "20.11.0",
    "architecture": "x64"
  },
  "usage": {
    "toolCalls": {
      "create_entities": 15,
      "search_nodes": 8,
      "get_relations": 3
    },
    "performance": {
      "avgResponseTime": 45.2,
      "errorRate": 0.01
    }
  },
  "configuration": {
    "contextCount": 3,
    "memoryFileSize": "1-10MB",
    "featuresEnabled": ["contexts", "versioning", "ai-summaries"]
  }
}
```

## 🔍 Transparency

### View Your Data
You can always see exactly what would be shared:
```bash
mcp-client: preview_telemetry_data
```

### Opt-Out Anytime
Disable telemetry sharing at any time:
```bash
mcp-client: configure_telemetry_sharing --enableCommunityPR false
```

## 📈 Community Insights

### Monthly Reports
- **Feature adoption trends**
- **Performance benchmarks**
- **Configuration patterns**
- **Error rate analysis**

### Public Analytics
All processed insights are available in the `analytics/` directory and updated monthly via GitHub Actions.

## 🤝 Community Guidelines

### Submission Ethics
- **Voluntary participation** - No automatic collection
- **Full transparency** - See everything before submitting
- **Easy opt-out** - Disable at any time
- **No tracking** - Session-based only

### Data Usage
- **Improve the project** - Focus on feature development
- **Performance optimization** - Identify bottlenecks
- **Compatibility testing** - Ensure broad support
- **Community health** - Track adoption and satisfaction

## 🛡️ Security

### Data Protection
- **Local processing** - All anonymization happens client-side
- **No external calls** - Data goes directly to GitHub PR
- **Encrypted transmission** - HTTPS only
- **Public visibility** - All submissions are public and reviewable

### Review Process
1. **Automated validation** - Checks for PII and schema compliance
2. **Community review** - Anyone can review telemetry PRs
3. **Auto-merge** - Valid submissions are automatically merged
4. **Transparency** - All data is publicly accessible

## 📞 Support

### Questions?
- **GitHub Issues**: Tag with `telemetry` label
- **Discussions**: Use GitHub Discussions for questions
- **Documentation**: See `/docs/TELEMETRY_TECHNICAL.md`

### Reporting Issues
If you find any privacy concerns or bugs:
1. Create an issue with `telemetry` label
2. Include steps to reproduce
3. We'll investigate immediately

---

## 🔄 Updates

This program evolves based on community feedback. Check back monthly for updates and improvements!

**Last Updated**: 2025-08-02  
**Version**: 1.0.0
