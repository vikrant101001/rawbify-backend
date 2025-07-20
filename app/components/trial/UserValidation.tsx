'use client'

import { useState } from 'react'
import { Button } from '../ui/button'

interface UserValidationProps {
  onValidationSuccess: (userId: string) => void
  isActive: boolean
}

export default function UserValidation({ onValidationSuccess, isActive }: UserValidationProps) {
  const [userId, setUserId] = useState('')
  const [isValidating, setIsValidating] = useState(false)
  const [validationError, setValidationError] = useState('')
  const [isValidated, setIsValidated] = useState(false)

  const handleValidation = async () => {
    if (!userId.trim()) {
      setValidationError('Please enter your User ID')
      return
    }

    setIsValidating(true)
    setValidationError('')

    try {
      const response = await fetch('/api/validate-user', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ userId: userId }),
      })

      const result = await response.json()

      if (result.allowed) {
        setIsValidated(true)
        onValidationSuccess(userId)
      } else {
        setValidationError('Invalid User ID. Please check your email for the correct ID.')
      }
    } catch (error) {
      setValidationError('Validation failed. Please try again.')
    } finally {
      setIsValidating(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleValidation()
    }
  }

  return (
    <div className={`mb-8 ${!isActive ? 'opacity-50' : ''}`}>
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
        <span className={`w-6 h-6 rounded-full flex items-center justify-center text-sm font-bold mr-3 ${
          isValidated ? 'bg-green-600 text-white' : isActive ? 'bg-blue-600 text-white' : 'bg-gray-300 text-gray-500'
        }`}>
          0
        </span>
        Validate Your Access
      </h3>
      
      <div className="max-w-md mx-auto">
        {!isValidated ? (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Enter your User ID:
              </label>
              <input
                type="text"
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Enter the User ID from your email"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={!isActive || isValidating}
              />
              <p className="text-xs text-gray-500 mt-1">
                Check your email for the User ID we sent you
              </p>
            </div>
            
            {validationError && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-start">
                  <svg className="w-5 h-5 text-red-400 mt-0.5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div>
                    <p className="text-sm text-red-800 font-medium">Access Denied</p>
                    <p className="text-sm text-red-700 mt-1">
                      {validationError}
                    </p>
                    <div className="mt-3">
                      <a 
                        href="#waitlist" 
                        className="text-blue-600 hover:text-blue-500 text-sm font-medium"
                        onClick={() => {
                          const waitlistSection = document.getElementById('waitlist')
                          if (waitlistSection) {
                            waitlistSection.scrollIntoView({ behavior: 'smooth' })
                          }
                        }}
                      >
                        Join Waitlist →
                      </a>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            <div className="text-center">
              <Button 
                onClick={handleValidation}
                disabled={!isActive || isValidating || !userId.trim()}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
              >
                {isValidating ? (
                  <div className="flex items-center space-x-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>Validating...</span>
                  </div>
                ) : (
                  'Validate Access'
                )}
              </Button>
            </div>
            
            <div className="text-xs text-gray-500 text-center">
              <p>Test User IDs: test123, demo456, trial789, user_admin</p>
            </div>
          </div>
        ) : (
          <div className="text-center">
            <div className="text-green-600 mb-4">
              <svg className="mx-auto h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="font-medium text-gray-900">Access Granted!</p>
            <p className="text-sm text-gray-600 mt-1">Welcome, User ID: {userId}</p>
          </div>
        )}
      </div>
    </div>
  )
} 