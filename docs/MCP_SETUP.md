# WorldInsights - MCP Setup Guide

## Overview

This guide will help you set up Model Context Protocol (MCP) servers to give the AI assistant full visibility and control over the WorldInsights project.

---

## What is MCP?

Model Context Protocol (MCP) allows AI assistants to:
- **Read/Write files** in your project
- **Control browsers** for testing
- **Query databases** directly
- **Execute commands** safely
- **View screenshots** and images

---

## Prerequisites

```bash
# Ensure you have Node.js installed (for npx)
node --version  # Should be v16+
npm --version   # Should be v8+

# If not installed:
brew install node  # macOS
```

---

## Step 1: Install MCP Servers

Run these commands in your terminal:

```bash
# Filesystem access (view/edit files, see screenshots)
npm install -g @modelcontextprotocol/server-filesystem

# Browser automation (test frontend, take screenshots)
npm install -g @modelcontextprotocol/server-playwright

# SQLite/DuckDB access (query databases)
npm install -g @modelcontextprotocol/server-sqlite

# Optional: Puppeteer for advanced browser automation
npm install -g @modelcontextprotocol/server-puppeteer
```

---

## Step 2: Configure Global MCP Settings

Edit your global Qwen settings at `~/.qwen/settings.json`:

```bash
# Open the file
nano ~/.qwen/settings.json

# Or use your preferred editor
code ~/.qwen/settings.json
```

Add this configuration:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/Users/achbj/Code/bonzainsights/WorldInsights"
      ]
    },
    "playwright": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-playwright"]
    },
    "sqlite": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sqlite"]
    }
  }
}
```

---

## Step 3: Project Configuration (Already Done)

I've already created `.qwen/mcp.json` in your project root with:
- Filesystem access to the project directory
- Playwright for browser automation
- Proper permissions configured

---

## Step 4: Verify Installation

After configuring, restart your Qwen/IDE and verify:

1. **Check MCP servers are loaded** - You should see MCP status in your Qwen interface
2. **Test filesystem access** - Ask the AI to list files in the project
3. **Test browser automation** - Ask the AI to open the homepage

---

## What This Enables

### Filesystem Access ✅
- View any file in the project
- Read logs and debug output
- See screenshots you share
- Edit configuration files
- Create new files/folders

### Browser Automation ✅
- Open the application in browser
- Take screenshots automatically
- Test interactive features
- Verify responsive design
- Debug frontend issues

### Database Access ✅
- Query DuckDB directly
- Check data ingestion status
- Verify cached data
- Inspect user data (if any)

---

## Usage Examples

### View Screenshots

Once MCP is set up, you can share screenshots and I can:
- See the actual error/issue
- Identify the problematic component
- Suggest specific fixes

### Test Frontend

I can:
```
- Open http://localhost:5000/dashboard/builder
- Take a screenshot
- Check if chart renders correctly
- Verify responsive design
```

### Debug Issues

I can:
```
- Check application logs
- Query database for data issues
- Inspect network requests
- Verify API responses
```

---

## Troubleshooting

### MCP Servers Not Loading

```bash
# Check if servers are installed
npm list -g @modelcontextprotocol/server-filesystem

# Reinstall if needed
npm install -g @modelcontextprotocol/server-filesystem --force
```

### Permission Errors

```bash
# Fix permissions on macOS
sudo chown -R $(whoami) /Users/achbj/.qwen
```

### Path Issues

Ensure the path in `settings.json` matches your actual project path:
```json
"/Users/achbj/Code/bonzainsights/WorldInsights"
```

---

## Security Notes

- MCP servers only have access to specified directories
- Filesystem write access is restricted to the project
- Browser automation runs in your user context
- Database access is read-only by default

---

## Next Steps

1. **Install MCP servers** (Step 1)
2. **Configure global settings** (Step 2)
3. **Restart Qwen/IDE**
4. **Share a screenshot** to test

Once set up, I'll be able to:
- ✅ See your screenshots
- ✅ Control the browser for testing
- ✅ Access logs and debug info
- ✅ Query databases
- ✅ Make informed fixes

---

**Questions?** Let me know which step you're stuck on and I'll help!
