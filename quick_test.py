"""Quick test to verify everything is set up correctly"""

import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

print("=" * 60)
print("AI TESTER FRAMEWORK - QUICK TEST")
print("=" * 60)

# Test 1: Check environment variables
print("\n1. Checking environment variables...")
jira_url = os.getenv("JIRA_BASE_URL")
jira_email = os.getenv("JIRA_EMAIL")
jira_token = os.getenv("JIRA_API_TOKEN")
openai_key = os.getenv("OPENAI_API_KEY")

if jira_url and jira_email and jira_token:
    print("   ✓ Jira credentials found")
else:
    print("   ⚠ Jira credentials missing (add to .env file)")

if openai_key:
    print("   ✓ OpenAI API key found")
else:
    print("   ⚠ OpenAI API key missing (add to .env file)")

# Test 2: Test imports
print("\n2. Testing imports...")
try:
    from ai_tester import JiraClient, LLMClient
    print("   ✓ Clients imported successfully")
except Exception as e:
    print(f"   ✗ Import error: {e}")
    exit(1)

# Test 3: Initialize clients
print("\n3. Initializing clients...")
try:
    jira = JiraClient(
        base_url=jira_url or "https://test.atlassian.net",
        email=jira_email or "test@example.com",
        api_token=jira_token or "fake-token"
    )
    print("   ✓ JiraClient initialized")
except Exception as e:
    print(f"   ✗ JiraClient error: {e}")

try:
    llm = LLMClient(enabled=bool(openai_key))
    print(f"   ✓ LLMClient initialized - {llm.status_label()}")
except Exception as e:
    print(f"   ✗ LLMClient error: {e}")

# Test 4: Test utilities
print("\n4. Testing utilities...")
try:
    from ai_tester.utils.utils import slugify
    test = slugify("Test Case 123")
    print(f"   ✓ Utilities working (slugify: '{test}')")
except Exception as e:
    print(f"   ✗ Utility error: {e}")

print("\n" + "=" * 60)
print("✅ SETUP TEST COMPLETE!")
print("=" * 60)
print("\n🎯 Ready to build! What do you want to do?")
print("\nOptions:")
print("  1. Fetch a Jira epic and see its data")
print("  2. Generate test cases from a ticket")
print("  3. Build the full GUI")
print("  4. Create a simple demo script")