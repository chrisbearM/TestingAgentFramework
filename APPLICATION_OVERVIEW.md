# AI Tester Framework - Application Overview

## What is it?

AI Tester Framework is a testing assistant that generates test plans and test cases from Jira requirements. You give it an Epic or user story from Jira, and it creates comprehensive test documentation automatically.

---

## Core Features

The application has three main features:

1. **Epic Analysis** - Analyzes large Epics and creates organized test tickets
2. **Test Case Generation** - Generates detailed test cases with step-by-step instructions
3. **Ticket Improvement** - Takes poorly written tickets and restructures them for clarity

---

## The AI Agents

The application uses 14 specialized AI agents that work together:

**Epic Analysis Agents:**

1. **Strategic Planner** - Analyzes Epics and proposes 3 different testing strategies
2. **Evaluator** - Scores each strategy on testability, coverage, manageability, independence, and parallel execution
3. **Test Ticket Generator** - Creates test tickets based on the chosen strategy
4. **Test Ticket Reviewer** - Reviews generated test tickets for quality and completeness
5. **Questioner** - Asks clarifying questions about unclear requirements
6. **Gap Analyzer** - Analyzes and prioritizes requirement gaps
7. **Coverage Reviewer** - Analyzes how well test tickets cover the Epic
8. **Requirements Fixer** - Creates additional test tickets to fill coverage gaps

**Test Case Generation Agents:**

9. **Ticket Analyzer** - Assesses ticket readiness for test case generation
10. **Ticket Improver** - Takes poorly written tickets and restructures them
11. **Test Case Generator** - Creates individual test cases with detailed steps
12. **Test Case Critic** - Reviews generated test cases and identifies quality issues
13. **Test Case Fixer** - Fixes test cases based on critic feedback
14. **Test Case Reviewer** - (Optional) Provides additional review and improvement suggestions when requested by user

---

## Feature 1: Epic Analysis

### How Users Experience It

When you start an Epic analysis, here's what happens:

1. You enter a Jira Epic key (like "PROJ-123")
2. The system fetches the Epic and all its child tickets from Jira
3. It downloads any attachments (PDFs, Word docs, images)
4. You get 3 different strategic approaches for testing
5. You pick the strategy you prefer
6. The system generates test tickets based on that strategy
7. You see a coverage analysis showing what's covered and what's missing
8. You can apply fixes to improve coverage

### Behind the Scenes - How It Works

#### Step 1: Gathering the Data

First, the system connects to Jira and pulls down everything related to the Epic:

- The Epic itself (title, description, all the details)
- All the child tickets linked to that Epic
- Any documents attached (PDFs get text extracted, Word docs get processed)
- Currently images are blocked for security, but the system notes they exist

The system also cleans up Jira's formatting - converting wiki markup to markdown so it's easier to read.

#### Step 2: Strategic Planner Thinks Through Approaches

The Strategic Planner agent reads through everything - the Epic description, all the child tickets, any documents attached. It's trying to understand the full scope of what needs testing.

Then it creates 3 completely different strategies. For example, if you're testing a payment system:

- **Strategy A** might organize tests by user journey (checkout flow, refund flow, payment history)
- **Strategy B** might organize by technical component (payment gateway, database, notifications, reporting)
- **Strategy C** might organize by risk level (test critical payment processing first, then nice-to-have features)

For each strategy, it explains the rationale and breaks it down into 4-6 test categories. This gives you options - maybe you're short on time and want to focus on high-risk areas first, or maybe you want comprehensive user journey testing.

#### Step 3: You Choose a Strategy

The system shows you all 3 strategies with their rationale. You pick the one that makes the most sense for your project, timeline, and team.

#### Step 4: Test Ticket Generator Creates Tickets

Now the Test Ticket Generator takes your chosen strategy and creates actual test tickets.

For each test category in the strategy, it creates 1-3 test tickets. Each ticket has:

- **Summary** - A clear title describing what will be tested
- **Background** - Context about why this testing is important
- **Test Scope** - Exactly what will and won't be tested
- **Acceptance Criteria** - 5-8 specific things to verify (like "Verify payment processes with valid credit card")
- **Source Requirements** - Which child tickets from the Epic this test ticket covers

So if your strategy had 6 test categories, you might end up with 10-15 test tickets covering the whole Epic.

#### Step 5: Questioner Looks for Unclear Requirements

While the Strategic Planner and Test Ticket Generator are working, the Questioner agent runs in parallel, reading through the Epic and child tickets with a critical eye. It's looking for ambiguities and gaps.

It generates questions like:

