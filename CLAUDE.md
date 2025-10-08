# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Structure

This is a Multi-Agent Stock Research System built with:
- **Backend**: FastAPI + LangGraph + Tavily API for web search
- **Frontend**: React + TypeScript with CRED-inspired design
- **Database**: MongoDB Atlas (connection string in .env)
- **AI**: OpenAI GPT-4 for agent intelligence

## Key Commands

### Backend Development
```bash
# Start backend server
cd stock-research-system/backend
python3 -m uvicorn main:app --reload --port 8000

# Run backend tests
cd stock-research-system/backend
pytest

# Test MongoDB connection
python3 test_mongo_cert.py

# Deploy to production
./deploy.sh
```

### Frontend Development
```bash
# Start frontend development server
cd stock-research-system/frontend
npm start

# Build for production
npm run build

# Run frontend tests
npm test
```

### E2E Testing
```bash
cd stock-research-system/e2e-tests
npx playwright test

# With headed mode for debugging
npx playwright test --headed
```

### Docker Compose
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

## Architecture Overview

### Agent System
The system uses LangGraph with **EnhancedStockWorkflow** orchestrating 10 expert agents:
1. **ExpertFundamentalAgent**: Financial statements and fundamentals analysis
2. **ExpertTechnicalAgent**: Chart patterns and technical indicators
3. **ExpertRiskAgent**: Risk assessment and portfolio analysis
4. **ExpertSynthesisAgent**: Combines base analysis insights
5. **TavilyNewsIntelligenceAgent**: Real-time news and intelligence (optional, requires Tavily API)
6. **TavilySentimentTrackerAgent**: Market sentiment analysis (optional, requires Tavily API)
7. **MacroContextAgent**: Macroeconomic context and trends (optional, requires Tavily API)
8. **HybridOrchestrator**: Final synthesis and recommendations
9. **ChartAnalyticsAgent**: Deep chart and pattern analysis
10. **PortfolioOptimizationAgent**: Portfolio allocation and optimization

All agents inherit from `BaseAgent` class in `backend/agents/base.py` and implement an async `execute()` method.

### Real-Time Communication (SSE + Long Polling)
The system uses **Server-Sent Events (SSE)** as the primary method for real-time updates, with **long polling** as a fallback:

**SSE Endpoints:**
- `/api/v1/analysis/{analysis_id}/stream` - Progress updates (polls MongoDB every 500ms)
- `/api/v1/analysis/{analysis_id}/cost-stream` - Cost optimization metrics
- `/api/v1/analysis/{analysis_id}/agent-dag` - Agent execution DAG visualization

**Long Polling:**
- Implemented in `backend/services/polling_service.py`
- Default timeout: 30 seconds
- Job tracking and cooperative cancellation support

**WebSocket (Legacy):**
- Still available at `/ws`, `/ws/notifications`, `/ws/analysis/{analysis_id}` for backward compatibility
- Being phased out in favor of SSE
- Used for notifications and market data subscriptions

Progress tracking includes:
- Agent execution status and progress percentage
- Intermediate results from each agent
- Error messages and failure handling
- Completion notifications with final results

### Database Schema
MongoDB collections:
- `analyses`: User queries and configurations
- `agent_executions`: Performance metrics per agent
- `analysis_results`: Final recommendations
- `users`: User profiles

### API Integration
- **Tavily API**: Web search (rate limited, use sparingly)
- **OpenAI API**: LLM operations
- MongoDB uses certifi for SSL certificates

## Critical Patterns

### Agent Development
```python
# All agents follow this pattern
class NewAgent(BaseAgent):
    async def execute(self, state: dict) -> dict:
        # 1. Send progress update
        await self.send_progress("Starting analysis...")

        # 2. Perform work
        result = await self.process_data(state)

        # 3. Save to MongoDB
        await self.save_result(result)

        # 4. Return updated state
        return {"agent_results": result}
```

### Frontend Components
- Use CRED design tokens from `src/styles/theme.ts`
- All interactive elements need `data-test` attributes
- SSE connection handling in real-time hooks with automatic reconnection
- Polling fallback for browsers without SSE support

### Frontend Features (Implemented)
The frontend currently implements:
1. **Market Overview** - Real-time market data, trending stocks, sector performance
2. **Portfolio Management** - Holdings, metrics, performance tracking, rebalancing
3. **Deep Analysis Drawer** - Comprehensive stock analysis with multi-agent insights
4. **User Profile** - Risk preferences, investment goals, portfolio configuration

**NOT Implemented:**
- AI Chatbot (backend API exists at `/api/v1/chat` but no frontend UI)

### Error Handling
- MongoDB SSL errors → Check IP whitelist in Atlas dashboard
- Agent timeouts → 60 second limit per agent
- SSE connection errors → Automatic reconnection with exponential backoff
- Long polling fallback → Activates when SSE unavailable

## Environment Configuration

Required environment variables in `backend/.env`:
```
TAVILY_API_KEY=your_key
OPENAI_API_KEY=your_key
MONGODB_URL=mongodb+srv://...
JWT_SECRET=your_secret
ENVIRONMENT=development
```

Frontend `.env`:
```
REACT_APP_API_URL=http://localhost:8000
```

## Performance Targets
- API response time: < 200ms (excluding agent processing)
- Frontend load time: < 3 seconds
- Complete analysis: < 120 seconds
- SSE polling interval: 500ms for progress updates
- Long polling timeout: 30 seconds default

## Testing Strategy
- Backend: pytest with async support (80% coverage target)
- Frontend: Jest + React Testing Library
- E2E: Playwright using data-test selectors only
- Always run tests before deploying

## Known Issues
1. MongoDB connection requires IP whitelisting in Atlas dashboard
2. Tavily API has rate limits - Redis caching implemented for optimization
3. SSE connections poll MongoDB every 500ms - may need optimization for scale
4. CORS configuration needed for cross-origin requests
5. Frontend WebSocket logic disabled to prevent infinite loops (using SSE instead)

## MCP Integration
The project is configured with MCP servers for:
- `playwright`: Browser automation
- `puppeteer`: Alternative browser control
- `filesystem`: File operations
- `memgraph`: Graph database operations

Configuration in `.mcp.json` at repository root.