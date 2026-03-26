#!/usr/bin/env python3
"""
Plotly Dash Dashboard for Kubernetes Log Anomaly Detection
Features: Model Drift Detection, Prophet Forecasting, Comprehensive Monitoring
"""

import sys
sys.path.insert(0, '.')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import re

import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from pymongo import MongoClient
from config import MONGODB_URI, MONGODB_DB, MONGODB_COLLECTION, FEATURE_PATTERNS
from data_extractor import MongoDBFeatureExtractor
from model import IsolationForestAnomalyDetector
from prophet import Prophet
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# INITIALIZE DASH APP
# ============================================================================

app = dash.Dash(__name__)
app.title = "K8s Log Anomaly Detection Dashboard"

# ============================================================================
# DATA LOADING & PROCESSING
# ============================================================================

def load_data():
    """Load latest chunks from MongoDB and extract features"""
    extractor = MongoDBFeatureExtractor()
    if not extractor.connect():
        return None, None, None
    
    chunks = extractor.fetch_latest_chunks(limit=12)
    df = extractor.aggregate_chunk_features(chunks)
    extractor.disconnect()
    
    return df, chunks, extractor

def train_model(df):
    """Train Isolation Forest and get predictions"""
    if len(df) == 0:
        return None, np.array([]), np.array([])
    
    detector = IsolationForestAnomalyDetector()
    results = detector.train(df)  # Returns a dictionary!
    
    predictions = results['predictions']
    scores = results['anomaly_scores']
    
    return detector, predictions, scores

