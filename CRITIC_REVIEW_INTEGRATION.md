# Critic Review Integration

## Overview

The critic review system has been properly integrated into `generate_test_cases.py` to ensure high-quality test case generation with automatic retry and improvement mechanisms.

## How It Works

### 1. Critic Review Function (`critic_review`)
Located at lines 15-72 in `generate_test_cases.py`

**Purpose**: Reviews generated test cases and rejects nonsensical or low-quality ones

**Checks performed**:
- Test case count matches requirements × 3 formula
- Tests are realistic and executable
- Tests actually test what they claim to test
- Steps are detailed enough (3-8 steps per test)
- No repetitive or redundant tests

**Returns**:
```json
{
  "approved": true/false,
  "overall_quality": "excellent|good|needs_improvement|poor",
  "confidence_score": 0-100,
  "issues_found": [
    {
      "test_case_title": "...",
      "description": "What's wrong",
      "suggestion": "How to fix"
    }
  ],
  "summary": "Brief review summary",
  "recommendation": "Approve or list specific fixes"
}
```

### 2. Retry Mechanism (`generate_test_cases_with_retry`)
Located at lines 74-160 in `generate_test_cases.py`

**Key Features**:

1. **Automatic Retry**: If critic rejects test cases (approved=false), automatically regenerates with specific feedback
2. **Max Retries**: Configurable maximum retry attempts (default: 2)
3. **Feedback Loop**: Each retry includes detailed issues and suggestions from previous attempt
4. **Progressive Improvement**: Appends critic feedback to prompt for targeted improvements

**Workflow**:
```
Attempt 1: Generate test cases
         ↓
   Critic Review
         ↓
   Rejected? → Retry with feedback
         ↓
Attempt 2: Regenerate with improvements
         ↓
   Critic Review
         ↓
   Rejected? → Retry again
         ↓
Attempt 3: Final attempt
         ↓
   Return results (approved or not)
```

### 3. Integration in Main Function
Located at lines 396-414 in `generate_test_cases.py`

**Usage**:
```python
result, critic_data = generate_test_cases_with_retry(
    llm=llm,
    sys_prompt=sys_prompt,
    user_prompt=user_prompt,
    summary=summary,
    requirements_for_review=None,
    max_retries=2
)
```

## Example Output

### When Test Cases Are Approved
```
👨‍⚖️  Critic Review (Attempt 1)...
   Quality:     GOOD
   Confidence:  85%
   Status:      ✅ APPROVED

   ✅ AI generation complete!
```

### When Test Cases Are Rejected (with retry)
```
👨‍⚖️  Critic Review (Attempt 1)...
   Quality:     NEEDS_IMPROVEMENT
   Confidence:  60%
   Status:      ⚠️  HAS ISSUES

   ❌ Test cases rejected. Issues found:
      1. REQ-001 Positive: Form displays heading 'Enquiry'
         Problem: Only 1 step, needs 3-8 steps for thoroughness
         Fix: Add steps for opening app, navigating to form, verifying heading text

      2. REQ-001 Negative: Form heading is missing
         Problem: Nonsensical negative test - can't test missing heading
         Fix: Change to test incorrect heading text or styling issues

   💡 Recommendation: Add more detailed steps and fix nonsensical negative tests

🔄 Retry attempt 1/2...
   Regenerating test cases based on critic feedback...

👨‍⚖️  Critic Review (Attempt 2)...
   Quality:     GOOD
   Confidence:  82%
   Status:      ✅ APPROVED
```

### When Max Retries Reached
```
👨‍⚖️  Critic Review (Attempt 3)...
   Quality:     NEEDS_IMPROVEMENT
   Confidence:  70%
   Status:      ⚠️  HAS ISSUES

   ⚠️  Max retries reached. Proceeding with current results despite issues.
   Issues summary:
      1. REQ-005 Edge Case: First name field with maximum characters
      2. REQ-006 Negative: Last name field is left empty
      3. REQ-011 Positive: 'Interested in' list displays solution names
```

## Benefits

1. **Quality Assurance**: Ensures test cases meet minimum quality standards
2. **Automatic Improvement**: No manual intervention needed for retries
3. **Specific Feedback**: AI learns from detailed issue descriptions
4. **Prevents Nonsensical Tests**: Catches and fixes illogical test cases
5. **Step Completeness**: Enforces 3-8 steps per test case
6. **Formula Validation**: Verifies requirements × 3 = test cases

## Configuration

You can adjust the retry behavior:

```python
# In generate_test_cases function (line 397)
result, critic_data = generate_test_cases_with_retry(
    llm=llm,
    sys_prompt=sys_prompt,
    user_prompt=user_prompt,
    summary=summary,
    requirements_for_review=None,
    max_retries=2  # Change this to 1 or 3 as needed
)
```

## Common Issues Caught by Critic

1. **Too Few Steps**: Test cases with only 1-2 steps
2. **Nonsensical Negative Tests**: Tests that don't make logical sense
3. **Wrong Test Count**: Not following requirements × 3 formula
4. **Repetitive Tests**: Multiple tests checking the same thing
5. **Unrealistic Tests**: Tests that can't actually be executed
6. **Poor Step Details**: Steps without clear actions or expectations

## Limitations

- Maximum 3 attempts (1 initial + 2 retries)
- If critic review fails technically, proceeds with results
- On final attempt, proceeds even if not approved
- Each retry increases API costs and execution time

## Future Improvements

- [ ] Add configurable approval threshold
- [ ] Support partial approval (approve some tests, reject others)
- [ ] Track improvement metrics across attempts
- [ ] Save all attempts for comparison
- [ ] Add option for manual review before retry
