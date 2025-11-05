"""
AI Test Ticket Generator
Fetches a Jira Epic and generates test tickets by splitting it into functional areas
Includes comprehensive attachment processing (images, PDFs, Word docs)
"""

import os
import json
import argparse
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv
from ai_tester import JiraClient, LLMClient
from ai_tester.utils.utils import adf_to_plaintext, safe_json_extract
from ai_tester.agents import StrategicPlannerAgent, EvaluationAgent

# Load environment
load_dotenv()


def fetch_and_process_attachments(jira: JiraClient, issue_keys: List[str], max_images: int = 15) -> Dict:
    """
    Fetch and process attachments from multiple issues.

    Args:
        jira: JiraClient instance
        issue_keys: List of issue keys to fetch attachments from
        max_images: Maximum number of images to process

    Returns:
        Dict with 'documents' and 'images' lists
    """
    print(f"\n📎 Fetching attachments from {len(issue_keys)} issue(s)...")

    all_attachments = []
    for issue_key in issue_keys:
        attachments = jira.get_attachments(issue_key)
        if attachments:
            print(f"   Found {len(attachments)} attachment(s) in {issue_key}")
            for att in attachments:
                processed = jira.process_attachment(att)
                if processed:
                    processed['source_issue'] = issue_key
                    all_attachments.append(processed)

    # Separate documents and images
    documents = [att for att in all_attachments if att.get("type") == "document"]
    images = [att for att in all_attachments if att.get("type") == "image"]

    # Limit images
    if len(images) > max_images:
        print(f"   ⚠️  Limiting to first {max_images} images (found {len(images)})")
        images = images[:max_images]

    print(f"   ✅ Processed: {len(documents)} document(s), {len(images)} image(s)")

    return {
        'documents': documents,
        'images': images
    }


def analyze_images_with_vision(llm: LLMClient, images: List[Dict]) -> str:
    """
    Analyze images using GPT-4o vision API.

    Args:
        llm: LLMClient instance
        images: List of processed image attachments

    Returns:
        Text analysis of images
    """
    if not images:
        return ""

    print(f"   🔍 Analyzing {len(images)} image(s) with GPT-4o Vision...")

    try:
        from openai import OpenAI
        client = OpenAI(api_key=llm.api_key)
    except Exception as e:
        print(f"   ⚠️  OpenAI import failed: {e}")
        return ""

    # Build vision request
    content = [
        {
            "type": "text",
            "text": (
                "You are analyzing images attached to a Jira Epic for software testing purposes. "
                "For each image, describe:\n"
                "1. What UI elements, screens, or diagrams are shown\n"
                "2. Any text, labels, buttons, or form fields visible\n"
                "3. Workflows, user interactions, or processes illustrated\n"
                "4. Error messages, validation rules, or business logic\n"
                "5. Any technical details relevant for test ticket creation\n\n"
                "Be specific and detailed. This information will be used to create test tickets."
            )
        }
    ]

    # Add all images
    for img in images:
        content.append({
            "type": "image_url",
            "image_url": {
                "url": img.get("data_url"),
                "detail": "high"
            }
        })

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": content}],
            max_tokens=2000
        )

        analysis = response.choices[0].message.content
        print(f"   ✅ Image analysis complete ({len(analysis)} chars)")
        return analysis

    except Exception as e:
        print(f"   ⚠️  Error analyzing images: {e}")
        return ""


def format_attachments_for_prompt(documents: List[Dict], images: List[Dict], image_analysis: str = "") -> str:
    """Format attachments for inclusion in prompts."""
    if not documents and not images:
        return ""

    lines = []

    # Add documents
    if documents:
        lines.append("\n📄 ATTACHED DOCUMENTS:")
        for doc in documents:
            filename = doc.get("filename", "unknown")
            source = doc.get("source_issue", "N/A")
            content = doc.get("content", "")

            # Truncate long documents
            if len(content) > 2000:
                content = content[:2000] + "\n\n...[truncated for length]"

            lines.append(f"\n--- {filename} (from {source}) ---")
            lines.append(content)

    # Add image analysis
    if images and image_analysis:
        lines.append("\n\n🖼️ IMAGE ANALYSIS:")
        lines.append("The following images were attached:")
        for img in images:
            filename = img.get("filename", "unknown")
            source = img.get("source_issue", "N/A")
            lines.append(f"  - {filename} (from {source})")
        lines.append(f"\nAnalysis:\n{image_analysis}")

    return "\n".join(lines)


