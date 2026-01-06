/**
 * Dashboard Screen
 * داشبورد اصلی با نمودارهای real-time
 */

import React, { useEffect, useState } from 'react';
import {
  View,
  ScrollView,
  StyleSheet,
  RefreshControl,
  Text,
  Dimensions
} from 'react-native';
import { LineChart, BarChart } from 'react-native-chart-kit';
import { Card, Title, Paragraph, Button } from 'react-native-paper';
import { useAppSelector, useAppDispatch } from '../../store/hooks';
import { fetchDashboardData } from '../../store/slices/dashboardSlice';
import { useWebSocket } from '../../services/websocket';

const { width } = Dimensions.get('window');

export const DashboardScreen: React.FC = () => {
  const dispatch = useAppDispatch();
  const { data, loading, error } = useAppSelector(state => state.dashboard);
  const [refreshing, setRefreshing] = useState(false);
  
  // WebSocket برای داده‌های real-time
  const ws = useWebSocket();
  
  useEffect(() => {
    // بارگذاری داده‌های اولیه
    dispatch(fetchDashboardData());
    
    // گوش دادن به داده‌های real-time
    ws.on('sensor_data', (data) => {
      // به‌روزرسانی داده‌ها
      dispatch(updateRealTimeData(data));
    });
    
    return () => {
      ws.off('sensor_data');
    };
  }, []);
  
  const onRefresh = async () => {
    setRefreshing(true);
    await dispatch(fetchDashboardData());
    setRefreshing(false);
  };
  
  // آماده‌سازی داده‌های نمودار
  const eegChartData = {
    labels: data.eeg_data?.labels || [],
    datasets: [{
      data: data.eeg_data?.values || [],
      color: (opacity = 1) => `rgba(134, 65, 244, ${opacity})`,
      strokeWidth: 2
    }]
  };
  
  const biomarkerChartData = {
    labels: data.biomarkers?.labels || [],
    datasets: [{
      data: data.biomarkers?.values || []
    }]
  };
  
  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      {/* کارت وضعیت کلی */}
      <Card style={styles.card}>
        <Card.Content>
          <Title>وضعیت کلی</Title>
          <View style={styles.statusRow}>
            <View style={styles.statusItem}>
              <Text style={styles.statusLabel}>امتیاز خطر</Text>
              <Text style={[styles.statusValue, getRiskColor(data.risk_score)]}>
                {(data.risk_score * 100).toFixed(1)}%
              </Text>
            </View>
            <View style={styles.statusItem}>
              <Text style={styles.statusLabel}>وضعیت سیستم</Text>
              <Text style={styles.statusValue}>
                {data.system_status || 'فعال'}
              </Text>
            </View>
          </View>
        </Card.Content>
      </Card>
      
      {/* نمودار EEG */}
      <Card style={styles.card}>
        <Card.Content>
          <Title>سیگنال‌های عصبی (EEG)</Title>
          {data.eeg_data && (
            <LineChart
              data={eegChartData}
              width={width - 40}
              height={220}
              chartConfig={{
                backgroundColor: '#ffffff',
                backgroundGradientFrom: '#ffffff',
                backgroundGradientTo: '#ffffff',
                decimalPlaces: 2,
                color: (opacity = 1) => `rgba(134, 65, 244, ${opacity})`,
                labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
                style: {
                  borderRadius: 16
                }
              }}
              bezier
              style={styles.chart}
            />
          )}
        </Card.Content>
      </Card>
      
      {/* نمودار بیومارکرها */}
      <Card style={styles.card}>
        <Card.Content>
          <Title>بیومارکرها</Title>
          {data.biomarkers && (
            <BarChart
              data={biomarkerChartData}
              width={width - 40}
              height={220}
              chartConfig={{
                backgroundColor: '#ffffff',
                backgroundGradientFrom: '#ffffff',
                backgroundGradientTo: '#ffffff',
                decimalPlaces: 2,
                color: (opacity = 1) => `rgba(0, 122, 255, ${opacity})`,
                labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`
              }}
              style={styles.chart}
            />
          )}
        </Card.Content>
      </Card>
      
      {/* آخرین پیش‌بینی */}
      <Card style={styles.card}>
        <Card.Content>
          <Title>آخرین پیش‌بینی</Title>
          <Paragraph>
            احتمال حمله: {(data.prediction?.attack_probability * 100).toFixed(1)}%
          </Paragraph>
          <Paragraph>
            شدت پیش‌بینی شده: {(data.prediction?.attack_severity * 100).toFixed(1)}%
          </Paragraph>
          <Paragraph>
            مدت زمان پیش‌بینی: {data.prediction?.attack_duration?.toFixed(1)} ساعت
          </Paragraph>
        </Card.Content>
      </Card>
      
      {/* هشدارها */}
      {data.alerts && data.alerts.length > 0 && (
        <Card style={[styles.card, styles.alertCard]}>
          <Card.Content>
            <Title style={styles.alertTitle}>هشدارها</Title>
            {data.alerts.map((alert, index) => (
              <View key={index} style={styles.alertItem}>
                <Text style={styles.alertText}>{alert.message}</Text>
                <Text style={styles.alertTime}>{alert.timestamp}</Text>
              </View>
            ))}
          </Card.Content>
        </Card>
      )}
    </ScrollView>
  );
};

const getRiskColor = (riskScore: number) => {
  if (riskScore < 0.3) return { color: '#4CAF50' }; // سبز
  if (riskScore < 0.7) return { color: '#FF9800' }; // نارنجی
  return { color: '#F44336' }; // قرمز
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
  statusRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 10,
  },
  statusItem: {
    alignItems: 'center',
  },
  statusLabel: {
    fontSize: 12,
    color: '#666',
  },
  statusValue: {
    fontSize: 24,
    fontWeight: 'bold',
    marginTop: 5,
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
  alertCard: {
    borderLeftWidth: 4,
    borderLeftColor: '#F44336',
  },
  alertTitle: {
    color: '#F44336',
  },
  alertItem: {
    marginVertical: 5,
    padding: 10,
    backgroundColor: '#fff3cd',
    borderRadius: 5,
  },
  alertText: {
    fontSize: 14,
  },
  alertTime: {
    fontSize: 12,
    color: '#666',
    marginTop: 5,
  },
});

