"""Quick test to verify setup"""

from ai_tester import JiraClient, LLMClient, TestCase, TestStep
from ai_tester.utils import slugify, safe_json_extract

# Test utilities
print("Testing utilities...")
assert slugify("Test Case 123") == "test-case-123"
print("✓ Utilities work!")

# Test models
print("Testing models...")
test_case = TestCase(title="Login Test")
test_case.add_step("Navigate to login", "Login page displays")
assert len(test_case.steps) == 1
print("✓ Models work!")

# Test clients (will fail without credentials, but tests imports)
print("Testing client imports...")
try:
    jira = JiraClient("https://test.atlassian.net", "test@example.com", "fake-token")
    print("✓ JiraClient imports!")
except:
    print("✓ JiraClient imports!")

try:
    llm = LLMClient(enabled=False)
    print("✓ LLMClient imports!")
except:
    print("✓ LLMClient imports!")

print("\n🎉 ALL TESTS PASSED! Your setup is complete!")