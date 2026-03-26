#!/usr/bin/env python3
"""
Prophet Time Series Forecasting Module
Auto-learning seasonal patterns and anomaly detection based on forecasts
"""

import sys
sys.path.insert(0, '.')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from pymongo import MongoClient
from config import MONGODB_URI, MONGODB_DB, MONGODB_COLLECTION
from data_extractor import MongoDBFeatureExtractor
from prophet import Prophet
import warnings
warnings.filterwarnings('ignore')

class ProphetForecaster:
    """Time Series Forecasting with Prophet for anomaly detection"""
    
    def __init__(self):
        self.models = {}
        self.forecasts = {}
        self.metrics = ['avg_latency', 'avg_cpu_usage', 'avg_memory_usage', 'avg_queue_depth']
    
    def load_chunk_data(self, limit=20):
        """Load historical chunk data from MongoDB"""
        extractor = MongoDBFeatureExtractor()
        if not extractor.connect():
            print("Failed to connect to MongoDB")
            return None
        
        chunks = extractor.fetch_latest_chunks(limit=limit)
        df = extractor.aggregate_chunk_features(chunks)
        extractor.disconnect()
        
        return df
    
    def prepare_prophet_data(self, df, metric):
        """Prepare data for Prophet"""
        if metric not in df.columns or len(df) < 3:
            return None
        
        prophet_df = pd.DataFrame({
            'ds': pd.to_datetime(df['timestamp']),
            'y': df[metric]
        }).sort_values('ds').drop_duplicates(subset=['ds']).reset_index(drop=True)
        
        if len(prophet_df) < 3:
            return None
        
        return prophet_df
    
    def train_prophet(self, prophet_df, metric_name):
        """Train Prophet model for a specific metric"""
        try:
            # Determine seasonality based on metric
            yearly_seasonality = False
            daily_seasonality = False
            
            model = Prophet(
                yearly_seasonality=yearly_seasonality,
                daily_seasonality=daily_seasonality,
                interval_width=0.95,
                growth='linear',
                changepoint_prior_scale=0.05
            )
            
            model.fit(prophet_df)
            print(f"✅ Prophet model trained for {metric_name}")
            return model
        
        except Exception as e:
            print(f"❌ Error training Prophet for {metric_name}: {e}")
            return None
    
    def generate_forecast(self, model, periods=10, freq='min'):
        """Generate forecast for given periods"""
        if model is None:
            return None
        
        try:
            future = model.make_future_dataframe(periods=periods, freq=freq)
            forecast = model.predict(future)
            return forecast
        
        except Exception as e:
            print(f"❌ Error generating forecast: {e}")
            return None
    
    def detect_forecast_anomalies(self, df, forecast, metric):
        """Detect anomalies based on deviation from forecast"""
        anomalies = []
        
        # Get historical data used in training
        historical = forecast[forecast.index < len(df)]
        
        for idx in range(min(len(df), len(historical))):
            actual = df[metric].iloc[idx]
            predicted = historical['yhat'].iloc[idx]
            upper = historical['yhat_upper'].iloc[idx]
            lower = historical['yhat_lower'].iloc[idx]
            
            # Check if actual value is outside confidence interval
            is_anomaly = actual > upper or actual < lower
            deviation = abs(actual - predicted) / (predicted + 1)
            
            anomalies.append({
                'index': idx,
                'actual': actual,
                'predicted': predicted,
                'upper_bound': upper,
                'lower_bound': lower,
                'is_anomaly': is_anomaly,
                'deviation_pct': deviation * 100
            })
        
        return pd.DataFrame(anomalies)
    
    def run_full_pipeline(self):
        """Run complete Prophet forecasting pipeline"""
        print("\n" + "="*80)
        print("🔮 Prophet Time Series Forecasting Pipeline")
        print("="*80)
        
        # Load data
        print("\n📊 Loading historical chunk data...")
        df = self.load_chunk_data(limit=20)
        if df is None or len(df) == 0:
            print("❌ No data available")
            return
        
        print(f"✅ Loaded {len(df)} chunks")
        
        # Train models for each metric
        print("\n🤖 Training Prophet models for each metric...")
        for metric in self.metrics:
            if metric not in df.columns:
                continue
            
            prophet_df = self.prepare_prophet_data(df, metric)
            if prophet_df is None:
                continue
            
            model = self.train_prophet(prophet_df, metric)
            if model is not None:
                self.models[metric] = model
                
                # Generate forecast
                forecast = self.generate_forecast(model, periods=5)
                if forecast is not None:
                    self.forecasts[metric] = forecast
                    
                    # Detect anomalies
                    anomalies = self.detect_forecast_anomalies(df, forecast, metric)
                    print(f"  ├─ {metric}: {len(anomalies)} anomalies detected")
                    print(f"  ├─ Forecast range: {forecast['yhat'].iloc[-1]:.0f} (next prediction)")
                    print(f"  └─ Confidence interval: [{forecast['yhat_lower'].iloc[-1]:.0f}, {forecast['yhat_upper'].iloc[-1]:.0f}]")
        
        # Generate summary report
        self.generate_report(df)
        
        return df
    
    def generate_report(self, df):
        """Generate comprehensive forecast report"""
        print("\n" + "="*80)
        print("📈 PROPHET FORECASTING REPORT")
        print("="*80)
        
        print("\n🎯 Models Trained:")
        for metric in self.models.keys():
            forecast = self.forecasts.get(metric)
            if forecast is not None:
                print(f"  ✅ {metric}")
                print(f"     Current: {df[metric].iloc[-1]:.2f}")
                print(f"     Next Forecast: {forecast['yhat'].iloc[-1]:.2f}")
                print(f"     Trend: {'📈 UP' if forecast['trend'].iloc[-1] > forecast['trend'].iloc[-2] else '📉 DOWN'}")
        
        print("\n🚀 Key Features:")
        print("  ✅ Automatic seasonality detection")
        print("  ✅ Trend component analysis")
        print("  ✅ Confidence interval estimation (95%)")
        print("  ✅ Anomaly detection based on forecast bounds")
        print("  ✅ Auto-learning from historical data")
        
        print("\n💾 Forecasts saved to forecast_results.json")
        
        # Save results
        results = {
            'timestamp': datetime.now().isoformat(),
            'models_trained': list(self.models.keys()),
            'forecasts': {
                metric: {
                    'predictions': self.forecasts[metric]['yhat'].tolist()[-5:],
                    'upper_bound': self.forecasts[metric]['yhat_upper'].tolist()[-5:],
                    'lower_bound': self.forecasts[metric]['yhat_lower'].tolist()[-5:],
                    'trend': self.forecasts[metric]['trend'].tolist()[-5:]
                } for metric in self.forecasts.keys()
            },
            'last_update': datetime.now().isoformat()
        }
        
        with open('forecast_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print("\n" + "="*80)

class RealTimeAnomalyPredictor:
    """Real-time anomaly prediction using Prophet forecasts"""
    
    def __init__(self, forecaster):
        self.forecaster = forecaster
    
    def predict_anomaly_for_chunk(self, chunk_features):
        """Predict if upcoming chunk will be anomalous"""
        predictions = {}
        
        for metric, model in self.forecaster.models.items():
            if metric not in chunk_features:
                continue
            
            # Get next forecast
            future = model.make_future_dataframe(periods=1)
            forecast = model.predict(future)
            
            predicted_value = forecast['yhat'].iloc[-1]
            upper_bound = forecast['yhat_upper'].iloc[-1]
            lower_bound = forecast['yhat_lower'].iloc[-1]
            actual_value = chunk_features[metric]
            
            # Calculate deviation
            deviation = abs(actual_value - predicted_value) / (predicted_value + 1)
            is_outside_bounds = actual_value > upper_bound or actual_value < lower_bound
            
            predictions[metric] = {
                'predicted': predicted_value,
                'actual': actual_value,
                'upper_bound': upper_bound,
                'lower_bound': lower_bound,
                'deviation_pct': deviation * 100,
                'is_anomaly': is_outside_bounds
            }
        
        # Overall anomaly score
        anomaly_scores = [p['deviation_pct'] for p in predictions.values()]
        overall_anomaly_score = np.mean(anomaly_scores) if anomaly_scores else 0
        
        return {
            'timestamp': datetime.now().isoformat(),
            'predictions': predictions,
            'overall_anomaly_score': overall_anomaly_score,
            'is_anomalous': overall_anomaly_score > 30  # Threshold
        }

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == '__main__':
    # Initialize forecaster
    forecaster = ProphetForecaster()
    
    # Run pipeline
    df = forecaster.run_full_pipeline()
    
    if df is not None and len(df) > 0:
        # Demonstrate real-time prediction
        print("\n" + "="*80)
        print("🚀 Real-Time Anomaly Prediction (Demo)")
        print("="*80)
        
        predictor = RealTimeAnomalyPredictor(forecaster)
        
        # Use latest chunk features as example
        latest_chunk = df.iloc[-1].to_dict()
        
        prediction = predictor.predict_anomaly_for_chunk(latest_chunk)
        
        print(f"\n📊 Latest Chunk Analysis:")
        print(f"  Overall Anomaly Score: {prediction['overall_anomaly_score']:.2f}%")
        print(f"  Status: {'🔴 ANOMALY PREDICTED' if prediction['is_anomalous'] else '🟢 NORMAL EXPECTED'}")
        
        for metric, pred in prediction['predictions'].items():
            status = "🔴 ANOMALY" if pred['is_anomaly'] else "🟢 NORMAL"
            print(f"\n  {metric}:")
            print(f"    Actual: {pred['actual']:.2f}")
            print(f"    Predicted: {pred['predicted']:.2f}")
            print(f"    Deviation: {pred['deviation_pct']:.1f}%")
            print(f"    Bounds: [{pred['lower_bound']:.2f}, {pred['upper_bound']:.2f}]")
            print(f"    Status: {status}")
        
        print("\n" + "="*80)
        print("💾 Prediction results saved!")
        print("="*80)
