#!/bin/bash

# WorldInsights MCP Setup Script
# This script installs and configures MCP servers for the project

set -e

echo "========================================"
echo "WorldInsights MCP Server Setup"
echo "========================================"
echo ""

# Check if Node.js is installed
echo "→ Checking Node.js installation..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed!"
    echo "   Please install Node.js from https://nodejs.org/"
    echo "   Or use: brew install node"
    exit 1
fi

echo "✅ Node.js found: $(node --version)"
echo "✅ npm found: $(npm --version)"
echo ""

# Check if ~/.qwen directory exists
echo "→ Checking Qwen configuration directory..."
if [ ! -d "$HOME/.qwen" ]; then
    echo "❌ ~/.qwen directory not found!"
    echo "   Please ensure Qwen is installed and configured."
    exit 1
fi

echo "✅ Qwen directory found: $HOME/.qwen"
echo ""

# Install MCP servers
echo "→ Installing MCP servers..."
echo ""

echo "   Installing @modelcontextprotocol/server-filesystem..."
npm install -g @modelcontextprotocol/server-filesystem 2>&1 | tail -2

echo "   Installing @modelcontextprotocol/server-playwright..."
npm install -g @modelcontextprotocol/server-playwright 2>&1 | tail -2

echo "   Installing @modelcontextprotocol/server-sqlite..."
npm install -g @modelcontextprotocol/server-sqlite 2>&1 | tail -2

echo ""
echo "✅ MCP servers installed successfully!"
echo ""

# Create or update global settings
echo "→ Configuring global Qwen settings..."

SETTINGS_FILE="$HOME/.qwen/settings.json"

# Backup existing settings if they exist
if [ -f "$SETTINGS_FILE" ]; then
    cp "$SETTINGS_FILE" "$SETTINGS_FILE.backup.$(date +%Y%m%d%H%M%S)"
    echo "   Backed up existing settings to $SETTINGS_FILE.backup.*"
fi

# Create new settings with MCP configuration
cat > "$SETTINGS_FILE" << 'EOF'
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/Users/achbj/Code/bonzainsights/WorldInsights"
      ],
      "enabled": true
    },
    "playwright": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-playwright"
      ],
      "enabled": true
    },
    "sqlite": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-sqlite"
      ],
      "enabled": true
    }
  },
  "permissions": {
    "filesystem": {
      "read": true,
      "write": true,
      "allowedPaths": [
        "/Users/achbj/Code/bonzainsights/WorldInsights"
      ]
    },
    "playwright": {
      "enabled": true,
      "allowBrowserAutomation": true
    },
    "sqlite": {
      "enabled": true,
      "readOnly": false
    }
  }
}
EOF

echo "✅ Global settings configured: $SETTINGS_FILE"
echo ""

# Verify installation
echo "→ Verifying MCP server installation..."
echo ""

echo "   Checking filesystem server..."
if npx -y @modelcontextprotocol/server-filesystem --version &> /dev/null; then
    echo "   ✅ Filesystem server OK"
else
    echo "   ⚠️  Filesystem server may have issues"
fi

echo "   Checking playwright server..."
if npx -y @modelcontextprotocol/server-playwright --version &> /dev/null; then
    echo "   ✅ Playwright server OK"
else
    echo "   ⚠️  Playwright server may have issues"
fi

echo "   Checking sqlite server..."
if npx -y @modelcontextprotocol/server-sqlite --version &> /dev/null; then
    echo "   ✅ SQLite server OK"
else
    echo "   ⚠️  SQLite server may have issues"
fi

echo ""
echo "========================================"
echo "✅ MCP Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Restart your Qwen/IDE"
echo "2. The MCP servers should load automatically"
echo "3. Share a screenshot to test filesystem access"
echo ""
echo "Configuration file: $SETTINGS_FILE"
echo "Project config: $(pwd)/.qwen/mcp.json"
echo ""
echo "To verify MCP is working, ask the AI to:"
echo "  - List files in the project"
echo "  - Open the homepage in browser"
echo "  - Take a screenshot"
echo ""
