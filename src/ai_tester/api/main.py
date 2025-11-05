"""
FastAPI backend for AI Tester Framework.
Provides REST API and WebSocket endpoints for the web UI.
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from ai_tester.clients.jira_client import JiraClient
from ai_tester.clients.llm_client import LLMClient
from ai_tester.agents.strategic_planner import StrategicPlannerAgent
from ai_tester.agents.evaluator import EvaluationAgent
from ai_tester.agents.ticket_analyzer import TicketAnalyzerAgent
from ai_tester.core.models import TestCase, TestStep

# Initialize FastAPI app
app = FastAPI(
    title="AI Tester Framework API",
    description="Backend API for AI-powered test case and test ticket generation",
    version="3.0.0"
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global clients (will be initialized with credentials)
jira_client: Optional[JiraClient] = None
llm_client: Optional[LLMClient] = None

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_progress(self, message: dict):
        """Send progress update to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()


# ============================================================================
# Request/Response Models
# ============================================================================

class JiraCredentials(BaseModel):
    base_url: str
    email: str
    api_token: str

class TicketKey(BaseModel):
    key: str

class EpicAnalysisRequest(BaseModel):
    epic_key: str
    include_attachments: bool = True

class TestCaseGenerationRequest(BaseModel):
    ticket_key: str
    include_attachments: bool = True

class TestTicketGenerationRequest(BaseModel):
    epic_key: str
    selected_option_index: Optional[int] = None

class StrategicOption(BaseModel):
    strategy: str
    description: str
    test_tickets: List[Dict[str, Any]]
    rationale: str
    advantages: List[str]
    disadvantages: List[str]
    evaluation: Optional[Dict[str, Any]] = None

class TestCaseResponse(BaseModel):
    test_cases: List[Dict[str, Any]]
    ticket_info: Dict[str, Any]
    generated_at: str


# ============================================================================
# Authentication & Setup
# ============================================================================

@app.post("/api/auth/login")
async def login(credentials: JiraCredentials):
    """Initialize Jira and LLM clients with credentials."""
    global jira_client, llm_client

    print("\n" + "="*80)
    print("DEBUG: Login attempt starting")
    print(f"DEBUG: Base URL: {credentials.base_url}")
    print(f"DEBUG: Email: {credentials.email}")
    print(f"DEBUG: API Token length: {len(credentials.api_token)} characters")
    print(f"DEBUG: API Token starts with: {credentials.api_token[:4]}..." if credentials.api_token else "DEBUG: No API token provided")
    print("="*80 + "\n")

    try:
        print("DEBUG: Initializing JiraClient...")
        # Initialize clients
        jira_client = JiraClient(
            base_url=credentials.base_url,
            email=credentials.email,
            api_token=credentials.api_token
        )
        print("DEBUG: JiraClient initialized successfully")

        print("DEBUG: Initializing LLMClient...")
        llm_client = LLMClient()
        print("DEBUG: LLMClient initialized successfully")

        # Test connection by making a simple search request
        # This validates credentials without requiring a specific issue
        print("DEBUG: Testing Jira connection with search_jql...")
        try:
            jira_client.search_jql("", ["key"], max_results=1)
            print("DEBUG: Jira connection test successful!")
        except Exception as jql_error:
            print(f"DEBUG: Jira connection test FAILED: {str(jql_error)}")
            print(f"DEBUG: Error type: {type(jql_error).__name__}")
            raise

        print("DEBUG: Authentication successful - returning success response\n")
        return {
            "success": True,
            "message": "Successfully authenticated with Jira",
            "jira_url": credentials.base_url
        }
    except Exception as e:
        print("\n" + "="*80)
        print("DEBUG: Authentication FAILED")
        print(f"DEBUG: Exception type: {type(e).__name__}")
        print(f"DEBUG: Exception message: {str(e)}")
        print(f"DEBUG: Exception args: {e.args}")

        # Print full traceback for debugging
        import traceback
        print("DEBUG: Full traceback:")
        print(traceback.format_exc())
        print("="*80 + "\n")

        error_message = str(e).lower()

        # Parse specific error types
        if "401" in error_message or "unauthorized" in error_message:
            detail = "Invalid credentials. Please check your email and API token."
        elif "403" in error_message or "forbidden" in error_message:
            detail = "Access denied. Your account may not have permission to access this Jira instance."
        elif "404" in error_message or "not found" in error_message:
            detail = "Jira instance not found. Please verify the base URL is correct."
        elif "timeout" in error_message or "timed out" in error_message:
            detail = "Connection timeout. Please check your network connection and Jira URL."
        elif "connection" in error_message or "network" in error_message:
            detail = "Cannot connect to Jira. Please verify the base URL and your internet connection."
        elif "ssl" in error_message or "certificate" in error_message:
            detail = "SSL certificate error. Please check the Jira URL uses HTTPS."
        else:
            detail = f"Authentication failed: {str(e)}"

        print(f"DEBUG: Sending error response: {detail}\n")
        raise HTTPException(status_code=401, detail=detail)


