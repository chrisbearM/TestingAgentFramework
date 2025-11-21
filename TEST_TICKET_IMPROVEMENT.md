# Test Ticket Improvement - UEX-326 Example

**Goal**: Test enhanced ticket improver against original ticket and compare to Rovo

---

## Original Ticket (UEX-326)

**Summary**: [ECO] Ecosystem catalogue basic enquiry form

**Description**:
```
Introduction

In UEX-221: [ECO] Build a 'interested in ...' query list
Done
 a query list was created

This task is about

creating a basic Enquiry form  - Submission of the form not included

adding list details to the form



Implementation

Please create a basic Enquiry form that can be used for later submission to support (SalesForce integration not included)

The pop up  form should have:

Heading 'Enquiry'

x to close button, with hover over name 'Close'.

will close the pop up but keep the details while the session is still ongoing

Introduction text 'Please complete the form below, and a Unity expert will be in touch shortly to assist you with your selected solutions.'

Users query fields  (Basics for now)

'First name'  - Required & Free text

'Last name' - Required & Free text

'Company name' - Required  & free text

'Region' - Required, Drop down list of Regions (With ability to search the list)

'Email' - Required,  with testing for a valid email

'Phone number' - Optional, with testing for a valid mobile number (basic validation)

'Interested in' list

List the items from the list builder, solution name only

'Cancel' button

Will close the pop up but will remember the details while in session

'Send' button

default is Deactivate

and will only become active if all the required field have been entered.

Form details will not be saved out of session, the refreshing or closing the browser will lose the data

image-20250825-100751.png
image-20250825-101552.png
Grooming Notes: Dev implemented, estimating for testing only.
```

**Acceptance Criteria**:
```
Ensure the form

lists the selected interested solutions

User can close the form and change selection, when the form opens the list should load accordingly

The required fields are checked and show as required

The fields that can are checked for Validity - Email and Mobile number

Send button is disabled and active according to the
```

---

## Rovo's Improved Version

**Description**:
```
Background:
As part of UEX-221: [ECO] Build a 'interested in ...' query list, a query list was created. This story focuses on building a basic "Enquiry" form as a popup modal, which will later support submission to Salesforce (integration not included in this ticket). The form will allow users to express interest in solutions from the catalogue.

Scope:

Implement a popup "Enquiry" form UI.
Populate the "Interested in" list from the existing list builder.
No backend submission or data persistence beyond session scope.

Requirements
Form Fields:

First Name (Required, free text)
Last Name (Required, free text)
Company Name (Required, free text)
Region (Required, dropdown with search)
Email (Required, must be valid format)
Phone Number (Optional, must be valid mobile format)
Interested In (Multi-select, populated from list builder)

UI Elements:

Heading: "Enquiry"
Introduction Text: "Please complete the form below, and a Unity expert will be in touch shortly to assist you with your selected solutions."
Close Button: 'X' with hover tooltip "Close" (closes popup, retains data in session)
Cancel Button: Closes popup, retains data in session
Send Button: Disabled by default, enabled only when all required fields are valid

Session Handling:

Form data is retained only for the current browser session.
Refreshing or closing the browser will clear all form data.
```

**Acceptance Criteria**:
```
Form Rendering & Data Population

The popup form displays all specified fields and UI elements.
"Interested In" list is populated from the list builder, showing solution names only.

Field Validation

Required fields are visually indicated.
Email field validates for standard email format (e.g., user@domain.com).
Phone number field validates for mobile number format (e.g., digits only, min/max length, optional country code).
Invalid fields display appropriate error messages.

Button States

"Send" button is disabled until all required fields are valid.
"Send" button becomes enabled only when all validations pass.
"Cancel" and "Close" buttons close the popup and retain form data in session.

Session Behavior

Closing the popup and reopening during the same session restores previous input.
Refreshing or closing the browser clears all form data.

Edge Cases & Error Scenarios

Attempting to submit with invalid or incomplete required fields keeps "Send" disabled.
If the "Interested In" list is empty, the form should display a message or disable submission.
If the region list fails to load, display an error and disable region selection.
If the user enters an invalid email or phone number, show inline error messages and prevent submission.
If the session expires or storage is unavailable, notify the user that data cannot be retained.

Accessibility

All form fields and buttons are accessible via keyboard navigation.
Form labels are associated with inputs for screen readers.
```

**Technical Considerations**:
```
Use client-side validation for all fields.
Store form data in sessionStorage or a suitable in-memory store.
Ensure the form is responsive and works on all supported browsers.
Handle errors gracefully (e.g., failed dropdown loads, storage issues).
Prepare for future integration with Salesforce (structure code for easy extension).
Ensure no personally identifiable information is persisted beyond the session.
```

