# Quick Start Guide - AI Tester Framework UI

Get up and running in 5 minutes!

## Prerequisites
- Python 3.9+
- Node.js 18+
- Jira API token
- OpenAI API key

## Installation (One Time Only)

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install frontend dependencies
cd frontend
npm install
cd ..

# 3. Create .env file with your OpenAI key
echo "OPENAI_API_KEY=your_key_here" > .env
```

## Running the App

### Windows
```bash
start_ui.bat
```

### Mac/Linux
```bash
chmod +x start_ui.sh
./start_ui.sh
```

### Manual Start
```bash
# Terminal 1 - Backend
cd src/ai_tester/api
python -m uvicorn main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

## Access the App

Open your browser to: **http://localhost:3000**

## First Time Use

1. **Login Page**
   - Enter Jira URL: `https://your-domain.atlassian.net`
   - Enter your Jira email
   - Enter your Jira API token ([Get one here](https://id.atlassian.com/manage-profile/security/api-tokens))
   - Click "Sign In"

2. **Dashboard**
   - Choose "Epic Analysis" or "Test Generation"

3. **Epic Analysis** (Multi-Agent Feature)
   - Enter Epic key (e.g., `UEX-17`)
   - Click "Analyze Epic"
   - Wait for AI to generate 3 strategic options
   - Review scores and recommendations
   - Select an option
   - Generate test tickets

4. **Test Generation**
   - Enter ticket key (e.g., `UEX-326`)
   - Click "Generate Test Cases"
   - Review generated test cases
   - Select cases to export
   - Click "Export" to download JSON

## Key URLs

- **Frontend UI**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Stopping the App

### If using start script:
- Close both terminal windows

### If using manual start:
- Press `Ctrl+C` in both terminals

## Troubleshooting

**Can't access localhost:3000?**
- Check if frontend is running: Look for "Local: http://localhost:3000" in terminal
- Try http://127.0.0.1:3000

**Authentication fails?**
- Verify Jira API token is valid
- Check Jira URL format (must include https://)
- Ensure token has proper permissions

**Backend won't start?**
- Run: `pip install -r requirements.txt`
- Check if port 8000 is already in use

**Frontend won't start?**
- Run: `cd frontend && npm install`
- Check if port 3000 is already in use

## What's New?

This is the new **web-based UI** for AI Tester Framework v3.0.

Key improvements over legacy desktop app:
- ✅ **Multi-Agent System**: Strategic Planner + Evaluator for Epic analysis
- ✅ **Real-Time Updates**: WebSocket progress indicators
- ✅ **Modern UI**: Dark theme, responsive design
- ✅ **Web-Based**: Access from anywhere, no installation needed
- ✅ **Team-Ready**: Easy to share and collaborate

## Need Help?

- Detailed setup: See `UI_SETUP.md`
- Full overview: See `UI_OVERVIEW.md`
- API reference: Visit http://localhost:8000/docs
- Frontend docs: See `frontend/README.md`

---

**Ready to test smarter with AI?** 🚀
