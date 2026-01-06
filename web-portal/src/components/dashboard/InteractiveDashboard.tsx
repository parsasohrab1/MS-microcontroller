/**
 * Interactive Dashboard
 * داشبورد تعاملی با نمودارها، فیلترها، Export و Real-time updates
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
  Chip,
  Stack,
} from '@mui/material';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import * as XLSX from 'xlsx';
import jsPDF from 'jspdf';
import 'jspdf-autotable';
import { useWebSocket } from '../../hooks/useWebSocket';

// ============================================================================
// Types
// ============================================================================

interface DashboardData {
  timestamp: string;
  eegData: number[];
  biomarkers: {
    name: string;
    value: number;
  }[];
  riskScore: number;
  predictions: {
    attackProbability: number;
    attackSeverity: number;
  };
}

interface FilterOptions {
  dateRange: {
    start: Date | null;
    end: Date | null;
  };
  patientId?: string;
  biomarker?: string;
  riskScoreRange?: {
    min: number;
    max: number;
  };
}

// ============================================================================
// Component
// ============================================================================

export const InteractiveDashboard: React.FC = () => {
  const [data, setData] = useState<DashboardData[]>([]);
  const [filters, setFilters] = useState<FilterOptions>({
    dateRange: {
      start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000), // 7 days ago
      end: new Date(),
    },
  });
  const [selectedBiomarker, setSelectedBiomarker] = useState<string>('all');
  const [chartType, setChartType] = useState<'line' | 'bar'>('line');

  // WebSocket for real-time updates
  const { lastMessage, sendMessage } = useWebSocket('ws://api.example.com/ws/dashboard');

  // Process real-time updates
  useEffect(() => {
    if (lastMessage) {
      const newData = JSON.parse(lastMessage.data);
      setData(prev => [...prev, newData].slice(-1000)); // Keep last 1000 points
    }
  }, [lastMessage]);

  // Fetch historical data
  useEffect(() => {
    fetchHistoricalData();
  }, [filters]);

  const fetchHistoricalData = async () => {
    try {
      const response = await fetch('/api/v1/dashboard/data', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(filters),
      });
      const result = await response.json();
      setData(result.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    }
  };

  // Process data for charts
  const processedData = useMemo(() => {
    return data.map(item => ({
      timestamp: new Date(item.timestamp).toLocaleTimeString(),
      riskScore: item.riskScore,
      attackProbability: item.predictions.attackProbability,
      attackSeverity: item.predictions.attackSeverity,
      ...item.biomarkers.reduce((acc, biomarker) => {
        acc[biomarker.name] = biomarker.value;
        return acc;
      }, {} as Record<string, number>),
    }));
  }, [data, selectedBiomarker]);

  // Biomarker data for pie chart
  const biomarkerData = useMemo(() => {
    if (!data.length) return [];
    
    const latest = data[data.length - 1];
    return latest.biomarkers.map(b => ({
      name: b.name,
      value: b.value,
    }));
  }, [data]);

  // Risk score distribution
  const riskScoreDistribution = useMemo(() => {
    const ranges = [
      { name: 'Low (0-30)', count: 0 },
      { name: 'Medium (31-60)', count: 0 },
      { name: 'High (61-80)', count: 0 },
      { name: 'Critical (81-100)', count: 0 },
    ];

    data.forEach(item => {
      if (item.riskScore <= 30) ranges[0].count++;
      else if (item.riskScore <= 60) ranges[1].count++;
      else if (item.riskScore <= 80) ranges[2].count++;
      else ranges[3].count++;
    });

    return ranges;
  }, [data]);

  // Export to Excel
  const exportToExcel = () => {
    const worksheet = XLSX.utils.json_to_sheet(processedData);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Dashboard Data');
    XLSX.writeFile(workbook, `dashboard_${new Date().toISOString()}.xlsx`);
  };

  // Export to PDF
  const exportToPDF = () => {
    const doc = new jsPDF();
    
    // Title
    doc.setFontSize(18);
    doc.text('Dashboard Report', 14, 22);
    
    // Date range
    doc.setFontSize(12);
    doc.text(
      `Date Range: ${filters.dateRange.start?.toLocaleDateString()} - ${filters.dateRange.end?.toLocaleDateString()}`,
      14,
      30
    );

    // Summary table
    const summaryData = [
      ['Total Data Points', data.length.toString()],
      ['Average Risk Score', (data.reduce((sum, d) => sum + d.riskScore, 0) / data.length || 0).toFixed(2)],
      ['Max Risk Score', Math.max(...data.map(d => d.riskScore), 0).toString()],
      ['Min Risk Score', Math.min(...data.map(d => d.riskScore), 0).toString()],
    ];

    (doc as any).autoTable({
      startY: 40,
      head: [['Metric', 'Value']],
      body: summaryData,
    });

    doc.save(`dashboard_${new Date().toISOString()}.pdf`);
  };

  // COLORS for charts
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Box sx={{ p: 3 }}>
        {/* Filters */}
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Filters
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={3}>
              <DatePicker
                label="Start Date"
                value={filters.dateRange.start}
                onChange={(date) =>
                  setFilters({
                    ...filters,
                    dateRange: { ...filters.dateRange, start: date },
                  })
                }
                renderInput={(params) => <FormControl fullWidth {...params} />}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <DatePicker
                label="End Date"
                value={filters.dateRange.end}
                onChange={(date) =>
                  setFilters({
                    ...filters,
                    dateRange: { ...filters.dateRange, end: date },
                  })
                }
                renderInput={(params) => <FormControl fullWidth {...params} />}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Biomarker</InputLabel>
                <Select
                  value={selectedBiomarker}
                  onChange={(e) => setSelectedBiomarker(e.target.value)}
                  label="Biomarker"
                >
                  <MenuItem value="all">All</MenuItem>
                  {biomarkerData.map((b) => (
                    <MenuItem key={b.name} value={b.name}>
                      {b.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Chart Type</InputLabel>
                <Select
                  value={chartType}
                  onChange={(e) => setChartType(e.target.value as 'line' | 'bar')}
                  label="Chart Type"
                >
                  <MenuItem value="line">Line</MenuItem>
                  <MenuItem value="bar">Bar</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>

          {/* Export Buttons */}
          <Stack direction="row" spacing={2} sx={{ mt: 2 }}>
            <Button variant="contained" onClick={exportToExcel}>
              Export to Excel
            </Button>
            <Button variant="contained" onClick={exportToPDF}>
              Export to PDF
            </Button>
          </Stack>
        </Paper>

        {/* Charts */}
        <Grid container spacing={3}>
          {/* Risk Score Chart */}
          <Grid item xs={12} md={8}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Risk Score Over Time
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                {chartType === 'line' ? (
                  <LineChart data={processedData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="riskScore"
                      stroke="#8884d8"
                      name="Risk Score"
                    />
                    <Line
                      type="monotone"
                      dataKey="attackProbability"
                      stroke="#82ca9d"
                      name="Attack Probability"
                    />
                  </LineChart>
                ) : (
                  <BarChart data={processedData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="riskScore" fill="#8884d8" name="Risk Score" />
                    <Bar dataKey="attackProbability" fill="#82ca9d" name="Attack Probability" />
                  </BarChart>
                )}
              </ResponsiveContainer>
            </Paper>
          </Grid>

          {/* Biomarker Pie Chart */}
          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Biomarkers Distribution
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={biomarkerData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {biomarkerData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>

          {/* Risk Score Distribution */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Risk Score Distribution
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={riskScoreDistribution}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>

          {/* Real-time Status */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Real-time Status
              </Typography>
              <Stack spacing={2}>
                <Chip
                  label={`Total Data Points: ${data.length}`}
                  color="primary"
                  variant="outlined"
                />
                <Chip
                  label={`Latest Risk Score: ${data[data.length - 1]?.riskScore || 'N/A'}`}
                  color={data[data.length - 1]?.riskScore > 70 ? 'error' : 'success'}
                  variant="outlined"
                />
                <Chip
                  label={`Last Update: ${new Date().toLocaleTimeString()}`}
                  color="info"
                  variant="outlined"
                />
              </Stack>
            </Paper>
          </Grid>
        </Grid>
      </Box>
    </LocalizationProvider>
  );
};

