#!/bin/bash

# Stock Research System - MCP Setup Script
# This script installs all required MCP servers for the project

echo "🚀 Setting up MCP servers for Stock Research System..."
echo "================================================="

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install Node.js first."
    exit 1
fi

echo "📦 Installing MCP servers globally..."

# Core MCP servers
echo "1. Installing filesystem server..."
npm install -g @modelcontextprotocol/server-filesystem

echo "2. Installing GitHub server..."
npm install -g @modelcontextprotocol/server-github

echo "3. Installing Ripgrep server..."
npm install -g @mseep/mcp-ripgrep

echo "4. Installing Playwright server..."
npm install -g @automatalabs/mcp-server-playwright

echo "5. Installing Context7 server..."
npm install -g @upstash/context7-mcp

echo "6. Installing Mermaid server..."
npm install -g @peng-shawn/mermaid-mcp-server

echo "7. Installing Sequential Thinking server..."
npm install -g @modelcontextprotocol/server-sequential-thinking

echo "8. Installing Puppeteer server..."
npm install -g @modelcontextprotocol/server-puppeteer

# Check if Python uv is installed for Python-based servers
echo "📦 Setting up Python-based MCP servers..."
if ! command -v uvx &> /dev/null; then
    echo "Installing uv for Python MCP servers..."
    python3 -m pip install --user uv
fi

# Create MCP configuration directory
MCP_CONFIG_DIR="$HOME/.cursor"
mkdir -p "$MCP_CONFIG_DIR"

echo "📝 Creating MCP configuration..."
cat > "$MCP_CONFIG_DIR/mcp.json" << 'EOF'
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/vivek/Documents/Tavily/stock-research-system", "/Users/vivek"]
    },

    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "ghp_REPLACE_WITH_YOUR_TOKEN"
      }
    },

    "ripgrep": {
      "command": "npx",
      "args": ["-y", "@mseep/mcp-ripgrep"]
    },

    "playwright": {
      "command": "npx",
      "args": ["-y", "@automatalabs/mcp-server-playwright"]
    },

    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-puppeteer"]
    },

    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"],
      "env": {
        "CONTEXT7_API_KEY": "c7_REPLACE_WITH_YOUR_KEY"
      }
    },

    "mermaid": {
      "command": "npx",
      "args": ["-y", "@peng-shawn/mermaid-mcp-server"]
    },

    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    }
  }
}
EOF

echo "✅ MCP configuration saved to $MCP_CONFIG_DIR/mcp.json"

echo ""
echo "================================================="
echo "✨ MCP Setup Complete!"
echo "================================================="
echo ""
echo "Next steps:"
echo "1. Add your API keys to ~/.cursor/mcp.json:"
echo "   - Replace ghp_REPLACE_WITH_YOUR_TOKEN with your GitHub token"
echo "   - Replace c7_REPLACE_WITH_YOUR_KEY with your Context7 API key"
echo ""
echo "2. Restart Cursor IDE"
echo ""
echo "3. Go to: Settings → MCP → Refresh"
echo ""
echo "Available MCP servers:"
echo "  ✓ filesystem - File operations"
echo "  ✓ github - Version control"
echo "  ✓ ripgrep - Fast code search"
echo "  ✓ playwright - Browser automation"
echo "  ✓ puppeteer - Alternative browser automation"
echo "  ✓ context7 - Live documentation"
echo "  ✓ mermaid - Diagram generation"
echo "  ✓ sequential-thinking - Reasoning scaffold"
echo ""
echo "For MongoDB and PostgreSQL servers, add connection strings to mcp.json"