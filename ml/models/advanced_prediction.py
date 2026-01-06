"""
Advanced Prediction Models
مدل‌های پیش‌بینی پیشرفته برای MS
"""

import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from typing import Dict, Tuple, Optional
import joblib
from pathlib import Path
import json
from datetime import datetime


class AdvancedPredictionModel:
    """مدل پیش‌بینی پیشرفته با چندین خروجی"""
    
    def __init__(self, model_path: Optional[str] = None):
        """
        مقداردهی اولیه
        
        Args:
            model_path: مسیر مدل ذخیره شده (اختیاری)
        """
        self.model = None
        self.scaler = None
        self.model_path = model_path
        
        if model_path and Path(model_path).exists():
            self.load_model(model_path)
    
    def build_model(self, input_shape: Tuple[int, ...]) -> keras.Model:
        """
        ساخت مدل با چندین خروجی
        
        خروجی‌ها:
        1. احتمال وقوع حمله (binary classification)
        2. شدت حمله (regression: 0-1)
        3. مدت زمان حمله (regression: hours)
        4. پاسخ به درمان (regression: 0-1)
        5. پیشرفت بیماری (regression: 0-1)
        """
        inputs = keras.Input(shape=input_shape, name='input_features')
        
        # Shared layers
        x = layers.Dense(128, activation='relu', name='shared_dense_1')(inputs)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.3)(x)
        
        x = layers.Dense(64, activation='relu', name='shared_dense_2')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.3)(x)
        
        x = layers.Dense(32, activation='relu', name='shared_dense_3')(x)
        
        # Output 1: احتمال وقوع حمله (binary)
        attack_probability = layers.Dense(1, activation='sigmoid', name='attack_probability')(x)
        
        # Output 2: شدت حمله (regression)
        attack_severity = layers.Dense(1, activation='sigmoid', name='attack_severity')(x)
        
        # Output 3: مدت زمان حمله (regression)
        attack_duration = layers.Dense(1, activation='relu', name='attack_duration')(x)
        
        # Output 4: پاسخ به درمان (regression)
        treatment_response = layers.Dense(1, activation='sigmoid', name='treatment_response')(x)
        
        # Output 5: پیشرفت بیماری (regression)
        disease_progression = layers.Dense(1, activation='sigmoid', name='disease_progression')(x)
        
        model = keras.Model(
            inputs=inputs,
            outputs={
                'attack_probability': attack_probability,
                'attack_severity': attack_severity,
                'attack_duration': attack_duration,
                'treatment_response': treatment_response,
                'disease_progression': disease_progression
            },
            name='advanced_prediction_model'
        )
        
        return model
    
    def compile_model(self, learning_rate: float = 0.001):
        """کامپایل مدل"""
        if self.model is None:
            raise ValueError("Model not built. Call build_model() first.")
        
        self.model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
            loss={
                'attack_probability': 'binary_crossentropy',
                'attack_severity': 'mse',
                'attack_duration': 'mse',
                'treatment_response': 'mse',
                'disease_progression': 'mse'
            },
            loss_weights={
                'attack_probability': 1.0,
                'attack_severity': 0.8,
                'attack_duration': 0.6,
                'treatment_response': 0.7,
                'disease_progression': 0.5
            },
            metrics={
                'attack_probability': 'accuracy',
                'attack_severity': 'mae',
                'attack_duration': 'mae',
                'treatment_response': 'mae',
                'disease_progression': 'mae'
            }
        )
    
    def train(
        self,
        X_train: np.ndarray,
        y_train: Dict[str, np.ndarray],
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[Dict[str, np.ndarray]] = None,
        epochs: int = 100,
        batch_size: int = 32,
        validation_split: float = 0.2
    ) -> keras.callbacks.History:
        """
        آموزش مدل
        
        Args:
            X_train: ویژگی‌های آموزشی
            y_train: برچسب‌های آموزشی (dict با keys: attack_probability, attack_severity, ...)
            X_val: ویژگی‌های validation (اختیاری)
            y_val: برچسب‌های validation (اختیاری)
            epochs: تعداد epochs
            batch_size: اندازه batch
            validation_split: نسبت validation (اگر X_val ارائه نشده باشد)
        """
        if self.model is None:
            raise ValueError("Model not built. Call build_model() first.")
        
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=1e-7
            ),
            keras.callbacks.ModelCheckpoint(
                'best_model.h5',
                monitor='val_loss',
                save_best_only=True
            )
        ]
        
        if X_val is not None and y_val is not None:
            validation_data = (X_val, y_val)
            validation_split = None
        else:
            validation_data = None
        
        history = self.model.fit(
            X_train,
            y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            validation_data=validation_data,
            callbacks=callbacks,
            verbose=1
        )
        
        return history
    
    def predict(self, X: np.ndarray) -> Dict[str, np.ndarray]:
        """
        پیش‌بینی
        
        Returns:
            dict با keys: attack_probability, attack_severity, attack_duration,
                         treatment_response, disease_progression
        """
        if self.model is None:
            raise ValueError("Model not loaded or built.")
        
        # Normalize if scaler exists
        if self.scaler is not None:
            X = self.scaler.transform(X)
        
        predictions = self.model.predict(X, verbose=0)
        
        return {
            'attack_probability': predictions['attack_probability'].flatten(),
            'attack_severity': predictions['attack_severity'].flatten(),
            'attack_duration': predictions['attack_duration'].flatten(),
            'treatment_response': predictions['treatment_response'].flatten(),
            'disease_progression': predictions['disease_progression'].flatten()
        }
    
    def save_model(self, model_path: str):
        """ذخیره مدل"""
        Path(model_path).parent.mkdir(parents=True, exist_ok=True)
        
        # ذخیره مدل Keras
        self.model.save(f"{model_path}.h5")
        
        # ذخیره scaler
        if self.scaler is not None:
            joblib.dump(self.scaler, f"{model_path}_scaler.pkl")
        
        # ذخیره metadata
        metadata = {
            'input_shape': self.model.input_shape[1:],
            'output_names': list(self.model.output_names),
            'saved_at': datetime.now().isoformat()
        }
        with open(f"{model_path}_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def load_model(self, model_path: str):
        """بارگذاری مدل"""
        # بارگذاری مدل Keras
        self.model = keras.models.load_model(f"{model_path}.h5")
        
        # بارگذاری scaler
        scaler_path = f"{model_path}_scaler.pkl"
        if Path(scaler_path).exists():
            self.scaler = joblib.load(scaler_path)
        
        self.model_path = model_path
    
    def convert_to_tflite(self, output_path: str, quantize: bool = True):
        """
        تبدیل به TensorFlow Lite برای استفاده در میکروکنترلر
        
        Args:
            output_path: مسیر خروجی
            quantize: آیا باید quantization انجام شود
        """
        if self.model is None:
            raise ValueError("Model not loaded or built.")
        
        converter = tf.lite.TFLiteConverter.from_keras_model(self.model)
        
        if quantize:
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
            converter.target_spec.supported_types = [tf.float16]
        
        tflite_model = converter.convert()
        
        with open(output_path, 'wb') as f:
            f.write(tflite_model)
        
        print(f"TFLite model saved to {output_path}")
        print(f"Model size: {len(tflite_model) / 1024:.2f} KB")

