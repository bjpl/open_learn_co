/**
 * Authentication Validation Schemas
 * Zod schemas for form validation with password strength checking
 */

import { z } from 'zod'

// Password strength validation
const passwordStrengthRegex = {
  lowercase: /[a-z]/,
  uppercase: /[A-Z]/,
  number: /\d/,
  special: /[!@#$%^&*(),.?":{}|<>]/,
}

export const passwordSchema = z
  .string()
  .min(8, 'Password must be at least 8 characters')
  .max(128, 'Password must not exceed 128 characters')
  .refine((password) => passwordStrengthRegex.lowercase.test(password), {
    message: 'Password must contain at least one lowercase letter',
  })
  .refine((password) => passwordStrengthRegex.uppercase.test(password), {
    message: 'Password must contain at least one uppercase letter',
  })
  .refine((password) => passwordStrengthRegex.number.test(password), {
    message: 'Password must contain at least one number',
  })
  .refine((password) => passwordStrengthRegex.special.test(password), {
    message: 'Password must contain at least one special character',
  })

// Login schema
export const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(1, 'Password is required'),
})

export type LoginData = z.infer<typeof loginSchema>

// Registration schema
export const registerSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: passwordSchema,
  full_name: z
    .string()
    .min(2, 'Name must be at least 2 characters')
    .max(100, 'Name must not exceed 100 characters')
    .regex(/^[a-zA-ZÀ-ÿ\s\-']+$/, 'Name contains invalid characters'),
  preferred_language: z.enum(['es', 'en']).default('es'),
})

export type RegisterData = z.infer<typeof registerSchema>

// Password reset request schema
export const passwordResetRequestSchema = z.object({
  email: z.string().email('Invalid email address'),
})

export type PasswordResetRequestData = z.infer<typeof passwordResetRequestSchema>

// Password reset confirm schema
export const passwordResetConfirmSchema = z
  .object({
    token: z.string().min(20, 'Invalid reset token'),
    new_password: passwordSchema,
    confirm_password: z.string().min(1, 'Please confirm your password'),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: 'Passwords do not match',
    path: ['confirm_password'],
  })

export type PasswordResetConfirmData = z.infer<typeof passwordResetConfirmSchema>

// Profile update schema
export const profileUpdateSchema = z.object({
  full_name: z
    .string()
    .min(2, 'Name must be at least 2 characters')
    .max(100, 'Name must not exceed 100 characters')
    .regex(/^[a-zA-ZÀ-ÿ\s\-']+$/, 'Name contains invalid characters')
    .optional(),
  preferred_language: z.enum(['es', 'en']).optional(),
})

export type ProfileUpdateData = z.infer<typeof profileUpdateSchema>

// Password strength calculator
export interface PasswordStrength {
  score: number // 0-7
  label: string
  color: string
}

export function getPasswordStrength(password: string): PasswordStrength {
  let score = 0

  // Length score (0-2 points)
  if (password.length >= 8) score++
  if (password.length >= 12) score++

  // Character variety (0-4 points)
  if (passwordStrengthRegex.lowercase.test(password)) score++
  if (passwordStrengthRegex.uppercase.test(password)) score++
  if (passwordStrengthRegex.number.test(password)) score++
  if (passwordStrengthRegex.special.test(password)) score++

  // Additional complexity (0-1 point)
  if (password.length >= 16) score++

  // Determine label and color
  let label: string
  let color: string

  if (score <= 2) {
    label = 'Weak'
    color = 'bg-red-500'
  } else if (score <= 4) {
    label = 'Fair'
    color = 'bg-yellow-500'
  } else if (score <= 5) {
    label = 'Good'
    color = 'bg-blue-500'
  } else {
    label = 'Strong'
    color = 'bg-green-500'
  }

  return { score, label, color }
}
