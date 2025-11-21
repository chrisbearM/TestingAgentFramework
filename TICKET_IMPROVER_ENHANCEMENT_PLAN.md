# Ticket Improver Enhancement Plan

**Goal**: Surpass Atlassian Rovo's ticket improvement quality

**Date**: January 20, 2025

---

## Analysis: Rovo vs Our Current Implementation

### Rovo's Key Strengths

1. **Grouped Acceptance Criteria** ⭐⭐⭐ CRITICAL
   - ACs organized into themed sections
   - Sections: Form Rendering, Field Validation, Button States, Session Behavior, Edge Cases, Accessibility
   - Easier to scan, understand, and test

2. **Accessibility Section** ⭐⭐⭐ MISSING ENTIRELY
   - Dedicated AC section for accessibility
   - Keyboard navigation
   - Screen reader support

3. **Out of Scope Section** ⭐⭐
   - Explicitly states what's NOT included
   - Prevents scope creep
   - Currently we exclude this!

4. **Testing Notes Section** ⭐⭐
   - Separate from ACs
   - Test strategy guidance
   - Browser/device compatibility

5. **Integrated Edge Cases** ⭐
   - Edge cases within AC sections
   - Not separated
   - More natural flow

6. **Comprehensive Technical Considerations** ⭐⭐
   - Future-proofing considerations
   - Security implications
   - Browser compatibility
   - Error handling strategy

### Our Current Strengths

1. ✅ **User Story Format** - Proper "As a/I want/so that"
2. ✅ **Markdown Structure** - Clean headers and formatting
3. ✅ **Style Matching** - Matches original author's tone
4. ✅ **Format Consistency** - Single AC format throughout

---

## Enhancement Strategy

### Phase 1: Critical Improvements (High Impact)

#### 1.1 Add AC Grouping/Categorization

**Current**:
```
Acceptance Criteria
1. Verify the pop-up form displays with the title 'Enquiry'.
2. Confirm the close button (x) closes the pop-up...
3. Check that the introductory text is displayed correctly.
4. Ensure 'First name', 'Last name', and 'Company name' fields...
... (flat list of 11 items)
```

**Enhanced**:
```
Acceptance Criteria

### Form Rendering & Data Population
- The popup form displays all specified fields and UI elements.
- "Interested In" list is populated from the list builder.

### Field Validation
- Required fields are visually indicated.
- Email field validates for standard email format.
- Phone number validates for mobile format.
- Invalid fields display error messages.

### Button States
- "Send" button disabled until all required fields valid.
- "Cancel" and "Close" retain data in session.

### Session Behavior
- Closing popup retains data in current session.
- Browser refresh/close clears all data.

### Edge Cases & Error Scenarios
- Invalid/incomplete fields keeps "Send" disabled.
- Empty "Interested In" list prevents submission.
- Region load failure displays error.

### Accessibility
- All fields accessible via keyboard navigation.
- Labels associated with inputs for screen readers.
```

**Implementation**:
- After generating ACs, use LLM to categorize them
- Common categories: UI/Display, Data/Validation, Behavior, Edge Cases, Accessibility, Security, Performance
- Group related ACs under category headers

#### 1.2 Add Accessibility ACs

**Add to prompt**:
```
ALWAYS include accessibility acceptance criteria covering:
- Keyboard navigation (tab order, enter/escape keys)
- Screen reader support (ARIA labels, semantic HTML)
- Focus indicators
- Color contrast (if UI heavy)
- Error announcements for assistive technologies
```

**Auto-generate if not present**:
- "All interactive elements accessible via keyboard"
- "Form labels properly associated with inputs"
- "Error messages announced to screen readers"
- "Focus indicators visible on all interactive elements"

#### 1.3 Add "Out of Scope" Section

**Current**: Explicitly excluded in system prompt

**Enhanced**: Add as optional section
```
## Out of Scope
- Backend submission or Salesforce integration
- Persistent storage beyond browser session
- Advanced validation (phone number international formats)
```

**Implementation**:
- Analyze description for "not included", "future work", "out of scope"
- Auto-generate based on what's mentioned but not required
- If unclear, infer from typical project scope boundaries

