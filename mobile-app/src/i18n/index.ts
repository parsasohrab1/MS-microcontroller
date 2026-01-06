/**
 * Internationalization (i18n)
 * پشتیبانی از چند زبان: فارسی، انگلیسی، عربی
 */

import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import * as Localization from 'expo-localization';
import AsyncStorage from '@react-native-async-storage/async-storage';

// ============================================================================
// Translations
// ============================================================================

const resources = {
  en: {
    translation: {
      // Common
      common: {
        ok: 'OK',
        cancel: 'Cancel',
        save: 'Save',
        delete: 'Delete',
        edit: 'Edit',
        back: 'Back',
        next: 'Next',
        previous: 'Previous',
        loading: 'Loading...',
        error: 'Error',
        success: 'Success',
        retry: 'Retry',
        close: 'Close',
      },
      // Navigation
      navigation: {
        home: 'Home',
        dashboard: 'Dashboard',
        symptoms: 'Symptoms',
        medications: 'Medications',
        reports: 'Reports',
        settings: 'Settings',
        profile: 'Profile',
      },
      // Authentication
      auth: {
        login: 'Login',
        logout: 'Logout',
        register: 'Register',
        email: 'Email',
        password: 'Password',
        forgotPassword: 'Forgot Password?',
        rememberMe: 'Remember Me',
      },
      // Symptoms
      symptoms: {
        title: 'Symptom Tracking',
        addSymptom: 'Add Symptom',
        severity: 'Severity',
        notes: 'Notes',
        date: 'Date',
        time: 'Time',
      },
      // Medications
      medications: {
        title: 'Medications',
        addMedication: 'Add Medication',
        reminder: 'Reminder',
        dosage: 'Dosage',
        frequency: 'Frequency',
      },
      // Settings
      settings: {
        title: 'Settings',
        language: 'Language',
        theme: 'Theme',
        notifications: 'Notifications',
        privacy: 'Privacy',
        about: 'About',
      },
    },
  },
  fa: {
    translation: {
      // Common
      common: {
        ok: 'تأیید',
        cancel: 'لغو',
        save: 'ذخیره',
        delete: 'حذف',
        edit: 'ویرایش',
        back: 'بازگشت',
        next: 'بعدی',
        previous: 'قبلی',
        loading: 'در حال بارگذاری...',
        error: 'خطا',
        success: 'موفق',
        retry: 'تلاش مجدد',
        close: 'بستن',
      },
      // Navigation
      navigation: {
        home: 'خانه',
        dashboard: 'داشبورد',
        symptoms: 'علائم',
        medications: 'داروها',
        reports: 'گزارش‌ها',
        settings: 'تنظیمات',
        profile: 'پروفایل',
      },
      // Authentication
      auth: {
        login: 'ورود',
        logout: 'خروج',
        register: 'ثبت نام',
        email: 'ایمیل',
        password: 'رمز عبور',
        forgotPassword: 'رمز عبور را فراموش کرده‌اید؟',
        rememberMe: 'مرا به خاطر بسپار',
      },
      // Symptoms
      symptoms: {
        title: 'پیگیری علائم',
        addSymptom: 'افزودن علائم',
        severity: 'شدت',
        notes: 'یادداشت',
        date: 'تاریخ',
        time: 'زمان',
      },
      // Medications
      medications: {
        title: 'داروها',
        addMedication: 'افزودن دارو',
        reminder: 'یادآوری',
        dosage: 'دوز',
        frequency: 'فرکانس',
      },
      // Settings
      settings: {
        title: 'تنظیمات',
        language: 'زبان',
        theme: 'تم',
        notifications: 'اعلان‌ها',
        privacy: 'حریم خصوصی',
        about: 'درباره',
      },
    },
  },
  ar: {
    translation: {
      // Common
      common: {
        ok: 'موافق',
        cancel: 'إلغاء',
        save: 'حفظ',
        delete: 'حذف',
        edit: 'تعديل',
        back: 'رجوع',
        next: 'التالي',
        previous: 'السابق',
        loading: 'جاري التحميل...',
        error: 'خطأ',
        success: 'نجاح',
        retry: 'إعادة المحاولة',
        close: 'إغلاق',
      },
      // Navigation
      navigation: {
        home: 'الرئيسية',
        dashboard: 'لوحة التحكم',
        symptoms: 'الأعراض',
        medications: 'الأدوية',
        reports: 'التقارير',
        settings: 'الإعدادات',
        profile: 'الملف الشخصي',
      },
      // Authentication
      auth: {
        login: 'تسجيل الدخول',
        logout: 'تسجيل الخروج',
        register: 'التسجيل',
        email: 'البريد الإلكتروني',
        password: 'كلمة المرور',
        forgotPassword: 'نسيت كلمة المرور؟',
        rememberMe: 'تذكرني',
      },
      // Symptoms
      symptoms: {
        title: 'تتبع الأعراض',
        addSymptom: 'إضافة عرض',
        severity: 'الشدة',
        notes: 'ملاحظات',
        date: 'التاريخ',
        time: 'الوقت',
      },
      // Medications
      medications: {
        title: 'الأدوية',
        addMedication: 'إضافة دواء',
        reminder: 'تذكير',
        dosage: 'الجرعة',
        frequency: 'التكرار',
      },
      // Settings
      settings: {
        title: 'الإعدادات',
        language: 'اللغة',
        theme: 'المظهر',
        notifications: 'الإشعارات',
        privacy: 'الخصوصية',
        about: 'حول',
      },
    },
  },
};

// ============================================================================
// i18n Configuration
// ============================================================================

const LANGUAGE_KEY = '@app_language';

// Get saved language or device language
const getInitialLanguage = async (): Promise<string> => {
  try {
    const savedLanguage = await AsyncStorage.getItem(LANGUAGE_KEY);
    if (savedLanguage && resources[savedLanguage as keyof typeof resources]) {
      return savedLanguage;
    }
    
    // Get device language
    const deviceLanguage = Localization.locale.split('-')[0];
    if (resources[deviceLanguage as keyof typeof resources]) {
      return deviceLanguage;
    }
    
    // Default to English
    return 'en';
  } catch (error) {
    console.error('Error getting initial language:', error);
    return 'en';
  }
};

// Initialize i18n
i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: 'en', // Will be set dynamically
    fallbackLng: 'en',
    compatibilityJSON: 'v3',
    interpolation: {
      escapeValue: false,
    },
    react: {
      useSuspense: false,
    },
  });

// Set initial language
getInitialLanguage().then(lng => {
  i18n.changeLanguage(lng);
});

// ============================================================================
// Language Manager
// ============================================================================

export const LanguageManager = {
  /**
   * Change language
   */
  changeLanguage: async (language: string) => {
    if (resources[language as keyof typeof resources]) {
      await AsyncStorage.setItem(LANGUAGE_KEY, language);
      await i18n.changeLanguage(language);
    }
  },

  /**
   * Get current language
   */
  getCurrentLanguage: (): string => {
    return i18n.language;
  },

  /**
   * Get available languages
   */
  getAvailableLanguages: (): string[] => {
    return Object.keys(resources);
  },

  /**
   * Get language name
   */
  getLanguageName: (code: string): string => {
    const names: Record<string, string> = {
      en: 'English',
      fa: 'فارسی',
      ar: 'العربية',
    };
    return names[code] || code;
  },
};

export default i18n;

