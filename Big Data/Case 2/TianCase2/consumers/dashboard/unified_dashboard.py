#!/usr/bin/env python3
"""
Unified Traffic Dashboard - Combines Live and Analysis Dashboards
Provides sidebar navigation to toggle between Live View and Analysis View
Port: 8052
"""

import dash
from dash import dcc, html, Input, Output, State, no_update
import plotly.graph_objs as go
import pandas as pd
import psycopg2
from datetime import datetime, timedelta
import numpy as np
from collections import deque
from kafka import KafkaConsumer
import json
import threading
import time

# ========== CONFIGURATION ==========

DB_CONFIG = {
    'dbname': 'traffic_db',
    'user': 'tian'
}

KAFKA_CONFIG = {
    'bootstrap_servers': ['localhost:9092'],
    'auto_offset_reset': 'latest',
    'enable_auto_commit': True,
    'group_id': 'unified_dashboard_group',
    'value_deserializer': lambda x: json.loads(x.decode('utf-8'))
}

# Live data storage
MAX_POINTS = 60  # Keep last 60 data points
sensor_data = {
    'SOUND': {'timestamps': deque(maxlen=MAX_POINTS), 'values': deque(maxlen=MAX_POINTS)},
    'DISTANCE': {'timestamps': deque(maxlen=MAX_POINTS), 'values': deque(maxlen=MAX_POINTS)}
}
has_real_data = False
message_count = 0  # Track total messages received

# ========== DATABASE FUNCTIONS ==========

