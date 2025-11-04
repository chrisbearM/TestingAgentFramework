"""AI Tester Framework"""

from .core.models import (
    TestStep,
    Requirement,
    TestCase,
    GeneratedTestTicket,
    EpicContext,
    Priority
)

from .clients.jira_client import JiraClient
from .clients.llm_client import LLMClient

__version__ = "1.0.0"

__all__ = [
    'TestStep',
    'Requirement',
    'TestCase',
    'GeneratedTestTicket',
    'EpicContext',
    'Priority',
    'JiraClient',
    'LLMClient',
]