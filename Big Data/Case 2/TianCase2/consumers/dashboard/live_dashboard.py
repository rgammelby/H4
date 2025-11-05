#!/usr/bin/env python3
"""
🚀 LIVE TRAFFIC MONITORING DASHBOARD 🚀
Real-time sensor data visualization with 60-second rolling window
"""

import dash
from dash import dcc, html, Input, Output
import plotly.graph_objs as go
import pandas as pd
import json
import threading
import time
from collections import deque
from datetime import datetime, timezone
from kafka import KafkaConsumer
import numpy as np

# Global data storage for live streaming
MAX_POINTS = 60  # Show last 60 data points
sensor_data = deque(maxlen=MAX_POINTS)
data_lock = threading.Lock()
message_count = 0
latest_sound = 0
latest_distance = 0
has_real_data = False  # Track if we have real data

def kafka_consumer_thread():
    """Background thread to consume Kafka messages"""
    global sensor_data, message_count, latest_sound, latest_distance
    
    try:
        consumer = KafkaConsumer(
            'sensors',
            bootstrap_servers=['localhost:9092'],
            auto_offset_reset='latest',  # Start from latest messages
            enable_auto_commit=True,
            group_id='live_dashboard_group',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            consumer_timeout_ms=100,  # Non-blocking timeout
            fetch_min_bytes=1,
            fetch_max_wait_ms=100
        )
        
        print("🔗 Connected to Kafka topic 'sensors'")
        
        while True:
            try:
                # Poll for messages with timeout to prevent blocking
                message_batch = consumer.poll(timeout_ms=100)
                
                if message_batch:
                    for topic_partition, messages in message_batch.items():
                        for message in messages:
                            try:
                                data = message.value
                                
                                # Parse timestamp from 'ts' field
                                if 'ts' in data:
                                    # Fix double timezone issue in timestamp
                                    ts_str = data['ts'].replace('Z', '').replace('+00:00+00:00', '+00:00')
                                    timestamp = datetime.fromisoformat(ts_str)
                                    # Convert to local timezone for display
                                    if timestamp.tzinfo is not None:
                                        timestamp = timestamp.astimezone()
                                else:
                                    timestamp = datetime.now()
                                
                                # Handle Arduino format: {"type": "SOUND", "value": 68, "ts": "..."}
                                sensor_type = data.get('type', '').upper()
                                value = float(data.get('value', 0))
                                
                                if sensor_type == 'SOUND':
                                    latest_sound = value
                                elif sensor_type == 'DISTANCE':
                                    latest_distance = value
                                else:
                                    # Try alternative format
                                    latest_sound = float(data.get('sound_level', data.get('SOUND', latest_sound)))
                                    latest_distance = float(data.get('distance', data.get('DISTANCE', latest_distance)))
                                
                                # Create combined data point with both values
                                new_data = {
                                    'timestamp': timestamp,
                                    'sound_level': latest_sound,
                                    'distance': latest_distance
                                }
                                
                                with data_lock:
                                    # Clear sample data on first real message
                                    global has_real_data
                                    if not has_real_data:
                                        sensor_data.clear()
                                        has_real_data = True
                                    
                                    sensor_data.append(new_data)
                                    message_count += 1
                                
                            except Exception as e:
                                print(f"⚠️ Error processing message: {e}")
                                continue
                
                # Small delay to prevent CPU overuse
                time.sleep(0.05)
                
            except Exception as e:
                print(f"⚠️ Consumer poll error: {e}")
                time.sleep(0.5)
                continue
                
    except Exception as e:
        print(f"❌ Kafka connection error: {e}")
        print("📊 Running with sample data only")

# Start Kafka consumer in background
kafka_thread = threading.Thread(target=kafka_consumer_thread, daemon=True)
kafka_thread.start()

# Initialize Dash app
app = dash.Dash(__name__)
app.title = "🌊 Live Traffic Sensors"

