/**
 * Medication Reminder Screen
 * یادآوری مصرف دارو
 */

import React, { useEffect, useState } from 'react';
import {
  View,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  Alert
} from 'react-native';
import { Card, Title, Paragraph, Button, Checkbox } from 'react-native-paper';
import { useAppSelector, useAppDispatch } from '../../store/hooks';
import { fetchMedications, markMedicationTaken } from '../../store/slices/medicationsSlice';
import * as Notifications from 'expo-notifications';

export const MedicationReminderScreen: React.FC = () => {
  const dispatch = useAppDispatch();
  const { medications, loading } = useAppSelector(state => state.medications);
  const [todayMedications, setTodayMedications] = useState<any[]>([]);
  
  useEffect(() => {
    dispatch(fetchMedications());
    setupNotifications();
  }, []);
  
  useEffect(() => {
    // فیلتر داروهای امروز
    const today = new Date().toDateString();
    const todayMeds = medications.filter(med => {
      const medDate = new Date(med.scheduled_time).toDateString();
      return medDate === today && !med.taken;
    });
    setTodayMedications(todayMeds);
  }, [medications]);
  
  const setupNotifications = async () => {
    // درخواست مجوز
    const { status } = await Notifications.requestPermissionsAsync();
    
    if (status === 'granted') {
      // تنظیم notification handler
      Notifications.setNotificationHandler({
        handleNotification: async () => ({
          shouldShowAlert: true,
          shouldPlaySound: true,
          shouldSetBadge: true,
        }),
      });
      
      // ایجاد notifications برای داروها
      for (const med of medications) {
        await scheduleNotification(med);
      }
    }
  };
  
  const scheduleNotification = async (medication: any) => {
    const trigger = new Date(medication.scheduled_time);
    const now = new Date();
    
    if (trigger > now) {
      await Notifications.scheduleNotificationAsync({
        content: {
          title: 'یادآوری مصرف دارو',
          body: `زمان مصرف ${medication.name} رسیده است`,
          sound: true,
        },
        trigger: trigger,
      });
    }
  };
  
  const handleMarkTaken = async (medicationId: string) => {
    Alert.alert(
      'تأیید مصرف',
      'آیا دارو را مصرف کرده‌اید؟',
      [
        { text: 'لغو', style: 'cancel' },
        {
          text: 'تأیید',
          onPress: async () => {
            await dispatch(markMedicationTaken(medicationId));
            Alert.alert('موفق', 'مصرف دارو ثبت شد');
          }
        }
      ]
    );
  };
  
  return (
    <ScrollView style={styles.container}>
      <Card style={styles.card}>
        <Card.Content>
          <Title>داروهای امروز</Title>
          {todayMedications.length === 0 ? (
            <Paragraph>دارویی برای امروز برنامه‌ریزی نشده است</Paragraph>
          ) : (
            todayMedications.map((med) => (
              <Card key={med.id} style={styles.medicationCard}>
                <Card.Content>
                  <View style={styles.medicationRow}>
                    <View style={styles.medicationInfo}>
                      <Text style={styles.medicationName}>{med.name}</Text>
                      <Text style={styles.medicationTime}>
                        {new Date(med.scheduled_time).toLocaleTimeString('fa-IR')}
                      </Text>
                      <Text style={styles.medicationDose}>
                        دوز: {med.dose} {med.unit}
                      </Text>
                    </View>
                    <Button
                      mode="contained"
                      onPress={() => handleMarkTaken(med.id)}
                      disabled={med.taken}
                    >
                      {med.taken ? 'مصرف شده' : 'ثبت مصرف'}
                    </Button>
                  </View>
                </Card.Content>
              </Card>
            ))
          )}
        </Card.Content>
      </Card>
      
      {/* تاریخچه مصرف */}
      <Card style={styles.card}>
        <Card.Content>
          <Title>تاریخچه مصرف</Title>
          {medications
            .filter(med => med.taken)
            .slice(0, 10)
            .map((med) => (
              <View key={med.id} style={styles.historyItem}>
                <Text>{med.name}</Text>
                <Text style={styles.historyDate}>
                  {new Date(med.taken_at).toLocaleString('fa-IR')}
                </Text>
              </View>
            ))}
        </Card.Content>
      </Card>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  card: {
    margin: 10,
    elevation: 4,
  },
  medicationCard: {
    marginVertical: 5,
    backgroundColor: '#fff',
  },
  medicationRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  medicationInfo: {
    flex: 1,
  },
  medicationName: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  medicationTime: {
    fontSize: 14,
    color: '#666',
    marginTop: 5,
  },
  medicationDose: {
    fontSize: 12,
    color: '#999',
    marginTop: 3,
  },
  historyItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  historyDate: {
    fontSize: 12,
    color: '#666',
  },
});

