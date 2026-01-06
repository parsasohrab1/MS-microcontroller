/**
 * Doctor Dashboard
 * داشبورد پزشک برای مدیریت چند بیمار
 */

import React, { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  TextField,
  InputAdornment
} from '@mui/material';
import {
  Search as SearchIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon
} from '@mui/icons-material';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useAppSelector, useAppDispatch } from '../../store/hooks';
import { fetchPatients, fetchDashboardStats } from '../../store/slices/patientsSlice';

export const DoctorDashboard: React.FC = () => {
  const dispatch = useAppDispatch();
  const { patients, stats, loading } = useAppSelector(state => state.patients);
  const [searchQuery, setSearchQuery] = useState('');
  
  useEffect(() => {
    dispatch(fetchPatients());
    dispatch(fetchDashboardStats());
  }, [dispatch]);
  
  // فیلتر بیماران
  const filteredPatients = patients.filter(patient =>
    patient.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    patient.id.toLowerCase().includes(searchQuery.toLowerCase())
  );
  
  // آماده‌سازی داده‌های نمودار
  const riskTrendData = stats.riskTrend?.map((item: any) => ({
    date: item.date,
    average: item.averageRisk,
    high: item.highRiskCount
  })) || [];
  
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        داشبورد پزشک
      </Typography>
      
      {/* آمار کلی */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                تعداد کل بیماران
              </Typography>
              <Typography variant="h4">
                {stats.totalPatients}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                بیماران فعال
              </Typography>
              <Typography variant="h4" color="success.main">
                {stats.activePatients}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                هشدارهای فعال
              </Typography>
              <Typography variant="h4" color="warning.main">
                {stats.activeAlerts}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                میانگین امتیاز خطر
              </Typography>
              <Typography variant="h4" color="error.main">
                {(stats.averageRiskScore * 100).toFixed(1)}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      {/* نمودار روند خطر */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            روند امتیاز خطر (7 روز گذشته)
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={riskTrendData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="average" stroke="#8884d8" name="میانگین" />
              <Line type="monotone" dataKey="high" stroke="#82ca9d" name="خطر بالا" />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
      
      {/* لیست بیماران */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6">
              لیست بیماران
            </Typography>
            <TextField
              placeholder="جستجو..."
              size="small"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
            />
          </Box>
          
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>نام بیمار</TableCell>
                  <TableCell>شناسه</TableCell>
                  <TableCell>امتیاز خطر</TableCell>
                  <TableCell>وضعیت</TableCell>
                  <TableCell>آخرین به‌روزرسانی</TableCell>
                  <TableCell>عملیات</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredPatients.map((patient) => (
                  <TableRow key={patient.id}>
                    <TableCell>{patient.name}</TableCell>
                    <TableCell>{patient.id}</TableCell>
                    <TableCell>
                      <Chip
                        label={`${(patient.riskScore * 100).toFixed(1)}%`}
                        color={
                          patient.riskScore > 0.7 ? 'error' :
                          patient.riskScore > 0.4 ? 'warning' : 'success'
                        }
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      {patient.hasActiveAlert ? (
                        <Chip
                          icon={<WarningIcon />}
                          label="هشدار فعال"
                          color="warning"
                          size="small"
                        />
                      ) : (
                        <Chip
                          icon={<CheckCircleIcon />}
                          label="عادی"
                          color="success"
                          size="small"
                        />
                      )}
                    </TableCell>
                    <TableCell>
                      {new Date(patient.lastUpdate).toLocaleDateString('fa-IR')}
                    </TableCell>
                    <TableCell>
                      <IconButton
                        size="small"
                        onClick={() => window.location.href = `/patients/${patient.id}`}
                      >
                        مشاهده جزئیات
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  );
};

