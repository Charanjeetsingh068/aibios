/**
 * AI-BOS Mobile Design Tokens
 * Replicates the Web CSS design tokens for React Native stylesheets.
 */

export const SPACING = {
  space1: 4,
  space2: 8,
  space3: 12,
  space4: 16,
  space6: 24,
  space8: 32,
  space12: 48,
  space16: 64,
};

export const BORDER_RADIUS = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  full: 9999,
};

export const TYPOGRAPHY = {
  sizes: {
    xs: 12,
    sm: 14,
    base: 16,
    lg: 18,
    xl: 20,
    xxl: 24,
    xxxl: 30,
  },
  weights: {
    normal: '400' as const,
    medium: '500' as const,
    semibold: '600' as const,
    bold: '700' as const,
  },
};

export const COLORS = {
  light: {
    bgPrimary: '#f8fafc',
    bgSecondary: '#ffffff',
    bgTertiary: '#f1f5f9',
    textPrimary: '#0f172a',
    textSecondary: '#475569',
    textTertiary: '#94a3b8',
    borderColor: '#e2e8f0',
    brand: '#2563eb',
    success: '#10b981',
    danger: '#ef4444',
  },
  dark: {
    bgPrimary: '#0b0f19',
    bgSecondary: '#111827',
    bgTertiary: '#1f2937',
    textPrimary: '#f9fafb',
    textSecondary: '#9ca3af',
    textTertiary: '#6b7280',
    borderColor: '#1f2937',
    brand: '#3b82f6',
    success: '#34d399',
    danger: '#f87171',
  },
};