# Enhanced CSS styling
app.layout = html.Div([
    html.Div([
        html.H1("🌊 Live Traffic Sensor Dashboard", 
                style={
                    'textAlign': 'center',
                    'color': '#2E86AB',
                    'marginBottom': '10px',
                    'fontFamily': 'Arial, sans-serif',
                    'textShadow': '2px 2px 4px rgba(0,0,0,0.1)'
                }),
        
        html.P("Real-time monitoring with 60-second rolling window",
               style={
                   'textAlign': 'center',
                   'color': '#666',
                   'fontSize': '16px',
                   'marginBottom': '20px'
               })
    ], style={'padding': '20px'}),
    
    # Status Cards
    html.Div([
        html.Div([
            html.H3(id="sound-value", style={'margin': '0', 'color': '#F18F01'}),
            html.P("🔊 Sound Level", style={'margin': '5px 0', 'color': '#666'})
        ], style={
            'textAlign': 'center',
            'background': 'linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%)',
            'padding': '20px',
            'borderRadius': '15px',
            'boxShadow': '0 4px 8px rgba(0,0,0,0.1)',
            'flex': '1',
            'margin': '0 10px'
        }),
        
        html.Div([
            html.H3(id="distance-value", style={'margin': '0', 'color': '#2E86AB'}),
            html.P("📏 Distance", style={'margin': '5px 0', 'color': '#666'})
        ], style={
            'textAlign': 'center',
            'background': 'linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%)',
            'padding': '20px',
            'borderRadius': '15px',
            'boxShadow': '0 4px 8px rgba(0,0,0,0.1)',
            'flex': '1',
            'margin': '0 10px'
        }),
        
        html.Div([
            html.H3(id="message-count", style={'margin': '0', 'color': '#A23B72'}),
            html.P("📡 Live Messages", style={'margin': '5px 0', 'color': '#666'})
        ], style={
            'textAlign': 'center',
            'background': 'linear-gradient(135deg, #F3E5F5 0%, #E1BEE7 100%)',
            'padding': '20px',
            'borderRadius': '15px',
            'boxShadow': '0 4px 8px rgba(0,0,0,0.1)',
            'flex': '1',
            'margin': '0 10px'
        })
    ], style={
        'display': 'flex',
        'justifyContent': 'center',
        'margin': '20px',
        'gap': '20px'
    }),
    
    # Main Chart
    html.Div([
        dcc.Graph(
            id='live-sensor-chart',
            style={'height': '500px'}
        )
    ], style={
        'margin': '20px',
        'background': 'white',
        'borderRadius': '15px',
        'boxShadow': '0 4px 12px rgba(0,0,0,0.1)',
        'padding': '20px'
    }),
    
    # Auto-refresh interval
    dcc.Interval(
        id='interval-component',
        interval=1000,  # Update every 1 second
        n_intervals=0
    ),
    
    # Footer
    html.Div([
        html.P("🔄 Updates every second | 📊 Shows last 60 data points",
               style={
                   'textAlign': 'center',
                   'color': '#999',
                   'fontSize': '12px',
                   'margin': '10px'
               })
    ])
], style={
    'backgroundColor': '#f8f9fa',
    'minHeight': '100vh',
    'fontFamily': 'Arial, sans-serif'
})

@app.callback(
    [Output('live-sensor-chart', 'figure'),
     Output('sound-value', 'children'),
     Output('distance-value', 'children'),
     Output('message-count', 'children')],
    [Input('interval-component', 'n_intervals')]
)
def update_dashboard(n):
    """Update all dashboard components"""
    global sensor_data, message_count
    
    with data_lock:
        if not sensor_data:
            # If no data, return empty chart
            fig = go.Figure()
            fig.add_annotation(
                text="Waiting for sensor data...",
                x=0.5, y=0.5,
                xref="paper", yref="paper",
                showarrow=False,
                font=dict(size=16, color="#666")
            )
            fig.update_layout(
                plot_bgcolor='white',
                paper_bgcolor='white',
                title="Live Sensor Data",
                height=450
            )
            return fig, "-- dB", "-- cm", str(message_count)
        
        # Convert to DataFrame for easier handling
        df = pd.DataFrame(list(sensor_data))
        
        # Get latest values
        latest_sound = df['sound_level'].iloc[-1] if not df.empty else 0
        latest_distance = df['distance'].iloc[-1] if not df.empty else 0
        
        # Create time series chart
        fig = go.Figure()
        
        # Sound level trace with area fill
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['sound_level'],
            mode='lines',
            name='🔊 Sound Level (dB)',
            line=dict(color='#F18F01', width=3, shape='spline'),
            fill='tonexty',
            fillcolor='rgba(241, 143, 1, 0.1)',
            hovertemplate='<b>Sound Level</b><br>%{y:.1f} dB<br>%{x}<extra></extra>'
        ))
        
        # Distance trace with area fill
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['distance'],
            mode='lines',
            name='📏 Distance (cm)',
            line=dict(color='#2E86AB', width=3, shape='spline'),
            fill='tozeroy',
            fillcolor='rgba(46, 134, 171, 0.1)',
            hovertemplate='<b>Distance</b><br>%{y:.1f} cm<br>%{x}<extra></extra>'
        ))
        
        # Enhanced layout
        fig.update_layout(
            title={
                'text': '🌊 Live Sensor Waveform (Last 60 Data Points)',
                'x': 0.5,
                'font': {'size': 18, 'color': '#2E86AB'}
            },
            xaxis_title='Time',
            yaxis_title='Sensor Values',
            height=450,
            plot_bgcolor='white',
            paper_bgcolor='white',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            hovermode='x unified',
            xaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='#E0E0E0',
                tickformat='%H:%M:%S'
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='#E0E0E0',
                range=[0, 250]  # Increased range to show up to 2.5 meters
            )
        )
        
    return (
        fig,
        f"{latest_sound:.1f} dB",
        f"{latest_distance:.1f} cm", 
        str(message_count)
    )

if __name__ == '__main__':
    print("🚀 Starting Live Traffic Dashboard...")
    print("📊 Dashboard: http://localhost:8050")
    print("🔄 Auto-refresh: Every 1 second")
    print("📈 Window: Last 60 data points")
    print("💡 Press Ctrl+C to stop")
    
    app.run(
        host='0.0.0.0',
        port=8050,
        debug=False
    )