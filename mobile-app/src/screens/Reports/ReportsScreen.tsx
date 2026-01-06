/**
 * Reports Screen
 * گزارش‌های خودکار روزانه/هفتگی/ماهانه
 */

import React, { useState } from 'react';
import {
  View,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  Text,
  Alert
} from 'react-native';
import { Card, Title, Paragraph, Button, SegmentedButtons } from 'react-native-paper';
import { useAppSelector } from '../../store/hooks';
import { generateReport, exportToPDF } from '../../services/reports';
import { shareFile } from '../../utils/share';

type ReportPeriod = 'daily' | 'weekly' | 'monthly';

export const ReportsScreen: React.FC = () => {
  const [selectedPeriod, setSelectedPeriod] = useState<ReportPeriod>('daily');
  const [generating, setGenerating] = useState(false);
  const { reports } = useAppSelector(state => state.reports);
  
  const handleGenerateReport = async () => {
    setGenerating(true);
    try {
      const report = await generateReport(selectedPeriod);
      Alert.alert('موفق', 'گزارش با موفقیت ایجاد شد');
    } catch (error) {
      Alert.alert('خطا', 'خطا در ایجاد گزارش');
    } finally {
      setGenerating(false);
    }
  };
  
  const handleExportPDF = async (reportId: string) => {
    try {
      const pdfPath = await exportToPDF(reportId);
      await shareFile(pdfPath, 'application/pdf');
    } catch (error) {
      Alert.alert('خطا', 'خطا در export گزارش');
    }
  };
  
  const currentReport = reports.find(r => r.period === selectedPeriod && r.isLatest);
  
  return (
    <ScrollView style={styles.container}>
      {/* انتخاب دوره */}
      <Card style={styles.card}>
        <Card.Content>
          <Title>انتخاب دوره گزارش</Title>
          <SegmentedButtons
            value={selectedPeriod}
            onValueChange={(value) => setSelectedPeriod(value as ReportPeriod)}
            buttons={[
              { value: 'daily', label: 'روزانه' },
              { value: 'weekly', label: 'هفتگی' },
              { value: 'monthly', label: 'ماهانه' },
            ]}
          />
        </Card.Content>
      </Card>
      
      {/* گزارش فعلی */}
      {currentReport && (
        <Card style={styles.card}>
          <Card.Content>
            <Title>گزارش {getPeriodLabel(selectedPeriod)}</Title>
            <Paragraph>تاریخ: {currentReport.date}</Paragraph>
            <Paragraph>دوره: {currentReport.startDate} تا {currentReport.endDate}</Paragraph>
            
            <View style={styles.statsContainer}>
              <View style={styles.statItem}>
                <Text style={styles.statLabel}>میانگین امتیاز خطر</Text>
                <Text style={styles.statValue}>
                  {(currentReport.averageRiskScore * 100).toFixed(1)}%
                </Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statLabel}>تعداد هشدارها</Text>
                <Text style={styles.statValue}>{currentReport.alertCount}</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statLabel}>تعداد حملات</Text>
                <Text style={styles.statValue}>{currentReport.attackCount}</Text>
              </View>
            </View>
            
            <Button
              mode="contained"
              onPress={() => handleExportPDF(currentReport.id)}
              style={styles.button}
            >
              Export به PDF
            </Button>
          </Card.Content>
        </Card>
      )}
      
      {/* ایجاد گزارش جدید */}
      <Card style={styles.card}>
        <Card.Content>
          <Title>ایجاد گزارش جدید</Title>
          <Button
            mode="contained"
            onPress={handleGenerateReport}
            loading={generating}
            disabled={generating}
            style={styles.button}
          >
            ایجاد گزارش {getPeriodLabel(selectedPeriod)}
          </Button>
        </Card.Content>
      </Card>
      
      {/* تاریخچه گزارش‌ها */}
      <Card style={styles.card}>
        <Card.Content>
          <Title>تاریخچه گزارش‌ها</Title>
          {reports
            .filter(r => r.period === selectedPeriod)
            .map((report) => (
              <TouchableOpacity
                key={report.id}
                style={styles.reportItem}
                onPress={() => handleExportPDF(report.id)}
              >
                <Text style={styles.reportDate}>{report.date}</Text>
                <Text style={styles.reportPeriod}>
                  {report.startDate} - {report.endDate}
                </Text>
              </TouchableOpacity>
            ))}
        </Card.Content>
      </Card>
    </ScrollView>
  );
};

const getPeriodLabel = (period: ReportPeriod): string => {
  switch (period) {
    case 'daily': return 'روزانه';
    case 'weekly': return 'هفتگی';
    case 'monthly': return 'ماهانه';
    default: return '';
  }
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
  statsContainer: {
    marginVertical: 15,
  },
  statItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  statLabel: {
    fontSize: 14,
    color: '#666',
  },
  statValue: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  button: {
    marginTop: 10,
  },
  reportItem: {
    padding: 15,
    backgroundColor: '#f9f9f9',
    borderRadius: 5,
    marginVertical: 5,
  },
  reportDate: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  reportPeriod: {
    fontSize: 12,
    color: '#666',
    marginTop: 5,
  },
});

