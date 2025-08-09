# 🛡️ Privacy-First Telemetry Policy

## Overview

The Enhanced MCP Knowledge Graph includes **optional, privacy-first telemetry** to help improve the server for the community while maintaining complete user privacy. This document outlines exactly what we collect, what we never collect, and how you maintain full control over your data.

## 🎯 What We Collect (Anonymous Only)

### Session Data
- **Anonymous Session ID**: Ephemeral UUID regenerated per session
- **System Fingerprint**: Hashed combination of OS type, Node.js version, and architecture
- **Feature Flags**: Which features are enabled (contexts, versioning, AI summaries)

### Usage Metrics
- **Tool Usage Counts**: Counters for each tool usage (no content)
- **Performance Metrics**: Response times and error rates
- **Configuration Patterns**: Anonymized ranges for context count and memory file sizes

### System Information
- **Operating System Type**: Windows, macOS, Linux (hashed)
- **Node.js Version**: Major version only (hashed)
- **Architecture**: x64, ARM64, etc. (hashed)

## 🚫 What We NEVER Collect

### Personal Information
- ❌ Names, emails, or any personal identifiers
- ❌ Knowledge graph content, entities, relations, or observations
- ❌ File paths, directory structures, or project names
- ❌ API keys, credentials, or client configurations
- ❌ IP addresses, hostnames, or network data
- ❌ User queries, AI interactions, or conversation content

### Sensitive Data
- ❌ Source code, file contents, or project data
- ❌ Environment variables or system configuration
- ❌ Browser history or application usage
- ❌ Any data that could identify you or your projects

## 🔐 Privacy Controls

### Multiple Opt-out Methods

1. **Environment Variable** (Recommended)
   ```bash
   export MCP_KG_NO_TELEMETRY=1
   ```

2. **Configuration File**
   ```json
   {
     "telemetry": {
       "enabled": false
     }
   }
   ```

3. **CLI Flag**
   ```bash
   npx mcp-knowledge-graph --no-telemetry
   ```

4. **Runtime API**
   - Use the `view_privacy_settings()` tool
   - Call `disable_telemetry()` programmatically

5. **Auto-detection**
   - Automatically disabled in development environments
   - Disabled when `NODE_ENV=development`

### Runtime Control

```javascript
// Check current status
const status = await get_telemetry_status();

// Export your data for transparency
const data = await export_telemetry_data();

// Reset your anonymous ID
await reset_telemetry_id();

// Configure privacy settings
await view_privacy_settings();
```

## 🏠 Local Processing Only

### Zero External Communication
- **No network calls** - All processing happens locally
- **No data transmission** - Nothing is sent to external servers
- **No cloud storage** - All data remains on your machine
- **No third-party services** - Complete independence

### Client-Side Aggregation
- **Real-time anonymization** - Data is hashed before storage
- **Local cache only** - 30-day retention, then auto-deletion
- **Differential privacy** - Noise added to prevent fingerprinting
- **Transparent processing** - You can see exactly how data is processed

## 📊 Data Lifecycle

### Collection
- **Ephemeral sessions** - Data tied to current session only
- **Minimal collection** - Only essential metrics
- **Immediate anonymization** - No raw data storage

### Processing
- **Real-time aggregation** - Data processed immediately
- **Hash-based anonymization** - All identifiers are hashed
- **Noise injection** - Differential privacy techniques

### Storage
- **Local cache** - Stored only on your machine
- **30-day retention** - Automatic cleanup
- **Encrypted storage** - Local encryption at rest
- **User control** - You can delete at any time

### Deletion
- **Auto-cleanup** - Automatic deletion after 30 days
- **Manual deletion** - Use `reset_telemetry_id()` anytime
- **Complete removal** - No residual data left behind

## 🔍 Transparency Tools

### View Your Data
```bash
# Export anonymized telemetry data
npx mcp-knowledge-graph export-telemetry

# View privacy settings interactively
npx mcp-knowledge-graph privacy-settings
```

### Audit Capabilities
- **Complete transparency** - See exactly what's collected
- **Data export** - Download your anonymized data
- **Privacy dashboard** - Interactive configuration
- **Audit logs** - Track what telemetry has been collected

## 🛡️ Security Measures

### Data Protection
- **Hash-based anonymization** - SHA-256 hashing of all identifiers
- **Differential privacy** - Mathematical privacy guarantees
- **Local encryption** - AES-256 encryption for cached data
- **Secure deletion** - Cryptographic erasure on cleanup

### Privacy Guarantees
- **Zero-knowledge design** - Server never sees raw data
- **No persistent identifiers** - Session-based IDs only
- **Aggregated insights** - Individual data never exposed
- **User sovereignty** - Complete user control over data

## 🎯 Community Benefits

### How Telemetry Helps
- **Feature prioritization** - Focus on most-used features
- **Performance optimization** - Target real bottlenecks
- **Compatibility improvements** - Ensure support across environments
- **Bug detection** - Identify and fix issues faster
- **Community insights** - Understand usage patterns

### Anonymous Aggregation
- **Community health metrics** - Overall project health
- **Feature adoption rates** - Which features are valuable
- **Performance benchmarks** - Across different environments
- **Compatibility matrix** - Ensure broad support

## 🚨 Privacy Violations

### Zero Tolerance Policy
- **No personal data collection** - Ever
- **No content analysis** - Never
- **No tracking** - Session-based only
- **No third-party sharing** - Complete isolation

### Immediate Response
- **Instant disable** - Any privacy concern = telemetry disabled
- **Full transparency** - Immediate disclosure of any issues
- **User notification** - Alert users to any changes
- **Community oversight** - Open source for verification

## 📋 Compliance

### Standards Adherence
- **GDPR compliant** - Right to be forgotten, data portability
- **CCPA compliant** - California privacy rights
- **Privacy by design** - Built-in privacy protections
- **Minimal data** - Data minimization principles

### Open Source Verification
- **Public codebase** - Full transparency
- **Community audit** - Open for inspection
- **No hidden telemetry** - Everything is visible
- **Fork-friendly** - Easy to remove telemetry entirely

## 🆘 Getting Help

### Privacy Support
- **GitHub Issues** - Report privacy concerns
- **Documentation** - Comprehensive privacy guides
- **Community** - Open source community support
- **Transparency** - All decisions made in public

### Contact
- **Issues**: [GitHub Issues](https://github.com/VoiceLessQ/mcp-knowledge-graph/issues)
- **Discussions**: [GitHub Discussions](https://github.com/VoiceLessQ/mcp-knowledge-graph/discussions)
- **Email**: Privacy concerns can be raised via GitHub

## 🔄 Updates to This Policy

### Version Control
- **Public changelog** - All policy changes documented
- **Community review** - Changes discussed openly
- **User notification** - Notified of significant changes
- **Backward compatibility** - No retroactive changes

### Current Version
- **Policy Version**: 1.0.0
- **Last Updated**: 2025-08-02
- **Effective Date**: 2025-08-02

---

## 📝 Summary

**The Enhanced MCP Knowledge Graph telemetry system is designed with privacy as the primary concern. We collect only anonymous, aggregated usage statistics to improve the project for everyone, while giving you complete control over your data. You can opt out at any time using multiple methods, and all processing happens locally on your machine.**

**Your privacy is not just respected—it's built into the foundation of this system.**
