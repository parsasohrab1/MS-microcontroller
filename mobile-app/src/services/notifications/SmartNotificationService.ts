/**
 * Smart Notification Service
 * سیستم اعلان‌های هوشمند با شخصی‌سازی، اولویت‌بندی، Quiet hours و Grouping
 */

import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

// ============================================================================
// Types
// ============================================================================

export type NotificationPriority = 'low' | 'normal' | 'high' | 'critical';

export interface NotificationCategory {
  id: string;
  name: string;
  priority: NotificationPriority;
  sound?: string;
  vibration?: boolean;
  badge?: boolean;
}

export interface NotificationSettings {
  enabled: boolean;
  quietHours: {
    enabled: boolean;
    start: string; // HH:mm format
    end: string; // HH:mm format
  };
  categories: {
    [categoryId: string]: {
      enabled: boolean;
      priority: NotificationPriority;
    };
  };
  grouping: boolean;
  personalization: {
    enabled: boolean;
    preferences: {
      [key: string]: any;
    };
  };
}

export interface NotificationData {
  id: string;
  title: string;
  body: string;
  category: string;
  priority: NotificationPriority;
  data?: any;
  scheduledFor?: Date;
  groupKey?: string;
}

// ============================================================================
// Notification Service
// ============================================================================

class SmartNotificationService {
  private settings: NotificationSettings | null = null;
  private readonly SETTINGS_KEY = '@notification_settings';

  /**
   * Initialize notification service
   */
  async initialize(): Promise<void> {
    // Request permissions
    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;

    if (existingStatus !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }

    if (finalStatus !== 'granted') {
      throw new Error('Notification permissions not granted');
    }

    // Configure notification handler
    Notifications.setNotificationHandler({
      handleNotification: async () => ({
        shouldShowAlert: true,
        shouldPlaySound: true,
        shouldSetBadge: true,
      }),
    });

    // Load settings
    await this.loadSettings();

    // Register notification categories
    await this.registerCategories();
  }

  /**
   * Register notification categories
   */
  private async registerCategories(): Promise<void> {
    const categories: NotificationCategory[] = [
      {
        id: 'medication_reminder',
        name: 'Medication Reminder',
        priority: 'high',
        sound: 'default',
        vibration: true,
        badge: true,
      },
      {
        id: 'symptom_alert',
        name: 'Symptom Alert',
        priority: 'critical',
        sound: 'default',
        vibration: true,
        badge: true,
      },
      {
        id: 'appointment',
        name: 'Appointment',
        priority: 'normal',
        sound: 'default',
        vibration: false,
        badge: true,
      },
      {
        id: 'general',
        name: 'General',
        priority: 'low',
        sound: 'default',
        vibration: false,
        badge: false,
      },
    ];

    // Register categories (iOS)
    if (Platform.OS === 'ios') {
      await Notifications.setNotificationCategoryAsync('medication_reminder', [
        {
          identifier: 'TAKE_MEDICATION',
          buttonTitle: 'Take Medication',
          options: { opensAppToForeground: true },
        },
        {
          identifier: 'SNOOZE',
          buttonTitle: 'Snooze',
          options: { opensAppToForeground: false },
        },
      ]);

      await Notifications.setNotificationCategoryAsync('symptom_alert', [
        {
          identifier: 'VIEW_SYMPTOM',
          buttonTitle: 'View',
          options: { opensAppToForeground: true },
        },
      ]);
    }
  }

  /**
   * Load settings from storage
   */
  private async loadSettings(): Promise<void> {
    try {
      const stored = await AsyncStorage.getItem(this.SETTINGS_KEY);
      if (stored) {
        this.settings = JSON.parse(stored);
      } else {
        // Default settings
        this.settings = {
          enabled: true,
          quietHours: {
            enabled: false,
            start: '22:00',
            end: '08:00',
          },
          categories: {},
          grouping: true,
          personalization: {
            enabled: true,
            preferences: {},
          },
        };
        await this.saveSettings();
      }
    } catch (error) {
      console.error('Error loading notification settings:', error);
      this.settings = this.getDefaultSettings();
    }
  }

  /**
   * Save settings to storage
   */
  private async saveSettings(): Promise<void> {
    try {
      await AsyncStorage.setItem(
        this.SETTINGS_KEY,
        JSON.stringify(this.settings)
      );
    } catch (error) {
      console.error('Error saving notification settings:', error);
    }
  }

  /**
   * Get default settings
   */
  private getDefaultSettings(): NotificationSettings {
    return {
      enabled: true,
      quietHours: {
        enabled: false,
        start: '22:00',
        end: '08:00',
      },
      categories: {},
      grouping: true,
      personalization: {
        enabled: true,
        preferences: {},
      },
    };
  }

