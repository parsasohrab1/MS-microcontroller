/**
 * Toast Component
 * نمایش feedback بصری برای اقدامات کاربر
 */

import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  TouchableOpacity,
  Dimensions,
} from 'react-native';
import { useTheme } from '../../theme/ThemeProvider';
import { useTranslation } from 'react-i18next';

// ============================================================================
// Types
// ============================================================================

export type ToastType = 'success' | 'error' | 'warning' | 'info';

interface ToastProps {
  message: string;
  type?: ToastType;
  duration?: number;
  onClose?: () => void;
  visible: boolean;
}

// ============================================================================
// Component
// ============================================================================

export const Toast: React.FC<ToastProps> = ({
  message,
  type = 'info',
  duration = 3000,
  onClose,
  visible,
}) => {
  const { theme } = useTheme();
  const { t } = useTranslation();
  const slideAnim = useRef(new Animated.Value(-100)).current;
  const opacityAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (visible) {
      // Show animation
      Animated.parallel([
        Animated.spring(slideAnim, {
          toValue: 0,
          useNativeDriver: true,
          tension: 65,
          friction: 8,
        }),
        Animated.timing(opacityAnim, {
          toValue: 1,
          duration: theme.animations.duration.normal,
          useNativeDriver: true,
        }),
      ]).start();

      // Auto hide
      const timer = setTimeout(() => {
        hide();
      }, duration);

      return () => clearTimeout(timer);
    } else {
      hide();
    }
  }, [visible]);

  const hide = () => {
    Animated.parallel([
      Animated.timing(slideAnim, {
        toValue: -100,
        duration: theme.animations.duration.normal,
        useNativeDriver: true,
      }),
      Animated.timing(opacityAnim, {
        toValue: 0,
        duration: theme.animations.duration.normal,
        useNativeDriver: true,
      }),
    ]).start(() => {
      onClose?.();
    });
  };

  const getBackgroundColor = (): string => {
    switch (type) {
      case 'success':
        return theme.colors.success;
      case 'error':
        return theme.colors.error;
      case 'warning':
        return theme.colors.warning;
      case 'info':
        return theme.colors.info;
      default:
        return theme.colors.info;
    }
  };

  if (!visible) return null;

  return (
    <Animated.View
      style={[
        styles.container,
        {
          transform: [{ translateY: slideAnim }],
          opacity: opacityAnim,
        },
      ]}
      pointerEvents="box-none"
    >
      <View
        style={[
          styles.toast,
          {
            backgroundColor: getBackgroundColor(),
            borderRadius: theme.borderRadius.md,
            padding: theme.spacing.md,
          },
        ]}
      >
        <Text
          style={[
            styles.message,
            {
              color: theme.colors.onPrimary,
              fontSize: theme.typography.body.fontSize,
            },
          ]}
        >
          {message}
        </Text>
        <TouchableOpacity onPress={hide} style={styles.closeButton}>
          <Text
            style={[
              styles.closeText,
              {
                color: theme.colors.onPrimary,
              },
            ]}
          >
            {t('common.close')}
          </Text>
        </TouchableOpacity>
      </View>
    </Animated.View>
  );
};

// ============================================================================
// Toast Manager (Singleton)
// ============================================================================

class ToastManager {
  private listeners: Array<(toast: ToastProps) => void> = [];
  private currentToast: ToastProps | null = null;

  show(message: string, type: ToastType = 'info', duration = 3000) {
    const toast: ToastProps = {
      message,
      type,
      duration,
      visible: true,
    };

    this.currentToast = toast;
    this.listeners.forEach(listener => listener(toast));
  }

  success(message: string, duration = 3000) {
    this.show(message, 'success', duration);
  }

  error(message: string, duration = 3000) {
    this.show(message, 'error', duration);
  }

  warning(message: string, duration = 3000) {
    this.show(message, 'warning', duration);
  }

  info(message: string, duration = 3000) {
    this.show(message, 'info', duration);
  }

  subscribe(listener: (toast: ToastProps) => void) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  hide() {
    if (this.currentToast) {
      this.currentToast.visible = false;
      this.listeners.forEach(listener => listener(this.currentToast!));
      this.currentToast = null;
    }
  }
}

export const toastManager = new ToastManager();

// ============================================================================
// Hook
// ============================================================================

export const useToast = () => {
  const [toast, setToast] = React.useState<ToastProps>({
    message: '',
    type: 'info',
    visible: false,
  });

  React.useEffect(() => {
    const unsubscribe = toastManager.subscribe(setToast);
    return unsubscribe;
  }, []);

  return {
    show: (message: string, type?: ToastType, duration?: number) =>
      toastManager.show(message, type, duration),
    success: (message: string, duration?: number) =>
      toastManager.success(message, duration),
    error: (message: string, duration?: number) =>
      toastManager.error(message, duration),
    warning: (message: string, duration?: number) =>
      toastManager.warning(message, duration),
    info: (message: string, duration?: number) =>
      toastManager.info(message, duration),
    hide: () => toastManager.hide(),
    toast,
  };
};

// ============================================================================
// Styles
// ============================================================================

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: 50,
    left: 0,
    right: 0,
    alignItems: 'center',
    zIndex: 9999,
  },
  toast: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    minWidth: Dimensions.get('window').width * 0.8,
    maxWidth: Dimensions.get('window').width * 0.9,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  message: {
    flex: 1,
    marginRight: 8,
  },
  closeButton: {
    padding: 4,
  },
  closeText: {
    fontSize: 12,
    fontWeight: '600',
  },
});