def analyze_epic_for_splits(llm, epic_context, attachments_context: str = ""):
    """
    Analyze Epic + children and recommend how to split into test tickets.

    Args:
        llm: LLMClient instance
        epic_context: Epic context dict
        attachments_context: Formatted attachment context string

    Returns:
        Tuple of (split_plan_dict, error_message)
    """
    sys_prompt = """You are a Senior Business Analyst / Test Strategist.
Your task is to analyze an Epic and its child tickets, then recommend how to structure test tickets.

ANALYSIS APPROACH:
1. Review all child tickets and group by functional area or user journey
2. Each test ticket should cover 5-8 acceptance criteria (black-box)
3. Group related functionality together
4. Consider risk, complexity, and testability

GROUPING STRATEGIES:
- By functional area (e.g., 'Authentication', 'Data Migration', 'UI Components')
- By user journey (e.g., 'New User Onboarding', 'Power User Workflow')
- By feature module (e.g., 'Payment Processing', 'Report Generation')
- By priority/risk (high-risk features get dedicated tickets)

OUTPUT FORMAT (JSON):
{
  "recommended_splits": [
    {
      "functional_area": "Name of functional area",
      "description": "Brief description of what this test ticket covers",
      "child_tickets": ["UEX-101", "UEX-102", "UEX-105"],
      "estimated_test_cases": 6,
      "priority": "High|Medium|Low",
      "rationale": "Why these tickets are grouped together"
    }
  ],
  "total_test_tickets": 3,
  "coverage_notes": "Any important notes about coverage"
}

REQUIREMENTS:
- Recommend 2-5 test tickets
- Each focused on a clear functional area
- Each covering related child tickets
- Ensure all child tickets are covered"""

    # Build context
    context_summary = f"""Epic: {epic_context.get('epic_key')} - {epic_context.get('epic_summary', '')}
Description: {epic_context.get('epic_desc', '')[:500]}

Child Tickets ({len(epic_context.get('children', []))} total):
"""

    # Add child ticket details
    children = epic_context.get('children', [])[:20]  # Limit to 20 for token management
    for child in children:
        context_summary += f"\n- {child.get('key', '')}: {child.get('summary', '')}"
        desc = child.get('desc', '')
        if desc:
            context_summary += f"\n  {desc[:200]}..."

    if len(epic_context.get('children', [])) > 20:
        context_summary += f"\n\n... and {len(epic_context.get('children', [])) - 20} more tickets"

    user_prompt = f"""{context_summary}

{attachments_context}

Based on the above (including any attached documents/images), recommend how to structure test tickets.
Each test ticket should have a clear functional focus and cover 5-8 black-box acceptance criteria.
Provide your recommended structure in JSON format."""

    response_text, error = llm.complete_json(sys_prompt, user_prompt, max_tokens=2000)

    if error:
        return (None, error)

    split_data = safe_json_extract(response_text) if response_text else None
    return (split_data, None)


