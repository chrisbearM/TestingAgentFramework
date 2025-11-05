# AI Tester Framework v3.0 - Web UI Overview

## What We Built

A complete **modern web application** that replaces and enhances the legacy PySide6 desktop app with:

### 🎨 Frontend (React + Tailwind CSS)
- **Technology**: React 18, Vite, Tailwind CSS, React Router
- **Location**: `frontend/` directory
- **Key Features**:
  - Dark "Nebula" theme matching legacy app
  - Responsive, modern UI
  - Real-time progress updates via WebSocket
  - Interactive components for test cases and strategic options

### 🚀 Backend (FastAPI)
- **Technology**: FastAPI, Uvicorn, WebSockets
- **Location**: `src/ai_tester/api/main.py`
- **Key Features**:
  - RESTful API endpoints
  - WebSocket for real-time updates
  - Integration with existing framework (Jira, OpenAI, agents)
  - CORS support for frontend

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      React Frontend                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────────┐  │
│  │ Dashboard│  │  Epic    │  │  Test Case Generation    │  │
│  │          │  │ Analysis │  │                          │  │
│  └──────────┘  └──────────┘  └──────────────────────────┘  │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP REST + WebSocket
┌─────────────────────┴───────────────────────────────────────┐
│                    FastAPI Backend                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Auth         │  │ Epic/Ticket  │  │ Multi-Agent      │  │
│  │ Endpoints    │  │ Loading      │  │ Orchestration    │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
┌───────┴────────┐         ┌────────┴─────────┐
│  Jira Client   │         │  Multi-Agent     │
│  (Existing)    │         │  System (New)    │
│                │         │                  │
│  - Get Issues  │         │  - Strategic     │
│  - Get Epics   │         │    Planner       │
│  - Get Children│         │  - Evaluator     │
└────────────────┘         │  - (Future       │
                           │    agents...)    │
                           └──────────────────┘
```

## File Structure

```
ai-tester-framework/
├── src/ai_tester/
│   └── api/                        # 🆕 NEW: FastAPI backend
│       ├── __init__.py
│       └── main.py                 # API endpoints, WebSocket
│
├── frontend/                       # 🆕 NEW: React frontend
│   ├── src/
│   │   ├── api/
│   │   │   └── client.js          # Axios API client
│   │   ├── components/
│   │   │   ├── Layout.jsx         # Main app layout
│   │   │   ├── ProgressIndicator.jsx
│   │   │   ├── StrategicOptions.jsx    # Multi-agent options display
│   │   │   └── TestCaseEditor.jsx      # Test case viewer/editor
│   │   ├── context/
│   │   │   ├── AuthContext.jsx    # Authentication state
│   │   │   └── WebSocketContext.jsx    # Real-time updates
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx      # Home page
│   │   │   ├── EpicAnalysis.jsx   # Multi-agent Epic workflow
│   │   │   ├── Login.jsx          # Jira authentication
│   │   │   └── TestGeneration.jsx # Test case generation
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── README.md
│
├── requirements.txt               # ✏️ UPDATED: Added FastAPI deps
├── start_ui.bat                   # 🆕 NEW: Windows startup script
├── start_ui.sh                    # 🆕 NEW: Linux/Mac startup script
├── UI_SETUP.md                    # 🆕 NEW: Setup instructions
└── UI_OVERVIEW.md                 # 🆕 NEW: This file
```

## Key Features

### 1. Epic Analysis with Multi-Agent System 🤖

**Page**: Epic Analysis (`/epic-analysis`)

**Workflow**:
1. User enters Epic key (e.g., `UEX-17`)
2. System loads Epic from Jira
3. **Strategic Planner Agent** generates 3 strategic approaches:
   - User Journey Split
   - Technical Layer Split
   - Risk-Based Split
   - Functional Area Split
   - Test Type Split
4. **Evaluator Agent** scores each approach on:
   - Testability
   - Coverage
   - Manageability
   - Independence
   - Parallel Execution
5. User reviews options side-by-side:
   - View scores
   - Read advantages/disadvantages
   - See proposed test tickets
   - Check AI recommendations
6. User selects preferred option
7. Click "Generate Test Tickets" to create tickets

**UI Components**:
- `EpicAnalysis.jsx` - Main page
- `StrategicOptions.jsx` - Multi-agent options display
- `ProgressIndicator.jsx` - Real-time updates

### 2. Test Case Generation 📝

**Page**: Test Generation (`/test-generation`)

**Workflow**:
1. User enters ticket key (e.g., `UEX-326`)
2. System loads ticket from Jira
3. AI generates comprehensive test cases
4. User reviews test cases:
   - View test steps
   - Check preconditions
   - Review expected results
   - See test data
5. Select test cases to export
6. Export to JSON

**UI Components**:
- `TestGeneration.jsx` - Main page
- `TestCaseEditor.jsx` - Test case viewer/editor

### 3. Real-Time Progress Updates ⚡

**Technology**: WebSocket (`ws://localhost:8000/ws/progress`)

