/**
 * Advanced Search System
 * سیستم جستجوی پیشرفته با فیلترهای چندگانه و ذخیره جستجوهای پرکاربرد
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  TextField,
  Button,
  Chip,
  Stack,
  Autocomplete,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import SaveIcon from '@mui/icons-material/Save';
import DeleteIcon from '@mui/icons-material/Delete';
import SearchIcon from '@mui/icons-material/Search';

// ============================================================================
// Types
// ============================================================================

interface SearchFilter {
  field: string;
  operator: 'equals' | 'contains' | 'greaterThan' | 'lessThan' | 'between' | 'in';
  value: any;
  value2?: any; // For 'between' operator
}

interface SavedSearch {
  id: string;
  name: string;
  filters: SearchFilter[];
  createdAt: Date;
  lastUsed: Date;
  useCount: number;
}

interface SearchResult {
  id: string;
  patientId: string;
  timestamp: string;
  data: any;
}

// ============================================================================
// Component
// ============================================================================

export const AdvancedSearch: React.FC = () => {
  const [filters, setFilters] = useState<SearchFilter[]>([]);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>([]);
  const [loading, setLoading] = useState(false);
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [searchName, setSearchName] = useState('');

  // Load saved searches
  useEffect(() => {
    loadSavedSearches();
  }, []);

  const loadSavedSearches = async () => {
    try {
      const response = await fetch('/api/v1/search/saved');
      const data = await response.json();
      setSavedSearches(data);
    } catch (error) {
      console.error('Error loading saved searches:', error);
    }
  };

  // Add filter
  const addFilter = () => {
    setFilters([
      ...filters,
      {
        field: 'patientId',
        operator: 'equals',
        value: '',
      },
    ]);
  };

  // Remove filter
  const removeFilter = (index: number) => {
    setFilters(filters.filter((_, i) => i !== index));
  };

  // Update filter
  const updateFilter = (index: number, updates: Partial<SearchFilter>) => {
    const newFilters = [...filters];
    newFilters[index] = { ...newFilters[index], ...updates };
    setFilters(newFilters);
  };

  // Execute search
  const executeSearch = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/search/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filters }),
      });
      const data = await response.json();
      setResults(data.results);
    } catch (error) {
      console.error('Error executing search:', error);
    } finally {
      setLoading(false);
    }
  };

  // Save search
  const saveSearch = async () => {
    if (!searchName.trim()) return;

    try {
      const response = await fetch('/api/v1/search/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: searchName,
          filters,
        }),
      });
      await loadSavedSearches();
      setSaveDialogOpen(false);
      setSearchName('');
    } catch (error) {
      console.error('Error saving search:', error);
    }
  };

  // Load saved search
  const loadSavedSearch = (savedSearch: SavedSearch) => {
    setFilters(savedSearch.filters);
    // Update use count
    fetch(`/api/v1/search/saved/${savedSearch.id}/use`, { method: 'POST' });
  };

  // Delete saved search
  const deleteSavedSearch = async (id: string) => {
    try {
      await fetch(`/api/v1/search/saved/${id}`, { method: 'DELETE' });
      await loadSavedSearches();
    } catch (error) {
      console.error('Error deleting saved search:', error);
    }
  };

  // Available fields
  const availableFields = [
    { value: 'patientId', label: 'Patient ID' },
    { value: 'timestamp', label: 'Timestamp' },
    { value: 'riskScore', label: 'Risk Score' },
    { value: 'biomarker', label: 'Biomarker' },
    { value: 'symptom', label: 'Symptom' },
    { value: 'medication', label: 'Medication' },
  ];

  // Available operators
  const availableOperators = [
    { value: 'equals', label: 'Equals' },
    { value: 'contains', label: 'Contains' },
    { value: 'greaterThan', label: 'Greater Than' },
    { value: 'lessThan', label: 'Less Than' },
    { value: 'between', label: 'Between' },
    { value: 'in', label: 'In' },
  ];

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Box sx={{ p: 3 }}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h5" gutterBottom>
            Advanced Search
          </Typography>

          {/* Saved Searches */}
          {savedSearches.length > 0 && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle1" gutterBottom>
                Saved Searches
              </Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap">
                {savedSearches
                  .sort((a, b) => b.useCount - a.useCount)
                  .slice(0, 5)
                  .map((search) => (
                    <Chip
                      key={search.id}
                      label={`${search.name} (${search.useCount})`}
                      onClick={() => loadSavedSearch(search)}
                      onDelete={() => deleteSavedSearch(search.id)}
                      color="primary"
                      variant="outlined"
                    />
                  ))}
              </Stack>
            </Box>
          )}

          {/* Filters */}
          <Stack spacing={2}>
            {filters.map((filter, index) => (
              <Paper key={index} sx={{ p: 2 }}>
                <Stack direction="row" spacing={2} alignItems="center">
                  <Autocomplete
                    options={availableFields}
                    getOptionLabel={(option) => option.label}
                    value={availableFields.find((f) => f.value === filter.field)}
                    onChange={(_, newValue) =>
                      updateFilter(index, { field: newValue?.value || '' })
                    }
                    sx={{ width: 200 }}
                    renderInput={(params) => <TextField {...params} label="Field" />}
                  />

                  <FormControl sx={{ width: 150 }}>
                    <InputLabel>Operator</InputLabel>
                    <Select
                      value={filter.operator}
                      onChange={(e) =>
                        updateFilter(index, { operator: e.target.value as any })
                      }
                      label="Operator"
                    >
                      {availableOperators.map((op) => (
                        <MenuItem key={op.value} value={op.value}>
                          {op.label}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>

                  {filter.operator === 'between' ? (
                    <>
                      <TextField
                        label="Value 1"
                        value={filter.value}
                        onChange={(e) =>
                          updateFilter(index, { value: e.target.value })
                        }
                        sx={{ width: 150 }}
                      />
                      <TextField
                        label="Value 2"
                        value={filter.value2}
                        onChange={(e) =>
                          updateFilter(index, { value2: e.target.value })
                        }
                        sx={{ width: 150 }}
                      />
                    </>
                  ) : filter.operator === 'in' ? (
                    <TextField
                      label="Values (comma separated)"
                      value={filter.value}
                      onChange={(e) =>
                        updateFilter(index, { value: e.target.value })
                      }
                      sx={{ width: 300 }}
                    />
                  ) : filter.field === 'timestamp' ? (
                    <DatePicker
                      label="Date"
                      value={filter.value ? new Date(filter.value) : null}
                      onChange={(date) =>
                        updateFilter(index, { value: date?.toISOString() })
                      }
                      renderInput={(params) => (
                        <TextField {...params} sx={{ width: 200 }} />
                      )}
                    />
                  ) : (
                    <TextField
                      label="Value"
                      value={filter.value}
                      onChange={(e) =>
                        updateFilter(index, { value: e.target.value })
                      }
                      sx={{ width: 200 }}
                    />
                  )}

                  <IconButton
                    onClick={() => removeFilter(index)}
                    color="error"
                  >
                    <DeleteIcon />
                  </IconButton>
                </Stack>
              </Paper>
            ))}

            {/* Actions */}
            <Stack direction="row" spacing={2}>
              <Button variant="outlined" onClick={addFilter}>
                Add Filter
              </Button>
              <Button
                variant="contained"
                startIcon={<SearchIcon />}
                onClick={executeSearch}
                disabled={loading || filters.length === 0}
              >
                Search
              </Button>
              {filters.length > 0 && (
                <Button
                  variant="outlined"
                  startIcon={<SaveIcon />}
                  onClick={() => setSaveDialogOpen(true)}
                >
                  Save Search
                </Button>
              )}
            </Stack>
          </Stack>

          {/* Results */}
          {results.length > 0 && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="h6" gutterBottom>
                Results ({results.length})
              </Typography>
              {/* Render results */}
              <Stack spacing={1}>
                {results.map((result) => (
                  <Paper key={result.id} sx={{ p: 2 }}>
                    <Typography variant="body1">
                      Patient: {result.patientId}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {new Date(result.timestamp).toLocaleString()}
                    </Typography>
                  </Paper>
                ))}
              </Stack>
            </Box>
          )}
        </Paper>

        {/* Save Dialog */}
        <Dialog open={saveDialogOpen} onClose={() => setSaveDialogOpen(false)}>
          <DialogTitle>Save Search</DialogTitle>
          <DialogContent>
            <TextField
              autoFocus
              margin="dense"
              label="Search Name"
              fullWidth
              variant="outlined"
              value={searchName}
              onChange={(e) => setSearchName(e.target.value)}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setSaveDialogOpen(false)}>Cancel</Button>
            <Button onClick={saveSearch} variant="contained">
              Save
            </Button>
          </DialogActions>
        </Dialog>
      </Box>
    </LocalizationProvider>
  );
};

