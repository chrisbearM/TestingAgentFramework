"""
Jira API Client
Extracted from legacy code - handles all Jira operations
"""

import requests
from typing import List, Dict, Optional


# Import from the utils module
try:
    from ai_tester.utils.utils import (
        adf_to_plaintext, 
        clean_jira_text_for_llm,
        extract_text_from_pdf,
        extract_text_from_word,
        encode_image_to_base64
    )
except ImportError:
    # Fallback for testing
    def adf_to_plaintext(adf: dict) -> str: return str(adf)
    def clean_jira_text_for_llm(text: str) -> str: return text
    def extract_text_from_pdf(pdf_bytes: bytes) -> str: return ""
    def extract_text_from_word(docx_bytes: bytes) -> str: return ""
    def encode_image_to_base64(image_bytes: bytes, mime_type: str) -> str: return ""


class JiraClient:
    """Client for interacting with Jira API."""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Jira client.
        
        Args:
            base_url: Jira base URL (e.g., https://yourcompany.atlassian.net)
            email: Your Jira email
            api_token: Your Jira API token
        """
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
        })

    def get_issue(self, key: str) -> Dict:
        """
        Fetch a single Jira issue.
        
        Args:
            key: Issue key (e.g., 'PROJ-123')
            
        Returns:
            Issue data as dictionary
        """
        url = f"{self.base_url}/rest/api/3/issue/{key}"
        r = self.session.get(url, timeout=30)
        if r.status_code == 404:
            raise ValueError("Issue not found or you lack permission.")
        r.raise_for_status()
        return r.json()
    
    def get_attachments(self, issue_key: str) -> List[Dict]:
        """
        Fetch all attachments for an issue.
        
        Args:
            issue_key: Issue key (e.g., 'PROJ-123')
            
        Returns:
            List of attachment metadata dictionaries
        """
        try:
            issue = self.get_issue(issue_key)
            attachments = issue.get("fields", {}).get("attachment", [])
            print(f"DEBUG: Found {len(attachments)} attachments for {issue_key}")
            return attachments
        except Exception as e:
            print(f"DEBUG: Error fetching attachments for {issue_key}: {e}")
            return []
    
    def download_attachment(self, attachment_url: str) -> Optional[bytes]:
        """Download attachment content from URL."""
        try:
            print(f"DEBUG: Downloading attachment from {attachment_url}")
            r = self.session.get(attachment_url, timeout=60)
            r.raise_for_status()
            print(f"DEBUG: Downloaded {len(r.content)} bytes")
            return r.content
        except Exception as e:
            print(f"DEBUG: Error downloading attachment: {e}")
            return None
    
    def process_attachment(self, attachment: Dict) -> Optional[Dict]:
        """
        Process an attachment and extract content.
        
        Args:
            attachment: Attachment metadata from Jira
            
        Returns:
            Dict with filename, type, and content, or None if processing failed
        """
        filename = attachment.get("filename", "unknown")
        mime_type = attachment.get("mimeType", "")
        size = attachment.get("size", 0)
        content_url = attachment.get("content", "")
        
        print(f"DEBUG: Processing attachment: {filename} ({mime_type}, {size} bytes)")
        
        # Skip if too large (> 10MB)
        max_size = 10 * 1024 * 1024
        if size > max_size:
            print(f"DEBUG: Skipping {filename} - too large ({size} bytes)")
            return None
        
        # Download the file
        file_bytes = self.download_attachment(content_url)
        if not file_bytes:
            return None
        
        result = {
            "filename": filename,
            "mime_type": mime_type,
            "size": size
        }
        
        # PDF files
        if mime_type == "application/pdf" or filename.lower().endswith('.pdf'):
            text = extract_text_from_pdf(file_bytes)
            result["type"] = "document"
            result["content"] = text
            return result
        
        # Word documents
        elif mime_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
                          "application/msword"] or filename.lower().endswith(('.docx', '.doc')):
            text = extract_text_from_word(file_bytes)
            result["type"] = "document"
            result["content"] = text
            return result
        
        # Images
        elif mime_type.startswith("image/"):
            if mime_type in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
                base64_data = encode_image_to_base64(file_bytes, mime_type)
                result["type"] = "image"
                result["content"] = base64_data
                result["data_url"] = f"data:{mime_type};base64,{base64_data}"
                return result
            else:
                print(f"DEBUG: Unsupported image format: {mime_type}")
                return None
        
        # Plain text files
        elif mime_type.startswith("text/") or filename.lower().endswith(('.txt', '.md', '.csv')):
            try:
                text = file_bytes.decode('utf-8')
                result["type"] = "document"
                result["content"] = text
                return result
            except Exception as e:
                print(f"DEBUG: Error decoding text file: {e}")
                return None
        
        else:
            print(f"DEBUG: Unsupported file type: {mime_type}")
            return None

    def _agile_epic_issues(self, epic_key: str, fields: List[str]) -> Optional[List[Dict]]:
        """Try to fetch epic issues using Jira Software endpoint."""
        base = f"{self.base_url}/rest/agile/1.0/epic/{epic_key}/issue"
        params = {
            "fields": ",".join(fields),
            "maxResults": "200",
            "startAt": "0",
        }
        issues: List[Dict] = []
        while True:
            r = self.session.get(base, params=params, timeout=30)
            if r.status_code in (401, 403, 404, 405):
                return None
            if r.status_code >= 400:
                return None
            data = r.json()
            batch = data.get("issues", []) or []
            issues.extend(batch)
            if len(batch) < int(params["maxResults"]):
                break
            params["startAt"] = str(int(params["startAt"]) + int(params["maxResults"]))
        return issues

    def _search_once(self, api_ver: str, method: str, jql: str, fields: List[str], max_results: int):
        """Execute a single JQL search request."""
        url = f"{self.base_url}/rest/api/{api_ver}/search"
        if method == "POST":
            payload = {
                "jql": jql,
                "maxResults": max_results,
                "fields": fields
            }
            r = self.session.post(url, json=payload, timeout=30)
        else:
            params = {"jql": jql, "maxResults": str(max_results), "fields": ",".join(fields)}
            r = self.session.get(url, params=params, timeout=30)
        
        if r.status_code == 410:
            return None
        if r.status_code >= 400:
            raise requests.HTTPError(f"{r.status_code} {r.reason}: {r.text}")
        return r.json().get("issues", [])

    def search_jql(self, jql: str, fields: List[str], max_results: int = 200) -> List[Dict]:
        """
        Execute JQL search with automatic fallback across API versions.
        
        Args:
            jql: JQL query string
            fields: List of fields to retrieve
            max_results: Maximum results to return
            
        Returns:
            List of issues matching the query
        """
        variants = [("3", "POST"), ("3", "GET"), ("2", "POST"), ("2", "GET")]
        last_err = None
        all_410 = True
        
        for ver, method in variants:
            try:
                issues = self._search_once(ver, method, jql, fields, max_results)
                if issues is not None:
                    all_410 = False
                    return issues
            except Exception as e:
                all_410 = False
                last_err = e
                continue
        
        if all_410:
            print(f"DEBUG: All search variants returned HTTP 410 for JQL: {jql}")
            return []
        
        raise ValueError(f"Jira search failed for all variants. Last error: {last_err}")

    def get_children_of_epic(self, epic_key: str) -> List[Dict]:
        """
        Get all child issues of an epic using multiple strategies.
        
        Args:
            epic_key: Epic key (e.g., 'PROJ-123')
            
        Returns:
            List of child issues
        """
        fields = ["summary", "description", "issuetype", "status"]

        # Try Agile endpoint first
        agile = self._agile_epic_issues(epic_key, fields)
        if isinstance(agile, list) and agile:
            return agile

        # Fall back to JQL search
        jql_variants = [
            f'parent = {epic_key}',
            f'"Epic Link" = {epic_key}',
            f'issue in childIssuesOf("{epic_key}")',
            f'parentEpic = {epic_key}',
        ]
        seen = set()
        results: List[Dict] = []
        last_err = None
        for jql in jql_variants:
            try:
                issues = self.search_jql(jql, fields, max_results=500)
                for it in issues:
                    key = it.get("key")
                    if key and key not in seen:
                        seen.add(key)
                        results.append(it)
            except Exception as e:
                last_err = e
                continue

        if not results and last_err:
            raise ValueError(
                f"Could not fetch child issues for epic {epic_key}. "
                f"Last error: {last_err}"
            )
        return results
    
    def get_initiative_details(self, initiative_key: str) -> Dict:
        """
        Fetch an Initiative and all its related Epics and their children.
        
        Args:
            initiative_key: Initiative key (e.g., 'PROJ-123')
            
        Returns:
            Dict with initiative and epics data
        """
        # Get the Initiative
        initiative = self.get_issue(initiative_key)
        init_fields = initiative.get("fields", {})
        init_summary = init_fields.get("summary", initiative_key)
        init_desc = init_fields.get("description")
        
        # Parse description
        if isinstance(init_desc, dict) and init_desc.get("type") == "doc":
            init_desc_plain = adf_to_plaintext(init_desc)
        elif isinstance(init_desc, str):
            init_desc_plain = init_desc
        else:
            init_desc_plain = ""
        
        init_desc_plain = clean_jira_text_for_llm(init_desc_plain)
        
        epic_issues = []
        seen_epics = set()
        
        # Check for issue links
        issue_links = init_fields.get("issuelinks", [])
        for link in issue_links:
            linked_issue = link.get("outwardIssue") or link.get("inwardIssue")
            if linked_issue:
                linked_key = linked_issue.get("key")
                linked_type = linked_issue.get("fields", {}).get("issuetype", {}).get("name", "")
                
                if "epic" in linked_type.lower() and linked_key not in seen_epics:
                    seen_epics.add(linked_key)
                    try:
                        epic_full = self.get_issue(linked_key)
                        epic_issues.append(epic_full)
                    except Exception as e:
                        print(f"DEBUG: Could not fetch Epic {linked_key}: {e}")
        
        # Check subtasks
        subtasks = init_fields.get("subtasks", [])
        for subtask in subtasks:
            subtask_key = subtask.get("key")
            subtask_type = subtask.get("fields", {}).get("issuetype", {}).get("name", "")
            if "epic" in subtask_type.lower() and subtask_key not in seen_epics:
                seen_epics.add(subtask_key)
                try:
                    epic_full = self.get_issue(subtask_key)
                    epic_issues.append(epic_full)
                except Exception as e:
                    print(f"DEBUG: Could not fetch Epic {subtask_key}: {e}")
        
        # Try JQL fallback
        if not epic_issues:
            try:
                jql = f'parent = {initiative_key} AND issuetype = Epic'
                epic_issues = self.search_jql(jql, ["summary", "description"], max_results=100)
            except Exception as e:
                print(f"DEBUG: JQL search for epics failed: {e}")
        
        # Process each epic and get its children
        processed_epics = []
        for epic in epic_issues:
            epic_key = epic.get("key")
            epic_fields = epic.get("fields", {})
            epic_summary = epic_fields.get("summary", epic_key)
            epic_desc = epic_fields.get("description")
            
            # Parse epic description
            if isinstance(epic_desc, dict) and epic_desc.get("type") == "doc":
                epic_desc_plain = adf_to_plaintext(epic_desc)
            elif isinstance(epic_desc, str):
                epic_desc_plain = epic_desc
            else:
                epic_desc_plain = ""
            
            epic_desc_plain = clean_jira_text_for_llm(epic_desc_plain)
            
            # Get epic children
            try:
                children = self.get_children_of_epic(epic_key) if epic_key else []
            except Exception as e:
                print(f"DEBUG: Could not fetch children for {epic_key}: {e}")
                children = []
            
            processed_epics.append({
                "key": epic_key,
                "summary": epic_summary,
                "description": epic_desc_plain,
                "children": children
            })
        
        return {
            "initiative": {
                "key": initiative_key,
                "summary": init_summary,
                "description": init_desc_plain
            },
            "epics": processed_epics
        }