#### 1.4 Add "Testing Notes" Section

**New section after Technical Notes**:
```
## Testing Notes
- Manual and automated tests should cover all acceptance criteria
- Test across supported browsers (Chrome, Firefox, Safari, Edge)
- Test on mobile and desktop viewports
- Verify session storage behavior in different browsers
- Test with keyboard-only navigation
```

**Implementation**:
- Generate based on ticket complexity
- Include browser/device testing if UI involved
- Include integration testing if multiple systems
- Include accessibility testing always

---

### Phase 2: Quality Improvements (Medium Impact)

#### 2.1 Enhanced Technical Considerations

**Current**:
```
Technical Notes
Ensure that the form is responsive and accessible, following best practices for user interface design.
```

**Enhanced**:
```
## Technical Considerations
- Use client-side validation for all fields
- Store form data in sessionStorage (not localStorage)
- Ensure responsive design (mobile-first approach)
- Handle errors gracefully (dropdown load failures, storage unavailable)
- Prepare for future Salesforce integration (structure code for easy extension)
- Ensure no PII persisted beyond session (GDPR compliance)
- Use debouncing for email/phone validation (improve UX)
```

**Add to prompt**:
```
Technical Considerations should include:
1. Implementation approach (libraries, patterns)
2. Data storage strategy
3. Error handling approach
4. Future extensibility considerations
5. Security/privacy implications
6. Performance optimizations
7. Browser compatibility requirements
```

#### 2.2 Integrate Edge Cases into ACs

**Current**: Separate sections

**Enhanced**: Include as subsection within ACs
```
### Edge Cases & Error Scenarios
- Attempting to submit with invalid fields keeps "Send" disabled
- Empty "Interested In" list displays message and disables submission
- Region list load failure displays error and disables field
- Invalid email/phone shows inline errors and prevents submission
- Session expiry/storage unavailable notifies user
```

---

### Phase 3: Advanced Features (Nice to Have)

#### 3.1 Domain-Specific AC Templates

**Create templates for common ticket types**:

- **Form/UI tickets**: Form Rendering, Field Validation, Button States, Accessibility
- **API tickets**: Request/Response, Authentication, Error Handling, Rate Limiting
- **Integration tickets**: Data Flow, Error Handling, Rollback, Monitoring
- **Performance tickets**: Load Time, Resource Usage, Scaling, Degradation

**Implementation**:
- Detect ticket type from summary/description keywords
- Apply relevant template for AC categorization
- Ensure all categories covered

#### 3.2 Requirement Traceability

**Add section linking ACs to requirements**:
```
## Requirements Traceability
| Requirement | Acceptance Criteria |
|-------------|-------------------|
| R1: Required field validation | AC-2.1, AC-2.2 |
| R2: Session data retention | AC-4.1, AC-4.2 |
```

#### 3.3 Risk Analysis

**Add optional section**:
```
## Risk Analysis
- **HIGH**: Form data loss on refresh (user frustration) → Mitigate with session warning
- **MEDIUM**: Email validation false positives → Use standard regex, allow override
- **LOW**: Region dropdown slow to load → Add loading indicator
```

---

## Implementation Plan

### Step 1: Update Pydantic Model (10 minutes)

Add new fields to `ImprovedTicket`:
```python
class ImprovedTicket(BaseModel):
    summary: str
    description: str  # Now includes Scope and Out of Scope
    acceptance_criteria: Dict[str, List[str]]  # Changed to grouped format
    accessibility_criteria: List[str] = Field(default_factory=list)
    edge_cases: List[str] = Field(default_factory=list)  # Can be removed if integrated
    error_scenarios: List[str] = Field(default_factory=list)  # Can be removed if integrated
    technical_notes: str = ""
    testing_notes: str = Field(default="", description="Testing strategy and considerations")
    out_of_scope: List[str] = Field(default_factory=list, description="What's explicitly excluded")
```

### Step 2: Update System Prompt (20 minutes)