@app.get("/api/auth/status")
async def auth_status():
    """Check if clients are initialized."""
    is_jira_initialized = jira_client is not None
    is_llm_initialized = llm_client is not None
    is_authenticated = is_jira_initialized and is_llm_initialized

    print("\n" + "-"*80)
    print("DEBUG: Auth status check")
    print(f"DEBUG: jira_client exists: {is_jira_initialized}")
    print(f"DEBUG: llm_client exists: {is_llm_initialized}")
    print(f"DEBUG: Is authenticated: {is_authenticated}")
    if jira_client:
        print(f"DEBUG: Jira base URL: {jira_client.base_url}")
    print("-"*80 + "\n")

    return {
        "authenticated": is_authenticated,
        "jira_url": jira_client.base_url if jira_client else None
    }


# ============================================================================
# Epic & Ticket Loading
# ============================================================================

@app.post("/api/epics/load")
async def load_epic(request: EpicAnalysisRequest):
    """Load Epic from Jira with all children and attachments."""
    if not jira_client:
        raise HTTPException(status_code=401, detail="Not authenticated")

    await manager.send_progress({
        "type": "progress",
        "step": "loading_epic",
        "message": f"Loading Epic {request.epic_key}..."
    })

    try:
        # Fetch Epic
        epic = jira_client.get_issue(request.epic_key)

        await manager.send_progress({
            "type": "progress",
            "step": "loading_children",
            "message": "Loading child tickets..."
        })

        # Fetch children
        children = jira_client.get_children_of_epic(request.epic_key)

        if request.include_attachments:
            await manager.send_progress({
                "type": "progress",
                "step": "loading_attachments",
                "message": "Processing attachments..."
            })

            # Process attachments for Epic and children
            # (Implementation similar to legacy app)

        await manager.send_progress({
            "type": "complete",
            "message": "Epic loaded successfully"
        })

        return {
            "epic": epic,
            "children": children,
            "child_count": len(children)
        }

    except Exception as e:
        await manager.send_progress({
            "type": "error",
            "message": str(e)
        })
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tickets/{ticket_key}")
async def get_ticket(ticket_key: str):
    """Get a single Jira ticket by key."""
    if not jira_client:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        ticket = jira_client.get_issue(ticket_key)
        return ticket
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Ticket not found: {str(e)}")


@app.post("/api/tickets/{ticket_key}/analyze")
async def analyze_ticket(ticket_key: str):
    """Analyze a ticket for test case generation readiness."""
    if not jira_client or not llm_client:
        raise HTTPException(status_code=401, detail="Not authenticated")

    await manager.send_progress({
        "type": "progress",
        "step": "loading_ticket",
        "message": f"Loading ticket {ticket_key}..."
    })

    try:
        # Load ticket
        ticket = jira_client.get_issue(ticket_key)

        await manager.send_progress({
            "type": "progress",
            "step": "analyzing",
            "message": "Analyzing ticket readiness..."
        })

        # Analyze ticket
        analyzer = TicketAnalyzerAgent(llm_client)
        assessment = await asyncio.to_thread(
            analyzer.analyze_ticket,
            ticket
        )

        await manager.send_progress({
            "type": "complete",
            "message": "Analysis complete"
        })

        return {
            "ticket_key": ticket_key,
            "assessment": assessment,
            "analyzed_at": datetime.now().isoformat()
        }

    except Exception as e:
        await manager.send_progress({
            "type": "error",
            "message": str(e)
        })
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Multi-Agent Test Ticket Generation
# ============================================================================