  /**
   * Check if notification should be sent (considering quiet hours)
   */
  private shouldSendNotification(priority: NotificationPriority): boolean {
    if (!this.settings?.enabled) {
      return false;
    }

    // Critical notifications always sent
    if (priority === 'critical') {
      return true;
    }

    // Check quiet hours
    if (this.settings.quietHours.enabled) {
      const now = new Date();
      const currentTime = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
      const { start, end } = this.settings.quietHours;

      // Handle quiet hours that span midnight
      if (start > end) {
        if (currentTime >= start || currentTime < end) {
          // Only allow critical during quiet hours
          return priority === 'critical';
        }
      } else {
        if (currentTime >= start && currentTime < end) {
          // Only allow critical during quiet hours
          return priority === 'critical';
        }
      }
    }

    return true;
  }

  /**
   * Schedule notification
   */
  async scheduleNotification(
    notification: NotificationData
  ): Promise<string> {
    if (!this.shouldSendNotification(notification.priority)) {
      throw new Error('Notification blocked by settings');
    }

    const notificationContent: Notifications.NotificationRequestInput = {
      content: {
        title: notification.title,
        body: notification.body,
        data: notification.data || {},
        sound: true,
        badge: notification.priority !== 'low',
        priority: this.mapPriority(notification.priority),
        categoryIdentifier: notification.category,
        // Grouping
        threadIdentifier: notification.groupKey || notification.category,
      },
      trigger: notification.scheduledFor
        ? notification.scheduledFor
        : null, // Immediate
    };

    const notificationId = await Notifications.scheduleNotificationAsync(
      notificationContent
    );

    return notificationId;
  }

  /**
   * Send immediate notification
   */
  async sendNotification(notification: NotificationData): Promise<string> {
    return this.scheduleNotification(notification);
  }

  /**
   * Cancel notification
   */
  async cancelNotification(notificationId: string): Promise<void> {
    await Notifications.cancelScheduledNotificationAsync(notificationId);
  }

  /**
   * Cancel all notifications
   */
  async cancelAllNotifications(): Promise<void> {
    await Notifications.cancelAllScheduledNotificationsAsync();
  }

  /**
   * Get notification settings
   */
  async getSettings(): Promise<NotificationSettings> {
    if (!this.settings) {
      await this.loadSettings();
    }
    return this.settings!;
  }

  /**
   * Update notification settings
   */
  async updateSettings(settings: Partial<NotificationSettings>): Promise<void> {
    if (!this.settings) {
      await this.loadSettings();
    }

    this.settings = {
      ...this.settings!,
      ...settings,
    };

    await this.saveSettings();
  }

  /**
   * Enable/disable notifications
   */
  async setEnabled(enabled: boolean): Promise<void> {
    await this.updateSettings({ enabled });
  }

  /**
   * Set quiet hours
   */
  async setQuietHours(
    enabled: boolean,
    start: string,
    end: string
  ): Promise<void> {
    await this.updateSettings({
      quietHours: {
        enabled,
        start,
        end,
      },
    });
  }

  /**
   * Set category settings
   */
  async setCategorySettings(
    categoryId: string,
    enabled: boolean,
    priority: NotificationPriority
  ): Promise<void> {
    if (!this.settings) {
      await this.loadSettings();
    }

    this.settings!.categories[categoryId] = {
      enabled,
      priority,
    };

    await this.saveSettings();
  }

  /**
   * Map priority to Expo notification priority
   */
  private mapPriority(priority: NotificationPriority): 'min' | 'low' | 'default' | 'high' | 'max' {
    switch (priority) {
      case 'low':
        return 'low';
      case 'normal':
        return 'default';
      case 'high':
        return 'high';
      case 'critical':
        return 'max';
      default:
        return 'default';
    }
  }

  /**
   * Personalize notification based on user preferences
   */
  personalizeNotification(
    notification: NotificationData,
    userPreferences: any
  ): NotificationData {
    if (!this.settings?.personalization.enabled) {
      return notification;
    }

    // Apply personalization based on preferences
    const personalized = { ...notification };

    // Example: Adjust priority based on user preferences
    if (userPreferences.priorityOverrides?.[notification.category]) {
      personalized.priority = userPreferences.priorityOverrides[notification.category];
    }

    // Example: Customize message based on preferences
    if (userPreferences.messageTemplates?.[notification.category]) {
      personalized.body = userPreferences.messageTemplates[notification.category]
        .replace('{title}', notification.title);
    }

    return personalized;
  }
}

// ============================================================================
// Singleton
// ============================================================================

export const smartNotificationService = new SmartNotificationService();

