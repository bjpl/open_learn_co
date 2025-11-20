'use client'

import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react'

interface PaginationProps {
  currentPage: number
  totalPages: number
  totalItems: number
  itemsPerPage: number
  onPageChange: (page: number) => void
}

export default function Pagination({
  currentPage,
  totalPages,
  totalItems,
  itemsPerPage,
  onPageChange
}: PaginationProps) {
  const startItem = (currentPage - 1) * itemsPerPage + 1
  const endItem = Math.min(currentPage * itemsPerPage, totalItems)

  const getPageNumbers = () => {
    const pages = []
    const maxVisible = 7

    if (totalPages <= maxVisible) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i)
      }
    } else {
      if (currentPage <= 4) {
        for (let i = 1; i <= 5; i++) pages.push(i)
        pages.push(-1) // Ellipsis
        pages.push(totalPages)
      } else if (currentPage >= totalPages - 3) {
        pages.push(1)
        pages.push(-1)
        for (let i = totalPages - 4; i <= totalPages; i++) pages.push(i)
      } else {
        pages.push(1)
        pages.push(-1)
        for (let i = currentPage - 1; i <= currentPage + 1; i++) pages.push(i)
        pages.push(-1)
        pages.push(totalPages)
      }
    }

    return pages
  }

  return (
    <nav aria-label="Pagination navigation" className="bg-white dark:bg-gray-800 px-4 py-3 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-between flex-wrap gap-4">
        {/* Results Info */}
        <div className="text-sm text-gray-700 dark:text-gray-300" role="status" aria-live="polite">
          Showing <span className="font-medium">{startItem}</span> to{' '}
          <span className="font-medium">{endItem}</span> of{' '}
          <span className="font-medium">{totalItems}</span> results
        </div>

        {/* Pagination Controls */}
        <div className="flex items-center space-x-2" role="group" aria-label="Pagination controls">
          {/* First Page */}
          <button
            onClick={() => onPageChange(1)}
            disabled={currentPage === 1}
            className="p-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            aria-label="Go to first page"
            aria-disabled={currentPage === 1}
          >
            <ChevronsLeft className="w-4 h-4 text-gray-600 dark:text-gray-400" aria-hidden="true" />
          </button>

          {/* Previous Page */}
          <button
            onClick={() => onPageChange(currentPage - 1)}
            disabled={currentPage === 1}
            className="p-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            aria-label="Go to previous page"
            aria-disabled={currentPage === 1}
          >
            <ChevronLeft className="w-4 h-4 text-gray-600 dark:text-gray-400" aria-hidden="true" />
          </button>

          {/* Page Numbers */}
          <div className="flex items-center space-x-1">
            {getPageNumbers().map((pageNum, index) =>
              pageNum === -1 ? (
                <span key={`ellipsis-${index}`} className="px-3 py-2 text-gray-500 dark:text-gray-400" aria-hidden="true">
                  ...
                </span>
              ) : (
                <button
                  key={pageNum}
                  onClick={() => onPageChange(pageNum)}
                  aria-label={`Go to page ${pageNum}`}
                  aria-current={currentPage === pageNum ? 'page' : undefined}
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    currentPage === pageNum
                      ? 'bg-yellow-500 text-white'
                      : 'border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                  }`}
                >
                  {pageNum}
                </button>
              )
            )}
          </div>

          {/* Next Page */}
          <button
            onClick={() => onPageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
            className="p-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            aria-label="Go to next page"
            aria-disabled={currentPage === totalPages}
          >
            <ChevronRight className="w-4 h-4 text-gray-600 dark:text-gray-400" aria-hidden="true" />
          </button>

          {/* Last Page */}
          <button
            onClick={() => onPageChange(totalPages)}
            disabled={currentPage === totalPages}
            className="p-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            aria-label="Go to last page"
            aria-disabled={currentPage === totalPages}
          >
            <ChevronsRight className="w-4 h-4 text-gray-600 dark:text-gray-400" aria-hidden="true" />
          </button>
        </div>
      </div>
    </nav>
  )
}