@app.post("/api/epics/{epic_key}/analyze")
async def analyze_epic(epic_key: str):
    """
    Use Strategic Planner to generate 3 strategic options for splitting an Epic.
    Then use Evaluator to score each option.
    """
    if not jira_client or not llm_client:
        raise HTTPException(status_code=401, detail="Not authenticated")

    await manager.send_progress({
        "type": "progress",
        "step": "loading_epic",
        "message": f"Loading Epic {epic_key}..."
    })

    try:
        # Load Epic and children
        epic = jira_client.get_issue(epic_key)
        children_raw = jira_client.get_children_of_epic(epic_key)

        await manager.send_progress({
            "type": "progress",
            "step": "strategic_planning",
            "message": "Strategic Planner is analyzing the Epic..."
        })

        # Initialize agents
        planner = StrategicPlannerAgent(llm_client)
        evaluator = EvaluationAgent(llm_client)

        # Generate strategic options
        # Build context for strategic planner
        
        # Process epic description (convert from ADF if needed)
        epic_description = epic.get('fields', {}).get('description', '')
        if isinstance(epic_description, dict):
            from ai_tester.utils.utils import adf_to_plaintext
            epic_description = adf_to_plaintext(epic_description)
        elif epic_description is None:
            epic_description = ''
        
        # Transform children to expected format and convert descriptions
        children = []
        for child in children_raw:
            fields = child.get('fields', {})
            desc = fields.get('description', '')
            
            # Convert ADF description to plaintext if needed
            if isinstance(desc, dict):
                from ai_tester.utils.utils import adf_to_plaintext
                desc = adf_to_plaintext(desc)
            elif desc is None:
                desc = ''
            
            children.append({
                'key': child.get('key', ''),
                'summary': fields.get('summary', ''),
                'desc': desc
            })
        
        epic_context = {
            'epic_key': epic.get('key'),
            'epic_summary': epic.get('fields', {}).get('summary'),
            'epic_desc': epic_description,
            'children': children
        }

        # Call the run method which internally calls propose_splits
        options, error = await asyncio.to_thread(
            planner.run,
            epic_context
        )

        if error:
            raise Exception(error)

        await manager.send_progress({
            "type": "progress",
            "step": "evaluation",
            "message": "Evaluating strategic options..."
        })

        # Evaluate each option
        evaluated_options = []
        for i, option in enumerate(options):
            eval_context = {
                'option': option,
                'epic_context': epic_context
            }

            evaluation, eval_error = await asyncio.to_thread(
                evaluator.run,
                eval_context
            )

            if eval_error:
                print(f"Warning: Failed to evaluate option {i+1}: {eval_error}")
                evaluation = {}

            option_with_eval = {
                **option,
                "evaluation": evaluation
            }
            evaluated_options.append(option_with_eval)

            await manager.send_progress({
                "type": "progress",
                "step": "evaluation",
                "message": f"Evaluated option {i+1} of {len(options)}"
            })

        await manager.send_progress({
            "type": "complete",
            "message": "Analysis complete"
        })

        return {
            "epic_key": epic_key,
            "options": evaluated_options,
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        await manager.send_progress({
            "type": "error",
            "message": str(e)
        })
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/test-tickets/generate")
async def generate_test_tickets(request: TestTicketGenerationRequest):
    """
    Generate test tickets based on selected strategic option.
    """
    if not jira_client or not llm_client:
        raise HTTPException(status_code=401, detail="Not authenticated")

    await manager.send_progress({
        "type": "progress",
        "step": "generating",
        "message": "Generating test tickets..."
    })

    try:
        # This would implement the full test ticket generation logic
        # Similar to generate_test_tickets.py but with WebSocket updates

        # For now, return placeholder
        return {
            "success": True,
            "test_tickets": [],
            "message": "Test ticket generation completed"
        }

    except Exception as e:
        await manager.send_progress({
            "type": "error",
            "message": str(e)
        })
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Test Case Generation
# ============================================================================

@app.post("/api/test-cases/generate")
async def generate_test_cases(request: TestCaseGenerationRequest):
    """Generate test cases for a Jira ticket using multi-agent workflow."""
    if not jira_client or not llm_client:
        raise HTTPException(status_code=401, detail="Not authenticated")

    await manager.send_progress({
        "type": "progress",
        "step": "loading_ticket",
        "message": f"Loading ticket {request.ticket_key}..."
    })

    try:
        # Load ticket
        ticket = jira_client.get_issue(request.ticket_key)
        fields = ticket.get("fields", {})
        summary = fields.get("summary", "")

        # Get description
        description = fields.get("description", "")
        if isinstance(description, dict):
            from ai_tester.utils.utils import adf_to_plaintext
            description = adf_to_plaintext(description)

        # Get acceptance criteria
        acceptance_criteria = ""
        for field_key, field_value in fields.items():
            if "acceptance" in field_key.lower() or "criteria" in field_key.lower():
                if isinstance(field_value, str):
                    acceptance_criteria = field_value
                elif isinstance(field_value, dict):
                    from ai_tester.utils.utils import adf_to_plaintext
                    acceptance_criteria = adf_to_plaintext(field_value)

        await manager.send_progress({
            "type": "progress",
            "step": "generating",
            "message": "AI is generating test cases (this may take 30-60 seconds)..."
        })

        # Import helper functions from generate_test_cases.py
        from ai_tester.utils.test_case_generator import critic_review, fixer, generate_test_cases_with_retry

        # Build prompts
        sys_prompt = """You are an expert QA test case designer. Your task is to analyze Jira tickets and create comprehensive, detailed test cases.

TESTING PHILOSOPHY:
For EACH requirement identified, create exactly THREE test cases:
1. One POSITIVE test (happy path)
2. One NEGATIVE test (error handling)
3. One EDGE CASE test (boundary conditions)

This ensures complete coverage with clear traceability.

REQUIRED JSON OUTPUT:
{
  "requirements": [
    {"id": "REQ-001", "description": "Clear requirement", "source": "Acceptance Criteria"}
  ],
  "test_cases": [
    {
      "requirement_id": "REQ-001",
      "requirement_desc": "Brief summary",
      "title": "REQ-001 Positive: Title",
      "priority": 1,
      "test_type": "Positive",
      "tags": ["tag1", "tag2"],
      "steps": [
        {"action": "Specific action", "expected": "Expected result"}
      ]
    }
  ]
}

MANDATORY RULES:
1. Identify ALL requirements first - be exhaustive
2. For EACH requirement, create EXACTLY 3 test cases
3. Formula: N requirements → N × 3 test cases
4. Each test case must have 3-8 detailed steps"""

        user_prompt = f"""Analyze this Jira ticket and generate comprehensive test cases:

TICKET: {request.ticket_key}
SUMMARY: {summary}

DESCRIPTION:
{description[:2000]}

ACCEPTANCE CRITERIA:
{acceptance_criteria if acceptance_criteria else "No explicit acceptance criteria provided - extract requirements from description"}

Generate test cases following the 3-per-requirement rule (Positive, Negative, Edge Case)."""

        # Generate test cases with critic review
        result, critic_data = await asyncio.to_thread(
            generate_test_cases_with_retry,
            llm=llm_client,
            sys_prompt=sys_prompt,
            user_prompt=user_prompt,
            summary=summary,
            requirements_for_review=None,
            max_retries=2
        )

        if not result:
            raise Exception("Failed to generate test cases after retries")

        requirements = result.get("requirements", [])
        test_cases_raw = result.get("test_cases", [])

        await manager.send_progress({
            "type": "complete",
            "message": f"Generated {len(test_cases_raw)} test cases successfully"
        })

        return TestCaseResponse(
            test_cases=test_cases_raw,
            ticket_info={
                "key": ticket["key"],
                "summary": summary,
                "description": description[:500],
                "requirements_count": len(requirements)
            },
            generated_at=datetime.now().isoformat()
        )

    except Exception as e:
        await manager.send_progress({
            "type": "error",
            "message": str(e)
        })
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WebSocket for Real-time Progress
# ============================================================================

@app.websocket("/ws/progress")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time progress updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Echo back for heartbeat
            await websocket.send_json({"type": "heartbeat"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ============================================================================
# Health Check
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "name": "AI Tester Framework API",
        "version": "3.0.0",
        "status": "running"
    }


@app.get("/api/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "authenticated": jira_client is not None and llm_client is not None,
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
