/**
 * Theme Provider
 * پشتیبانی از تم روشن/تاریک و Material Design / HIG
 */

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useColorScheme } from 'react-native';
import { ThemeProvider as PaperThemeProvider } from 'react-native-paper';
import { MD3LightTheme, MD3DarkTheme } from 'react-native-paper';
import { DefaultTheme as NavigationLightTheme, DarkTheme as NavigationDarkTheme } from '@react-navigation/native';

// ============================================================================
// Custom Colors
// ============================================================================

const lightColors = {
  primary: '#6200EE',
  primaryVariant: '#3700B3',
  secondary: '#03DAC6',
  secondaryVariant: '#018786',
  background: '#FFFFFF',
  surface: '#FFFFFF',
  error: '#B00020',
  onPrimary: '#FFFFFF',
  onSecondary: '#000000',
  onBackground: '#000000',
  onSurface: '#000000',
  onError: '#FFFFFF',
  disabled: '#BDBDBD',
  placeholder: '#9E9E9E',
  backdrop: 'rgba(0, 0, 0, 0.5)',
  // Custom colors
  success: '#4CAF50',
  warning: '#FF9800',
  info: '#2196F3',
  divider: '#E0E0E0',
  card: '#F5F5F5',
};

const darkColors = {
  primary: '#BB86FC',
  primaryVariant: '#3700B3',
  secondary: '#03DAC6',
  secondaryVariant: '#03DAC6',
  background: '#121212',
  surface: '#1E1E1E',
  error: '#CF6679',
  onPrimary: '#000000',
  onSecondary: '#000000',
  onBackground: '#FFFFFF',
  onSurface: '#FFFFFF',
  onError: '#000000',
  disabled: '#424242',
  placeholder: '#757575',
  backdrop: 'rgba(0, 0, 0, 0.7)',
  // Custom colors
  success: '#66BB6A',
  warning: '#FFA726',
  info: '#42A5F5',
  divider: '#424242',
  card: '#2C2C2C',
};

// ============================================================================
// Theme Types
// ============================================================================

export type ThemeMode = 'light' | 'dark' | 'auto';

export interface AppTheme {
  mode: 'light' | 'dark';
  colors: typeof lightColors;
  spacing: {
    xs: number;
    sm: number;
    md: number;
    lg: number;
    xl: number;
    xxl: number;
  };
  borderRadius: {
    sm: number;
    md: number;
    lg: number;
    xl: number;
    round: number;
  };
  typography: {
    h1: { fontSize: number; fontWeight: string; lineHeight: number };
    h2: { fontSize: number; fontWeight: string; lineHeight: number };
    h3: { fontSize: number; fontWeight: string; lineHeight: number };
    body: { fontSize: number; fontWeight: string; lineHeight: number };
    caption: { fontSize: number; fontWeight: string; lineHeight: number };
  };
  shadows: {
    sm: object;
    md: object;
    lg: object;
  };
  animations: {
    duration: {
      fast: number;
      normal: number;
      slow: number;
    };
    easing: {
      easeIn: string;
      easeOut: string;
      easeInOut: string;
    };
  };
}

// ============================================================================
// Theme Context
// ============================================================================

interface ThemeContextType {
  theme: AppTheme;
  themeMode: ThemeMode;
  setThemeMode: (mode: ThemeMode) => void;
  toggleTheme: () => void;
  isDark: boolean;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

// ============================================================================
// Theme Provider Component
// ============================================================================

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const systemColorScheme = useColorScheme();
  const [themeMode, setThemeMode] = useState<ThemeMode>('auto');
  const [isDark, setIsDark] = useState(systemColorScheme === 'dark');

  useEffect(() => {
    if (themeMode === 'auto') {
      setIsDark(systemColorScheme === 'dark');
    } else {
      setIsDark(themeMode === 'dark');
    }
  }, [themeMode, systemColorScheme]);

  const theme: AppTheme = {
    mode: isDark ? 'dark' : 'light',
    colors: isDark ? darkColors : lightColors,
    spacing: {
      xs: 4,
      sm: 8,
      md: 16,
      lg: 24,
      xl: 32,
      xxl: 48,
    },
    borderRadius: {
      sm: 4,
      md: 8,
      lg: 12,
      xl: 16,
      round: 9999,
    },
    typography: {
      h1: { fontSize: 32, fontWeight: 'bold', lineHeight: 40 },
      h2: { fontSize: 24, fontWeight: 'bold', lineHeight: 32 },
      h3: { fontSize: 20, fontWeight: '600', lineHeight: 28 },
      body: { fontSize: 16, fontWeight: '400', lineHeight: 24 },
      caption: { fontSize: 12, fontWeight: '400', lineHeight: 16 },
    },
    shadows: {
      sm: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.18,
        shadowRadius: 1.0,
        elevation: 1,
      },
      md: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.23,
        shadowRadius: 2.62,
        elevation: 4,
      },
      lg: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.30,
        shadowRadius: 4.65,
        elevation: 8,
      },
    },
    animations: {
      duration: {
        fast: 150,
        normal: 300,
        slow: 500,
      },
      easing: {
        easeIn: 'ease-in',
        easeOut: 'ease-out',
        easeInOut: 'ease-in-out',
      },
    },
  };

  const toggleTheme = () => {
    setThemeMode(prev => {
      if (prev === 'auto') return 'light';
      if (prev === 'light') return 'dark';
      return 'auto';
    });
  };

  const paperTheme = isDark ? MD3DarkTheme : MD3LightTheme;
  const navigationTheme = isDark ? NavigationDarkTheme : NavigationLightTheme;

  // Merge custom colors
  const customPaperTheme = {
    ...paperTheme,
    colors: {
      ...paperTheme.colors,
      ...theme.colors,
    },
  };

  const customNavigationTheme = {
    ...navigationTheme,
    colors: {
      ...navigationTheme.colors,
      primary: theme.colors.primary,
      background: theme.colors.background,
      card: theme.colors.surface,
      text: theme.colors.onBackground,
      border: theme.colors.divider,
      notification: theme.colors.error,
    },
  };

  return (
    <ThemeContext.Provider
      value={{
        theme,
        themeMode,
        setThemeMode,
        toggleTheme,
        isDark,
      }}
    >
      <PaperThemeProvider theme={customPaperTheme}>
        {children}
      </PaperThemeProvider>
    </ThemeContext.Provider>
  );
};

// ============================================================================
// Hook
// ============================================================================

export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
};

// ============================================================================
// Export Navigation Theme
// ============================================================================

export const getNavigationTheme = (isDark: boolean) => {
  const baseTheme = isDark ? NavigationDarkTheme : NavigationLightTheme;
  const colors = isDark ? darkColors : lightColors;
  
  return {
    ...baseTheme,
    colors: {
      ...baseTheme.colors,
      primary: colors.primary,
      background: colors.background,
      card: colors.surface,
      text: colors.onBackground,
      border: colors.divider,
      notification: colors.error,
    },
  };
};

