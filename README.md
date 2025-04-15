# Gemini MCP Server

Model Context Protocol (MCP) server implementation that enables Claude Desktop to interact with Google's Gemini AI models.

## Features

- Full MCP protocol support
- Real-time response streaming
- Secure API key handling
- Configurable model parameters
- TypeScript implementation

## Quick Start

### Get Gemini API Key

1. Visit Google AI Studio
2. Create a new API key

### Configure Claude Desktop

Locate your config file:
- Mac: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

Add Gemini configuration:

```json
{
  "mcpServers": {
    "gemini": {
      "command": "npx",
      "args": ["-y", "github:aliargun/mcp-server-gemini"],
      "env": {
        "GEMINI_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

### Restart Claude Desktop

## Documentation

- [Claude Desktop Setup Guide](docs/setup.md) - Detailed setup instructions
- [Examples and Usage](docs/examples.md) - Usage examples and advanced configuration
- [Implementation Notes](docs/implementation.md) - Technical implementation details
- [Development Guide](docs/development.md) - Guide for developers
- [Troubleshooting Guide](docs/troubleshooting.md) - Common issues and solutions

## Local Development

```bash
# Clone repository
git clone https://github.com/aliargun/mcp-server-gemini.git
cd mcp-server-gemini

# Install dependencies
npm install

# Start development server
npm run dev
```

## Contributing

Contributions are welcome! Please see our [Contributing Guide](CONTRIBUTING.md).

## Common Issues

### Connection Issues
- Check if port 3005 is available
- Verify internet connection
- See [Troubleshooting Guide](docs/troubleshooting.md)

### API Key Problems
- Verify API key is correct
- Check permissions
- See [Setup Guide](docs/setup.md)

## Security

- API keys are handled via environment variables only
- No sensitive data is logged or stored
- Regular security updates

## License

MIT
