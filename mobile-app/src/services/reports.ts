/**
 * Reports Service
 * سرویس گزارش‌گیری
 */

import api from './api';

export interface Report {
  id: string;
  patient_id: string;
  period: 'daily' | 'weekly' | 'monthly';
  date: string;
  startDate: string;
  endDate: string;
  averageRiskScore: number;
  alertCount: number;
  attackCount: number;
  isLatest: boolean;
}

export const generateReport = async (period: 'daily' | 'weekly' | 'monthly'): Promise<Report> => {
  const response = await api.post('/reports/generate', { period });
  return response.data;
};

export const exportToPDF = async (reportId: string): Promise<string> => {
  const response = await api.get(`/reports/${reportId}/export`, {
    params: { format: 'pdf' },
    responseType: 'blob'
  });
  
  // ذخیره فایل
  const blob = new Blob([response.data], { type: 'application/pdf' });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `report_${reportId}.pdf`;
  link.click();
  
  return url;
};

export const getReports = async (period?: 'daily' | 'weekly' | 'monthly'): Promise<Report[]> => {
  const params = period ? { period } : {};
  const response = await api.get('/reports', { params });
  return response.data;
};