- "What should happen when a user uploads a file larger than 10MB?"
- "Should users be able to edit their order after submitting payment?"
- "What validation rules apply to phone numbers?"

These questions are categorized (Edge Cases, Error Handling, Performance, etc.) and prioritized (Critical, Important, Minor).

#### Step 6: Gap Analyzer Prioritizes Real Gaps

The Gap Analyzer takes all those questions and figures out which ones represent actual coverage gaps versus just nice-to-know details.

It groups related gaps together and provides specific recommendations. For example:

- **Critical Gap**: "No error handling specified for payment failures - could miss major user-facing bugs. Recommend adding test ticket for payment error scenarios."

#### Step 7: Coverage Reviewer Analyzes Completeness

This is where the system does a thorough review of how well your test tickets cover the Epic. The Coverage Reviewer looks at:

**Epic Coverage:**

- What are the key requirements in the Epic description?
- Are items marked "Out of Scope" (it won't flag those as gaps)
- Which requirements are covered by the test tickets?
- Which requirements have no test coverage?

**Child Ticket Coverage:**

- For each child ticket, is it covered by at least one test ticket?
- Is the coverage complete or only partial?
- Which child tickets have zero coverage?

**Gap Identification:**

- Lists specific requirements that aren't covered
- Lists child tickets that aren't covered
- Identifies missing test scenarios (error cases, edge cases)
- Assigns severity to each gap (Critical, Important, Minor)

It then calculates an overall coverage score (0-100):

- 90-100: Comprehensive coverage
- 70-89: Adequate coverage
- Below 70: Insufficient coverage

Finally, it provides specific recommendations like "Add test ticket for payment gateway timeout scenarios to cover child ticket PROJ-48."

#### Step 8: Requirements Fixer Creates Solutions

If your coverage isn't perfect (and it usually isn't on the first pass), the Requirements Fixer agent creates solutions.

It focuses on the Critical and Important gaps first. For each gap, it either:

**Creates a new test ticket:**

- Full structure just like the Test Ticket Generator created
- Explicitly states which gap it addresses
- Lists which requirements or child tickets it covers

**Suggests updates to existing tickets:**

- Identifies which ticket to update
- Provides the updated content
- Explains what changed and why

For example:

- **New Ticket**: "Test Ticket: Payment Gateway Timeout Handling" - addresses the critical gap around error handling
- **Update**: Add "Verify error message displays for expired card" to the existing Payment Processing ticket

It also estimates how much the coverage score will improve if you apply these fixes (e.g., "This will increase coverage from 75% to 95%").

#### Step 9: You Review and Apply

The frontend shows you:

