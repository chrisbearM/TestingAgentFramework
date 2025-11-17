"""
View Manager for Saved Filters and Views
Manages user-defined filter configurations and saved views
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from threading import Lock
import uuid


class ViewManager:
    """
    In-memory view manager for saved filters and views.
    Stores views by session_id with optional default view tracking.
    """

    def __init__(self):
        """Initialize view manager."""
        self._views: Dict[str, Dict[str, Any]] = {}  # session_id -> {views: {}, default_view_id: str}
        self._lock = Lock()

    def save_view(
        self,
        session_id: str,
        name: str,
        filters: Dict[str, Any],
        description: Optional[str] = None,
        is_default: bool = False
    ) -> str:
        """
        Save a new view/filter configuration.

        Args:
            session_id: Session identifier
            name: Name for this saved view
            filters: Filter configuration object
            description: Optional description
            is_default: Whether this should be the default view

        Returns:
            View ID
        """
        with self._lock:
            view_id = str(uuid.uuid4())

            if session_id not in self._views:
                self._views[session_id] = {
                    'views': {},
                    'default_view_id': None
                }

            view = {
                'id': view_id,
                'name': name,
                'filters': filters,
                'description': description,
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'is_default': is_default
            }

            self._views[session_id]['views'][view_id] = view

            # Set as default if requested
            if is_default:
                self._views[session_id]['default_view_id'] = view_id

            print(f"DEBUG ViewManager: Saved view {view_id} ('{name}') for session {session_id}")
            return view_id

    def load_view(self, session_id: str, view_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a specific view.

        Args:
            session_id: Session identifier
            view_id: View identifier

        Returns:
            View data if found, None otherwise
        """
        with self._lock:
            if session_id not in self._views:
                print(f"DEBUG ViewManager: Session {session_id} not found")
                return None

            session = self._views[session_id]

            if view_id not in session['views']:
                print(f"DEBUG ViewManager: View {view_id} not found in session {session_id}")
                return None

            view = session['views'][view_id]
            print(f"DEBUG ViewManager: Loaded view {view_id} for session {session_id}")
            return view

    def list_views(self, session_id: str) -> List[Dict[str, Any]]:
        """
        List all views for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of view summaries
        """
        with self._lock:
            if session_id not in self._views:
                return []

            session = self._views[session_id]
            views = []

            for view_id, view in session['views'].items():
                views.append({
                    'id': view['id'],
                    'name': view['name'],
                    'description': view['description'],
                    'filters': view['filters'],
                    'created_at': view['created_at'].isoformat(),
                    'updated_at': view['updated_at'].isoformat(),
                    'is_default': view_id == session['default_view_id']
                })

            # Sort by name
            views.sort(key=lambda x: x['name'].lower())

            print(f"DEBUG ViewManager: Listed {len(views)} views for session {session_id}")
            return views

    def update_view(
        self,
        session_id: str,
        view_id: str,
        name: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None
    ) -> bool:
        """
        Update an existing view.

        Args:
            session_id: Session identifier
            view_id: View identifier
            name: Optional new name
            filters: Optional new filters
            description: Optional new description

        Returns:
            True if updated successfully, False otherwise
        """
        with self._lock:
            if session_id not in self._views:
                return False

            session = self._views[session_id]

            if view_id not in session['views']:
                return False

            view = session['views'][view_id]

            # Update fields
            if name is not None:
                view['name'] = name
            if filters is not None:
                view['filters'] = filters
            if description is not None:
                view['description'] = description

            view['updated_at'] = datetime.now()

            print(f"DEBUG ViewManager: Updated view {view_id} for session {session_id}")
            return True

    def delete_view(self, session_id: str, view_id: str) -> bool:
        """
        Delete a view.

        Args:
            session_id: Session identifier
            view_id: View identifier

        Returns:
            True if deleted successfully, False otherwise
        """
        with self._lock:
            if session_id not in self._views:
                return False

            session = self._views[session_id]

            if view_id not in session['views']:
                return False

            # Clear default if this was the default view
            if session['default_view_id'] == view_id:
                session['default_view_id'] = None

            del session['views'][view_id]

            print(f"DEBUG ViewManager: Deleted view {view_id} for session {session_id}")
            return True

    def set_default_view(self, session_id: str, view_id: Optional[str]) -> bool:
        """
        Set a view as the default for this session.

        Args:
            session_id: Session identifier
            view_id: View identifier (None to clear default)

        Returns:
            True if set successfully, False otherwise
        """
        with self._lock:
            if session_id not in self._views:
                return False

            session = self._views[session_id]

            # Validate view exists if not clearing
            if view_id is not None and view_id not in session['views']:
                return False

            session['default_view_id'] = view_id

            print(f"DEBUG ViewManager: Set default view to {view_id} for session {session_id}")
            return True

    def get_default_view(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the default view for a session.

        Args:
            session_id: Session identifier

        Returns:
            Default view data if set, None otherwise
        """
        with self._lock:
            if session_id not in self._views:
                return None

            session = self._views[session_id]
            default_view_id = session['default_view_id']

            if not default_view_id or default_view_id not in session['views']:
                return None

            view = session['views'][default_view_id]
            print(f"DEBUG ViewManager: Loaded default view {default_view_id} for session {session_id}")
            return view

    def clear_session(self, session_id: str) -> bool:
        """
        Clear all views for a session.

        Args:
            session_id: Session identifier

        Returns:
            True if cleared successfully, False otherwise
        """
        with self._lock:
            if session_id not in self._views:
                return False

            del self._views[session_id]
            print(f"DEBUG ViewManager: Cleared session {session_id}")
            return True

    def get_stats(self) -> Dict[str, Any]:
        """
        Get view manager statistics.

        Returns:
            Dictionary with statistics
        """
        with self._lock:
            total_sessions = len(self._views)
            total_views = sum(len(session['views']) for session in self._views.values())
            sessions_with_default = sum(
                1 for session in self._views.values()
                if session['default_view_id'] is not None
            )

            return {
                'total_sessions': total_sessions,
                'total_views': total_views,
                'sessions_with_default': sessions_with_default,
                'avg_views_per_session': total_views / total_sessions if total_sessions > 0 else 0
            }


# Global view manager instance
view_manager = ViewManager()
