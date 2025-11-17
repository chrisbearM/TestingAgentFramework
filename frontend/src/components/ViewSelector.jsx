import React, { useState, useRef, useEffect } from 'react'
import { Eye, Star, Edit, Trash2, ChevronDown, Plus, X } from 'lucide-react'
import clsx from 'clsx'

export default function ViewSelector({ views, currentView, onSelectView, onCreateView, onEditView, onDeleteView, onSetDefault }) {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef(null)

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleSelectView = (view) => {
    onSelectView(view)
    setIsOpen(false)
  }

  const handleClearView = () => {
    onSelectView(null)
    setIsOpen(false)
  }

  const handleEdit = (e, view) => {
    e.stopPropagation()
    onEditView(view)
    setIsOpen(false)
  }

  const handleDelete = (e, view) => {
    e.stopPropagation()
    if (window.confirm(`Are you sure you want to delete the view "${view.name}"?`)) {
      onDeleteView(view.id)
    }
  }

  const handleSetDefault = (e, view) => {
    e.stopPropagation()
    onSetDefault(view.id)
  }

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={clsx(
          'flex items-center space-x-2 px-4 py-2 rounded-lg border transition-colors',
          currentView
            ? 'bg-primary-500/10 border-primary-500/30 text-primary-400'
            : 'bg-dark-800 border-dark-700 text-gray-300 hover:bg-dark-700'
        )}
      >
        <Eye size={18} />
        <span className="font-medium">
          {currentView ? currentView.name : 'All Tickets'}
        </span>
        {currentView?.is_default && (
          <Star size={14} className="text-primary-400 fill-primary-400" />
        )}
        <ChevronDown size={16} className={clsx('transition-transform', isOpen && 'rotate-180')} />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute top-full left-0 mt-2 w-80 bg-dark-900 border border-dark-800 rounded-lg shadow-nebula-lg z-50 max-h-96 overflow-y-auto">
          {/* Header */}
          <div className="p-4 border-b border-dark-800">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-gray-100">Saved Views</h3>
              <button
                onClick={() => {
                  onCreateView()
                  setIsOpen(false)
                }}
                className="p-1.5 hover:bg-dark-800 rounded transition-colors"
                title="Save current view"
              >
                <Plus size={18} className="text-primary-400" />
              </button>
            </div>
          </div>

          {/* Views List */}
          <div className="py-2">
            {/* All Tickets (Clear Filter) */}
            <button
              onClick={handleClearView}
              className={clsx(
                'w-full px-4 py-3 text-left hover:bg-dark-800 transition-colors flex items-center justify-between',
                !currentView && 'bg-dark-800'
              )}
            >
              <div className="flex items-center space-x-3">
                <Eye size={16} className="text-gray-400" />
                <span className="text-gray-300">All Tickets</span>
              </div>
              {!currentView && (
                <div className="w-2 h-2 rounded-full bg-primary-500" />
              )}
            </button>

            {/* Divider */}
            {views.length > 0 && (
              <div className="border-t border-dark-800 my-2" />
            )}

            {/* Saved Views */}
            {views.length === 0 ? (
              <div className="px-4 py-6 text-center">
                <p className="text-sm text-gray-500 mb-2">No saved views yet</p>
                <button
                  onClick={() => {
                    onCreateView()
                    setIsOpen(false)
                  }}
                  className="text-sm text-primary-400 hover:text-primary-300 transition-colors"
                >
                  Create your first view
                </button>
              </div>
            ) : (
              views.map((view) => (
                <div
                  key={view.id}
                  className={clsx(
                    'group relative px-4 py-3 hover:bg-dark-800 transition-colors',
                    currentView?.id === view.id && 'bg-dark-800'
                  )}
                >
                  <button
                    onClick={() => handleSelectView(view)}
                    className="w-full text-left"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2">
                          <span className="text-gray-300 font-medium truncate">
                            {view.name}
                          </span>
                          {view.is_default && (
                            <Star size={12} className="text-primary-400 fill-primary-400 flex-shrink-0" />
                          )}
                        </div>
                        {view.description && (
                          <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                            {view.description}
                          </p>
                        )}
                      </div>
                      {currentView?.id === view.id && (
                        <div className="w-2 h-2 rounded-full bg-primary-500 flex-shrink-0 ml-2 mt-1" />
                      )}
                    </div>
                  </button>

                  {/* Action Buttons (Show on hover) */}
                  <div className="absolute right-2 top-2 hidden group-hover:flex items-center space-x-1 bg-dark-900 rounded border border-dark-700 p-1">
                    {!view.is_default && (
                      <button
                        onClick={(e) => handleSetDefault(e, view)}
                        className="p-1 hover:bg-dark-800 rounded transition-colors"
                        title="Set as default"
                      >
                        <Star size={14} className="text-gray-400 hover:text-primary-400" />
                      </button>
                    )}
                    <button
                      onClick={(e) => handleEdit(e, view)}
                      className="p-1 hover:bg-dark-800 rounded transition-colors"
                      title="Edit view"
                    >
                      <Edit size={14} className="text-gray-400 hover:text-primary-400" />
                    </button>
                    <button
                      onClick={(e) => handleDelete(e, view)}
                      className="p-1 hover:bg-dark-800 rounded transition-colors"
                      title="Delete view"
                    >
                      <Trash2 size={14} className="text-gray-400 hover:text-red-400" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-dark-800">
            <p className="text-xs text-gray-500 text-center">
              {views.length} saved {views.length === 1 ? 'view' : 'views'}
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