**Enhanced structure**:
```
DESCRIPTION FORMAT:
## Background - Context and why this work is needed
## User Story - As a [role], I want [feature], so that [benefit]
## Scope - What IS included (bullet points)
## Requirements - Detailed functional requirements
## Out of Scope - What is NOT included (prevents scope creep)

ACCEPTANCE CRITERIA FORMAT - GROUPED:
Organize ACs into logical categories based on ticket type:

For UI/Form tickets:
### UI/Display & Data
### Field Validation
### User Interactions
### Session/State Management
### Edge Cases & Error Scenarios
### Accessibility

For API tickets:
### Request Handling
### Response Format
### Authentication/Authorization
### Error Handling
### Performance

For Integration tickets:
### Data Flow
### Error Handling & Rollback
### Monitoring & Logging
### Edge Cases

ALWAYS include Accessibility section if UI involved
ALWAYS include Edge Cases & Error Scenarios

TECHNICAL CONSIDERATIONS:
- Implementation approach (libraries, frameworks, patterns)
- Data storage/state management
- Error handling strategy
- Future extensibility
- Security/privacy implications
- Performance considerations
- Browser/platform compatibility

TESTING NOTES:
- Test strategy (manual, automated, integration)
- Browser/device coverage
- Accessibility testing requirements
- Edge case testing approach
- Performance testing (if applicable)
```

### Step 3: Post-Processing AC Grouping (30 minutes)

**Add function to categorize ACs**:
```python
def _categorize_acceptance_criteria(
    self,
    acs: List[str],
    ticket_type: str
) -> Dict[str, List[str]]:
    """
    Use LLM to categorize ACs into logical groups

    Returns:
    {
        "UI/Display & Data": ["AC1", "AC2"],
        "Field Validation": ["AC3", "AC4"],
        ...
    }
    """
    # Use quick LLM call to categorize
    # Or use pattern matching for common categories
```

### Step 4: Testing & Validation (20 minutes)

**Test cases**:
1. Form/UI ticket (like the example) → Should have 6-7 AC categories
2. API ticket → Should have 5-6 AC categories
3. Integration ticket → Should have 4-5 AC categories
4. Simple bug fix → Should have minimal categorization

---

## Success Metrics

### Quantitative
- **AC Categorization**: 100% of improved tickets have grouped ACs
- **Accessibility Coverage**: 100% of UI tickets have accessibility ACs
- **Out of Scope**: 80%+ of tickets have out of scope section
- **Testing Notes**: 100% of tickets have testing notes

### Qualitative (User Feedback)
- "Easier to understand than Rovo" ✅
- "More comprehensive coverage" ✅
- "Better organized for testing" ✅
- "Matches our team's style" ✅

---

## Rollout Plan

### Phase 1 (Week 1): Core Improvements
- [ ] Update Pydantic model
- [ ] Update system prompt with new structure
- [ ] Add AC categorization logic
- [ ] Add accessibility AC generation
- [ ] Test with 5 sample tickets

### Phase 2 (Week 2): Polish & Validation
- [ ] Add "Out of Scope" detection
- [ ] Add "Testing Notes" generation
- [ ] Enhanced Technical Considerations
- [ ] Test with 20 diverse tickets
- [ ] A/B test vs Rovo on 10 tickets

### Phase 3 (Week 3): Advanced Features
- [ ] Domain-specific templates
- [ ] Requirement traceability
- [ ] Risk analysis (optional)
- [ ] Production rollout

---

## Expected Outcome

**Before**:
- Flat list of 10-15 ACs
- Basic technical notes
- Separated edge cases/errors
- No accessibility focus
- No scope clarity

**After**:
- Grouped ACs (5-7 categories)
- Comprehensive technical considerations
- Integrated edge cases
- Dedicated accessibility section
- Clear scope boundaries
- Testing guidance

**Result**: Surpasses Rovo in organization, comprehensiveness, and testability while maintaining style consistency.

---

## Next Steps

1. Review this plan and approve approach
2. Implement Phase 1 changes
3. Test with original ticket example
4. Compare output to Rovo
5. Iterate based on feedback

**Estimated Total Time**: 2-3 hours for Phase 1 implementation