def analyze_epic_with_multi_agent(llm, epic_context, attachments_context: str = "", auto_select_best: bool = False) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Multi-agent workflow for analyzing Epic and recommending test ticket structure.

    Uses Strategic Planner and Evaluation agents to propose and score multiple approaches.

    Args:
        llm: LLMClient instance
        epic_context: Epic context dict with epic_key, epic_summary, epic_desc, children
        attachments_context: Formatted attachment context string
        auto_select_best: If True, automatically selects highest-scored option without user prompt

    Returns:
        Tuple of (split_plan_dict, error_message)
    """
    print("\n" + "=" * 80)
    print("MULTI-AGENT STRATEGIC ANALYSIS")
    print("=" * 80)

    # Step 1: Strategic Planning
    print("\n[1/3] Strategic Planner Agent - Proposing split options...")
    planner = StrategicPlannerAgent(llm)
    options, error = planner.propose_splits(epic_context)

    if error:
        return None, f"Strategic Planner failed: {error}"

    if not options or len(options) < 3:
        return None, f"Expected 3 options, got {len(options) if options else 0}"

    print(f"      Generated {len(options)} strategic options")

    # Step 2: Evaluate each option
    print("\n[2/3] Evaluation Agent - Scoring options...")
    evaluator = EvaluationAgent(llm)
    evaluated_options = []

    for i, option in enumerate(options, 1):
        print(f"      Evaluating option {i}/{len(options)}: {option['name']}...")
        evaluation, eval_error = evaluator.evaluate_split(option, epic_context)

        if eval_error:
            print(f"      Warning: Evaluation failed for option {i}: {eval_error}")
            # Assign default scores if evaluation fails
            evaluation = {
                'overall': 5.0,
                'testability': 5, 'coverage': 5, 'manageability': 5,
                'independence': 5, 'parallel_execution': 5,
                'recommendation': 'Evaluation unavailable'
            }

        evaluated_options.append({
            'option': option,
            'evaluation': evaluation,
            'overall_score': evaluation.get('overall', 0)
        })

    print(f"      Evaluation complete")

    # Step 3: Display options and let user select
    print("\n[3/3] Presenting options for selection...")
    print("\n" + "=" * 80)
    print("STRATEGIC OPTIONS - SELECT ONE")
    print("=" * 80)

    for i, item in enumerate(evaluated_options, 1):
        option = item['option']
        evaluation = item['evaluation']
        score = item['overall_score']

        print(f"\n{'-' * 80}")
        print(f"OPTION {i}: {option['name']} (Score: {score:.1f}/10)")
        print(f"{'-' * 80}")

        print(f"\nRationale:")
        print(f"  {option['rationale'][:200]}{'...' if len(option['rationale']) > 200 else ''}")

        print(f"\nProposed Test Tickets: {len(option['tickets'])}")
        for j, ticket in enumerate(option['tickets'], 1):
            child_tickets = ticket.get('scope', 'N/A').replace('Covers child tickets: ', '')
            print(f"  {j}. {ticket['title']}")
            print(f"     Priority: {ticket['priority']} | Est. Cases: {ticket['estimated_test_cases']} | Scope: {child_tickets}")

        print(f"\nEvaluation Scores:")
        print(f"  Testability:        {evaluation.get('testability', 0)}/10")
        print(f"  Coverage:           {evaluation.get('coverage', 0)}/10")
        print(f"  Manageability:      {evaluation.get('manageability', 0)}/10")
        print(f"  Independence:       {evaluation.get('independence', 0)}/10")
        print(f"  Parallel Execution: {evaluation.get('parallel_execution', 0)}/10")

        print(f"\nRecommendation: {evaluation.get('recommendation', 'N/A')}")

    # Get user selection
    highest_scored_idx = max(range(len(evaluated_options)), key=lambda i: evaluated_options[i]['overall_score'])

    if auto_select_best:
        # Auto-select highest scored option (for testing/automation)
        selected_idx = highest_scored_idx
        print(f"\n[AUTO] Auto-selecting highest-scored option: {selected_idx + 1}")
    else:
        # Interactive user selection
        print("\n" + "=" * 80)
        print("\nSelect an option (1-3) or press Enter for highest-scored option:")

        while True:
            user_input = input(f"\nYour choice [default: {highest_scored_idx + 1}]: ").strip()

            if not user_input:
                selected_idx = highest_scored_idx
                print(f"Using highest-scored option: {selected_idx + 1}")
                break

            try:
                selected_idx = int(user_input) - 1
                if 0 <= selected_idx < len(evaluated_options):
                    break
                else:
                    print(f"Please enter a number between 1 and {len(evaluated_options)}")
            except ValueError:
                print("Invalid input. Please enter a number.")

    # Convert selected option to split_data format
    selected = evaluated_options[selected_idx]
    selected_option = selected['option']
    selected_evaluation = selected['evaluation']

    print(f"\nSelected: {selected_option['name']} (Score: {selected['overall_score']:.1f}/10)")

    # Convert to the format expected by generate_test_ticket()
    recommended_splits = []
    for ticket in selected_option['tickets']:
        # Extract child ticket keys from scope
        scope_text = ticket.get('scope', '')
        child_tickets = []

        # Parse "Covers child tickets: KEY-1, KEY-2, KEY-3"
        if 'Covers child tickets:' in scope_text or 'Covers child ticket:' in scope_text:
            keys_part = scope_text.split(':', 1)[1].strip()
            child_tickets = [key.strip() for key in keys_part.replace(' and ', ', ').split(',')]

        recommended_splits.append({
            'functional_area': ticket['title'].replace('Test Ticket: ', ''),
            'description': ticket.get('description', ''),
            'child_tickets': child_tickets,
            'estimated_test_cases': ticket.get('estimated_test_cases', 20),
            'priority': ticket.get('priority', 'Medium'),
            'rationale': f"From strategic option: {selected_option['name']}"
        })

    split_data = {
        'recommended_splits': recommended_splits,
        'total_test_tickets': len(recommended_splits),
        'coverage_notes': f"Selected strategy: {selected_option['name']}. {selected_evaluation.get('recommendation', '')}",
        'strategic_analysis': {
            'selected_strategy': selected_option['name'],
            'overall_score': selected['overall_score'],
            'all_options': [opt['option']['name'] for opt in evaluated_options],
            'evaluation': selected_evaluation
        }
    }

    return split_data, None


def generate_test_ticket(llm, epic_context, split_info, attachments_context: str = ""):
    """
    Generate a single test ticket for a functional area.

    Args:
        llm: LLMClient instance
        epic_context: Epic context dict
        split_info: Split information for this test ticket
        attachments_context: Formatted attachment context string

    Returns:
        Tuple of (ticket_content_dict, error_message)
    """

    functional_area = split_info.get('functional_area', 'Unknown Area')
    child_ticket_keys = split_info.get('child_tickets', [])

    # Get the actual child ticket details
    relevant_children = [
        child for child in epic_context.get('children', [])
        if child.get('key') in child_ticket_keys
    ]

    sys_prompt = """You are a Senior Business Analyst / Product Owner tasked with creating test tickets.

