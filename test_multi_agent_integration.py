"""
Test Multi-Agent Integration with generate_test_tickets.py
Tests that the multi-agent workflow properly integrates without calling Jira
"""

import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ai_tester import LLMClient
from generate_test_tickets import analyze_epic_with_multi_agent

# Load environment
load_dotenv()


def create_test_epic_context():
    """Create a sample Epic context for testing."""
    return {
        'epic_key': 'UEX-17',
        'epic_summary': 'AUT Contact Us Enquiry Form',
        'epic_desc': """
        Implement a comprehensive contact us enquiry form for AUT website.
        Form should collect user information, enquiry details, and handle submissions.
        Must include validation, error handling, and confirmation screens.
        """,
        'children': [
            {
                'key': 'UEX-326',
                'summary': 'Create enquiry form UI with all required fields',
                'desc': 'Design and implement the form layout with proper styling'
            },
            {
                'key': 'UEX-327',
                'summary': 'Add form validation for all input fields',
                'desc': 'Client-side and server-side validation for email, phone, etc.'
            },
            {
                'key': 'UEX-328',
                'summary': 'Implement form submission and backend API',
                'desc': 'Create API endpoint to receive and process form submissions'
            },
            {
                'key': 'UEX-329',
                'summary': 'Add confirmation screen after successful submission',
                'desc': 'Show success message with submission reference number'
            },
            {
                'key': 'UEX-330',
                'summary': 'Implement error handling and user feedback',
                'desc': 'Handle API errors, validation errors, and network issues'
            }
        ]
    }


def test_multi_agent_workflow():
    """Test the multi-agent workflow integration."""
    print("=" * 80)
    print("TESTING MULTI-AGENT INTEGRATION")
    print("=" * 80)

    # Initialize LLM client
    llm = LLMClient(enabled=True, model=os.getenv("OPENAI_MODEL", "gpt-4o"))

    if not llm.enabled:
        print("\nError: OpenAI API key not found or invalid!")
        print("Please add OPENAI_API_KEY to your .env file")
        return False

    print(f"\nLLM Status: {llm.status_label()}")

    # Get test context
    epic_context = create_test_epic_context()

    print(f"\nEpic: {epic_context['epic_key']} - {epic_context['epic_summary']}")
    print(f"Child Tickets: {len(epic_context['children'])}")

    # Run multi-agent workflow
    print("\nRunning multi-agent workflow...")
    print("Note: Auto-selecting best option for automated testing.\n")

    split_data, error = analyze_epic_with_multi_agent(llm, epic_context, attachments_context="", auto_select_best=True)

    if error:
        print(f"\nError: {error}")
        return False

    print("\n" + "=" * 80)
    print("WORKFLOW RESULT")
    print("=" * 80)

    print(f"\nTotal Test Tickets: {split_data.get('total_test_tickets', 0)}")
    print(f"Coverage Notes: {split_data.get('coverage_notes', 'N/A')}")

    if 'strategic_analysis' in split_data:
        analysis = split_data['strategic_analysis']
        print(f"\nSelected Strategy: {analysis.get('selected_strategy', 'N/A')}")
        print(f"Overall Score: {analysis.get('overall_score', 0):.1f}/10")
        print(f"All Options Considered: {', '.join(analysis.get('all_options', []))}")

    print(f"\nRecommended Splits:")
    for i, split in enumerate(split_data.get('recommended_splits', []), 1):
        print(f"\n  {i}. {split.get('functional_area', 'Unknown')}")
        print(f"     Priority: {split.get('priority', 'N/A')}")
        print(f"     Child Tickets: {', '.join(split.get('child_tickets', []))}")
        print(f"     Est. Test Cases: {split.get('estimated_test_cases', 0)}")

    print("\n" + "=" * 80)
    print("INTEGRATION TEST PASSED!")
    print("=" * 80)

    return True


if __name__ == "__main__":
    success = test_multi_agent_workflow()
    sys.exit(0 if success else 1)
