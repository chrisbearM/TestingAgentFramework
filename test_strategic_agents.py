"""
Test Script for Strategic Planner and Evaluation Agents
Tests the first part of Phase 1 multi-agent implementation
"""

import os
import json
from dotenv import load_dotenv
from ai_tester import JiraClient, LLMClient
from ai_tester.agents import StrategicPlannerAgent, EvaluationAgent

# Load environment
load_dotenv()


def create_test_epic_context():
    """
    Create a sample Epic context for testing.
    In real usage, this would come from Jira.
    """
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


def test_strategic_planner():
    """Test the Strategic Planner Agent"""
    print("=" * 80)
    print("TESTING STRATEGIC PLANNER AGENT")
    print("=" * 80)

    # Initialize LLM client
    llm = LLMClient(
        enabled=True,
        model=os.getenv("OPENAI_MODEL", "gpt-4o")
    )

    # Create agent
    planner = StrategicPlannerAgent(llm)

    # Get test context
    epic_context = create_test_epic_context()

    print(f"\nEpic: {epic_context['epic_key']} - {epic_context['epic_summary']}")
    print(f"   Child Tickets: {len(epic_context['children'])}")

    # Generate split options
    print("\nGenerating strategic split options...")
    options, error = planner.propose_splits(epic_context)

    if error:
        print(f"\nError: {error}")
        return None

    print(f"\nGenerated {len(options)} strategic options\n")

    # Display options
    for i, option in enumerate(options, 1):
        print(f"\n{'=' * 80}")
        print(f"OPTION {i}: {option['name']}")
        print(f"{'=' * 80}")
        print(f"\nRationale:")
        print(f"   {option['rationale']}")

        print(f"\nAdvantages:")
        for adv in option['advantages']:
            print(f"   - {adv}")

        print(f"\nDisadvantages:")
        for dis in option['disadvantages']:
            print(f"   - {dis}")

        print(f"\nProposed Test Tickets ({len(option['tickets'])}):")
        for j, ticket in enumerate(option['tickets'], 1):
            print(f"\n   Ticket {j}: {ticket['title']}")
            print(f"   Priority: {ticket['priority']}")
            print(f"   Scope: {ticket['scope']}")
            print(f"   Est. Test Cases: {ticket['estimated_test_cases']}")
            print(f"   Focus: {', '.join(ticket['focus_areas'])}")

    return options


def test_evaluator(options):
    """Test the Evaluation Agent"""
    print("\n" + "=" * 80)
    print("TESTING EVALUATION AGENT")
    print("=" * 80)

    if not options:
        print("\nSkipping evaluation - no options to evaluate")
        return

    # Initialize LLM client
    llm = LLMClient(
        enabled=True,
        model=os.getenv("OPENAI_MODEL", "gpt-4o")
    )

    # Create agent
    evaluator = EvaluationAgent(llm)

    # Get test context
    epic_context = create_test_epic_context()

    # Evaluate each option
    for i, option in enumerate(options, 1):
        print(f"\n{'=' * 80}")
        print(f"EVALUATING OPTION {i}: {option['name']}")
        print(f"{'=' * 80}")

        print("\nEvaluating...")
        evaluation, error = evaluator.evaluate_split(option, epic_context)

        if error:
            print(f"\nError: {error}")
            continue

        print(f"\nEVALUATION SCORES:")
        print(f"   Testability:        {evaluation['testability']}/10 - {evaluation['testability_notes']}")
        print(f"   Coverage:           {evaluation['coverage']}/10 - {evaluation['coverage_notes']}")
        print(f"   Manageability:      {evaluation['manageability']}/10 - {evaluation['manageability_notes']}")
        print(f"   Independence:       {evaluation['independence']}/10 - {evaluation['independence_notes']}")
        print(f"   Parallel Execution: {evaluation['parallel_execution']}/10 - {evaluation['parallel_execution_notes']}")

        print(f"\nOVERALL SCORE: {evaluation['overall']}/10")

        print(f"\nRecommendation:")
        print(f"   {evaluation['recommendation']}")

        if evaluation.get('concerns'):
            print(f"\nConcerns:")
            for concern in evaluation['concerns']:
                print(f"   - {concern}")

    print("\n" + "=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    # Test Strategic Planner
    options = test_strategic_planner()

    # Test Evaluator
    if options:
        test_evaluator(options)