YOUR ROLE:
- Analyze the Epic and child tickets to understand the feature
- Create a comprehensive test ticket for this functional area
- Focus on BLACK-BOX acceptance criteria for manual testing

CRITICAL REQUIREMENTS:
1. Summary: Follow format '[Epic Name] - Testing - [Functional Area]'
2. Description:
   - Clear context about what's being tested
   - At the END, add 'Source Tickets: KEY-123: Title, KEY-456: Title, ...'
3. Acceptance Criteria: 5-8 black-box criteria, each:
   - Focuses on USER-FACING behavior
   - Is VERIFIABLE by a manual tester
   - Avoids technical implementation details

BLACK-BOX vs WHITE-BOX:
✅ BLACK-BOX: 'User can select payment method from dropdown'
❌ WHITE-BOX: 'API calls /v2/payments endpoint'
✅ BLACK-BOX: 'System displays error message when invalid email entered'
❌ WHITE-BOX: 'Database updates user_payments table'

OUTPUT FORMAT (JSON):
{
  "summary": "[Epic Name] - Testing - [Functional Area]",
  "description": "Clear description of what's being tested. Include context and scope.\\n\\nSource Tickets: KEY-1: Title, KEY-2: Title",
  "acceptance_criteria": [
    "AC 1: Clear, testable acceptance criterion",
    "AC 2: Another clear criterion",
    "AC 3: ...",
    "AC 4: ...",
    "AC 5: ..."
  ],
  "priority": "High|Medium|Low",
  "estimated_effort": "Small|Medium|Large"
}"""

    user_prompt = f"""Epic: {epic_context.get('epic_key')} - {epic_context.get('epic_summary', '')}