**Features**:
- Live progress updates during long operations
- Step-by-step status (loading Epic, analyzing, evaluating)
- Error notifications
- Success confirmations

**Implementation**:
- `WebSocketContext.jsx` - WebSocket connection manager
- `ProgressIndicator.jsx` - Visual progress display

### 4. Dark Theme UI 🎨

**Design System**: "Nebula" theme

**Colors**:
- Background: Dark blue-gray (`#020617`, `#0f172a`, `#1e293b`)
- Primary: Blue (`#3b82f6`)
- Accent: Cyan, purple, green for different features
- Text: Light gray gradients

**Features**:
- Soft shadows and glow effects (`shadow-nebula`)
- Rounded corners
- Smooth transitions
- Professional, modern look

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login with Jira credentials
- `GET /api/auth/status` - Check authentication status

### Epic/Ticket Operations
- `POST /api/epics/load` - Load Epic with children
- `GET /api/tickets/{key}` - Get single ticket
- `POST /api/epics/{key}/analyze` - Multi-agent Epic analysis

### Test Generation
- `POST /api/test-cases/generate` - Generate test cases
- `POST /api/test-tickets/generate` - Generate test tickets

### Real-Time
- `WS /ws/progress` - WebSocket for progress updates

### Utility
- `GET /` - Health check
- `GET /api/health` - Detailed health status

Full API docs available at: **http://localhost:8000/docs**

## Comparison: Legacy vs New UI

| Feature | Legacy (PySide6) | New (React) | Status |
|---------|------------------|-------------|--------|
| Epic Analysis | ✅ | ✅ | Enhanced |
| Test Case Generation | ✅ | ✅ | Maintained |
| Test Ticket Generation | ✅ | ✅ | Enhanced |
| Multi-Agent Strategy | ❌ | ✅ | **New!** |
| Strategic Evaluation | ❌ | ✅ | **New!** |
| Real-Time Progress | ⚠️ (QProgressDialog) | ✅ (WebSocket) | Improved |
| Dark Theme | ✅ | ✅ | Maintained |
| Attachment Processing | ✅ | 🚧 | Planned |
| Export Options | ✅ (JSON, CSV) | ⚠️ (JSON only) | In Progress |
| Deployment | Desktop only | Web-based | Improved |
| Team Collaboration | ❌ | ✅ | New! |

✅ = Fully implemented
⚠️ = Partially implemented
🚧 = Planned
❌ = Not available

## What's New in v3.0

### Multi-Agent Architecture
- **Strategic Planner**: Proposes 3 different approaches for splitting Epics
- **Evaluator**: Scores each approach on 5 quality metrics
- **Visual Comparison**: Side-by-side comparison of strategic options
- **AI Recommendations**: Highlighted recommended approach

### Real-Time Updates
- WebSocket integration for live progress
- Step-by-step status updates
- Better user feedback during long operations

### Modern Web UI
- Accessible from any device
- No installation required (just browser)
- Easy to share with team
- Cloud deployment ready

### Enhanced UX
- Cleaner, more intuitive interface
- Better visual hierarchy
- Interactive components
- Responsive design

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt
cd frontend && npm install && cd ..

# 2. Set up environment
# Create .env file with OPENAI_API_KEY

# 3. Run the app (Windows)
start_ui.bat

# OR (Linux/Mac)
chmod +x start_ui.sh
./start_ui.sh

