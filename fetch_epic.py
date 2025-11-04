"""
Fetch Jira Epic - Demo Script
Shows epic details, child tickets, and attachments
"""

import os
from dotenv import load_dotenv
from ai_tester import JiraClient

# Load environment
load_dotenv()

def display_epic_info(epic_key: str):
    """Fetch and display information about a Jira epic."""
    
    print("\n" + "=" * 80)
    print(f"FETCHING EPIC: {epic_key}")
    print("=" * 80)
    
    # Initialize Jira client
    jira = JiraClient(
        base_url=os.getenv("JIRA_BASE_URL"),
        email=os.getenv("JIRA_EMAIL"),
        api_token=os.getenv("JIRA_API_TOKEN")
    )
    
    try:
        # Fetch the epic
        print("\n📥 Fetching epic...")
        epic = jira.get_issue(epic_key)
        
        # Extract basic info
        fields = epic.get("fields", {})
        summary = fields.get("summary", "N/A")
        status = fields.get("status", {}).get("name", "N/A")
        issue_type = fields.get("issuetype", {}).get("name", "N/A")
        
        print(f"\n✅ Epic Found!")
        print(f"\n📋 BASIC INFO:")
        print(f"   Key:     {epic_key}")
        print(f"   Type:    {issue_type}")
        print(f"   Summary: {summary}")
        print(f"   Status:  {status}")
        
        # Get description
        description = fields.get("description")
        if description:
            print(f"\n📝 DESCRIPTION:")
            if isinstance(description, dict):
                # ADF format - convert to plain text
                from ai_tester.utils.utils import adf_to_plaintext
                desc_text = adf_to_plaintext(description)
                # Show first 500 characters
                if len(desc_text) > 500:
                    print(f"   {desc_text[:500]}...")
                    print(f"   [+{len(desc_text) - 500} more characters]")
                else:
                    print(f"   {desc_text}")
            else:
                print(f"   {description[:500]}")
        
        # Get child issues
        print(f"\n👶 CHILD ISSUES:")
        print("   Fetching children...")
        children = jira.get_children_of_epic(epic_key)
        
        if children:
            print(f"   Found {len(children)} child issue(s):\n")
            for i, child in enumerate(children, 1):
                child_key = child.get("key", "N/A")
                child_fields = child.get("fields", {})
                child_summary = child_fields.get("summary", "N/A")
                child_type = child_fields.get("issuetype", {}).get("name", "N/A")
                child_status = child_fields.get("status", {}).get("name", "N/A")
                
                print(f"   {i}. [{child_key}] {child_type}")
                print(f"      Summary: {child_summary}")
                print(f"      Status:  {child_status}")
                print()
        else:
            print("   No child issues found")
        
        # Get attachments
        print(f"\n📎 ATTACHMENTS:")
        attachments = jira.get_attachments(epic_key)
        
        if attachments:
            print(f"   Found {len(attachments)} attachment(s):\n")
            for i, att in enumerate(attachments, 1):
                filename = att.get("filename", "N/A")
                mime_type = att.get("mimeType", "N/A")
                size = att.get("size", 0)
                size_kb = size / 1024
                
                print(f"   {i}. {filename}")
                print(f"      Type: {mime_type}")
                print(f"      Size: {size_kb:.1f} KB")
                print()
        else:
            print("   No attachments found")
        
        # Summary
        print("\n" + "=" * 80)
        print("✅ FETCH COMPLETE!")
        print("=" * 80)
        print(f"\nSummary:")
        print(f"  - Epic: {epic_key}")
        print(f"  - Children: {len(children)}")
        print(f"  - Attachments: {len(attachments)}")
        
    except ValueError as e:
        print(f"\n❌ Error: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main function."""
    print("\n" + "=" * 80)
    print("JIRA EPIC FETCHER")
    print("=" * 80)
    
    # Check credentials
    if not all([os.getenv("JIRA_BASE_URL"), os.getenv("JIRA_EMAIL"), os.getenv("JIRA_API_TOKEN")]):
        print("\n❌ Error: Jira credentials not found in .env file!")
        print("\nPlease add:")
        print("  JIRA_BASE_URL=https://yourcompany.atlassian.net")
        print("  JIRA_EMAIL=your-email@company.com")
        print("  JIRA_API_TOKEN=your-token")
        return
    
    # Get epic key from user
    print("\nEnter the Jira Epic key (e.g., UEX-123, PROJ-456)")
    print("Or press Enter to use a test key: UEX-123")
    
    epic_key = input("\nEpic Key: ").strip()
    
    if not epic_key:
        epic_key = "UEX-123"
        print(f"Using default: {epic_key}")
    
    # Fetch and display
    display_epic_info(epic_key)
    
    # Ask if they want to fetch another
    print("\n" + "-" * 80)
    another = input("\nFetch another epic? (y/n): ").strip().lower()
    if another == 'y':
        main()
    else:
        print("\n👋 Done! Ready to move to Option 2 (Generate Test Cases)?")


if __name__ == "__main__":
    main()