def get_db_connection():
    """Create a database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return None

def fetch_historical_data(hours_back=24):
    """Fetch sensor data from the database for analysis view"""
    conn = get_db_connection()
    if not conn:
        print("❌ No database connection available")
        return pd.DataFrame()
    
    try:
        query = f"""
            SELECT 
                event_ts as timestamp,
                sensor_type,
                value,
                device_id
            FROM readings
            WHERE event_ts >= NOW() - INTERVAL '{hours_back} hours'
            ORDER BY event_ts DESC
            LIMIT 50000
        """
        print(f"📊 Fetching data for last {hours_back} hours...")
        df = pd.read_sql_query(query, conn)
        conn.close()
        print(f"✅ Fetched {len(df)} records")
        return df
    except Exception as e:
        print(f"❌ Query error: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.close()
        return pd.DataFrame()

# ========== STATISTICS FUNCTIONS ==========

def calculate_statistics(df, sensor_type, noise_threshold=0):
    """Calculate statistics for a sensor type with noise filtering"""
    if df.empty:
        return {}
    
    sensor_df = df[df['sensor_type'] == sensor_type]
    
    if noise_threshold > 0:
        sensor_df = sensor_df[sensor_df['value'] >= noise_threshold]
    
    if sensor_df.empty:
        return {}
    
    return {
        'mean': sensor_df['value'].mean(),
        'median': sensor_df['value'].median(),
        'std': sensor_df['value'].std(),
        'min': sensor_df['value'].min(),
        'max': sensor_df['value'].max(),
        'count': len(sensor_df)
    }

def analyze_traffic_patterns(df, noise_threshold=50):
    """Analyze traffic patterns based on sensor data"""
    if df.empty:
        return {}
    
    sound_df = df[df['sensor_type'] == 'SOUND'].copy()
    distance_df = df[df['sensor_type'] == 'DISTANCE'].copy()
    
    sound_filtered = sound_df[sound_df['value'] >= noise_threshold]
    
    analysis = {}
    
    # Traffic intensity classification
    if not sound_filtered.empty:
        high_traffic = len(sound_filtered[sound_filtered['value'] >= 85])
        medium_traffic = len(sound_filtered[(sound_filtered['value'] >= 70) & 
                                            (sound_filtered['value'] < 85)])
        low_traffic = len(sound_filtered[sound_filtered['value'] < 70])
        total = len(sound_filtered)
        
        analysis['traffic_intensity'] = {
            'high': (high_traffic / total * 100) if total > 0 else 0,
            'medium': (medium_traffic / total * 100) if total > 0 else 0,
            'low': (low_traffic / total * 100) if total > 0 else 0
        }
        
        # Peak hours analysis
        sound_filtered['hour'] = pd.to_datetime(sound_filtered['timestamp']).dt.hour
        hourly_avg = sound_filtered.groupby('hour')['value'].mean()
        
        analysis['peak_hour'] = hourly_avg.idxmax() if not hourly_avg.empty else None
        analysis['quietest_hour'] = hourly_avg.idxmin() if not hourly_avg.empty else None
        analysis['hourly_data'] = hourly_avg.to_dict() if not hourly_avg.empty else {}
    
    # Proximity analysis
    if not distance_df.empty:
        very_close = len(distance_df[distance_df['value'] <= 10])
        close = len(distance_df[(distance_df['value'] > 10) & 
                                (distance_df['value'] <= 30)])
        far = len(distance_df[distance_df['value'] > 30])
        total_dist = len(distance_df)
        
        analysis['proximity'] = {
            'very_close': (very_close / total_dist * 100) if total_dist > 0 else 0,
            'close': (close / total_dist * 100) if total_dist > 0 else 0,
            'far': (far / total_dist * 100) if total_dist > 0 else 0
        }
    
    # Correlation analysis
    if not sound_df.empty and not distance_df.empty:
        sound_df['timestamp_rounded'] = pd.to_datetime(sound_df['timestamp']).dt.floor('1s')
        distance_df['timestamp_rounded'] = pd.to_datetime(distance_df['timestamp']).dt.floor('1s')
        
        merged = pd.merge(
            sound_df[['timestamp_rounded', 'value']].rename(columns={'value': 'sound'}),
            distance_df[['timestamp_rounded', 'value']].rename(columns={'value': 'distance'}),
            on='timestamp_rounded',
            how='inner'
        )
        
        if len(merged) > 10:
            correlation = merged['sound'].corr(merged['distance'])
            analysis['correlation'] = correlation if not pd.isna(correlation) else 0
    
    return analysis

# ========== KAFKA CONSUMER THREAD ==========

def kafka_consumer_thread():
    """Background thread to consume Kafka messages for live view"""
    global has_real_data, message_count
    
    print("🔌 Starting Kafka consumer thread...")
    
    try:
        consumer = KafkaConsumer('sensors', **KAFKA_CONFIG)
        print("✅ Connected to Kafka")
        
        for message in consumer:
            data = message.value
            # Support both 'type' (Arduino format) and 'sensor' formats
            sensor_type = data.get('type') or data.get('sensor')
            value = data.get('value')
            timestamp = data.get('ts', datetime.now().isoformat())
            
            print(f"🔍 DEBUG: sensor_type='{sensor_type}', value={value}, in sensor_data={sensor_type in sensor_data if sensor_type else False}")
            
            if sensor_type in sensor_data and value is not None:
                # Clear sample data on first real message
                if not has_real_data:
                    for sensor in sensor_data:
                        sensor_data[sensor]['timestamps'].clear()
                        sensor_data[sensor]['values'].clear()
                    has_real_data = True
                    print("✅ Receiving real data from Kafka")
                
                sensor_data[sensor_type]['timestamps'].append(timestamp)
                sensor_data[sensor_type]['values'].append(value)
                message_count += 1  # Increment total message counter
                print(f"📊 Received {sensor_type}: {value} (total messages: {message_count})")
    
    except Exception as e:
        print(f"❌ Kafka consumer error: {e}")
        import traceback
        traceback.print_exc()

# Start Kafka consumer in background thread
consumer_thread = threading.Thread(target=kafka_consumer_thread, daemon=True)
consumer_thread.start()

# ========== DASH APP ==========

app = dash.Dash(__name__, suppress_callback_exceptions=True)

# ========== LAYOUT ==========

app.layout = html.Div([
    # Sidebar
    html.Div([
        html.Div([
            html.H2("🚦 Traffic Dashboard", style={
                'color': 'white',
                'textAlign': 'center',
                'marginBottom': '30px',
                'fontSize': '24px'
            }),
            
            html.Hr(style={'borderColor': 'rgba(255,255,255,0.2)', 'margin': '20px 0'}),
            
            # Navigation buttons
            html.Div([
                html.Button([
                    html.Span('📡 ', style={'fontSize': '20px'}),
                    html.Span('Live View', style={'fontSize': '16px'})
                ], id='nav-live', n_clicks=0, style={
                    'width': '100%',
                    'padding': '15px',
                    'marginBottom': '10px',
                    'border': 'none',
                    'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    'color': 'white',
                    'borderRadius': '8px',
                    'cursor': 'pointer',
                    'fontSize': '16px',
                    'fontWeight': 'bold',
                    'transition': 'all 0.3s ease',
                    'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'
                }),
                
                html.Button([
                    html.Span('📊 ', style={'fontSize': '20px'}),
                    html.Span('Analysis View', style={'fontSize': '16px'})
                ], id='nav-analysis', n_clicks=0, style={
                    'width': '100%',
                    'padding': '15px',
                    'marginBottom': '10px',
                    'border': 'none',
                    'background': 'rgba(255,255,255,0.1)',
                    'color': 'white',
                    'borderRadius': '8px',
                    'cursor': 'pointer',
                    'fontSize': '16px',
                    'fontWeight': 'bold',
                    'transition': 'all 0.3s ease'
                })
            ]),
            
            html.Hr(style={'borderColor': 'rgba(255,255,255,0.2)', 'margin': '20px 0'}),
            
            html.Div([
                html.P('💡 Quick Info:', style={
                    'color': 'rgba(255,255,255,0.8)',
                    'fontSize': '14px',
                    'fontWeight': 'bold',
                    'marginBottom': '10px'
                }),
                html.P('📡 Live: Real-time Kafka stream', style={
                    'color': 'rgba(255,255,255,0.6)',
                    'fontSize': '12px',
                    'marginBottom': '5px'
                }),
                html.P('📊 Analysis: Historical database data', style={
                    'color': 'rgba(255,255,255,0.6)',
                    'fontSize': '12px',
                    'marginBottom': '5px'
                })
            ], style={'marginTop': '30px'})
            
        ], style={'padding': '20px'})
    ], style={
        'width': '250px',
        'height': '100vh',
        'position': 'fixed',
        'left': '0',
        'top': '0',
        'background': 'linear-gradient(180deg, #2c3e50 0%, #34495e 100%)',
        'boxShadow': '2px 0 10px rgba(0,0,0,0.1)',
        'zIndex': '1000',
        'overflowY': 'auto'
    }),
    
    # Main content area
    html.Div([
        html.Div(id='main-content')
    ], style={
        'marginLeft': '250px',
        'padding': '20px',
        'background': '#f5f7fa',
        'minHeight': '100vh'
    }),
    
    # Intervals for auto-refresh (will be disabled based on view)
    dcc.Interval(id='live-interval', interval=1*1000, n_intervals=0, disabled=False),  # 1 second for live
    dcc.Interval(id='analysis-interval', interval=10*1000, n_intervals=0, disabled=True),  # 10 seconds for analysis
    
    # Store for current view
    dcc.Store(id='current-view', data='live')
    
], style={'margin': '0', 'padding': '0', 'fontFamily': 'Arial, sans-serif'})

# ========== CALLBACKS ==========

# Callback to switch views and control intervals
@app.callback(
    [Output('current-view', 'data'),
     Output('nav-live', 'style'),
     Output('nav-analysis', 'style'),
     Output('live-interval', 'disabled'),
     Output('analysis-interval', 'disabled')],
    [Input('nav-live', 'n_clicks'),
     Input('nav-analysis', 'n_clicks')],
    [State('current-view', 'data')]
)
def switch_view(live_clicks, analysis_clicks, current_view):
    """Switch between live and analysis views"""
    ctx = dash.callback_context
    
    if not ctx.triggered:
        button_id = 'nav-live'
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    print(f"🔀 View switch: button={button_id}, live_clicks={live_clicks}, analysis_clicks={analysis_clicks}, current={current_view}")
    
    # Base styles for buttons
    base_style = {
        'width': '100%',
        'padding': '15px',
        'marginBottom': '10px',
        'border': 'none',
        'color': 'white',
        'borderRadius': '8px',
        'cursor': 'pointer',
        'fontSize': '16px',
        'fontWeight': 'bold',
        'transition': 'all 0.3s ease'
    }
    
    active_style = {
        **base_style,
        'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'
    }
    
    inactive_style = {
        **base_style,
        'background': 'rgba(255,255,255,0.1)',
        'boxShadow': 'none'
    }
    
    if button_id == 'nav-live':
        # Live view: enable live interval, disable analysis interval
        return 'live', active_style, inactive_style, False, True
    else:
        # Analysis view: disable live interval, enable analysis interval
        return 'analysis', inactive_style, active_style, True, False

# Callback to render content based on view - ONLY on view change, not on intervals
@app.callback(
    Output('main-content', 'children'),
    [Input('current-view', 'data')]
)
def render_content(view):
    """Render the appropriate view content based on current view - only triggered by view change"""
    if view == 'live':
        return render_live_view()
    else:
        return render_analysis_view()

# Separate callback for live view updates
@app.callback(
    [Output('live-sound-graph', 'figure'),
     Output('live-stats-sound-current', 'children'),
     Output('live-stats-distance-current', 'children'),
     Output('live-stats-points', 'children'),
     Output('live-update-time', 'children')],
    [Input('live-interval', 'n_intervals')],
    [State('current-view', 'data')],
    prevent_initial_call=True
)
def update_live_view(n_intervals, current_view):
    """Update live view data - only when on live view"""
    # Don't update if not on live view
    if current_view != 'live':
        raise dash.exceptions.PreventUpdate
    
    current_time = datetime.now().strftime('%H:%M:%S')
    
    # Debug: Check what's in sensor_data
    print(f"🔍 CALLBACK DEBUG: sensor_data keys: {list(sensor_data.keys())}")
    print(f"🔍 CALLBACK DEBUG: sensor_data['SOUND'] type: {type(sensor_data['SOUND'])}")
    print(f"🔍 CALLBACK DEBUG: sensor_data['SOUND'] keys: {list(sensor_data['SOUND'].keys()) if isinstance(sensor_data['SOUND'], dict) else 'NOT A DICT'}")
    
    # Read data from deques (deque operations are thread-safe)
    sound_timestamps = list(sensor_data['SOUND']['timestamps'])
    sound_values = list(sensor_data['SOUND']['values'])
    distance_timestamps = list(sensor_data['DISTANCE']['timestamps'])
    distance_values = list(sensor_data['DISTANCE']['values'])
    
    # Debug: Check data
    print(f"🔄 Updating live view - Sound points: {len(sound_values)}, Distance points: {len(distance_values)}")
    
    # Create live chart with waveform style - using dual Y-axes
    sound_trace = go.Scatter(
        x=sound_timestamps,
        y=sound_values,
        mode='lines',
        name='🔊 Sound Level (dB)',
        line=dict(color='#F18F01', width=3, shape='spline'),
        fill='tonexty',
        fillcolor='rgba(241, 143, 1, 0.1)',
        hovertemplate='<b>Sound Level</b><br>%{y:.1f} dB<br>%{x}<extra></extra>'
    )
    
    distance_trace = go.Scatter(
        x=distance_timestamps,
        y=distance_values,
        mode='lines',
        name='📏 Distance (cm)',
        line=dict(color='#2E86AB', width=3, shape='spline'),
        fill='tozeroy',
        fillcolor='rgba(46, 134, 171, 0.1)',
        hovertemplate='<b>Distance</b><br>%{y:.1f} cm<br>%{x}<extra></extra>'
    )
    
    live_fig = go.Figure(data=[sound_trace, distance_trace])
    
    live_fig.update_layout(
        title={
            'text': '🌊 Live Sensor Waveform (Last 60 Data Points)',
            'x': 0.5,
            'font': {'size': 18, 'color': '#2E86AB'}
        },
        xaxis=dict(
            title='Time',
            showgrid=True,
            gridwidth=1,
            gridcolor='#E0E0E0',
            tickformat='%H:%M:%S'
        ),
        yaxis=dict(
            title='Sensor Values',
            showgrid=True,
            gridwidth=1,
            gridcolor='#E0E0E0',
            range=[0, 250]
        ),
        hovermode='x unified',
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
        height=450
    )
    
    # Calculate current stats from thread-safe copies
    sound_current = sound_values[-1] if sound_values else 0
    distance_current = distance_values[-1] if distance_values else 0
    
    return [
        live_fig,
        f"{sound_current:.1f} dB",
        f"{distance_current:.1f} cm",
        f"{message_count}",  # Show total messages received
        current_time
    ]

# ========== LIVE VIEW RENDERER ==========

def render_live_view():
    """Render the live dashboard view"""
    
    # Initial values (will be updated by callback)
    sound_values = list(sensor_data['SOUND']['values'])
    distance_values = list(sensor_data['DISTANCE']['values'])
    
    sound_current = sound_values[-1] if sound_values else 0
    distance_current = distance_values[-1] if distance_values else 0
    sound_avg = np.mean(sound_values) if sound_values else 0
    distance_avg = np.mean(distance_values) if distance_values else 0
    
    # Create initial empty figure with waveform style - dual Y-axes
    sound_trace = go.Scatter(
        x=list(sensor_data['SOUND']['timestamps']),
        y=list(sensor_data['SOUND']['values']),
        mode='lines',
        name='🔊 Sound Level (dB)',
        line=dict(color='#F18F01', width=3, shape='spline'),
        fill='tonexty',
        fillcolor='rgba(241, 143, 1, 0.1)',
        hovertemplate='<b>Sound Level</b><br>%{y:.1f} dB<br>%{x}<extra></extra>'
    )
    
    distance_trace = go.Scatter(
        x=list(sensor_data['DISTANCE']['timestamps']),
        y=list(sensor_data['DISTANCE']['values']),
        mode='lines',
        name='📏 Distance (cm)',
        line=dict(color='#2E86AB', width=3, shape='spline'),
        fill='tozeroy',
        fillcolor='rgba(46, 134, 171, 0.1)',
        hovertemplate='<b>Distance</b><br>%{y:.1f} cm<br>%{x}<extra></extra>'
    )
    
    live_fig = go.Figure(data=[sound_trace, distance_trace])
    
    live_fig.update_layout(
        title={
            'text': '🌊 Live Sensor Waveform (Last 60 Data Points)',
            'x': 0.5,
            'font': {'size': 18, 'color': '#2E86AB'}
        },
        xaxis=dict(
            title='Time',
            showgrid=True,
            gridwidth=1,
            gridcolor='#E0E0E0',
            tickformat='%H:%M:%S'
        ),
        yaxis=dict(
            title='Sensor Values',
            showgrid=True,
            gridwidth=1,
            gridcolor='#E0E0E0',
            range=[0, 250]
        ),
        hovermode='x unified',
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
        height=450
    )
    
    return html.Div([
        # Header
        html.Div([
            html.H1("🌊 Live Traffic Sensor Dashboard", style={
                'textAlign': 'center',
                'color': '#2E86AB',
                'marginBottom': '10px',
                'fontFamily': 'Arial, sans-serif',
                'textShadow': '2px 2px 4px rgba(0,0,0,0.1)'
            }),
            html.P("Real-time monitoring with 60-second rolling window", style={
                'textAlign': 'center',
                'color': '#666',
                'fontSize': '16px',
                'marginBottom': '20px'
            })
        ], style={'padding': '20px'}),
        
        # Stats cards
        html.Div([
            # Sound card
            html.Div([
                html.H3(f"{sound_current:.1f} dB", id='live-stats-sound-current', style={
                    'margin': '0',
                    'color': '#F18F01'
                }),
                html.P("🔊 Sound Level", style={
                    'margin': '5px 0',
                    'color': '#666'
                })
            ], style={
                'textAlign': 'center',
                'background': 'linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%)',
                'padding': '20px',
                'borderRadius': '15px',
                'boxShadow': '0 4px 8px rgba(0,0,0,0.1)',
                'flex': '1',
                'margin': '0 10px'
            }),
            
            # Distance card
            html.Div([
                html.H3(f"{distance_current:.1f} cm", id='live-stats-distance-current', style={
                    'margin': '0',
                    'color': '#2E86AB'
                }),
                html.P("📏 Distance", style={
                    'margin': '5px 0',
                    'color': '#666'
                })
            ], style={
                'textAlign': 'center',
                'background': 'linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%)',
                'padding': '20px',
                'borderRadius': '15px',
                'boxShadow': '0 4px 8px rgba(0,0,0,0.1)',
                'flex': '1',
                'margin': '0 10px'
            }),
            
            # Live messages card
            html.Div([
                html.H3(f"{message_count}", id='live-stats-points', style={
                    'margin': '0',
                    'color': '#A23B72'
                }),
                html.P("📡 Live Messages", style={
                    'margin': '5px 0',
                    'color': '#666'
                })
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
        
        # Chart
        html.Div([
            dcc.Graph(id='live-sound-graph', figure=live_fig, style={'height': '500px'})
        ], style={
            'margin': '20px',
            'background': 'white',
            'borderRadius': '15px',
            'boxShadow': '0 4px 12px rgba(0,0,0,0.1)',
            'padding': '20px'
        }),
        
        # Footer
        html.Div([
            html.P([
                html.Span('🔄 Updates every second | ', style={'color': '#999'}),
                html.Span('📊 Chart shows last 60 data points', style={'color': '#999'}),
                html.Span(' | Last updated: ', style={'color': '#999'}),
                html.Span('--:--:--', id='live-update-time', style={'color': '#2E86AB', 'fontWeight': 'bold'})
            ], style={
                'textAlign': 'center',
                'fontSize': '12px',
                'margin': '10px'
            })
        ])
    ], style={
        'backgroundColor': '#f8f9fa',
        'minHeight': '100vh',
        'fontFamily': 'Arial, sans-serif'
    })

# ========== ANALYSIS VIEW RENDERER ==========

def render_analysis_view():
    """Render the analysis dashboard view with controls"""
    
    # Fetch initial data to display
    df = fetch_historical_data(hours_back=24)
    
    if df.empty:
        initial_content = html.Div([
            html.Div("📭", style={'fontSize': '60px', 'marginBottom': '20px'}),
            html.H3("No data available", style={'color': '#7f8c8d'}),
            html.P("Please check your database connection and ensure data is being collected.", 
                   style={'color': '#95a5a6'})
        ], style={'textAlign': 'center', 'padding': '60px', 'background': 'white', 'borderRadius': '10px'})
    else:
        initial_content = html.Div("Loading...", style={'textAlign': 'center', 'padding': '40px'})
    
    return html.Div([
        # Header
        html.Div([
            html.H1("📊 Traffic Data Analysis", style={
                'textAlign': 'center',
                'color': 'white',
                'marginBottom': '10px',
                'fontSize': '36px',
                'fontWeight': 'bold'
            }),
            html.P("Historical sensor data analysis with traffic pattern insights", style={
                'textAlign': 'center',
                'color': 'rgba(255,255,255,0.9)',
                'fontSize': '16px',
                'margin': '0'
            })
        ], style={
            'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            'padding': '30px',
            'marginBottom': '30px',
            'borderRadius': '10px',
            'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'
        }),
        
        # Control panel
        html.Div([
            html.Div([
                html.Label('📅 Time Range', style={'fontWeight': 'bold', 'marginBottom': '5px', 'display': 'block', 'color': '#2c3e50'}),
                dcc.Dropdown(
                    id='time-range-unified',
                    options=[
                        {'label': '⏱️ Last 1 Hour', 'value': 1},
                        {'label': '🕐 Last 6 Hours', 'value': 6},
                        {'label': '🕛 Last 12 Hours', 'value': 12},
                        {'label': '📆 Last 24 Hours', 'value': 24},
                        {'label': '📅 Last 48 Hours', 'value': 48}
                    ],
                    value=24,
                    style={'width': '100%'}
                )
            ], style={'flex': '1'}),
            
            html.Div([
                html.Label('🔊 Noise Threshold Filter', style={'fontWeight': 'bold', 'marginBottom': '5px', 'display': 'block', 'color': '#2c3e50'}),
                dcc.Slider(
                    id='noise-threshold-unified',
                    min=0,
                    max=100,
                    step=5,
                    value=50,
                    marks={0: '0dB', 25: '25', 50: '50', 75: '75', 100: '100dB'},
                    tooltip={"placement": "bottom", "always_visible": True}
                )
            ], style={'flex': '2'}),
            
            html.Div([
                html.Button('🔄 Refresh Data', id='refresh-button-unified', n_clicks=0, style={
                    'padding': '10px 20px',
                    'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    'color': 'white',
                    'border': 'none',
                    'borderRadius': '8px',
                    'cursor': 'pointer',
                    'fontWeight': 'bold',
                    'fontSize': '14px',
                    'marginTop': '20px'
                })
            ], style={'flex': '0'})
        ], style={
            'display': 'flex',
            'gap': '20px',
            'alignItems': 'flex-end',
            'background': 'white',
            'padding': '20px',
            'borderRadius': '10px',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
            'marginBottom': '20px'
        }),
        
        # Content placeholder
        html.Div(initial_content, id='analysis-content-unified')
    ])

# Callback to update analysis content
@app.callback(
    Output('analysis-content-unified', 'children'),
    [Input('refresh-button-unified', 'n_clicks'),
     Input('analysis-interval', 'n_intervals'),
     Input('time-range-unified', 'value'),
     Input('noise-threshold-unified', 'value')],
    [State('current-view', 'data')],
    prevent_initial_call=True
)
def update_analysis_content(n_clicks, n_intervals, time_range, noise_threshold, current_view):
    """Update analysis dashboard content"""
    
    # Only update if we're on analysis view
    if current_view != 'analysis':
        raise dash.exceptions.PreventUpdate
    
    current_time = datetime.now().strftime('%H:%M:%S')
    last_update_msg = f"Last updated: {current_time}"
    
    # Fetch data
    df = fetch_historical_data(hours_back=time_range)
    
    if df.empty:
        empty_msg = html.Div([
            html.Div("📭", style={'fontSize': '60px', 'marginBottom': '20px'}),
            html.H3("No data available", style={'color': '#7f8c8d'}),
            html.P("Please check your database connection and ensure data is being collected.", 
                   style={'color': '#95a5a6'})
        ], style={'textAlign': 'center', 'padding': '60px', 'background': 'white', 'borderRadius': '10px'})
        return empty_msg
    
    # Calculate statistics
    sound_stats = calculate_statistics(df, 'SOUND', noise_threshold)
    distance_stats = calculate_statistics(df, 'DISTANCE', 0)
    traffic_analysis = analyze_traffic_patterns(df, noise_threshold)
    
    # Create statistics HTML
    sound_stats_html = create_stats_card('🔊 Sound Statistics', sound_stats, 'dB', '#e74c3c') if sound_stats else html.Div("No data")
    distance_stats_html = create_stats_card('📏 Distance Statistics', distance_stats, 'cm', '#3498db') if distance_stats else html.Div("No data")
    traffic_analysis_html = create_traffic_card(traffic_analysis) if traffic_analysis else html.Div("No data")
    
    # Create charts
    sound_hist = create_histogram(df, 'SOUND', noise_threshold, '🔊 Sound Level Distribution', '#e74c3c')
    distance_hist = create_histogram(df, 'DISTANCE', 0, '📏 Distance Distribution', '#3498db')
    traffic_pie = create_traffic_pie(traffic_analysis)
    hourly_bar = create_hourly_bar(traffic_analysis)
    time_series = create_time_series(df, noise_threshold)
    
    return html.Div([
        # Stats cards
        html.Div([
            sound_stats_html,
            distance_stats_html,
            traffic_analysis_html
        ], style={'display': 'flex', 'gap': '20px', 'marginBottom': '20px'}),
        
        # Histograms
        html.Div([
            html.Div([dcc.Graph(figure=sound_hist, style={'height': '400px'})], 
                     style={'flex': '1', 'background': 'white', 'padding': '20px', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),
            html.Div([dcc.Graph(figure=distance_hist, style={'height': '400px'})], 
                     style={'flex': '1', 'background': 'white', 'padding': '20px', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'})
        ], style={'display': 'flex', 'gap': '20px', 'marginBottom': '20px'}),
        
        # Traffic analysis charts
        html.Div([
            html.Div([dcc.Graph(figure=traffic_pie, style={'height': '380px'})], 
                     style={'flex': '1', 'background': 'white', 'padding': '20px', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),
            html.Div([dcc.Graph(figure=hourly_bar, style={'height': '380px'})], 
                     style={'flex': '1', 'background': 'white', 'padding': '20px', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'})
        ], style={'display': 'flex', 'gap': '20px', 'marginBottom': '20px'}),
        
        # Time series
        html.Div([
            dcc.Graph(figure=time_series, style={'height': '500px'})
        ], style={'background': 'white', 'padding': '20px', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'marginBottom': '20px'}),
        
        # Footer
        html.Div([
            html.P([
                html.Span('🔄 Auto-refreshes every 10 seconds • ', style={'color': '#27ae60', 'fontWeight': 'bold'}),
                html.Span(last_update_msg, style={'color': '#7f8c8d'})
            ], style={'textAlign': 'center', 'margin': '0'})
        ], style={'padding': '15px'})
    ])

# ========== HELPER FUNCTIONS FOR CHARTS ==========

def create_stats_card(title, stats, unit, color):
    """Create a statistics card"""
    return html.Div([
        html.Div([
            html.Span(title.split()[0], style={'fontSize': '30px', 'marginRight': '10px'}),
            html.Span(' '.join(title.split()[1:]), style={'fontSize': '16px', 'fontWeight': 'bold', 'color': '#2c3e50'})
        ], style={'marginBottom': '15px'}),
        html.Div([
            html.Div([
                html.Div('Mean:', style={'fontSize': '12px', 'color': '#7f8c8d'}),
                html.Div(f"{stats.get('mean', 0):.2f} {unit}", style={'fontSize': '18px', 'fontWeight': 'bold', 'color': color})
            ], style={'marginBottom': '10px'}),
            html.Div([
                html.Div('Median:', style={'fontSize': '12px', 'color': '#7f8c8d'}),
                html.Div(f"{stats.get('median', 0):.2f} {unit}", style={'fontSize': '18px', 'fontWeight': 'bold', 'color': color})
            ], style={'marginBottom': '10px'}),
            html.Div([
                html.Div(f"Min: {stats.get('min', 0):.1f} | Max: {stats.get('max', 0):.1f}", 
                        style={'fontSize': '12px', 'color': '#7f8c8d'})
            ])
        ])
    ], style={
        'flex': '1',
        'background': 'white',
        'padding': '20px',
        'borderRadius': '10px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
        'border': f'2px solid {color}'
    })

def create_traffic_card(analysis):
    """Create traffic analysis card"""
    peak_hour = analysis.get('peak_hour', 'N/A')
    quietest_hour = analysis.get('quietest_hour', 'N/A')
    correlation = analysis.get('correlation', 0)
    
    return html.Div([
        html.Div([
            html.Span('🚦', style={'fontSize': '30px', 'marginRight': '10px'}),
            html.Span('Traffic Analysis', style={'fontSize': '16px', 'fontWeight': 'bold', 'color': '#2c3e50'})
        ], style={'marginBottom': '15px'}),
        html.Div([
            html.Div([
                html.Div('Peak Hour:', style={'fontSize': '12px', 'color': '#7f8c8d'}),
                html.Div(f"{peak_hour}:00" if peak_hour != 'N/A' else 'N/A', 
                        style={'fontSize': '18px', 'fontWeight': 'bold', 'color': '#e74c3c'})
            ], style={'marginBottom': '10px'}),
            html.Div([
                html.Div('Quietest Hour:', style={'fontSize': '12px', 'color': '#7f8c8d'}),
                html.Div(f"{quietest_hour}:00" if quietest_hour != 'N/A' else 'N/A', 
                        style={'fontSize': '18px', 'fontWeight': 'bold', 'color': '#27ae60'})
            ], style={'marginBottom': '10px'}),
            html.Div([
                html.Div(f"Correlation: {correlation:.3f}" if correlation else 'N/A', 
                        style={'fontSize': '12px', 'color': '#7f8c8d'})
            ])
        ])
    ], style={
        'flex': '1',
        'background': 'white',
        'padding': '20px',
        'borderRadius': '10px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
        'border': '2px solid #f39c12'
    })

def create_histogram(df, sensor_type, threshold, title, color):
    """Create histogram chart"""
    sensor_df = df[df['sensor_type'] == sensor_type]
    if threshold > 0 and sensor_type == 'SOUND':
        sensor_df = sensor_df[sensor_df['value'] >= threshold]
    
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=sensor_df['value'],
        nbinsx=30,
        marker=dict(color=color, line=dict(color='white', width=1)),
        opacity=0.8
    ))
    
    fig.update_layout(
        title={'text': title, 'font': {'size': 18, 'color': '#2c3e50'}},
        xaxis_title=f'{sensor_type.capitalize()} Value',
        yaxis_title='Frequency',
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=60, r=40, t=60, b=60)
    )
    
    return fig

def create_traffic_pie(analysis):
    """Create traffic intensity pie chart"""
    fig = go.Figure()
    
    if 'traffic_intensity' in analysis:
        intensity = analysis['traffic_intensity']
        fig.add_trace(go.Pie(
            labels=['🔴 High Traffic (≥85dB)', '🟡 Medium (70-85dB)', '🟢 Low (<70dB)'],
            values=[intensity['high'], intensity['medium'], intensity['low']],
            marker=dict(colors=['#e74c3c', '#f39c12', '#27ae60']),
            hole=0.4,
            textinfo='label+percent',
            textfont=dict(size=12)
        ))
    
    fig.update_layout(
        title={'text': '🚦 Traffic Intensity Distribution', 'font': {'size': 18, 'color': '#2c3e50'}},
        showlegend=True,
        legend=dict(orientation='v', yanchor='middle', y=0.5, xanchor='left', x=1.1),
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(t=80, b=40, l=40, r=180),
        height=380
    )
    
    return fig

def create_hourly_bar(analysis):
    """Create hourly pattern bar chart"""
    fig = go.Figure()
    
    if 'hourly_data' in analysis:
        hours = sorted(list(analysis['hourly_data'].keys()))
        values = [analysis['hourly_data'][h] for h in hours]
        
        fig.add_trace(go.Bar(
            x=hours,
            y=values,
            marker=dict(
                color=values,
                colorscale='RdYlGn_r',
                showscale=True,
                colorbar=dict(title='dB', x=1.05)
            ),
            text=[f'{v:.1f}dB' for v in values],
            textposition='outside'
        ))
    
    fig.update_layout(
        title={'text': '⏰ Hourly Traffic Pattern', 'font': {'size': 18, 'color': '#2c3e50'}},
        xaxis=dict(title='Hour of Day', tickmode='linear', tick0=0, dtick=1, range=[-0.5, 23.5]),
        yaxis=dict(title='Average Sound Level (dB)'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(t=80, b=60, l=60, r=100),
        height=380
    )
    
    return fig

def create_time_series(df, noise_threshold):
    """Create time series chart"""
    sound_df = df[df['sensor_type'] == 'SOUND']
    distance_df = df[df['sensor_type'] == 'DISTANCE']
    sound_filtered = sound_df[sound_df['value'] >= noise_threshold]
    
    fig = go.Figure()
    
    if not sound_filtered.empty:
        fig.add_trace(go.Scatter(
            x=sound_filtered['timestamp'],
            y=sound_filtered['value'],
            mode='lines',
            name='🔊 Sound Level',
            line=dict(color='#e74c3c', width=2.5),
            fill='tozeroy',
            fillcolor='rgba(231, 76, 60, 0.1)'
        ))
    
    if not distance_df.empty:
        fig.add_trace(go.Scatter(
            x=distance_df['timestamp'],
            y=distance_df['value'],
            mode='lines',
            name='📏 Distance',
            line=dict(color='#3498db', width=2.5),
            fill='tozeroy',
            fillcolor='rgba(52, 152, 219, 0.1)',
            yaxis='y2'
        ))
    
    fig.update_layout(
        title={'text': '📈 Time Series Analysis', 'font': {'size': 20, 'color': '#2c3e50'}},
        xaxis=dict(title='Time', gridcolor='rgba(0,0,0,0.1)'),
        yaxis=dict(
            title='Sound Level (dB)',
            title_font=dict(color='#e74c3c'),
            tickfont=dict(color='#e74c3c'),
            gridcolor='rgba(0,0,0,0.1)'
        ),
        yaxis2=dict(
            title='Distance (cm)',
            title_font=dict(color='#3498db'),
            tickfont=dict(color='#3498db'),
            overlaying='y',
            side='right'
        ),
        hovermode='x unified',
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=80, r=80, t=80, b=80)
    )
    
    return fig

# ========== RUN APP ==========

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Starting Unified Traffic Dashboard...")
    print("=" * 60)
    print("📡 Live View: Real-time Kafka stream (1-second refresh)")
    print("📊 Analysis View: Historical database analysis (10-second refresh)")
    print("-" * 60)
    print("🌐 Dashboard URL: http://127.0.0.1:8052")
    print("🌐 Or access via: http://0.0.0.0:8052")
    print("-" * 60)
    print("💡 Use the sidebar to toggle between Live and Analysis views")
    print("=" * 60)
    
    app.run(debug=False, port=8052, host='0.0.0.0')