# 4. Open browser
# http://localhost:3000
```

## Development Workflow

### Adding a New Page

1. Create page component: `frontend/src/pages/NewPage.jsx`
2. Add route in `App.jsx`
3. Add navigation link in `Layout.jsx`
4. Create API endpoint in `main.py` if needed

### Adding a New Agent

1. Implement agent in `src/ai_tester/agents/`
2. Add API endpoint in `main.py`
3. Create UI component to display agent results
4. Integrate into workflow pages

### Modifying UI Theme

Edit `frontend/tailwind.config.js`:
- Colors under `theme.extend.colors`
- Shadows under `theme.extend.boxShadow`

## Next Steps & Roadmap

### Phase 1: Core Completion (Current)
- ✅ FastAPI backend structure
- ✅ React frontend foundation
- ✅ Multi-agent Epic analysis UI
- ✅ Test case generation UI
- ✅ WebSocket real-time updates
- 🚧 Complete backend logic implementation

### Phase 2: Enhanced Features
- 🔜 Critic Agent integration
- 🔜 Refiner Agent integration
- 🔜 Attachment preview (images, PDFs)
- 🔜 Export to CSV/Azure DevOps
- 🔜 Test execution tracking

### Phase 3: Advanced Features
- 🔜 Ticket readiness assessment UI
- 🔜 Questioner Agent UI
- 🔜 Gap Analyzer visualization
- 🔜 Bulk operations
- 🔜 History/audit log

### Phase 4: Production Ready
- 🔜 User management
- 🔜 Team collaboration features
- 🔜 Performance optimization
- 🔜 Docker deployment
- 🔜 CI/CD pipeline

## Technology Choices Explained

### Why React?
- Modern, component-based architecture
- Large ecosystem and community
- Easy to maintain and extend
- Great developer experience

### Why FastAPI?
- Native async support (important for AI operations)
- Automatic API documentation
- Type hints integration (matches existing codebase)
- WebSocket support out of the box
- Fast and performant

### Why Tailwind CSS?
- Utility-first approach (fast development)
- Consistent design system
- Easy to customize
- No CSS file management
- Matches modern design trends

### Why Vite?
- Fast development server
- Modern build tool
- Better than Create React App
- Hot module replacement
- Optimized production builds

## Troubleshooting Common Issues

### Issue: Backend won't start
**Error**: `ModuleNotFoundError: No module named 'fastapi'`
**Fix**: `pip install -r requirements.txt`

### Issue: Frontend won't compile
**Error**: `Cannot find module...`
**Fix**: `cd frontend && npm install`

### Issue: CORS errors
**Error**: `Access blocked by CORS policy`
**Fix**: Ensure backend CORS settings include frontend URL

### Issue: WebSocket connection fails
**Error**: `WebSocket connection failed`
**Fix**: Check backend is running and accessible on port 8000

### Issue: Login fails
**Error**: `Authentication failed: 401`
**Fix**: Verify Jira credentials and API token permissions

## Performance Considerations

### Backend
- Use async operations for long-running tasks
- Background tasks for multi-agent processing
- Connection pooling for Jira API
- Caching for repeated requests

### Frontend
- Code splitting with React.lazy()
- Memoization for expensive components
- Virtual scrolling for long lists
- Debouncing for search inputs

### WebSocket
- Heartbeat mechanism to keep connection alive
- Automatic reconnection on disconnect
- Message batching for multiple updates

## Security Notes

### API Keys
- Never commit `.env` file
- Use environment variables
- Rotate keys regularly

### Authentication
- Jira credentials stored in backend memory only
- No persistent storage of passwords
- Session-based authentication (can be enhanced)

### CORS
- Configure allowed origins properly
- Don't use `allow_origins=["*"]` in production

## Contribution Guidelines

### Code Style
- **Python**: Follow PEP 8, use Black formatter
- **JavaScript**: Use ESLint configuration provided
- **Components**: One component per file
- **Naming**: PascalCase for components, camelCase for functions

### Git Workflow
1. Create feature branch from `main`
2. Make changes
3. Test locally
4. Create pull request
5. Review and merge

### Testing
- Backend: Add pytest tests for new endpoints
- Frontend: Add component tests (future)
- Integration: Test full workflows

## Resources

### Documentation
- FastAPI: https://fastapi.tiangolo.com/
- React: https://react.dev/
- Tailwind CSS: https://tailwindcss.com/
- Vite: https://vitejs.dev/

### Project Files
- Setup Guide: `UI_SETUP.md`
- Frontend README: `frontend/README.md`
- API Docs: http://localhost:8000/docs (when running)

### Legacy Code Reference
- Legacy App: `legacy/AI_Tester_29-10-25_ATTACHMENTS_FULL_v2.py`
- Original Functionality: Study this for feature parity

## Support

For questions or issues:
1. Check `UI_SETUP.md` for setup help
2. Review API docs at http://localhost:8000/docs
3. Check browser console for frontend errors
4. Check terminal for backend logs
5. Review this overview for architecture questions

---

**Built with ❤️ for AI-powered testing**

AI Tester Framework v3.0 - Modern, Multi-Agent, Maintainable
