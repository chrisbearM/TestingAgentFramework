# AI Tester Framework - UI Setup Guide

This guide will help you set up and run the new web UI for the AI Tester Framework.

## Architecture Overview

```
┌─────────────────────┐
│  React Frontend     │
│  (Port 3000)        │
└──────────┬──────────┘
           │ HTTP/WebSocket
           ↓
┌─────────────────────┐
│  FastAPI Backend    │
│  (Port 8000)        │
└──────────┬──────────┘
           │
     ┌─────┴──────┐
     ↓            ↓
┌─────────┐  ┌──────────┐
│  Jira   │  │ OpenAI   │
│   API   │  │   GPT-4o │
└─────────┘  └──────────┘
```

## Prerequisites

1. **Python 3.9+** with pip
2. **Node.js 18+** with npm
3. **Jira account** with API token
4. **OpenAI API key** (GPT-4o access)

## Installation

### 1. Install Python Dependencies

```bash
# From the project root
pip install -r requirements.txt
```

This installs:
- FastAPI & Uvicorn (web server)
- WebSockets support
- Existing framework dependencies (OpenAI, Jira client, etc.)

### 2. Install Frontend Dependencies

```bash
# Navigate to frontend directory
cd frontend

# Install npm packages
npm install

# Return to project root
cd ..
```

## Configuration

### 1. Environment Variables

Create a `.env` file in the project root:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Jira credentials (can also be entered via UI)
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your.email@company.com
JIRA_API_TOKEN=your_jira_api_token
```

### 2. Get API Keys

**Jira API Token:**
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Create new API token
3. Copy and save the token

**OpenAI API Key:**
1. Go to https://platform.openai.com/api-keys
2. Create new API key
3. Ensure you have GPT-4o access

## Running the Application

### Option 1: Run Both Servers Separately (Development)

**Terminal 1 - Backend:**
```bash
# From project root
cd src/ai_tester/api
python -m uvicorn main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
# From project root
cd frontend
npm run dev
```

Then open your browser to: **http://localhost:3000**

### Option 2: Startup Script (Recommended)

Create a startup script to run both servers:

**Windows (`start_ui.bat`):**
```batch
@echo off
echo Starting AI Tester Framework UI...

start cmd /k "cd src\ai_tester\api && python -m uvicorn main:app --reload --port 8000"
timeout /t 3
start cmd /k "cd frontend && npm run dev"

echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
```

**Linux/Mac (`start_ui.sh`):**
```bash
#!/bin/bash
echo "Starting AI Tester Framework UI..."

# Start backend
cd src/ai_tester/api
python -m uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start frontend
cd ../../../frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
```

Then run:
```bash
# Windows
start_ui.bat

# Linux/Mac
chmod +x start_ui.sh
./start_ui.sh
```

## Using the Application

### 1. Login

1. Open http://localhost:3000
2. Enter your Jira credentials:
   - Base URL: `https://your-domain.atlassian.net`
   - Email: Your Jira email
   - API Token: Your Jira API token
3. Click "Sign In"

### 2. Epic Analysis (Multi-Agent Workflow)

1. Navigate to **Epic Analysis**
2. Enter an Epic key (e.g., `UEX-17`)
3. Click **Analyze Epic**
4. Wait for multi-agent analysis:
   - Strategic Planner generates 3 approaches
   - Evaluator scores each approach
5. Review the strategic options:
   - View scores, advantages, disadvantages
   - See proposed test tickets
   - Compare evaluation metrics
6. Select your preferred option
7. Click **Generate Test Tickets**

### 3. Test Case Generation

1. Navigate to **Test Generation**
2. Enter a ticket key (e.g., `UEX-326`)
3. Click **Generate Test Cases**
4. Review generated test cases:
   - View test steps
   - Check preconditions
   - Review expected results
5. Select test cases to export
6. Click **Export** to download JSON

## Features

### Multi-Agent System

The new UI integrates with the multi-agent architecture:

- **Strategic Planner**: Analyzes Epics and proposes 3 strategic approaches
- **Evaluator**: Scores each approach on quality metrics
- **Visual Comparison**: Side-by-side comparison of strategies

### Real-Time Progress

WebSocket integration provides live updates:
- Epic loading progress
- Strategic planning status
- Test case generation progress

### Dark Theme

Professional "Nebula" theme matching the legacy desktop app:
- Dark blue/gray color scheme
- Primary blue accent (#3B82F6)
- Soft shadows and glow effects

## Troubleshooting

### Backend won't start

**Error**: `ModuleNotFoundError: No module named 'fastapi'`

**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

### Frontend won't start

**Error**: `Cannot find module...`

**Solution**: Install npm packages
```bash
cd frontend
npm install
```

### CORS errors

**Error**: `Access to XMLHttpRequest blocked by CORS policy`

**Solution**: Ensure backend is running on port 8000 and frontend on port 3000

### WebSocket connection fails

**Error**: `WebSocket connection failed`

**Solution**:
1. Check backend is running
2. Check WebSocket endpoint is accessible: `ws://localhost:8000/ws/progress`
3. Disable browser extensions that might block WebSockets

### Authentication fails

**Error**: `Authentication failed: 401 Unauthorized`

**Solution**:
1. Verify Jira credentials are correct
2. Check API token has proper permissions
3. Ensure Jira base URL is correct format: `https://domain.atlassian.net`

## API Documentation

Once the backend is running, visit:

**http://localhost:8000/docs** - Interactive API documentation (Swagger UI)

## Production Deployment

### Build Frontend

```bash
cd frontend
npm run build
```

This creates a `frontend/dist` folder with optimized static files.

### Serve with FastAPI

Modify `src/ai_tester/api/main.py` to serve static files:

```python
from fastapi.staticfiles import StaticFiles

# Add after CORS middleware
app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")
```

Then run:
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Access at: **http://localhost:8000**

### Docker Deployment (Optional)

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Build frontend
RUN cd frontend && npm install && npm run build

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "src.ai_tester.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t ai-tester-ui .
docker run -p 8000:8000 -e OPENAI_API_KEY=your_key ai-tester-ui
```

## Migration from Legacy App

The new UI replicates key features from the legacy PySide6 desktop app:

| Legacy Feature | New UI Location |
|----------------|-----------------|
| Epic Analysis | Epic Analysis page |
| Test Case Generation | Test Generation page |
| Strategic Planning (new) | Epic Analysis → Multi-agent options |
| Test Ticket Generation | Epic Analysis → Generate tickets |
| Dark Theme | Built-in (Nebula theme) |

## Next Steps

1. **Implement remaining backend logic**: Complete the TODO sections in `src/ai_tester/api/main.py`
2. **Add more agents**: Integrate Critic, Refiner agents into UI
3. **Export formats**: Add CSV, Azure DevOps export options
4. **Attachment handling**: Add image/PDF preview in UI
5. **Test execution**: Add test execution tracking features

## Support

For issues or questions:
- Check GitHub issues
- Review API docs at http://localhost:8000/docs
- Check browser console for frontend errors
- Check terminal logs for backend errors