def detect_drift(df):
    """Detect model drift using statistical tests"""
    if len(df) < 4:
        return {"status": "Insufficient data", "drift_score": 0, "latency_shift": 0, "memory_shift": 0}
    
    # Compare early vs late chunks
    early_latency = df['avg_latency'].iloc[:len(df)//2].mean()
    late_latency = df['avg_latency'].iloc[len(df)//2:].mean()
    
    early_memory = df['avg_memory_usage'].iloc[:len(df)//2].mean()
    late_memory = df['avg_memory_usage'].iloc[len(df)//2:].mean()
    
    latency_drift = abs(late_latency - early_latency) / (early_latency + 1)
    memory_drift = abs(late_memory - early_memory) / (early_memory + 1)
    
    drift_score = (latency_drift + memory_drift) / 2
    
    return {
        "status": "High" if drift_score > 0.2 else "Normal",
        "drift_score": drift_score,
        "latency_shift": late_latency - early_latency,
        "memory_shift": late_memory - early_memory
    }

def train_prophet_model(df):
    """Train Prophet for time series forecasting"""
    if len(df) < 3 or 'timestamp' not in df.columns:
        return None, None
    
    # Prepare data for Prophet
    try:
        prophet_df = pd.DataFrame({
            'ds': pd.to_datetime(df['timestamp']),
            'y': df['avg_latency']
        }).sort_values('ds').drop_duplicates(subset=['ds'])
        
        if len(prophet_df) < 3:
            return None, None
            
        model = Prophet(yearly_seasonality=False, daily_seasonality=False, 
                       interval_width=0.95, growth='linear')
        model.fit(prophet_df)
        
        # Forecast next 5 periods
        future = model.make_future_dataframe(periods=5, freq='min')
        forecast = model.predict(future)
        
        return model, forecast
    except Exception as e:
        print(f"Prophet error: {e}")
        return None, None

# ============================================================================
# DASHBOARD LAYOUT
# ============================================================================

app.layout = html.Div(style={'backgroundColor': '#0a0e1a', 'color': '#ffffff', 'minHeight': '100vh', 'padding': '0', 'margin': '0'}, children=[
    
    # Header
    html.Div([
        html.Div([
            html.H1("🚀 Kubernetes Log Anomaly Detection Dashboard", style={'textAlign': 'left', 'marginBottom': '5px', 'color': '#00d9ff', 'fontSize': '32px', 'fontWeight': 'bold'}),
            html.P("Real-time ML model monitoring with drift detection & Prophet forecasting", style={'textAlign': 'left', 'color': '#00ff88', 'marginBottom': '0px', 'fontSize': '14px'})
        ], style={'paddingLeft': '30px'})
    ], style={'backgroundColor': '#1a1f2e', 'padding': '25px 0', 'borderBottom': '2px solid #00d9ff', 'boxShadow': '0 4px 6px rgba(0, 217, 255, 0.1)'}),
    
    # Tabs with better styling
    html.Div([
        dcc.Tabs(id='tabs', value='overview', children=[
            
            # ===== TAB 1: OVERVIEW =====
            dcc.Tab(label='📊 Overview', value='overview', children=[
                html.Div(style={'padding': '30px'}, children=[
                    html.Div(id='kpi-cards', style={'display': 'grid', 'gridTemplateColumns': 'repeat(4, 1fr)', 'gap': '20px', 'marginBottom': '30px'}),
                    html.Div(style={'display': 'grid', 'gridTemplateColumns': 'repeat(2, 1fr)', 'gap': '20px', 'marginBottom': '20px'}, children=[
                        dcc.Graph(id='latency-trend', style={'height': '420px'}),
                        dcc.Graph(id='memory-trend', style={'height': '420px'}),
                    ]),
                    html.Div(style={'display': 'grid', 'gridTemplateColumns': 'repeat(2, 1fr)', 'gap': '20px'}, children=[
                        dcc.Graph(id='cpu-memory-scatter', style={'height': '420px'}),
                        dcc.Graph(id='anomaly-score-dist', style={'height': '420px'}),
                    ]),
                ])
            ]),
            
            # ===== TAB 2: MODEL DRIFT =====
            dcc.Tab(label='📉 Model Drift', value='drift', children=[
                html.Div(style={'padding': '30px'}, children=[
                    html.Div(id='drift-summary', style={'marginBottom': '25px', 'padding': '20px', 'backgroundColor': '#1a1f2e', 'borderRadius': '10px', 'borderLeft': '4px solid #00ff88'}),
                    html.Div(style={'display': 'grid', 'gridTemplateColumns': 'repeat(3, 1fr)', 'gap': '20px', 'marginBottom': '25px'}, children=[
                        dcc.Graph(id='latency-drift', style={'height': '380px'}),
                        dcc.Graph(id='memory-drift', style={'height': '380px'}),
                        dcc.Graph(id='cpu-drift', style={'height': '380px'}),
                    ]),
                    dcc.Graph(id='feature-stats', style={'height': '450px'}),
                ])
            ]),
            
            # ===== TAB 3: ANOMALIES =====
            dcc.Tab(label='🔴 Anomalies', value='anomalies', children=[
                html.Div(style={'padding': '30px'}, children=[
                    html.Div(id='anomaly-summary', style={'marginBottom': '25px', 'padding': '20px', 'backgroundColor': '#1a1f2e', 'borderRadius': '10px', 'borderLeft': '4px solid #ff3333'}),
                    dcc.Graph(id='anomaly-heatmap', style={'height': '430px', 'marginBottom': '20px'}),
                    html.Div(id='anomaly-table', style={'height': '450px', 'overflowY': 'auto', 'backgroundColor': '#1a1f2e', 'padding': '20px', 'borderRadius': '10px', 'border': '1px solid #00d9ff'}),
                ])
            ]),
            
            # ===== TAB 4: FEATURES =====
            dcc.Tab(label='🔍 Features', value='features', children=[
                html.Div(style={'padding': '30px'}, children=[
                    html.Div(style={'display': 'grid', 'gridTemplateColumns': 'repeat(2, 1fr)', 'gap': '20px', 'marginBottom': '20px'}, children=[
                        dcc.Graph(id='latency-dist', style={'height': '420px'}),
                        dcc.Graph(id='memory-dist', style={'height': '420px'}),
                    ]),
                    dcc.Graph(id='correlation-matrix', style={'height': '650px'}),
                ])
            ]),
            
            # ===== TAB 5: TIME SERIES & PROPHET =====
            dcc.Tab(label='📈 Time Series', value='timeseries', children=[
                html.Div(style={'padding': '30px'}, children=[
                    dcc.Graph(id='prophet-forecast', style={'height': '520px', 'marginBottom': '20px'}),
                    html.Div(style={'display': 'grid', 'gridTemplateColumns': 'repeat(2, 1fr)', 'gap': '20px'}, children=[
                        dcc.Graph(id='trend-decomposition', style={'height': '430px'}),
                        dcc.Graph(id='forecast-error', style={'height': '430px'}),
                    ]),
                ])
            ]),
        ], style={
            'backgroundColor': '#0a0e1a',
            'borderBottom': '2px solid #00d9ff'
        }),
    ], style={'backgroundColor': '#0a0e1a', 'padding': '0 30px'}),
    
    # Auto-refresh interval
    dcc.Interval(id='interval-component', interval=30*1000, n_intervals=0),
    
    # Store for caching data
    dcc.Store(id='data-store'),
])

# ============================================================================
# CALLBACKS
# ============================================================================

@app.callback(
    [Output('kpi-cards', 'children'),
     Output('latency-trend', 'figure'),
     Output('memory-trend', 'figure'),
     Output('cpu-memory-scatter', 'figure'),
     Output('anomaly-score-dist', 'figure'),
     Output('data-store', 'data')],
    [Input('interval-component', 'n_intervals')],
    prevent_initial_call=False
)
def update_overview(n):
    """Update Overview tab"""
    try:
        df, chunks, _ = load_data()
        if df is None or len(df) == 0:
            return [], {}, {}, {}, {}, {'error': 'No data'}
        
        detector, predictions, scores = train_model(df)
        
        df['anomaly'] = predictions
        df['anomaly_score'] = scores
        
        # Store data with safety checks
        data = {
            'df': df.to_json(orient='records'),
            'scores': scores.tolist() if isinstance(scores, np.ndarray) else list(scores),
            'predictions': predictions.tolist() if isinstance(predictions, np.ndarray) else list(predictions)
        }
        
        kpi_children = [
            html.Div([
                html.H3(f"{len(df)}", style={'color': '#00d9ff', 'marginBottom': '8px', 'fontSize': '28px', 'fontWeight': 'bold'}),
                html.P("Chunks", style={'color': '#00d9ff', 'fontSize': '14px', 'opacity': '0.8'})
            ], style={'padding': '20px', 'backgroundColor': '#1a1f2e', 'borderRadius': '10px', 'textAlign': 'center', 'border': '2px solid #00d9ff', 'boxShadow': '0 0 15px rgba(0, 217, 255, 0.2)'}),
            
            html.Div([
                html.H3(f"{(predictions==1).sum()}", style={'color': '#ff3333', 'marginBottom': '8px', 'fontSize': '28px', 'fontWeight': 'bold'}),
                html.P("Anomalies", style={'color': '#ff3333', 'fontSize': '14px', 'opacity': '0.8'})
            ], style={'padding': '20px', 'backgroundColor': '#1a1f2e', 'borderRadius': '10px', 'textAlign': 'center', 'border': '2px solid #ff3333', 'boxShadow': '0 0 15px rgba(255, 51, 51, 0.2)'}),
            
            html.Div([
                html.H3(f"{df['avg_latency'].mean():.0f}ms", style={'color': '#ffaa00', 'marginBottom': '8px', 'fontSize': '28px', 'fontWeight': 'bold'}),
                html.P("Avg Latency", style={'color': '#ffaa00', 'fontSize': '14px', 'opacity': '0.8'})
            ], style={'padding': '20px', 'backgroundColor': '#1a1f2e', 'borderRadius': '10px', 'textAlign': 'center', 'border': '2px solid #ffaa00', 'boxShadow': '0 0 15px rgba(255, 170, 0, 0.2)'}),
            
            html.Div([
                html.H3(f"{df['avg_memory_usage'].mean():.0f}%", style={'color': '#00ff88', 'marginBottom': '8px', 'fontSize': '28px', 'fontWeight': 'bold'}),
                html.P("Avg Memory", style={'color': '#00ff88', 'fontSize': '14px', 'opacity': '0.8'})
            ], style={'padding': '20px', 'backgroundColor': '#1a1f2e', 'borderRadius': '10px', 'textAlign': 'center', 'border': '2px solid #00ff88', 'boxShadow': '0 0 15px rgba(0, 255, 136, 0.2)'}),
        ]
        
        fig_latency = go.Figure()
        fig_latency.add_trace(go.Scatter(
            x=list(range(len(df))), y=df['avg_latency'],
            mode='lines+markers', name='Avg Latency',
            line=dict(color='#00d9ff', width=3),
            marker=dict(size=8, color=['#ff3333' if a else '#00d9ff' for a in df['anomaly']])
        ))
        fig_latency.update_layout(title='Latency Trend', hovermode='x unified', 
                                 plot_bgcolor='#0a0e1a', paper_bgcolor='#0a0e1a',
                                 font=dict(color='#ffffff', size=12),
                                 title_font=dict(size=16, color='#00d9ff'),
                                 xaxis=dict(gridcolor='#1a1f2e'),
                                 yaxis=dict(gridcolor='#1a1f2e'))
        
        fig_memory = go.Figure()
        fig_memory.add_trace(go.Scatter(
            x=list(range(len(df))), y=df['avg_memory_usage'],
            mode='lines+markers', name='Avg Memory',
            line=dict(color='#00ff88', width=3),
            marker=dict(size=8, color=['#ff3333' if a else '#00ff88' for a in df['anomaly']])
        ))
        fig_memory.update_layout(title='Memory Usage Trend', hovermode='x unified',
                                plot_bgcolor='#0a0e1a', paper_bgcolor='#0a0e1a',
                                font=dict(color='#ffffff', size=12),
                                title_font=dict(size=16, color='#00ff88'),
                                xaxis=dict(gridcolor='#1a1f2e'),
                                yaxis=dict(gridcolor='#1a1f2e'))
        
        fig_scatter = go.Figure()
        fig_scatter.add_trace(go.Scatter(
            x=df['avg_cpu_usage'], y=df['avg_memory_usage'],
            mode='markers', text=df['chunk_id'],
            marker=dict(
                size=10,
                color=df['anomaly_score'],
                colorscale=[[0, '#00ff88'], [0.5, '#ffaa00'], [1, '#ff3333']],
                showscale=True,
                colorbar=dict(title="Score")
            )
        ))
        fig_scatter.update_layout(title='CPU vs Memory (Anomaly Score)', 
                                 xaxis_title='CPU %', yaxis_title='Memory %',
                                 plot_bgcolor='#0a0e1a', paper_bgcolor='#0a0e1a',
                                 font=dict(color='#ffffff', size=12),
                                 title_font=dict(size=16, color='#ffaa00'),
                                 xaxis=dict(gridcolor='#1a1f2e'),
                                 yaxis=dict(gridcolor='#1a1f2e'),
                                 hovermode='closest')
        
        fig_dist = go.Figure()
        fig_dist.add_trace(go.Histogram(x=df['anomaly_score'], nbinsx=20, name='Anomaly Score',
                                       marker=dict(color='#00d9ff')))
        fig_dist.update_layout(title='Anomaly Score Distribution', hovermode='x unified',
                              plot_bgcolor='#0a0e1a', paper_bgcolor='#0a0e1a',
                              font=dict(color='#ffffff', size=12),
                              title_font=dict(size=16, color='#00d9ff'),
                              xaxis=dict(gridcolor='#1a1f2e'),
                              yaxis=dict(gridcolor='#1a1f2e'))
        
        return kpi_children, fig_latency, fig_memory, fig_scatter, fig_dist, data
    
    except Exception as e:
        print(f"❌ Error in overview: {e}")
        import traceback
        traceback.print_exc()
        error_data = {'error': str(e)[:200]}
        return [], {}, {}, {}, {}, error_data

@app.callback(
    [Output('drift-summary', 'children'),
     Output('latency-drift', 'figure'),
     Output('memory-drift', 'figure'),
     Output('cpu-drift', 'figure'),
     Output('feature-stats', 'figure')],
    [Input('data-store', 'data')]
)
def update_drift(data):
    """Update Model Drift tab"""
    try:
        if data is None or 'df' not in data:
            df, _, _ = load_data()
            if df is None or len(df) == 0:
                return html.Div("No data"), {}, {}, {}, {}
        else:
            df = pd.read_json(data['df'])
        drift = detect_drift(df)
        
        summary = html.Div([
            html.H3(f"Drift Status: {drift['status']}", style={'color': '#ff3333' if drift['status']=='High' else '#00ff88', 'marginBottom': '10px'}),
            html.P(f"Drift Score: {drift['drift_score']:.2%}"),
            html.P(f"Latency Shift: {drift['latency_shift']:.0f}ms"),
            html.P(f"Memory Shift: {drift['memory_shift']:.1f}%"),
        ])
        
        mid = len(df) // 2
        early = df.iloc[:mid]
        late = df.iloc[mid:]
        
        fig_lat = go.Figure()
        fig_lat.add_trace(go.Box(y=early['avg_latency'], name='Early', marker_color='#00d9ff'))
        fig_lat.add_trace(go.Box(y=late['avg_latency'], name='Late', marker_color='#ff3333'))
        fig_lat.update_layout(title='Latency Distribution Shift', plot_bgcolor='#1a1f26',
                             paper_bgcolor='#0f1419', font=dict(color='#ffffff'))
        
        fig_mem = go.Figure()
        fig_mem.add_trace(go.Box(y=early['avg_memory_usage'], name='Early', marker_color='#00d9ff'))
        fig_mem.add_trace(go.Box(y=late['avg_memory_usage'], name='Late', marker_color='#ff3333'))
        fig_mem.update_layout(title='Memory Distribution Shift', plot_bgcolor='#1a1f26',
                             paper_bgcolor='#0f1419', font=dict(color='#ffffff'))
        
        fig_cpu = go.Figure()
        fig_cpu.add_trace(go.Box(y=early['avg_cpu_usage'], name='Early', marker_color='#00d9ff'))
        fig_cpu.add_trace(go.Box(y=late['avg_cpu_usage'], name='Late', marker_color='#ff3333'))
        fig_cpu.update_layout(title='CPU Distribution Shift', plot_bgcolor='#1a1f26',
                             paper_bgcolor='#0f1419', font=dict(color='#ffffff'))
        
        features = ['avg_latency', 'avg_cpu_usage', 'avg_memory_usage', 'avg_queue_depth']
        early_means = [early[f].mean() if f in early.columns else 0 for f in features]
        late_means = [late[f].mean() if f in late.columns else 0 for f in features]
        
        fig_stats = go.Figure(data=[
            go.Bar(name='Early', x=features, y=early_means, marker_color='#00d9ff'),
            go.Bar(name='Late', x=features, y=late_means, marker_color='#ff3333')
        ])
        fig_stats.update_layout(title='Feature Mean Comparison (Drift Detection)',
                               plot_bgcolor='#1a1f26', paper_bgcolor='#0f1419',
                               font=dict(color='#ffffff'), barmode='group')
        
        return summary, fig_lat, fig_mem, fig_cpu, fig_stats
    
    except Exception as e:
        print(f"Error in drift: {e}")
        return html.Div(f"Error: {e}"), {}, {}, {}, {}

@app.callback(
    [Output('anomaly-summary', 'children'),
     Output('anomaly-heatmap', 'figure'),
     Output('anomaly-table', 'children')],
    [Input('data-store', 'data')]
)
def update_anomalies(data):
    """Update Anomalies tab"""
    try:
        if data is None or 'df' not in data:
            df, _, _ = load_data()
            if df is None or len(df) == 0:
                return html.Div("No data"), {}, html.Div("No anomalies")
        else:
            df = pd.read_json(data['df'])
        anomalies = df[df['anomaly'] == 1]
        
        summary = html.Div([
            html.H3(f"Anomalies Found: {len(anomalies)}", style={'color': '#ff3333' if len(anomalies) > 0 else '#00ff88', 'marginBottom': '10px'}),
            html.P(f"Anomaly Rate: {(len(anomalies)/len(df)*100):.1f}%" if len(df) > 0 else "0%"),
        ])
        
        if len(df) > 0:
            heatmap_data = df[['avg_latency', 'avg_cpu_usage', 'avg_memory_usage', 'avg_queue_depth']].T
            
            fig_heat = go.Figure(data=go.Heatmap(
                z=heatmap_data.values,
                y=heatmap_data.index,
                colorscale='RdYlGn_r',
            ))
            fig_heat.update_layout(title='Feature Heatmap', plot_bgcolor='#1a1f26',
                                  paper_bgcolor='#0f1419', font=dict(color='#ffffff'))
        else:
            fig_heat = {}
        
        if len(anomalies) > 0:
            table_rows = []
            for _, row in anomalies.iterrows():
                table_rows.append(html.Tr([
                    html.Td(str(row['chunk_id'])[:20], style={'borderBottom': '1px solid #333', 'padding': '10px'}),
                    html.Td(f"{row['avg_latency']:.0f}ms", style={'borderBottom': '1px solid #333', 'padding': '10px'}),
                    html.Td(f"{row['avg_memory_usage']:.1f}%", style={'borderBottom': '1px solid #333', 'padding': '10px'}),
                    html.Td(f"{row['anomaly_score']:.3f}", style={'borderBottom': '1px solid #333', 'padding': '10px', 'color': '#ff3333'}),
                ]))
            
            table = html.Table([
                html.Thead(html.Tr([
                    html.Th('Chunk ID', style={'padding': '10px', 'textAlign': 'left'}),
                    html.Th('Latency', style={'padding': '10px', 'textAlign': 'left'}),
                    html.Th('Memory', style={'padding': '10px', 'textAlign': 'left'}),
                    html.Th('Anomaly Score', style={'padding': '10px', 'textAlign': 'left'}),
                ])),
                html.Tbody(table_rows)
            ], style={'width': '100%', 'color': '#ffffff'})
        else:
            table = html.Div("✅ No anomalies detected!", style={'color': '#00ff88', 'padding': '20px', 'textAlign': 'center'})
        
        return summary, fig_heat, table
    
    except Exception as e:
        print(f"Error in anomalies: {e}")
        return html.Div(f"Error: {e}"), {}, html.Div(f"Error: {e}")

@app.callback(
    [Output('latency-dist', 'figure'),
     Output('memory-dist', 'figure'),
     Output('correlation-matrix', 'figure')],
    [Input('data-store', 'data')]
)
def update_features(data):
    """Update Features tab"""
    try:
        if data is None or 'df' not in data:
            df, _, _ = load_data()
            if df is None or len(df) == 0:
                return {}, {}, {}
        else:
            df = pd.read_json(data['df'])
        
        fig_lat = go.Figure()
        fig_lat.add_trace(go.Histogram(x=df['avg_latency'], nbinsx=15, name='Latency',
                                       marker=dict(color='#00d9ff')))
        fig_lat.update_layout(title='Latency Distribution', plot_bgcolor='#1a1f26',
                             paper_bgcolor='#0f1419', font=dict(color='#ffffff'))
        
        fig_mem = go.Figure()
        fig_mem.add_trace(go.Histogram(x=df['avg_memory_usage'], nbinsx=15, name='Memory',
                                       marker=dict(color='#00ff88')))
        fig_mem.update_layout(title='Memory Distribution', plot_bgcolor='#1a1f26',
                             paper_bgcolor='#0f1419', font=dict(color='#ffffff'))
        
        corr_features = [f for f in ['avg_latency', 'avg_cpu_usage', 'avg_memory_usage', 'avg_queue_depth'] if f in df.columns]
        if len(corr_features) > 1:
            corr_matrix = df[corr_features].corr()
            
            fig_corr = go.Figure(data=go.Heatmap(
                z=corr_matrix.values,
                x=corr_features,
                y=corr_features,
                colorscale='RdBu',
                zmid=0,
                text=np.round(corr_matrix.values, 2),
                texttemplate='%{text}',
                textfont={"size": 10},
            ))
            fig_corr.update_layout(title='Feature Correlation Matrix', plot_bgcolor='#1a1f26',
                                  paper_bgcolor='#0f1419', font=dict(color='#ffffff'))
        else:
            fig_corr = {}
        
        return fig_lat, fig_mem, fig_corr
    
    except Exception as e:
        print(f"Error in features: {e}")
        return {}, {}, {}

@app.callback(
    [Output('prophet-forecast', 'figure'),
     Output('trend-decomposition', 'figure'),
     Output('forecast-error', 'figure')],
    [Input('data-store', 'data')],
    prevent_initial_call=False
)
def update_timeseries(data):
    """Update Time Series tab with Prophet"""
    try:
        # If no cached data, load fresh
        if data is None or 'df' not in data:
            df, _, _ = load_data()
            if df is None or len(df) == 0:
                empty_fig = go.Figure().add_annotation(text="No data available")
                return empty_fig, empty_fig, empty_fig
        else:
            df = pd.read_json(data['df'])
        
        model, forecast = train_prophet_model(df)
        
        if model is None or forecast is None:
            empty_fig = go.Figure().add_annotation(text="Prophet model training failed")
            return empty_fig, empty_fig, empty_fig
        
        # ===== FIGURE 1: PROPHET FORECAST WITH CONFIDENCE INTERVALS =====
        fig_forecast = go.Figure()
        
        # Historical latency
        fig_forecast.add_trace(go.Scatter(
            x=list(range(len(df))), 
            y=df['avg_latency'] if 'avg_latency' in df.columns else [0]*len(df),
            mode='lines+markers', name='Historical Latency',
            line=dict(color='#00d9ff', width=2),
            marker=dict(size=6)
        ))
        
        # Forecast future values
        forecast_future = forecast[forecast['ds'] > df['timestamp'].max()] if 'timestamp' in df.columns else forecast.iloc[len(df):]
        
        if len(forecast_future) > 0:
            # Forecast line
            fig_forecast.add_trace(go.Scatter(
                x=list(range(len(df), len(df)+len(forecast_future))), 
                y=forecast_future['yhat'].values,
                mode='lines+markers', name='Forecast',
                line=dict(color='#ffaa00', width=2, dash='dash'),
                marker=dict(size=6)
            ))
            
            # Upper confidence bound
            fig_forecast.add_trace(go.Scatter(
                x=list(range(len(df), len(df)+len(forecast_future))),
                y=forecast_future['yhat_upper'].values,
                fill=None, mode='lines', line_color='rgba(0,0,0,0)',
                showlegend=False, name='Upper Bound'
            ))
            
            # Lower confidence bound (fills to upper)
            fig_forecast.add_trace(go.Scatter(
                x=list(range(len(df), len(df)+len(forecast_future))),
                y=forecast_future['yhat_lower'].values,
                fill='tonexty', mode='lines', line_color='rgba(0,0,0,0)',
                name='95% Confidence Interval', 
                fillcolor='rgba(255, 170, 0, 0.2)'
            ))
        
        fig_forecast.update_layout(
            title='Prophet Latency Forecast (5-step ahead with 95% CI)',
            xaxis_title='Time Period',
            yaxis_title='Latency (ms)',
            plot_bgcolor='#1a1f26', 
            paper_bgcolor='#0f1419',
            font=dict(color='#ffffff', size=12),
            hovermode='x unified',
            height=500,
            showlegend=True
        )
        
        # ===== FIGURE 2: TREND COMPONENT =====
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=list(range(len(forecast))), 
            y=forecast['trend'].values,
            mode='lines', name='Trend',
            line=dict(color='#00ff88', width=3, shape='spline'),
            fill='tozeroy',
            fillcolor='rgba(0, 255, 136, 0.1)'
        ))
        fig_trend.update_layout(
            title='Prophet Trend Component (Long-term Pattern)',
            xaxis_title='Time Period',
            yaxis_title='Trend Value (ms)',
            plot_bgcolor='#1a1f26', 
            paper_bgcolor='#0f1419',
            font=dict(color='#ffffff', size=12),
            hovermode='x unified',
            height=400
        )
        
        # ===== FIGURE 3: FORECAST ACCURACY =====
        fig_error = go.Figure()
        
        # Calculate MAPE (Mean Absolute Percentage Error)
        historical_in_forecast = forecast.iloc[:len(df)]
        if len(df) > 0:
            errors = []
            for i in range(min(len(df), len(historical_in_forecast))):
                actual = df['avg_latency'].iloc[i] if 'avg_latency' in df.columns else 0
                predicted = historical_in_forecast['yhat'].iloc[i]
                if actual != 0:
                    error = abs((actual - predicted) / actual) * 100
                else:
                    error = 0
                errors.append(error)
            
            colors = ['#00ff88' if e < 20 else '#ffaa00' if e < 40 else '#ff3333' for e in errors]
            
            fig_error.add_trace(go.Bar(
                x=list(range(len(errors))), 
                y=errors,
                marker=dict(color=colors),
                name='MAPE %',
                text=[f'{e:.1f}%' for e in errors],
                textposition='auto'
            ))
            
            fig_error.add_hline(y=20, line_dash='dash', line_color='#ffaa00', 
                              annotation_text='Warning (20%)', annotation_position='right')
        
        fig_error.update_layout(
            title='Forecast Accuracy - Mean Absolute Percentage Error (MAPE)',
            xaxis_title='Historical Period',
            yaxis_title='MAPE (%)',
            plot_bgcolor='#1a1f26', 
            paper_bgcolor='#0f1419',
            font=dict(color='#ffffff', size=12),
            hovermode='x unified',
            height=400,
            showlegend=False
        )
        
        return fig_forecast, fig_trend, fig_error
    
    except Exception as e:
        print(f"❌ Error in timeseries: {e}")
        import traceback
        traceback.print_exc()
        error_fig = go.Figure().add_annotation(
            text=f"Error: {str(e)[:100]}",
            showarrow=False
        )
        error_fig.update_layout(plot_bgcolor='#1a1f26', paper_bgcolor='#0f1419', font=dict(color='#ff3333'))
        return error_fig, error_fig, error_fig

# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*80)
    print("🚀 Plotly Dash Dashboard with Prophet Integration")
    print("="*80)
    print("\n📊 Dashboard Features:")
    print("  📊 Overview - KPIs, trends, anomaly distribution")
    print("  📉 Model Drift - Detect distribution shifts in metrics")
    print("  🔴 Anomalies - Anomalous chunks with heatmap")
    print("  🔍 Features - Feature distributions and correlations")
    print("  📈 Time Series - Prophet forecasting with confidence intervals")
    print("\n🌐 Open browser and navigate to: http://localhost:8050")
    print("="*80 + "\n")
    
    app.run(debug=False, host='0.0.0.0', port=8050)