**Out of Scope**:
```
Backend submission or integration with Salesforce.
Persistent storage beyond the browser session.
```

**Testing Notes**:
```
Manual and automated tests should cover all acceptance criteria, including edge cases and error scenarios.
Test with various browsers and devices for compatibility.
```

---

## Our Previous Version

**Summary**: [ECO] Ecosystem catalogue basic enquiry form with user input validation

**Description**:
```
## Background

This task focuses on creating a basic enquiry form that will allow users to submit their queries. The form will not include submission functionality at this stage, as it is intended for future integration with support systems. The aim is to gather user information and their areas of interest for follow-up by Unity experts.

## User Story

As a user, I want to fill out an enquiry form so that I can receive assistance from a Unity expert regarding my selected solutions.

## Requirements

- Create a pop-up form titled 'Enquiry'.
- Include a close button (x) with hover text 'Close' that will close the pop-up while retaining the entered details during the session.
- Display introductory text: 'Please complete the form below, and a Unity expert will be in touch shortly to assist you with your selected solutions.'
- Include the following user query fields:
  - 'First name' - Required & Free text
  - 'Last name' - Required & Free text
  - 'Company name' - Required & Free text
  - 'Region' - Required, Drop down list of Regions with search capability
  - 'Email' - Required, with validation for a valid email format
  - 'Phone number' - Optional, with basic validation for a valid mobile number
- Include an 'Interested in' list that displays items from the list builder, showing only the solution names.
- Add a 'Cancel' button that will close the pop-up while retaining the entered details during the session.
- Add a 'Send' button that is deactivated by default and becomes active only when all required fields are filled out.
- Ensure that form details are not saved outside the session; refreshing or closing the browser will result in data loss.
```

**Acceptance Criteria**:
```
1. Verify the pop-up form displays with the title 'Enquiry'.
2. Confirm the close button (x) closes the pop-up without losing entered details during the session.
3. Check that the introductory text is displayed correctly.
4. Ensure 'First name', 'Last name', and 'Company name' fields are marked as required and accept free text input.
5. Validate that the 'Region' field is a required drop-down list with search functionality.
6. Confirm that the 'Email' field requires a valid email format and is marked as required.
7. Ensure the 'Phone number' field is optional and validates for a basic mobile number format.
8. Verify the 'Interested in' list displays items from the list builder with only solution names.
9. Confirm the 'Cancel' button closes the pop-up while retaining entered details during the session.
10. Ensure the 'Send' button is deactivated by default and activates only when all required fields are filled.
11. Validate that refreshing or closing the browser results in loss of entered data.
```

**Edge Cases**:
```
User enters invalid email format; system should display an error message.
User enters invalid mobile number; system should display an error message.
User attempts to submit the form without filling required fields; system should prevent submission and highlight missing fields.
```

**Error Scenarios**:
```
If the user closes the browser, all entered data should be lost.
If the user refreshes the page, all entered data should be lost.
```

**Technical Notes**:
```
Ensure that the form is responsive and accessible, following best practices for user interface design.
```

---

## Expected New Output Structure

Based on enhanced prompt, we expect:

**Description** with 5 sections:
1. Background
2. User Story
3. Scope
4. Requirements
5. Out of Scope

**Acceptance Criteria** grouped into ~6 categories:
1. Form Rendering & Data Population
2. Field Validation
3. User Interactions & Button States
4. Session/State Management
5. Edge Cases & Error Scenarios
6. Accessibility

**Technical Notes**: 7-10 specific bullet points

**Testing Notes**: Comprehensive testing strategy

**Out of Scope**: 2-3 explicit exclusions

---

## Testing Instructions

1. Test via UI:
   - Navigate to ticket improvement page
   - Load ticket UEX-326
   - Click "Improve Ticket"
   - Review generated output

2. Compare to Rovo:
   - Check AC grouping (should have 6 categories)
   - Check accessibility section (should be present)
   - Check Out of Scope section (should list 2-3 items)
   - Check Technical Notes (should have 7-10 points)
   - Check Testing Notes (should cover browser, device, accessibility)

3. Success Criteria:
   - ✅ ACs grouped into themed categories
   - ✅ Accessibility section present
   - ✅ Out of Scope section present
   - ✅ Technical Notes comprehensive (7+ points)
   - ✅ Testing Notes detailed
   - ✅ Matches or exceeds Rovo's organization
   - ✅ Maintains original author's style

---

## Notes

Test this in the UI to see the actual output. The enhanced prompt should produce much better organized tickets that surpass Rovo's quality.
