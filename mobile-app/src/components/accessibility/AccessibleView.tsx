/**
 * Accessible View
 * کامپوننت برای دسترسی‌پذیری بهتر
 */

import React from 'react';
import { View, ViewProps, AccessibilityInfo } from 'react-native';
import { useTheme } from '../../theme/ThemeProvider';

// ============================================================================
// Props
// ============================================================================

interface AccessibleViewProps extends ViewProps {
  accessible?: boolean;
  accessibilityLabel?: string;
  accessibilityHint?: string;
  accessibilityRole?: 'button' | 'text' | 'header' | 'link' | 'image' | 'none';
  accessibilityState?: {
    disabled?: boolean;
    selected?: boolean;
    checked?: boolean;
  };
  accessibilityValue?: {
    min?: number;
    max?: number;
    now?: number;
    text?: string;
  };
  children: React.ReactNode;
}

// ============================================================================
// Component
// ============================================================================

export const AccessibleView: React.FC<AccessibleViewProps> = ({
  accessible = true,
  accessibilityLabel,
  accessibilityHint,
  accessibilityRole,
  accessibilityState,
  accessibilityValue,
  children,
  style,
  ...props
}) => {
  const { theme } = useTheme();

  return (
    <View
      accessible={accessible}
      accessibilityLabel={accessibilityLabel}
      accessibilityHint={accessibilityHint}
      accessibilityRole={accessibilityRole}
      accessibilityState={accessibilityState}
      accessibilityValue={accessibilityValue}
      style={[
        {
          // Ensure minimum touch target size (44x44 points)
          minHeight: 44,
          minWidth: 44,
        },
        style,
      ]}
      {...props}
    >
      {children}
    </View>
  );
};

// ============================================================================
// Accessibility Utilities
// ============================================================================

export const AccessibilityUtils = {
  /**
   * Announce message to screen reader
   */
  announce: (message: string) => {
    AccessibilityInfo.announceForAccessibility(message);
  },

  /**
   * Check if screen reader is enabled
   */
  isScreenReaderEnabled: async (): Promise<boolean> => {
    return await AccessibilityInfo.isScreenReaderEnabled();
  },

  /**
   * Check if reduce motion is enabled
   */
  isReduceMotionEnabled: async (): Promise<boolean> => {
    return await AccessibilityInfo.isReduceMotionEnabled();
  },
};