Functional Area: {functional_area}

Epic Description:
{epic_context.get('epic_desc', '')[:800]}

Relevant Child Tickets:
"""

    for child in relevant_children[:10]:  # Limit to 10
        user_prompt += f"\n- {child.get('key', '')}: {child.get('summary', '')}"
        desc = child.get('desc', '')
        if desc:
            user_prompt += f"\n  {desc[:300]}..."

    user_prompt += f"\n{attachments_context}\n\nCreate the test ticket now in JSON format (considering all attached documents and images)."

    response_text, error = llm.complete_json(sys_prompt, user_prompt, max_tokens=3000)

    if error:
        return (None, error)

    ticket_data = safe_json_extract(response_text) if response_text else None
    return (ticket_data, None)


def generate_test_tickets_for_epic(epic_key: str, use_multi_agent: bool = False):
    """
    Generate test tickets for a Jira Epic using AI.

    Args:
        epic_key: Jira Epic identifier
        use_multi_agent: If True, use multi-agent strategic planning workflow
    """

    print("\n" + "=" * 80)
    print(f"AI TEST TICKET GENERATOR - {epic_key}")
    print("=" * 80)

    # Initialize clients
    jira = JiraClient(
        base_url=os.getenv("JIRA_BASE_URL"),
        email=os.getenv("JIRA_EMAIL"),
        api_token=os.getenv("JIRA_API_TOKEN")
    )

    llm = LLMClient(enabled=True)

    if not llm.enabled:
        print("\n❌ Error: OpenAI API key not found or invalid!")
        print("Please add OPENAI_API_KEY to your .env file")
        return

    try:
        # Step 1: Fetch the Epic
        print(f"\n📥 Step 1: Fetching Epic from Jira...")
        epic = jira.get_issue(epic_key)

        fields = epic.get("fields", {})
        summary = fields.get("summary", "")
        issue_type = fields.get("issuetype", {}).get("name", "")

        print(f"   ✅ Found: [{issue_type}] {summary}")

        # Get description
        description = fields.get("description", "")
        if isinstance(description, dict):
            description = adf_to_plaintext(description)

        print(f"   Description: {len(description)} characters")

        # Step 2: Fetch children
        print(f"\n👶 Step 2: Fetching child tickets...")
        children = jira.get_children_of_epic(epic_key)

        if not children:
            print(f"\n⚠️  Warning: No child tickets found for {epic_key}")
            print("   Test ticket generation works best with child tickets.")
            return

        print(f"   ✅ Found {len(children)} child ticket(s)")

        # Step 2a: Fetch and process attachments
        print(f"\n📎 Step 2a: Processing attachments...")

        # Get all issue keys (Epic + children)
        all_issue_keys = [epic_key] + [child.get("key", "") for child in children if child.get("key")]

        # Fetch and process attachments
        attachments_data = fetch_and_process_attachments(jira, all_issue_keys, max_images=15)
        documents = attachments_data['documents']
        images = attachments_data['images']

        # Analyze images if any
        image_analysis = ""
        if images:
            print(f"\n🖼️  Step 2b: Analyzing images with GPT-4o Vision...")
            image_analysis = analyze_images_with_vision(llm, images)

        # Format attachments for prompts
        attachments_context = format_attachments_for_prompt(documents, images, image_analysis)

        # Build epic context
        epic_context = {
            'epic_key': epic_key,
            'epic_summary': summary,
            'epic_desc': description,
            'children': []
        }

        for child in children:
            child_fields = child.get("fields", {})
            child_desc = child_fields.get("description", "")
            if isinstance(child_desc, dict):
                child_desc = adf_to_plaintext(child_desc)

            epic_context['children'].append({
                'key': child.get("key", ""),
                'summary': child_fields.get("summary", ""),
                'desc': child_desc,
                'type': child_fields.get("issuetype", {}).get("name", "")
            })

        # Step 3: Analyze Epic and recommend splits
        print(f"\n🤖 Step 3: Analyzing Epic structure...")
        print(f"   Using: {llm.model}")
        print(f"   Mode: {'Multi-Agent Strategic Planning' if use_multi_agent else 'Single-Agent Analysis'}")
        print(f"   Including {len(documents)} document(s) and {len(images)} image(s) in analysis")
        print(f"   This may take {'60-90 seconds' if use_multi_agent else '30-45 seconds'}...")

        if use_multi_agent:
            split_data, split_error = analyze_epic_with_multi_agent(llm, epic_context, attachments_context)
        else:
            split_data, split_error = analyze_epic_for_splits(llm, epic_context, attachments_context)

        if split_error:
            print(f"\n❌ Error analyzing Epic: {split_error}")
            return

        if not split_data:
            print(f"\n❌ Error: Failed to parse split recommendations")
            return

        recommended_splits = split_data.get("recommended_splits", [])

        print(f"\n   ✅ Analysis complete!")
        print(f"\n📊 RECOMMENDED STRUCTURE:")
        print(f"   Total Test Tickets: {len(recommended_splits)}")
        print()

        for i, split in enumerate(recommended_splits, 1):
            area = split.get('functional_area', 'Unknown')
            child_keys = split.get('child_tickets', [])
            priority = split.get('priority', 'Medium')
            rationale = split.get('rationale', '')

            print(f"   {i}. {area}")
            print(f"      Priority: {priority}")
            print(f"      Child Tickets: {', '.join(child_keys)}")
            print(f"      Rationale: {rationale}")
            print()

        # Step 4: Generate test tickets
        print(f"\n🎯 Step 4: Generating test tickets...")
        print(f"   Generating {len(recommended_splits)} test ticket(s)...")
        print()

        generated_tickets = []

        for i, split in enumerate(recommended_splits, 1):
            area = split.get('functional_area', 'Unknown')
            print(f"   [{i}/{len(recommended_splits)}] Generating: {area}...")

            ticket_data, ticket_error = generate_test_ticket(llm, epic_context, split, attachments_context)

            if ticket_error:
                print(f"      ❌ Error: {ticket_error}")
                continue

            if not ticket_data:
                print(f"      ❌ Error: Failed to parse ticket data")
                continue

            # Add metadata
            ticket_data['functional_area'] = area
            ticket_data['source_tickets'] = split.get('child_tickets', [])
            ticket_data['epic_key'] = epic_key

            generated_tickets.append(ticket_data)
            print(f"      ✅ Generated successfully!")

        # Step 5: Display results
        print(f"\n" + "=" * 80)
        print(f"📊 GENERATION RESULTS")
        print("=" * 80)
        print(f"\n✅ Generated {len(generated_tickets)} test ticket(s)")

        # Display each ticket
        print(f"\n" + "=" * 80)
        print(f"🎫 TEST TICKETS:")
        print("=" * 80)

        for i, ticket in enumerate(generated_tickets, 1):
            print(f"\n{'─' * 80}")
            print(f"TICKET #{i}: {ticket.get('summary', 'No title')}")
            print(f"{'─' * 80}")
            print(f"Functional Area: {ticket.get('functional_area', 'N/A')}")
            print(f"Priority:        {ticket.get('priority', 'Medium')}")
            print(f"Effort:          {ticket.get('estimated_effort', 'N/A')}")
            print(f"Source Tickets:  {', '.join(ticket.get('source_tickets', []))}")

            print(f"\nDescription:")
            print(f"  {ticket.get('description', 'No description')}")

            print(f"\nAcceptance Criteria ({len(ticket.get('acceptance_criteria', []))}):")
            for j, ac in enumerate(ticket.get('acceptance_criteria', []), 1):
                print(f"  {j}. {ac}")

        # Step 6: Save to file
        print(f"\n" + "=" * 80)
        print(f"💾 SAVING RESULTS...")
        print("=" * 80)

        output_file = f"test_tickets_{epic_key.replace('-', '_')}.json"

        result = {
            'epic_key': epic_key,
            'epic_summary': summary,
            'analysis': split_data,
            'generated_tickets': generated_tickets,
            'attachments': {
                'documents_processed': len(documents),
                'images_processed': len(images),
                'image_analysis': image_analysis if images else None
            },
            'stats': {
                'child_tickets_analyzed': len(children),
                'recommended_splits': len(recommended_splits),
                'tickets_generated': len(generated_tickets),
                'total_acceptance_criteria': sum(
                    len(t.get('acceptance_criteria', [])) for t in generated_tickets
                ),
                'attachments_processed': len(documents) + len(images)
            }
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Saved to: {output_file}")

        # Summary
        print(f"\n" + "=" * 80)
        print(f"✅ GENERATION COMPLETE!")
        print("=" * 80)
        print(f"\nSummary:")
        print(f"  - Epic:                {epic_key}")
        print(f"  - Child Tickets:       {len(children)}")
        print(f"  - Attachments:         {len(documents)} document(s), {len(images)} image(s)")
        print(f"  - Test Tickets:        {len(generated_tickets)}")
        print(f"  - Total ACs:           {result['stats']['total_acceptance_criteria']}")
        print(f"  - Saved to:            {output_file}")

    except ValueError as e:
        print(f"\n❌ Error: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main function."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='AI Test Ticket Generator - Generate test tickets from Jira Epics',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_test_tickets.py                    # Interactive mode
  python generate_test_tickets.py UEX-123            # Generate for specific Epic
  python generate_test_tickets.py UEX-123 --multi-agent  # Use multi-agent mode
  python generate_test_tickets.py --multi-agent      # Interactive with multi-agent
        """
    )
    parser.add_argument(
        'epic_key',
        nargs='?',
        help='Jira Epic key (e.g., UEX-123). If not provided, will prompt interactively.'
    )
    parser.add_argument(
        '--multi-agent',
        action='store_true',
        help='Use multi-agent strategic planning workflow (Strategic Planner + Evaluation agents)'
    )

    args = parser.parse_args()

    print("\n" + "=" * 80)
    print("🤖 AI TEST TICKET GENERATOR")
    if args.multi_agent:
        print("   MODE: Multi-Agent Strategic Planning")
    print("=" * 80)

    # Check credentials
    if not all([os.getenv("JIRA_BASE_URL"), os.getenv("JIRA_EMAIL"), os.getenv("JIRA_API_TOKEN")]):
        print("\n❌ Error: Jira credentials not found in .env file!")
        return

    if not os.getenv("OPENAI_API_KEY"):
        print("\n❌ Error: OpenAI API key not found in .env file!")
        return

    print("\n✅ Credentials loaded")
    print(f"   Jira:   {os.getenv('JIRA_BASE_URL')}")
    print(f"   OpenAI: {os.getenv('OPENAI_MODEL', 'gpt-4o-2024-08-06')}")

    # Get Epic key
    epic_key = args.epic_key

    if not epic_key:
        print("\n" + "-" * 80)
        print("\nEnter the Jira Epic key to generate test tickets for:")
        print("(e.g., UEX-123, PROJ-456, STORY-789)")
        print("\nOr press Enter to use a test key: UEX-17")

        epic_key = input("\nEpic Key: ").strip().upper()

        if not epic_key:
            epic_key = "UEX-17"
            print(f"Using default: {epic_key}")

    # Generate test tickets
    generate_test_tickets_for_epic(epic_key, use_multi_agent=args.multi_agent)

    # Ask if they want to generate more (only in interactive mode)
    if not args.epic_key:
        print("\n" + "-" * 80)
        another = input("\nGenerate test tickets for another Epic? (y/n): ").strip().lower()
        if another == 'y':
            main()
        else:
            print("\n👋 Done!")
            print("\nNext steps:")
            print("  1. Review the generated JSON file")
            print("  2. Create the test tickets in Jira")
            print("  3. Optionally, generate test cases for each test ticket!")
    else:
        print("\n👋 Done!")
        print("\nNext steps:")
        print("  1. Review the generated JSON file")
        print("  2. Create the test tickets in Jira")
        print("  3. Optionally, generate test cases for each test ticket!")


if __name__ == "__main__":
    main()
