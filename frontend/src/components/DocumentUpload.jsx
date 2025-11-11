import React, { useRef, useState } from 'react'
import { Upload, X, FileText, Image, FileCode, File, Check } from 'lucide-react'
import clsx from 'clsx'

const getFileIcon = (fileType) => {
  if (fileType.startsWith('image/')) return Image
  if (fileType === 'application/pdf') return FileText
  if (fileType.includes('word') || fileType.includes('document')) return FileText
  if (fileType === 'text/markdown' || fileType === 'text/plain') return FileCode
  return File
}

const getFileTypeLabel = (fileType) => {
  if (fileType.startsWith('image/')) return 'Image'
  if (fileType === 'application/pdf') return 'PDF'
  if (fileType.includes('word')) return 'Word'
  if (fileType === 'text/markdown') return 'Markdown'
  if (fileType === 'text/plain') return 'Text'
  return 'Document'
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

export default function DocumentUpload({ files, onFilesChange, disabled }) {
  const fileInputRef = useRef(null)
  const [dragActive, setDragActive] = useState(false)

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(Array.from(e.dataTransfer.files))
    }
  }

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFiles(Array.from(e.target.files))
    }
  }

  const handleFiles = (newFiles) => {
    // Filter for supported file types
    const supportedTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/msword',
      'text/plain',
      'text/markdown',
      'image/png',
      'image/jpeg',
      'image/jpg',
      'image/gif',
      'image/webp'
    ]

    const validFiles = newFiles.filter(file =>
      supportedTypes.includes(file.type) ||
      file.name.endsWith('.md') ||
      file.name.endsWith('.txt')
    )

    if (validFiles.length < newFiles.length) {
      alert('Some files were skipped. Only PDF, Word, images, text, and markdown files are supported.')
    }

    // Combine with existing files, avoiding duplicates
    const existingNames = new Set(files.map(f => f.name))
    const uniqueFiles = validFiles.filter(f => !existingNames.has(f.name))

    if (uniqueFiles.length > 0) {
      onFilesChange([...files, ...uniqueFiles])
    }
  }

  const removeFile = (index) => {
    const newFiles = files.filter((_, i) => i !== index)
    onFilesChange(newFiles)
  }

  return (
    <div className="space-y-4">
      <label className="block text-sm font-medium text-gray-300 mb-2">
        Supporting Documents (Optional)
      </label>

      {/* Upload Area */}
      <div
        className={clsx(
          'relative border-2 border-dashed rounded-lg p-6 transition-colors',
          dragActive
            ? 'border-primary-500 bg-primary-500/10'
            : 'border-dark-700 bg-dark-800 hover:border-dark-600',
          disabled && 'opacity-50 cursor-not-allowed'
        )}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.docx,.doc,.txt,.md,image/*"
          onChange={handleFileInput}
          disabled={disabled}
          className="hidden"
        />

        <div className="text-center">
          <Upload className="mx-auto text-gray-400 mb-3" size={32} />
          <p className="text-sm text-gray-300 mb-1">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={disabled}
              className="text-primary-400 hover:text-primary-300 font-medium"
            >
              Click to upload
            </button>
            {' or drag and drop'}
          </p>
          <p className="text-xs text-gray-500">
            PDF, Word (.docx), Images (PNG, JPG), Text (.txt, .md)
          </p>
          <p className="text-xs text-gray-600 mt-1">
            Maximum 10MB per file
          </p>
        </div>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm text-gray-400">
            {files.length} {files.length === 1 ? 'document' : 'documents'} ready to upload
          </p>
          <div className="space-y-2">
            {files.map((file, index) => {
              const FileIcon = getFileIcon(file.type)
              const typeLabel = getFileTypeLabel(file.type)

              return (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-dark-800 border border-dark-700 rounded-lg group hover:border-dark-600 transition-colors"
                >
                  <div className="flex items-center space-x-3 flex-1 min-w-0">
                    <div className="flex-shrink-0">
                      <FileIcon className="text-primary-400" size={20} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-200 truncate">
                        {file.name}
                      </p>
                      <p className="text-xs text-gray-500">
                        {typeLabel} • {formatFileSize(file.size)}
                      </p>
                    </div>
                    <div className="flex-shrink-0">
                      <Check className="text-green-400" size={16} />
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => removeFile(index)}
                    disabled={disabled}
                    className="ml-3 p-1 text-gray-400 hover:text-red-400 hover:bg-red-900/20 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    title="Remove file"
                  >
                    <X size={16} />
                  </button>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Helper Text */}
      {files.length === 0 && (
        <p className="text-xs text-gray-500">
          Upload UI mockups, requirement documents, or design specifications to help the AI generate more accurate test tickets
        </p>
      )}
    </div>
  )
}
