# AI Tester Framework - Frontend

Modern React-based web UI for the AI Tester Framework v3.0.

## Features

- **Epic Analysis**: Load Epics and generate test tickets using multi-agent AI
  - Strategic Planner proposes 3 different approaches
  - Evaluator scores each approach
  - Visual comparison of strategic options

- **Test Generation**: Generate comprehensive test cases from Jira tickets
  - AI-powered test case generation
  - Interactive test case editor
  - Export to JSON

- **Real-time Updates**: WebSocket integration for live progress updates

- **Dark Theme**: Professional "Nebula" dark theme matching legacy app

## Tech Stack

- **React 18** - UI framework
- **Vite** - Build tool & dev server
- **Tailwind CSS** - Styling
- **React Router** - Navigation
- **Axios** - API client
- **Lucide React** - Icons

## Getting Started

### Prerequisites

- Node.js 18+ and npm

### Installation

```bash
# Install dependencies
npm install
```

### Development

```bash
# Start dev server (runs on http://localhost:3000)
npm run dev
```

The frontend expects the backend API to be running on `http://localhost:8000`.

### Build for Production

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── api/
│   │   └── client.js          # Axios API client
│   ├── components/
│   │   ├── Layout.jsx          # Main layout with sidebar
│   │   ├── ProgressIndicator.jsx
│   │   ├── StrategicOptions.jsx # Multi-agent strategic options
│   │   └── TestCaseEditor.jsx   # Test case viewer/editor
│   ├── context/
│   │   ├── AuthContext.jsx     # Authentication state
│   │   └── WebSocketContext.jsx # WebSocket connection
│   ├── pages/
│   │   ├── Dashboard.jsx       # Home page
│   │   ├── EpicAnalysis.jsx    # Epic analysis workflow
│   │   ├── Login.jsx           # Login page
│   │   └── TestGeneration.jsx  # Test case generation
│   ├── App.jsx                 # Main app component
│   ├── main.jsx               # Entry point
│   └── index.css              # Global styles
├── index.html
├── vite.config.js
├── tailwind.config.js
└── package.json
```

## Environment Variables

Create a `.env` file for custom configuration:

```env
VITE_API_URL=http://localhost:8000
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## API Integration

The frontend communicates with the FastAPI backend via:

- **REST API** (`/api/*`) - Standard CRUD operations
- **WebSocket** (`/ws/progress`) - Real-time progress updates

### Key API Endpoints

- `POST /api/auth/login` - Authenticate with Jira credentials
- `POST /api/epics/load` - Load Epic from Jira
- `POST /api/epics/{key}/analyze` - Multi-agent Epic analysis
- `POST /api/test-cases/generate` - Generate test cases
- `WS /ws/progress` - Real-time progress updates