- Current coverage score and level
- All identified gaps with severity
- Strengths (what's already well-covered)
- Specific recommendations

You can review the suggested fixes and click "Apply Fixes" to add them to your test tickets. If you want, you can run the coverage analysis again to see the new score.

### Complete End-to-End Flow

The Epic Analysis feature integrates seamlessly with Test Case Generation. Once you have generated test tickets from an Epic, you can take any of those test tickets and generate detailed test cases from them using Feature 2.

This provides complete end-to-end functionality:

1. **Epic Analysis** → Generates organized test tickets covering the Epic
2. **Test Case Generation** → Takes those test tickets and generates detailed step-by-step test cases

This means you can go from a large Epic to fully detailed, executable test cases ready for your QA team.

---

## Feature 2: Test Case Generation

### How Users Experience It

This feature is for creating detailed test cases from individual tickets:

1. You enter a Jira ticket key
2. You click "Generate Test Cases"
3. The system automatically preprocesses the ticket to clarify requirements
4. The system creates 9-21 initial test cases (3 per requirement)
5. The critic automatically reviews all test cases for quality issues
6. The fixer automatically corrects issues based on critic feedback
7. You see the final test cases
8. (Optional) You can request an additional review to identify further improvements
9. (Optional) You can apply those improvements
10. You can make manual edits inline if needed

### Behind the Scenes - How It Works

#### Step 1: Automatic Ticket Preprocessing

Before generating test cases, the system automatically runs the ticket through the Ticket Improver agent to ensure clear requirements. This happens behind the scenes without user intervention.

The Ticket Improver agent restructures the ticket:

**It takes a vague ticket like:**
"Fix the login thing - it's broken"

**And turns it into:**

- **Summary**: "User Authentication - Login Button Unresponsive on Chrome Mobile"
- **Description**: Restructured with clear sections (Overview, Acceptance Criteria, Out of Scope)
- **Acceptance Criteria**: Grouped by category (Functional Requirements, Error Handling, Performance)
- **Testing Notes**: Specific guidance like "Test with various email formats"
- **Edge Cases**: List of unusual scenarios to consider
- **Error Scenarios**: Expected error conditions
- **Out of Scope**: What's explicitly not included

This gives the test case generator much better material to work with.

#### Step 2: Extracting Testable Requirements

The system looks at the acceptance criteria (from the improved ticket or original if you didn't improve it) and extracts 3-7 testable requirements.

For example, from a login ticket it might extract:

1. "User login with valid credentials"
2. "User login with invalid credentials"
3. "Account lockout after failed attempts"
4. "Password reset functionality"

Each requirement becomes the basis for generating test cases.

#### Step 3: Test Case Generator Creates Initial Test Cases

For each requirement, the Test Case Generator creates 3 test cases:

**Positive Test (Happy Path):**

- Tests the normal, expected behavior
- Example: "User login with valid email and password"
- Steps walk through entering correct credentials and verifying successful login

**Negative Test (Error Handling):**

- Tests error conditions and invalid input
- Example: "User login with invalid password"
- Steps verify appropriate error messages display

**Edge Case Test (Boundary Conditions):**

- Tests unusual but valid scenarios
- Example: "User login with email containing special characters like 'user+test@sub.example.com'"
- Steps verify the system handles edge cases correctly

Each test case includes:

- Title describing what's being tested
- Description explaining the purpose
- Steps with expected results (formatted as alternating "Step 1: Do X" then "Expected Result: Y happens")
- Priority (High, Medium, Low)
- Type (Positive, Negative, Edge Case)

So if there are 5 requirements, you get 15 test cases total.

#### Step 4: The Critic Reviews Everything

The Test Case Critic automatically analyzes all generated test cases for quality issues. It checks:

- **Count**: Are there exactly 3 test cases per requirement (Positive, Negative, Edge Case)?
- **Realism**: Can these tests actually be executed by a QA tester?
- **Logic**: Do tests actually test what they claim to test?
- **Detail**: Are steps sufficiently detailed (simple tests need 3 steps, complex ones may need 8+)?
- **Format**: Does every "Step N:" have an "Expected Result:" immediately after?
- **Redundancy**: Are any tests repetitive or nonsensical?

For each problematic test case, the critic identifies:

- **What's wrong**: "Test case 2 only has 2 steps when it should have at least 3"
- **How to fix**: "Add a step to verify the confirmation message appears"
- **Severity**: Critical/High/Medium/Low

The critic provides an overall approval decision:

- **Approved**: High quality, no significant issues
- **Needs Improvement**: Has specific fixable issues

#### Step 5: The Fixer Corrects Issues

If the critic found issues, the Test Case Fixer automatically fixes them based on the specific feedback.

The fixer doesn't regenerate from scratch - it takes the existing test cases and surgically fixes the problems:

- **Too simplistic?** Adds more detailed steps
- **Doesn't make sense?** Rewrites to be logical and coherent
- **Redundant?** Removes duplicates or makes them unique
- **Missing Expected Result?** Adds it immediately after the step
- **Wrong count?** Adds missing tests or removes extras
- **Doesn't match requirement?** Aligns it properly

The Generator runs once, then the Critic → Fixer improvement loop can run up to 2 times automatically to ensure quality.

#### Step 6: You See the Results

The frontend displays the final test cases grouped by requirement. You can:

- Expand/collapse test cases
- See steps and expected results with visual distinction
- Edit test cases inline if you want to make manual tweaks
- See which requirement each test case covers

#### Step 7: Optional Additional Review

If you want even more refinement, you can click "Review Test Cases" to run an additional quality analysis. The Test Case Reviewer agent will:

- Analyze all test cases for completeness, clarity, coverage, and efficiency
- Identify missing scenarios or edge cases
- Find redundant tests
- Provide specific improvement suggestions

You'll see a detailed review showing:

- Overall quality score
- Specific issues with each test case
- Suggestions for improvements
- Missing test scenarios

#### Step 8: Optional Apply Improvements

If you like the suggestions from the review, you can click "Implement Improvements" and the system will:

- Fix the specific issues identified in existing test cases
- Add new test cases for the missing scenarios
- Ensure all improvements maintain proper formatting and quality standards

This is a final qaulity pass, then view the improved test cases and new test cases

---

## Feature 3: Standalone Ticket Improvement

### How Users Experience It

Sometimes you just need to quickly clarify a vague or poorly written ticket without generating full test cases:

1. You enter a Jira ticket key
2. You click "Improve Ticket"
3. The system restructures the ticket with clear sections
4. You see the improved version with organized acceptance criteria, testing notes, edge cases, and error scenarios
5. You can copy this improved structure back to Jira or use it as reference

### What It Does

The Ticket Improver agent takes any ticket (feature request, bug report, user story) and restructures it:

**Example - Before:**

```
"Users can't login sometimes and it's really annoying. We need to fix this asap."
```

**Example - After:**

- **Summary**: User Authentication - Intermittent Login Failures
- **Description**:
  - **Overview**: Users are experiencing sporadic login failures that prevent access to the application
  - **Current Behavior**: Login attempts sometimes fail without clear error messaging
  - **Expected Behavior**: Login should succeed consistently with valid credentials
- **Acceptance Criteria**:
  - _Functional Requirements_:
    - User can log in successfully with valid credentials 100% of the time
    - System displays specific error messages for different failure types
  - _Error Handling_:
    - Network timeout displays "Connection failed, please try again"
    - Invalid credentials display "Incorrect email or password"
    - Account lockout displays "Account temporarily locked"
- **Testing Notes**: Test under various network conditions (slow 3G, wifi, stable connection)
- **Edge Cases**:
  - Multiple rapid login attempts
  - Login during server maintenance window
  - Session cookies from previous version still present
- **Error Scenarios**:
  - Database connection timeout
  - Authentication service unavailable
  - Expired session tokens
- **Out of Scope**: Social login providers (separate ticket)

This feature is useful when you want to:

- Clarify requirements before starting development
- Improve an old ticket that lacks detail
- Standardize ticket format across your team
- Get a quick quality check on a ticket you wrote

---

## Data Processing

### Jira Integration

The system connects to Jira's REST API to:

- Fetch Epic details
- Fetch all child tickets using a query like "parent = EPIC-123"
- Download attachments directly from Jira

It also cleans up Jira's formatting - converting wiki markup to markdown, stripping HTML tags, preserving code blocks.

### Document Processing

**PDFs:** Uses PyPDF2 library to extract text from all pages and concatenate it into a single string.

**Word Documents:** Uses python-docx library to extract text from all paragraphs while preserving breaks.

**Images:** Currently blocked for security (Phase 2.1). The system notes the filename and size but doesn't process the image content.

### LLM Cost Optimization

The system implements several strategies to minimize LLM API costs while maintaining quality:

**Response Caching:**
The system caches all LLM responses in `.cache/llm/`. If you analyze the same Epic twice, the second time is nearly instant because it retrieves the cached response instead of calling the API again. The cache key is a hash of the prompt content, so if anything changes in the input, it regenerates.

**Prompt Caching (OpenAI):**
For supported models like GPT-4o, the system uses OpenAI's prompt caching feature. This caches the static portions of prompts (like system instructions and epic context) on OpenAI's servers, significantly reducing the tokens billed for repeated requests. Only the dynamic portions (like specific questions or requirements) count as new tokens.

**Token Validation:**
Before making any LLM calls, the system validates that prompts don't exceed token limits. This prevents failed API calls that waste money and ensures prompts are within the model's context window.

**Smart Model Selection:**
- Uses GPT-4o for complex strategic planning and analysis tasks
- Uses GPT-4o-mini (60x cheaper) for simpler tasks like reviews and validations
- Each agent is pre-assigned the most cost-effective model for its specific role

**Structured Outputs with JSON Schema:**
All agents use OpenAI's Structured Outputs feature with strict JSON schemas. Instead of generating free-form text that needs parsing, the LLM directly outputs valid JSON matching the schema. This:
- Reduces output tokens by eliminating verbose explanatory text
- Prevents retry costs from malformed JSON responses
- Enables response_format parameter which gives you a 50% discount on output tokens for models like GPT-4o
- Guarantees consistent, parseable responses without extra validation overhead

**Token Limit Enforcement:**
The system enforces maximum token limits for both inputs and outputs. Before every API call, it validates the prompt size and reserves space for the response. This prevents expensive failed calls and ensures costs stay predictable even with large epics or document uploads.

---

## Security Features

The system implements multiple layers of security to protect sensitive data and prevent attacks when interacting with LLMs.

### Phase 1: Field Whitelisting & Input Sanitization

**Jira Field Whitelisting:**
The system only sends safe, functional Jira fields to the LLM. Fields containing user information (reporter, assignee, creator), audit metadata (created, updated, worklog), or internal tracking data are completely blocked. This prevents accidentally exposing employee names, timestamps, or internal discussions to the AI.

**Attack Pattern Blocking:**
All user input is scanned for common attack vectors:
- **SQL Injection:** Blocks patterns like `'; DROP TABLE`, `UNION SELECT`, etc.
- **XSS Attacks:** Removes `<script>` tags, event handlers, and JavaScript injection attempts
- **Path Traversal:** Blocks `../` and `..\\` patterns that could access unauthorized files
- **Command Injection:** Filters shell metacharacters and command chaining attempts

### Phase 2.1: Maximum Image Security

**Complete Image Blocking:**
All uploaded images are blocked at the highest security level. The system records only metadata (filename, size, type) but never processes or sends image content to the LLM. This prevents accidental exposure of:
- Sensitive UI mockups or wireframes
- Screenshots containing proprietary information
- Architecture diagrams revealing internal systems
- Any visual data that could contain confidential information

### Phase 2.2: PII Detection with Presidio

**50+ Types of PII Detection:**
The system uses Microsoft's Presidio library to automatically detect and pseudonymize personally identifiable information:

- **Personal:** Names, emails, phone numbers, physical addresses
- **Financial:** Credit card numbers, bank accounts, IBAN codes
- **Identity:** Social Security Numbers (SSN), passport numbers, driver's licenses
- **Medical:** Medical record numbers, health insurance identifiers
- **Digital:** IP addresses, usernames, URLs containing PII

**Smart Pseudonymization:**
When PII is detected, it's replaced with synthetic identifiers that preserve the format but remove sensitive data. For example:
- `john.doe@company.com` becomes `[EMAIL_1]`
- `555-123-4567` becomes `[PHONE_1]`
- `4532-1234-5678-9010` becomes `[CREDIT_CARD_1]`

The mapping is stored so transformations can be reversed if needed for legitimate purposes.

### Phase 3: Prompt Injection Prevention

**Multi-Pattern Detection:**
All user-provided text (Jira summaries, descriptions, acceptance criteria) is sanitized to prevent prompt injection attacks. The system detects and neutralizes:

- **Instruction Override Attempts:** Phrases like "ignore previous instructions", "disregard all commands", "forget previous prompts"
- **Role Manipulation:** Attempts to change the AI's role like "you are now an admin", "act as a developer", "system: you are..."
- **Boundary Injection:** Fake message markers like `[system]:`, `[assistant]:`, `<system>`, etc.
- **Jailbreak Attempts:** Phrases like "developer mode", "jailbreak mode", "debug mode: enabled"

When dangerous patterns are detected, they're replaced with `[FILTERED]` to neutralize the attack while preserving context.

### Phase 4: Token Limit Validation

**Prevent Failed API Calls:**
Before making any LLM API call, the system validates that the prompt doesn't exceed the model's context window. Using tiktoken (OpenAI's tokenizer), it:
- Counts tokens in the full prompt (system message + user content + attachments)
- Compares against model limits (128k tokens for GPT-4o/GPT-4o-mini)
- Reserves space for the response (4,000 tokens by default)
- Raises clear errors if limits are exceeded, preventing wasted API calls

This validation happens in `src/ai_tester/utils/token_manager.py:46` and is applied across all agents.

### Phase 5: Error Handling & Silent Failure Prevention

**No More Silent Failures:**
All agents properly raise exceptions when errors occur, rather than returning fake data or hiding problems. For example, if a Jira API call fails, the system raises a clear `RuntimeError` with details, rather than returning a fake "Poor" quality score.

**Structured Error Responses:**
All exceptions include:
- Clear error messages explaining what went wrong
- Context about which operation failed (Jira fetch, LLM call, validation, etc.)
- Actionable guidance for resolving the issue

---

## Technology Stack

**Backend:**

- FastAPI (Python web framework)
- OpenAI GPT-4 (AI models)
- Jira REST API (Atlassian integration)
- PyPDF2 and python-docx (document processing)
- Presidio (PII detection)
- Pydantic (data validation)

**Frontend:**

- React (UI framework)
- Tailwind CSS (styling)
- WebSocket (real-time progress updates)

**Data Storage:**

- File-based cache for LLM responses
- In-memory session data
- Environment variables for configuration

---

## Glossary

**Epic** - A large body of work in Jira containing multiple related tickets (like a big feature or project phase).

**Child Ticket** - A ticket linked to an Epic representing a specific functional requirement.

**Test Ticket** - A ticket that contains testing scope and acceptance criteria (what to verify, not how to implement).

**Test Case** - An individual test scenario with step-by-step instructions and expected results.

**Black-Box Testing** - Testing from a user's perspective without knowing how the code works internally.

**Acceptance Criteria** - Specific conditions that must be met for a feature to be considered complete.

**Coverage Score** - A percentage (0-100) showing how much of the requirements have corresponding tests.

**Edge Case** - An unusual scenario at boundary conditions (like entering 1000 characters in a name field).

**Out of Scope** - Features or requirements explicitly excluded from the current work.
