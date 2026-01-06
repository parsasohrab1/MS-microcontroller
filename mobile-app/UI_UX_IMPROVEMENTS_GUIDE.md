# راهنمای بهبود UI/UX

## مقدمه

این راهنما نحوه استفاده از قابلیت‌های بهبود UI/UX را توضیح می‌دهد.

---

## 1. Theme Provider (تم روشن/تاریک)

### استفاده از Theme

```tsx
import { ThemeProvider, useTheme } from './src/theme/ThemeProvider';

// در App.tsx
function App() {
  return (
    <ThemeProvider>
      {/* Your app */}
    </ThemeProvider>
  );
}

// در کامپوننت‌ها
function MyComponent() {
  const { theme, isDark, toggleTheme } = useTheme();
  
  return (
    <View style={{ backgroundColor: theme.colors.background }}>
      <Text style={{ color: theme.colors.onBackground }}>
        Hello World
      </Text>
    </View>
  );
}
```

### تنظیمات Theme

```tsx
const { theme, themeMode, setThemeMode, toggleTheme } = useTheme();

// تغییر به تم تاریک
setThemeMode('dark');

// تغییر به تم روشن
setThemeMode('light');

// استفاده از تم سیستم
setThemeMode('auto');

// Toggle تم
toggleTheme();
```

---

## 2. Animated Components

### استفاده از AnimatedButton

```tsx
import { AnimatedButton } from './src/components/animations/AnimatedButton';

<AnimatedButton
  title="Save"
  onPress={() => handleSave()}
  variant="primary"
  size="medium"
  loading={isLoading}
  icon={<Icon name="save" />}
  fullWidth
/>
```

### Variants

```tsx
// Primary button
<AnimatedButton variant="primary" title="Primary" />

// Secondary button
<AnimatedButton variant="secondary" title="Secondary" />

// Outlined button
<AnimatedButton variant="outlined" title="Outlined" />

// Text button
<AnimatedButton variant="text" title="Text" />
```

### Sizes

```tsx
<AnimatedButton size="small" title="Small" />
<AnimatedButton size="medium" title="Medium" />
<AnimatedButton size="large" title="Large" />
```

---

## 3. Accessibility

### استفاده از AccessibleView

```tsx
import { AccessibleView } from './src/components/accessibility/AccessibleView';

<AccessibleView
  accessibilityLabel="Save button"
  accessibilityHint="Double tap to save your changes"
  accessibilityRole="button"
  accessibilityState={{ disabled: isLoading }}
>
  <Button onPress={handleSave} />
</AccessibleView>
```

### Accessibility Utilities

```tsx
import { AccessibilityUtils } from './src/components/accessibility/AccessibleView';

// Announce to screen reader
AccessibilityUtils.announce('Changes saved successfully');

// Check if screen reader is enabled
const isEnabled = await AccessibilityUtils.isScreenReaderEnabled();

// Check if reduce motion is enabled
const reduceMotion = await AccessibilityUtils.isReduceMotionEnabled();
```

---

## 4. Internationalization (i18n)

### استفاده از Translation

```tsx
import { useTranslation } from 'react-i18next';

function MyComponent() {
  const { t } = useTranslation();
  
  return (
    <View>
      <Text>{t('common.save')}</Text>
      <Text>{t('navigation.home')}</Text>
      <Text>{t('symptoms.title')}</Text>
    </View>
  );
}
```

### تغییر زبان

```tsx
import { LanguageManager } from './src/i18n';

// تغییر به فارسی
await LanguageManager.changeLanguage('fa');

// تغییر به انگلیسی
await LanguageManager.changeLanguage('en');

// تغییر به عربی
await LanguageManager.changeLanguage('ar');

// دریافت زبان فعلی
const currentLang = LanguageManager.getCurrentLanguage();

// دریافت زبان‌های موجود
const languages = LanguageManager.getAvailableLanguages();
```

### استفاده در LanguageSettingsScreen

```tsx
import { LanguageSettingsScreen } from './src/screens/Settings/LanguageSettingsScreen';

// در navigation
<Stack.Screen
  name="LanguageSettings"
  component={LanguageSettingsScreen}
/>
```

---

## 5. Toast Feedback

### استفاده از Toast

```tsx
import { useToast } from './src/components/feedback/Toast';

function MyComponent() {
  const toast = useToast();
  
  const handleSave = async () => {
    try {
      await saveData();
      toast.success('Data saved successfully');
    } catch (error) {
      toast.error('Failed to save data');
    }
  };
  
  return (
    <View>
      <Button onPress={handleSave} title="Save" />
      <Toast
        message={toast.toast.message}
        type={toast.toast.type}
        visible={toast.toast.visible}
        onClose={toast.hide}
      />
    </View>
  );
}
```

### انواع Toast

```tsx
// Success
toast.success('Operation completed successfully');

// Error
toast.error('An error occurred');

// Warning
toast.warning('Please check your input');

// Info
toast.info('New update available');
```

---

## بهترین روش‌ها

### 1. Theme
- استفاده از theme colors در همه کامپوننت‌ها
- پشتیبانی از تم روشن و تاریک
- استفاده از spacing و typography از theme

### 2. Animations
- استفاده از انیمیشن‌های روان
- رعایت duration مناسب
- استفاده از native driver

### 3. Accessibility
- اضافه کردن accessibility labels
- رعایت minimum touch target size (44x44)
- تست با screen readers

### 4. i18n
- استفاده از translation keys
- پشتیبانی از RTL برای فارسی و عربی
- تست با زبان‌های مختلف

### 5. Feedback
- نمایش feedback برای همه اقدامات
- استفاده از toast برای پیام‌های کوتاه
- استفاده از loading indicators

---

**آخرین به‌روزرسانی:** 2024

