/**
 * Symptom Tracking Screen
 * ثبت علائم دستی بیمار
 */

import React, { useState } from 'react';
import {
  View,
  ScrollView,
  StyleSheet,
  Text,
  Alert
} from 'react-native';
import { Card, Title, TextInput, Button, SegmentedButtons } from 'react-native-paper';
import { useAppDispatch } from '../../store/hooks';
import { submitSymptom } from '../../store/slices/symptomsSlice';
import * as ImagePicker from 'expo-image-picker';

type SymptomSeverity = 'mild' | 'moderate' | 'severe';

export const SymptomTrackingScreen: React.FC = () => {
  const dispatch = useAppDispatch();
  
  const [symptomType, setSymptomType] = useState('');
  const [severity, setSeverity] = useState<SymptomSeverity>('mild');
  const [description, setDescription] = useState('');
  const [images, setImages] = useState<string[]>([]);
  const [submitting, setSubmitting] = useState(false);
  
  const pickImage = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    
    if (status !== 'granted') {
      Alert.alert('خطا', 'دسترسی به گالری لازم است');
      return;
    }
    
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsMultipleSelection: true,
      quality: 0.8,
    });
    
    if (!result.canceled) {
      const newImages = result.assets.map(asset => asset.uri);
      setImages([...images, ...newImages]);
    }
  };
  
  const takePhoto = async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    
    if (status !== 'granted') {
      Alert.alert('خطا', 'دسترسی به دوربین لازم است');
      return;
    }
    
    const result = await ImagePicker.launchCameraAsync({
      quality: 0.8,
    });
    
    if (!result.canceled) {
      setImages([...images, result.assets[0].uri]);
    }
  };
  
  const handleSubmit = async () => {
    if (!symptomType.trim()) {
      Alert.alert('خطا', 'لطفاً نوع علائم را وارد کنید');
      return;
    }
    
    setSubmitting(true);
    
    try {
      await dispatch(submitSymptom({
        type: symptomType,
        severity,
        description,
        images,
        timestamp: new Date().toISOString()
      }));
      
      Alert.alert('موفق', 'علائم با موفقیت ثبت شد');
      
      // پاک کردن فرم
      setSymptomType('');
      setSeverity('mild');
      setDescription('');
      setImages([]);
    } catch (error) {
      Alert.alert('خطا', 'خطا در ثبت علائم');
    } finally {
      setSubmitting(false);
    }
  };
  
  return (
    <ScrollView style={styles.container}>
      <Card style={styles.card}>
        <Card.Content>
          <Title>ثبت علائم</Title>
          
          <TextInput
            label="نوع علائم"
            value={symptomType}
            onChangeText={setSymptomType}
            mode="outlined"
            style={styles.input}
            placeholder="مثلاً: خستگی، ضعف، تاری دید"
          />
          
          <Text style={styles.label}>شدت علائم</Text>
          <SegmentedButtons
            value={severity}
            onValueChange={(value) => setSeverity(value as SymptomSeverity)}
            buttons={[
              { value: 'mild', label: 'خفیف' },
              { value: 'moderate', label: 'متوسط' },
              { value: 'severe', label: 'شدید' },
            ]}
            style={styles.segmentedButtons}
          />
          
          <TextInput
            label="توضیحات (اختیاری)"
            value={description}
            onChangeText={setDescription}
            mode="outlined"
            multiline
            numberOfLines={4}
            style={styles.input}
            placeholder="توضیحات بیشتر در مورد علائم..."
          />
          
          <View style={styles.imageButtons}>
            <Button
              mode="outlined"
              onPress={pickImage}
              icon="image"
            >
              انتخاب از گالری
            </Button>
            <Button
              mode="outlined"
              onPress={takePhoto}
              icon="camera"
            >
              عکس بگیر
            </Button>
          </View>
          
          {images.length > 0 && (
            <View style={styles.imagePreview}>
              <Text>تصاویر انتخاب شده: {images.length}</Text>
              {/* نمایش preview تصاویر */}
            </View>
          )}
          
          <Button
            mode="contained"
            onPress={handleSubmit}
            loading={submitting}
            disabled={submitting}
            style={styles.submitButton}
          >
            ثبت علائم
          </Button>
        </Card.Content>
      </Card>
      
      {/* تاریخچه علائم */}
      <Card style={styles.card}>
        <Card.Content>
          <Title>تاریخچه علائم</Title>
          {/* TODO: نمایش تاریخچه */}
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
  input: {
    marginVertical: 10,
  },
  label: {
    fontSize: 14,
    marginTop: 10,
    marginBottom: 5,
  },
  segmentedButtons: {
    marginVertical: 10,
  },
  imageButtons: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginVertical: 15,
  },
  imagePreview: {
    marginVertical: 10,
    padding: 10,
    backgroundColor: '#f0f0f0',
    borderRadius: 5,
  },
  submitButton: {
    marginTop: 20,
  },
});

