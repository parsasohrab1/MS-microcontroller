/**
 * Patient Detail Page
 * صفحه جزئیات بیمار برای پزشک
 */

import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Tabs,
  Tab,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Slider
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Settings as SettingsIcon
} from '@mui/icons-material';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useAppSelector, useAppDispatch } from '../../store/hooks';
import { fetchPatientDetail, updateTreatmentParams } from '../../store/slices/patientsSlice';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div role="tabpanel" hidden={value !== index} {...other}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export const PatientDetailPage: React.FC = () => {
  const { patientId } = useParams<{ patientId: string }>();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { patientDetail, loading } = useAppSelector(state => state.patients);
  
  const [tabValue, setTabValue] = useState(0);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [treatmentParams, setTreatmentParams] = useState({
    stimulation_intensity: 0.5,
    stimulation_frequency: 100,
    drug_dose: 0.3
  });
  
  useEffect(() => {
    if (patientId) {
      dispatch(fetchPatientDetail(patientId));
    }
  }, [patientId, dispatch]);
  
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };
  
  const handleSaveSettings = () => {
    if (patientId) {
      dispatch(updateTreatmentParams({ patientId, params: treatmentParams }));
      setSettingsOpen(false);
    }
  };
  
  if (loading || !patientDetail) {
    return <Typography>در حال بارگذاری...</Typography>;
  }
  
  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate('/dashboard')}
          >
            بازگشت
          </Button>
          <Typography variant="h4">
            {patientDetail.name}
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<SettingsIcon />}
          onClick={() => setSettingsOpen(true)}
        >
          تنظیمات درمان
        </Button>
      </Box>
      
      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label="نظارت" />
          <Tab label="تحلیل‌ها" />
          <Tab label="درمان" />
          <Tab label="گزارش‌ها" />
        </Tabs>
      </Box>
      
      {/* Tab Panels */}
      <TabPanel value={tabValue} index={0}>
        {/* Monitoring Tab */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  امتیاز خطر (7 روز گذشته)
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={patientDetail.riskHistory}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="risk" stroke="#8884d8" />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  وضعیت فعلی
                </Typography>
                <Typography>امتیاز خطر: {(patientDetail.currentRisk * 100).toFixed(1)}%</Typography>
                <Typography>وضعیت سیستم: {patientDetail.systemStatus}</Typography>
                <Typography>آخرین به‌روزرسانی: {new Date(patientDetail.lastUpdate).toLocaleString('fa-IR')}</Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>
      
      <TabPanel value={tabValue} index={1}>
        {/* Analytics Tab */}
        <Typography variant="h6">تحلیل‌های پیشرفته</Typography>
        {/* TODO: اضافه کردن تحلیل‌ها */}
      </TabPanel>
      
      <TabPanel value={tabValue} index={2}>
        {/* Treatment Tab */}
        <Typography variant="h6">برنامه درمان فعلی</Typography>
        {/* TODO: نمایش برنامه درمان */}
      </TabPanel>
      
      <TabPanel value={tabValue} index={3}>
        {/* Reports Tab */}
        <Typography variant="h6">گزارش‌ها</Typography>
        {/* TODO: لیست گزارش‌ها */}
      </TabPanel>
      
      {/* Settings Dialog */}
      <Dialog open={settingsOpen} onClose={() => setSettingsOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>تنظیمات درمان</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <Typography gutterBottom>شدت تحریک</Typography>
            <Slider
              value={treatmentParams.stimulation_intensity}
              onChange={(e, value) => setTreatmentParams({
                ...treatmentParams,
                stimulation_intensity: value as number
              })}
              min={0}
              max={1}
              step={0.01}
              marks
              valueLabelDisplay="auto"
            />
            
            <Typography gutterBottom sx={{ mt: 3 }}>فرکانس تحریک (Hz)</Typography>
            <TextField
              fullWidth
              type="number"
              value={treatmentParams.stimulation_frequency}
              onChange={(e) => setTreatmentParams({
                ...treatmentParams,
                stimulation_frequency: parseFloat(e.target.value)
              })}
            />
            
            <Typography gutterBottom sx={{ mt: 3 }}>دوز دارو</Typography>
            <Slider
              value={treatmentParams.drug_dose}
              onChange={(e, value) => setTreatmentParams({
                ...treatmentParams,
                drug_dose: value as number
              })}
              min={0}
              max={1}
              step={0.01}
              marks
              valueLabelDisplay="auto"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSettingsOpen(false)}>لغو</Button>
          <Button onClick={handleSaveSettings} variant="contained">ذخیره</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

