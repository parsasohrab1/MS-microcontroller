/**
 * Language Settings Screen
 * تنظیمات زبان
 */

import React, { useState } from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import { List, RadioButton, Divider } from 'react-native-paper';
import { useTheme } from '../../theme/ThemeProvider';
import { LanguageManager, useTranslation } from '../../i18n';

// ============================================================================
// Component
// ============================================================================

export const LanguageSettingsScreen: React.FC = () => {
  const { theme } = useTheme();
  const { t, i18n } = useTranslation();
  const [selectedLanguage, setSelectedLanguage] = useState(i18n.language);

  const languages = LanguageManager.getAvailableLanguages();

  const handleLanguageChange = async (language: string) => {
    setSelectedLanguage(language);
    await LanguageManager.changeLanguage(language);
  };

  return (
    <ScrollView
      style={[
        styles.container,
        { backgroundColor: theme.colors.background },
      ]}
    >
      <List.Section>
        <List.Subheader>{t('settings.language')}</List.Subheader>
        
        {languages.map(language => (
          <React.Fragment key={language}>
            <List.Item
              title={LanguageManager.getLanguageName(language)}
              left={() => (
                <RadioButton
                  value={language}
                  status={selectedLanguage === language ? 'checked' : 'unchecked'}
                  onPress={() => handleLanguageChange(language)}
                />
              )}
              onPress={() => handleLanguageChange(language)}
              titleStyle={{
                color: theme.colors.onBackground,
              }}
            />
            <Divider />
          </React.Fragment>
        ))}
      </List.Section>
    </ScrollView>
  );
};

// ============================================================================
// Styles
// ============================================================================

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
});

