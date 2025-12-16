# Agent Gamma - Data Analytics Agent

A Google ADK-style agent for data analytics domain, running on port **8002**.

## Features

- 🔌 **KEP Protocol** - Full Knowledge Exchange Protocol support
- 🔄 **Multi-Agent Integration** - Auto-registers with peer agents
- 📊 **Data Analytics Domain** - Specialized for analytics queries
- 🌐 **REST API** - Standard HTTP endpoints

## Quick Start

```bash
# Install dependencies
poetry install

# Run the agent
poetry run python main.py

# Or with uvicorn
poetry run uvicorn main:app --reload --port 8002
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check (for Orchestrator) |
| `/api/v1/chat` | POST | Chat with the agent |
| `/api/v1/kep/register` | POST | Register external agent |
| `/api/v1/kep/agents` | GET | List registered agents |
| `/api/v1/kep/request` | POST | Process KEP request |
| `/api/v1/kep/history` | GET | Get exchange history |

## Integration with Orchestrator

This agent automatically appears in the DKMES Multi-Agent Orchestrator at `http://localhost:5173/` once running.

1. Start the agent on port 8002
2. Click "Add Agent" in Orchestrator
3. Enter port `8002`
4. Agent will appear in the network graph!

## Customization

Edit `main.py` to:
- Change `AGENT_ID`, `AGENT_NAME`, `AGENT_DOMAIN`
- Add actual data analytics logic in the `chat` and `process_kep_request` endpoints
- Integrate with your data sources
