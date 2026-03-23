# GTM Simulator - AI-Powered Pharma Strategy Generator

**Status:** 🚧 Under Development (Week 1 of 4)

## Overview

An AI-powered system that generates complete go-to-market (GTM) strategies for pharmaceutical drugs in 2-3 minutes.

**Input:** Drug name + Indication
**Output:** Complete GTM strategy PDF with:
- Market analysis & sizing
- Competitive positioning
- Pricing recommendations
- Payer intelligence
- Sales approach per persona

## Project Structure
```
project_9_gtm_simulator/
├── src/
│   ├── core/          # Configuration, LLM init
│   ├── service/       # FastAPI backend
│   ├── agents/        # LangGraph agents
│   ├── schema/        # State schemas
│   ├── ui/            # Streamlit components
│   └── utils/         # Utilities
├── pages/             # Streamlit pages
├── .streamlit/        # Streamlit config
├── Dockerfile         # Docker
├── docker-compose.yml # Local dev
└── requirements.txt   # Dependencies
```

## Setup

### Prerequisites
- Python 3.11+
- Docker Desktop
- API Keys: ANTHROPIC_API_KEY, TAVILY_API_KEY
- Ollama (optional, for local LLM)

### Installation
```bash
cd ~/Documents/project_9_gtm_simulator
cp .env.example .env
# Edit .env with your API keys
pip install -r requirements.txt
docker-compose up
```

### Access

- Streamlit UI: http://localhost:8501
- FastAPI docs: http://localhost:8080/docs

## Development Progress

- [x] Week 1: Infrastructure & Setup
- [ ] Week 2: FastAPI backend & Tools
- [ ] Week 3: Build 6 Agents (1-4)
- [ ] Week 4: Build 6 Agents (5-6) + UI
- [ ] Week 5: Deployment & Polish

## Architecture

6 parallel LangGraph agents:
1. **Market Research** - Trial landscape, market size
2. **Payer Intelligence** - HTA precedent, reimbursement
3. **Competitor Analysis** - Competitive positioning
4. **ICP Definition** - Ideal customer profile
5. **Messaging & Positioning** - Value propositions
6. **GTM Synthesis** - Final strategy assembly

## Tech Stack

- Frontend: Streamlit 1.52.0
- Backend: FastAPI 0.115.5
- Agents: LangGraph 1.0.0
- LLM: Claude Sonnet 3.5
- Local LLM: Ollama
- PDF: ReportLab 4.1.0
- Deployment: Docker + Railway

## Author

Pranjal Das - CSO @ Pienomial
- GitHub: github.com/LifeSciForge
- LinkedIn: linkedin.com/in/pranjal-das1

## License

MIT License