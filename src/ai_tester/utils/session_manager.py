"""
Session Manager for Draft Storage
Manages user sessions and draft data with TTL for auto-cleanup
"""
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from threading import Lock
import uuid


class SessionManager:
    """
    In-memory session manager for draft storage.
    Stores drafts by session_id with automatic expiration.
    """

    def __init__(self, ttl_hours: int = 24):
        """
        Initialize session manager.

        Args:
            ttl_hours: Time-to-live in hours (default: 24 hours)
        """
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
        self._ttl = timedelta(hours=ttl_hours)

    def save_draft(
        self,
        session_id: str,
        data_type: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Save a draft for a session.

        Args:
            session_id: Session identifier (typically user email or session token)
            data_type: Type of draft ('epic_analysis', 'test_tickets', 'test_cases')
            data: Draft data to save
            metadata: Optional metadata (epic_key, timestamp, etc.)

        Returns:
            Draft ID
        """
        with self._lock:
            draft_id = str(uuid.uuid4())

            if session_id not in self._sessions:
                self._sessions[session_id] = {
                    'drafts': {},
                    'created_at': datetime.now(),
                    'last_accessed': datetime.now()
                }

            draft = {
                'id': draft_id,
                'data_type': data_type,
                'data': data,
                'metadata': metadata or {},
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'expires_at': datetime.now() + self._ttl
            }

            self._sessions[session_id]['drafts'][draft_id] = draft
            self._sessions[session_id]['last_accessed'] = datetime.now()

            print(f"DEBUG SessionManager: Saved draft {draft_id} for session {session_id} (type: {data_type})")
            return draft_id

    def load_draft(self, session_id: str, draft_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a specific draft.

        Args:
            session_id: Session identifier
            draft_id: Draft identifier

        Returns:
            Draft data if found and not expired, None otherwise
        """
        with self._lock:
            if session_id not in self._sessions:
                print(f"DEBUG SessionManager: Session {session_id} not found")
                return None

            session = self._sessions[session_id]

            if draft_id not in session['drafts']:
                print(f"DEBUG SessionManager: Draft {draft_id} not found in session {session_id}")
                return None

            draft = session['drafts'][draft_id]

            # Check if expired
            if datetime.now() > draft['expires_at']:
                print(f"DEBUG SessionManager: Draft {draft_id} expired")
                del session['drafts'][draft_id]
                return None

            # Update last accessed
            session['last_accessed'] = datetime.now()

            print(f"DEBUG SessionManager: Loaded draft {draft_id} for session {session_id}")
            return draft

    def list_drafts(
        self,
        session_id: str,
        data_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all drafts for a session.

        Args:
            session_id: Session identifier
            data_type: Optional filter by data type

        Returns:
            List of draft summaries (without full data)
        """
        with self._lock:
            if session_id not in self._sessions:
                return []

            session = self._sessions[session_id]
            now = datetime.now()

            # Clean up expired drafts
            expired_ids = [
                draft_id for draft_id, draft in session['drafts'].items()
                if now > draft['expires_at']
            ]
            for draft_id in expired_ids:
                del session['drafts'][draft_id]

            # Build draft list
            drafts = []
            for draft_id, draft in session['drafts'].items():
                if data_type and draft['data_type'] != data_type:
                    continue

                drafts.append({
                    'id': draft['id'],
                    'data_type': draft['data_type'],
                    'metadata': draft['metadata'],
                    'created_at': draft['created_at'].isoformat(),
                    'updated_at': draft['updated_at'].isoformat(),
                    'expires_at': draft['expires_at'].isoformat()
                })

            # Sort by most recent first
            drafts.sort(key=lambda x: x['updated_at'], reverse=True)

            print(f"DEBUG SessionManager: Listed {len(drafts)} drafts for session {session_id}")
            return drafts

    def update_draft(
        self,
        session_id: str,
        draft_id: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update an existing draft.

        Args:
            session_id: Session identifier
            draft_id: Draft identifier
            data: Updated draft data
            metadata: Optional updated metadata

        Returns:
            True if updated successfully, False otherwise
        """
        with self._lock:
            if session_id not in self._sessions:
                return False

            session = self._sessions[session_id]

            if draft_id not in session['drafts']:
                return False

            draft = session['drafts'][draft_id]

            # Check if expired
            if datetime.now() > draft['expires_at']:
                del session['drafts'][draft_id]
                return False

            # Update draft
            draft['data'] = data
            if metadata:
                draft['metadata'].update(metadata)
            draft['updated_at'] = datetime.now()
            session['last_accessed'] = datetime.now()

            print(f"DEBUG SessionManager: Updated draft {draft_id} for session {session_id}")
            return True

    def delete_draft(self, session_id: str, draft_id: str) -> bool:
        """
        Delete a draft.

        Args:
            session_id: Session identifier
            draft_id: Draft identifier

        Returns:
            True if deleted successfully, False otherwise
        """
        with self._lock:
            if session_id not in self._sessions:
                return False

            session = self._sessions[session_id]

            if draft_id not in session['drafts']:
                return False

            del session['drafts'][draft_id]
            session['last_accessed'] = datetime.now()

            print(f"DEBUG SessionManager: Deleted draft {draft_id} for session {session_id}")
            return True

    def clear_session(self, session_id: str) -> bool:
        """
        Clear all drafts for a session.

        Args:
            session_id: Session identifier

        Returns:
            True if cleared successfully, False otherwise
        """
        with self._lock:
            if session_id not in self._sessions:
                return False

            del self._sessions[session_id]
            print(f"DEBUG SessionManager: Cleared session {session_id}")
            return True

    def cleanup_expired(self) -> int:
        """
        Remove expired sessions and drafts.

        Returns:
            Number of items removed
        """
        with self._lock:
            now = datetime.now()
            removed_count = 0

            # Remove expired sessions (not accessed in 7 days)
            session_expiry = now - timedelta(days=7)
            expired_sessions = [
                session_id for session_id, session in self._sessions.items()
                if session['last_accessed'] < session_expiry
            ]
            for session_id in expired_sessions:
                del self._sessions[session_id]
                removed_count += 1

            # Remove expired drafts in remaining sessions
            for session_id, session in self._sessions.items():
                expired_drafts = [
                    draft_id for draft_id, draft in session['drafts'].items()
                    if now > draft['expires_at']
                ]
                for draft_id in expired_drafts:
                    del session['drafts'][draft_id]
                    removed_count += 1

            if removed_count > 0:
                print(f"DEBUG SessionManager: Cleaned up {removed_count} expired items")

            return removed_count

    def get_stats(self) -> Dict[str, Any]:
        """
        Get session manager statistics.

        Returns:
            Dictionary with statistics
        """
        with self._lock:
            total_sessions = len(self._sessions)
            total_drafts = sum(len(session['drafts']) for session in self._sessions.values())

            now = datetime.now()
            active_drafts = sum(
                1 for session in self._sessions.values()
                for draft in session['drafts'].values()
                if now <= draft['expires_at']
            )

            return {
                'total_sessions': total_sessions,
                'total_drafts': total_drafts,
                'active_drafts': active_drafts,
                'expired_drafts': total_drafts - active_drafts,
                'ttl_hours': self._ttl.total_seconds() / 3600
            }


# Global session manager instance
session_manager = SessionManager(ttl_hours=24)
