#!/usr/bin/env python3
"""
📊 TRAFFIC DATA ANALYSIS DASHBOARD 📊
Historical sensor data analysis with noise threshold filtering
"""

import dash
from dash import dcc, html, Input, Output
import plotly.graph_objs as go
import pandas as pd
import psycopg2
from datetime import datetime, timedelta
import numpy as np

# Database connection parameters
# Using Unix socket (no host/port) for peer authentication
DB_CONFIG = {
    'dbname': 'traffic_db',
    'user': 'tian'
}

def get_db_connection():
    """Create a database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return None

def fetch_historical_data(hours_back=24):
    """Fetch sensor data from the database"""
    conn = get_db_connection()
    if not conn:
        print("❌ No database connection available")
        return pd.DataFrame()
    
    try:
        # Use proper SQL parameter substitution
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

def calculate_statistics(df, sensor_type, noise_threshold=0):
    """Calculate statistics for a sensor type with noise filtering"""
    if df.empty:
        return {}
    
    sensor_df = df[df['sensor_type'] == sensor_type]
    
    # Apply noise threshold filter
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
    
    # Separate sensor types
    sound_df = df[df['sensor_type'] == 'SOUND'].copy()
    distance_df = df[df['sensor_type'] == 'DISTANCE'].copy()
    
    # Filter sound by threshold
    sound_filtered = sound_df[sound_df['value'] >= noise_threshold]
    
    analysis = {}
    
    # Traffic intensity classification based on sound levels
    if not sound_filtered.empty:
        high_traffic = len(sound_filtered[sound_filtered['value'] >= 85])
        medium_traffic = len(sound_filtered[(sound_filtered['value'] >= 70) & (sound_filtered['value'] < 85)])
        low_traffic = len(sound_filtered[sound_filtered['value'] < 70])
        total = len(sound_filtered)
        
        analysis['traffic_intensity'] = {
            'high': (high_traffic / total * 100) if total > 0 else 0,
            'medium': (medium_traffic / total * 100) if total > 0 else 0,
            'low': (low_traffic / total * 100) if total > 0 else 0
        }
        
        # Peak hours analysis (by hour)
        sound_filtered['hour'] = pd.to_datetime(sound_filtered['timestamp']).dt.hour
        hourly_avg = sound_filtered.groupby('hour')['value'].mean()
        analysis['peak_hour'] = hourly_avg.idxmax() if not hourly_avg.empty else None
        analysis['quietest_hour'] = hourly_avg.idxmin() if not hourly_avg.empty else None
        analysis['hourly_data'] = hourly_avg.to_dict() if not hourly_avg.empty else {}
    
    # Proximity analysis based on distance
    if not distance_df.empty:
        very_close = len(distance_df[distance_df['value'] <= 10])  # < 10cm
        close = len(distance_df[(distance_df['value'] > 10) & (distance_df['value'] <= 30)])
        far = len(distance_df[distance_df['value'] > 30])
        total_dist = len(distance_df)
        
        analysis['proximity'] = {
            'very_close': (very_close / total_dist * 100) if total_dist > 0 else 0,
            'close': (close / total_dist * 100) if total_dist > 0 else 0,
            'far': (far / total_dist * 100) if total_dist > 0 else 0
        }
    
    # Correlation between sound and distance (if we can align them by time)
    if not sound_df.empty and not distance_df.empty:
        # Merge by timestamp (within 1 second tolerance)
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

# Initialize Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)

app.layout = html.Div([
    # Header with gradient
    html.Div([
        html.H1("📊 Traffic Data Analysis Dashboard", 
                style={
                    'textAlign': 'center', 
                    'color': 'white', 
                    'marginBottom': '5px',
                    'fontSize': '42px',
                    'fontWeight': '700',
                    'letterSpacing': '1px'
                }),
        html.P("Historical sensor data analysis with intelligent noise filtering",
               style={
                   'textAlign': 'center', 
                   'color': 'rgba(255,255,255,0.9)', 
                   'fontSize': '18px',
                   'fontWeight': '300'
               })
    ], style={
        'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'padding': '40px 20px',
        'borderRadius': '15px',
        'marginBottom': '30px',
        'boxShadow': '0 10px 40px rgba(0,0,0,0.1)'
    }),
    
    # Control Panel - Modern Card Design
    html.Div([
        html.Div([
            html.Div([
                html.Label('📅 Time Range', 
                          style={
                              'fontWeight': '600', 
                              'marginBottom': '8px',
                              'display': 'block',
                              'color': '#2c3e50',
                              'fontSize': '14px'
                          }),
                dcc.Dropdown(
                    id='time-range',
                    options=[
                        {'label': '🕐 Last 1 Hour', 'value': 1},
                        {'label': '🕕 Last 6 Hours', 'value': 6},
                        {'label': '🕐 Last 12 Hours', 'value': 12},
                        {'label': '📅 Last 24 Hours', 'value': 24},
                        {'label': '📆 Last 48 Hours', 'value': 48},
                    ],
                    value=24,
                    style={'width': '100%'}
                )
            ], style={
                'flex': '1',
                'marginRight': '20px',
                'minWidth': '200px'
            }),
            
            html.Div([
                html.Label('🔊 Noise Threshold Filter', 
                          style={
                              'fontWeight': '600',
                              'marginBottom': '15px',
                              'display': 'block',
                              'color': '#2c3e50',
                              'fontSize': '14px'
                          }),
                dcc.Slider(
                    id='noise-threshold',
                    min=0,
                    max=100,
                    step=5,
                    value=50,
                    marks={i: {'label': f'{i}dB', 'style': {'fontSize': '11px'}} for i in range(0, 101, 20)},
                    tooltip={"placement": "bottom", "always_visible": True}
                )
            ], style={
                'flex': '2',
                'marginRight': '20px',
                'minWidth': '300px'
            }),
            
            html.Div([
                html.Button('🔄 Refresh Data', 
                           id='refresh-button', 
                           n_clicks=0,
                           style={
                               'padding': '12px 30px',
                               'fontSize': '16px',
                               'backgroundColor': '#667eea',
                               'color': 'white',
                               'border': 'none',
                               'borderRadius': '8px',
                               'cursor': 'pointer',
                               'fontWeight': '600',
                               'transition': 'all 0.3s',
                               'boxShadow': '0 4px 15px rgba(102, 126, 234, 0.4)',
                               'width': '100%'
                           })
            ], style={
                'display': 'flex',
                'alignItems': 'flex-end',
                'minWidth': '150px'
            })
        ], style={
            'display': 'flex',
            'alignItems': 'flex-end',
            'flexWrap': 'wrap',
            'gap': '15px'
        })
    ], style={
        'padding': '30px',
        'backgroundColor': 'white',
        'borderRadius': '15px',
        'marginBottom': '30px',
        'boxShadow': '0 5px 25px rgba(0,0,0,0.08)'
    }),
    
    # Statistics Cards - Enhanced Design with Better Alignment
    html.Div([
        # Sound Statistics Card
        html.Div([
            html.Div([
                html.Div('🔊', style={'fontSize': '48px', 'marginBottom': '10px'}),
                html.H3('Sound Statistics', 
                       style={
                           'color': '#e74c3c',
                           'fontSize': '20px',
                           'fontWeight': '600',
                           'marginBottom': '0',
                           'marginTop': '5px'
                       })
            ], style={'textAlign': 'center', 'marginBottom': '20px'}),
            html.Div(id='sound-stats')
        ], style={
            'flex': '1',
            'backgroundColor': 'white',
            'padding': '25px',
            'borderRadius': '15px',
            'boxShadow': '0 5px 25px rgba(231, 76, 60, 0.15)',
            'border': '2px solid rgba(231, 76, 60, 0.1)',
            'minHeight': '280px',
            'display': 'flex',
            'flexDirection': 'column'
        }),
        
        # Distance Statistics Card
        html.Div([
            html.Div([
                html.Div('📏', style={'fontSize': '48px', 'marginBottom': '10px'}),
                html.H3('Distance Statistics',
                       style={
                           'color': '#3498db',
                           'fontSize': '20px',
                           'fontWeight': '600',
                           'marginBottom': '0',
                           'marginTop': '5px'
                       })
            ], style={'textAlign': 'center', 'marginBottom': '20px'}),
            html.Div(id='distance-stats')
        ], style={
            'flex': '1',
            'backgroundColor': 'white',
            'padding': '25px',
            'borderRadius': '15px',
            'boxShadow': '0 5px 25px rgba(52, 152, 219, 0.15)',
            'border': '2px solid rgba(52, 152, 219, 0.1)',
            'minHeight': '280px',
            'display': 'flex',
            'flexDirection': 'column'
        }),
        
        # Traffic Analysis Card
        html.Div([
            html.Div([
                html.Div('🚦', style={'fontSize': '48px', 'marginBottom': '10px'}),
                html.H3('Traffic Analysis',
                       style={
                           'color': '#9b59b6',
                           'fontSize': '20px',
                           'fontWeight': '600',
                           'marginBottom': '0',
                           'marginTop': '5px'
                       })
            ], style={'textAlign': 'center', 'marginBottom': '20px'}),
            html.Div(id='traffic-analysis')
        ], style={
            'flex': '1',
            'backgroundColor': 'white',
            'padding': '25px',
            'borderRadius': '15px',
            'boxShadow': '0 5px 25px rgba(155, 89, 182, 0.15)',
            'border': '2px solid rgba(155, 89, 182, 0.1)',
            'minHeight': '280px',
            'display': 'flex',
            'flexDirection': 'column'
        })
    ], style={
        'display': 'flex',
        'gap': '20px',
        'marginBottom': '30px',
        'flexWrap': 'wrap'
    }),
    
    # Charts Row 1 - Histograms Side by Side
    html.Div([
        html.Div([
            dcc.Graph(id='sound-histogram', style={'height': '400px'})
        ], style={
            'flex': '1',
            'backgroundColor': 'white',
            'padding': '20px',
            'borderRadius': '15px',
            'boxShadow': '0 5px 25px rgba(0,0,0,0.08)'
        }),
        
        html.Div([
            dcc.Graph(id='distance-histogram', style={'height': '400px'})
        ], style={
            'flex': '1',
            'backgroundColor': 'white',
            'padding': '20px',
            'borderRadius': '15px',
            'boxShadow': '0 5px 25px rgba(0,0,0,0.08)'
        })
    ], style={
        'display': 'flex',
        'gap': '20px',
        'marginBottom': '30px',
        'flexWrap': 'wrap'
    }),
    
    # Charts Row 2 - Traffic Analysis
    html.Div([
        html.Div([
            dcc.Graph(id='traffic-intensity-chart', style={'height': '380px'})
        ], style={
            'flex': '1',
            'backgroundColor': 'white',
            'padding': '20px',
            'borderRadius': '15px',
            'boxShadow': '0 5px 25px rgba(0,0,0,0.08)'
        }),
        
        html.Div([
            dcc.Graph(id='hourly-pattern-chart', style={'height': '380px'})
        ], style={
            'flex': '1',
            'backgroundColor': 'white',
            'padding': '20px',
            'borderRadius': '15px',
            'boxShadow': '0 5px 25px rgba(0,0,0,0.08)'
        })
    ], style={
        'display': 'flex',
        'gap': '20px',
        'marginBottom': '30px',
        'flexWrap': 'wrap'
    }),
    
    # Time Series Chart - Full Width
    html.Div([
        dcc.Graph(id='time-series-chart', style={'height': '500px'})
    ], style={
        'marginBottom': '30px',
        'backgroundColor': 'white',
        'padding': '20px',
        'borderRadius': '15px',
        'boxShadow': '0 5px 25px rgba(0,0,0,0.08)'
    }),
    
    # Footer
    html.Div([
        html.P([
            html.Span('🔄 Auto-refreshes every 10 seconds | Data from PostgreSQL Database | ', 
                     style={'color': '#95a5a6'}),
            html.Span(id='last-update-time', style={'color': '#667eea', 'fontWeight': '600'})
        ], style={
            'textAlign': 'center',
            'fontSize': '14px',
            'margin': '0'
        })
    ], style={
        'padding': '20px',
        'backgroundColor': 'white',
        'borderRadius': '15px',
        'boxShadow': '0 5px 25px rgba(0,0,0,0.08)'
    }),
    
    # Auto-refresh interval
    dcc.Interval(
        id='interval-component',
        interval=10*1000,  # Update every 10 seconds (was 30)
        n_intervals=0
    )
], style={
    'padding': '30px',
    'backgroundColor': '#f8f9fc',
    'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    'minHeight': '100vh'
})

@app.callback(
    [Output('sound-stats', 'children'),
     Output('distance-stats', 'children'),
     Output('traffic-analysis', 'children'),
     Output('sound-histogram', 'figure'),
     Output('distance-histogram', 'figure'),
     Output('traffic-intensity-chart', 'figure'),
     Output('hourly-pattern-chart', 'figure'),
     Output('time-series-chart', 'figure'),
     Output('last-update-time', 'children')],
    [Input('refresh-button', 'n_clicks'),
     Input('interval-component', 'n_intervals'),
     Input('time-range', 'value'),
     Input('noise-threshold', 'value')]
)
def update_dashboard(n_clicks, n_intervals, time_range, noise_threshold):
    """Update all dashboard components"""
    
    # Get current time for last update display
    from datetime import datetime
    current_time = datetime.now().strftime('%H:%M:%S')
    last_update_msg = f"Last updated: {current_time}"
    
    # Fetch data
    df = fetch_historical_data(hours_back=time_range)
    
    if df.empty:
        empty_msg = html.Div("No data available. Start the producer to collect data!", 
                            style={'textAlign': 'center', 'color': '#e74c3c', 'fontSize': '16px'})
        empty_fig = go.Figure()
        empty_fig.update_layout(
            xaxis={'visible': False},
            yaxis={'visible': False},
            annotations=[{
                'text': 'No data available',
                'xref': 'paper',
                'yref': 'paper',
                'showarrow': False,
                'font': {'size': 20, 'color': '#95a5a6'}
            }],
            paper_bgcolor='white'
        )
        return empty_msg, empty_msg, empty_msg, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, last_update_msg
    
    # Calculate statistics
    sound_stats = calculate_statistics(df, 'SOUND', noise_threshold)
    distance_stats = calculate_statistics(df, 'DISTANCE', 0)
    
    # Analyze traffic patterns
    traffic_analysis = analyze_traffic_patterns(df, noise_threshold)
    
    # Create statistics cards
    sound_stats_html = html.Div([
        html.Div([
            html.Div([
                html.Span('📊', style={'fontSize': '24px', 'marginRight': '10px'}),
                html.Span('Mean:', style={'color': '#7f8c8d', 'fontSize': '14px', 'fontWeight': '500'})
            ]),
            html.Div(f"{sound_stats.get('mean', 0):.2f} dB", 
                    style={'fontSize': '28px', 'fontWeight': '700', 'color': '#2c3e50', 'marginTop': '5px'})
        ], style={'marginBottom': '20px', 'paddingBottom': '15px', 'borderBottom': '2px solid #f8f9fa'}),
        
        html.Div([
            html.Div([
                html.Div([
                    html.Span('Median: ', style={'color': '#7f8c8d', 'fontSize': '13px'}),
                    html.Span(f"{sound_stats.get('median', 0):.2f} dB", style={'fontWeight': '600', 'fontSize': '15px', 'color': '#2c3e50'})
                ], style={'marginBottom': '10px'}),
                html.Div([
                    html.Span('Std Dev: ', style={'color': '#7f8c8d', 'fontSize': '13px'}),
                    html.Span(f"{sound_stats.get('std', 0):.2f} dB", style={'fontWeight': '600', 'fontSize': '15px', 'color': '#2c3e50'})
                ], style={'marginBottom': '10px'})
            ], style={'width': '50%', 'display': 'inline-block', 'verticalAlign': 'top'}),
            
            html.Div([
                html.Div([
                    html.Span('Min: ', style={'color': '#7f8c8d', 'fontSize': '13px'}),
                    html.Span(f"{sound_stats.get('min', 0):.2f} dB", style={'fontWeight': '600', 'fontSize': '15px', 'color': '#27ae60'})
                ], style={'marginBottom': '10px'}),
                html.Div([
                    html.Span('Max: ', style={'color': '#7f8c8d', 'fontSize': '13px'}),
                    html.Span(f"{sound_stats.get('max', 0):.2f} dB", style={'fontWeight': '600', 'fontSize': '15px', 'color': '#e74c3c'})
                ], style={'marginBottom': '10px'})
            ], style={'width': '50%', 'display': 'inline-block', 'verticalAlign': 'top'})
        ]),
        
        html.Div([
            html.Span('🔢 Total Samples: ', style={'color': '#7f8c8d', 'fontSize': '13px'}),
            html.Span(f"{sound_stats.get('count', 0):,}", 
                     style={'fontWeight': '700', 'fontSize': '18px', 'color': '#667eea'})
        ], style={'marginTop': '20px', 'paddingTop': '15px', 'borderTop': '2px solid #f8f9fa', 'textAlign': 'center'})
    ]) if sound_stats else html.Div([
        html.P("🚫 No data after filtering", 
              style={'color': '#e74c3c', 'textAlign': 'center', 'fontSize': '16px', 'padding': '20px'})
    ])
    
    distance_stats_html = html.Div([
        html.Div([
            html.Div([
                html.Span('📊', style={'fontSize': '24px', 'marginRight': '10px'}),
                html.Span('Mean:', style={'color': '#7f8c8d', 'fontSize': '14px', 'fontWeight': '500'})
            ]),
            html.Div(f"{distance_stats.get('mean', 0):.2f} cm", 
                    style={'fontSize': '28px', 'fontWeight': '700', 'color': '#2c3e50', 'marginTop': '5px'})
        ], style={'marginBottom': '20px', 'paddingBottom': '15px', 'borderBottom': '2px solid #f8f9fa'}),
        
        html.Div([
            html.Div([
                html.Div([
                    html.Span('Median: ', style={'color': '#7f8c8d', 'fontSize': '13px'}),
                    html.Span(f"{distance_stats.get('median', 0):.2f} cm", style={'fontWeight': '600', 'fontSize': '15px', 'color': '#2c3e50'})
                ], style={'marginBottom': '10px'}),
                html.Div([
                    html.Span('Std Dev: ', style={'color': '#7f8c8d', 'fontSize': '13px'}),
                    html.Span(f"{distance_stats.get('std', 0):.2f} cm", style={'fontWeight': '600', 'fontSize': '15px', 'color': '#2c3e50'})
                ], style={'marginBottom': '10px'})
            ], style={'width': '50%', 'display': 'inline-block', 'verticalAlign': 'top'}),
            
            html.Div([
                html.Div([
                    html.Span('Min: ', style={'color': '#7f8c8d', 'fontSize': '13px'}),
                    html.Span(f"{distance_stats.get('min', 0):.2f} cm", style={'fontWeight': '600', 'fontSize': '15px', 'color': '#27ae60'})
                ], style={'marginBottom': '10px'}),
                html.Div([
                    html.Span('Max: ', style={'color': '#7f8c8d', 'fontSize': '13px'}),
                    html.Span(f"{distance_stats.get('max', 0):.2f} cm", style={'fontWeight': '600', 'fontSize': '15px', 'color': '#e74c3c'})
                ], style={'marginBottom': '10px'})
            ], style={'width': '50%', 'display': 'inline-block', 'verticalAlign': 'top'})
        ]),
        
        html.Div([
            html.Span('🔢 Total Samples: ', style={'color': '#7f8c8d', 'fontSize': '13px'}),
            html.Span(f"{distance_stats.get('count', 0):,}", 
                     style={'fontWeight': '700', 'fontSize': '18px', 'color': '#3498db'})
        ], style={'marginTop': '20px', 'paddingTop': '15px', 'borderTop': '2px solid #f8f9fa', 'textAlign': 'center'})
    ]) if distance_stats else html.Div([
        html.P("🚫 No data available", 
              style={'color': '#e74c3c', 'textAlign': 'center', 'fontSize': '16px', 'padding': '20px'})
    ])
    
    # Traffic Analysis Card 
    traffic_analysis_html = html.Div([
        # Traffic Intensity
        html.Div([
            html.Div('🚦 Traffic Intensity', 
                    style={'color': '#7f8c8d', 'fontSize': '14px', 'fontWeight': '600', 'marginBottom': '10px'}),
            html.Div([
                html.Div([
                    html.Span(f"{traffic_analysis.get('traffic_intensity', {}).get('high', 0):.1f}%", 
                             style={'fontSize': '20px', 'fontWeight': '700', 'color': '#e74c3c'}),
                    html.Br(),
                    html.Span('High', style={'fontSize': '11px', 'color': '#7f8c8d'})
                ], style={'flex': '1', 'textAlign': 'center', 'padding': '5px'}),
                html.Div([
                    html.Span(f"{traffic_analysis.get('traffic_intensity', {}).get('medium', 0):.1f}%", 
                             style={'fontSize': '20px', 'fontWeight': '700', 'color': '#f39c12'}),
                    html.Br(),
                    html.Span('Medium', style={'fontSize': '11px', 'color': '#7f8c8d'})
                ], style={'flex': '1', 'textAlign': 'center', 'padding': '5px'}),
                html.Div([
                    html.Span(f"{traffic_analysis.get('traffic_intensity', {}).get('low', 0):.1f}%", 
                             style={'fontSize': '20px', 'fontWeight': '700', 'color': '#27ae60'}),
                    html.Br(),
                    html.Span('Low', style={'fontSize': '11px', 'color': '#7f8c8d'})
                ], style={'flex': '1', 'textAlign': 'center', 'padding': '5px'})
            ], style={'display': 'flex', 'marginBottom': '15px'})
        ], style={'marginBottom': '15px', 'paddingBottom': '15px', 'borderBottom': '2px solid #f8f9fa'}),
        
        # Peak/Quiet Hours
        html.Div([
            html.Div([
                html.Span('⏰ Peak Hour: ', style={'color': '#7f8c8d', 'fontSize': '12px'}),
                html.Span(f"{traffic_analysis.get('peak_hour', '--')}:00" if traffic_analysis.get('peak_hour') is not None else '--', 
                         style={'fontWeight': '600', 'fontSize': '14px', 'color': '#e74c3c'})
            ], style={'marginBottom': '10px'}),
            html.Div([
                html.Span('🌙 Quietest Hour: ', style={'color': '#7f8c8d', 'fontSize': '12px'}),
                html.Span(f"{traffic_analysis.get('quietest_hour', '--')}:00" if traffic_analysis.get('quietest_hour') is not None else '--', 
                         style={'fontWeight': '600', 'fontSize': '14px', 'color': '#27ae60'})
            ], style={'marginBottom': '10px'}),
            html.Div([
                html.Span('📊 Correlation: ', style={'color': '#7f8c8d', 'fontSize': '12px'}),
                html.Span(f"{traffic_analysis.get('correlation', 0):.3f}" if 'correlation' in traffic_analysis else 'N/A', 
                         style={'fontWeight': '600', 'fontSize': '14px', 'color': '#9b59b6'})
            ])
        ])
    ]) if traffic_analysis else html.Div([
        html.P("🚫 No analysis available", 
              style={'color': '#e74c3c', 'textAlign': 'center', 'fontSize': '16px', 'padding': '20px'})
    ])
    
    # Sound histogram
    sound_df = df[df['sensor_type'] == 'SOUND']
    sound_filtered = sound_df[sound_df['value'] >= noise_threshold] if noise_threshold > 0 else sound_df
    
    sound_hist = go.Figure()
    sound_hist.add_trace(go.Histogram(
        x=sound_filtered['value'],
        nbinsx=30,
        name='Sound Level',
        marker=dict(
            color='#e74c3c',
            line=dict(color='#c0392b', width=1)
        ),
        opacity=0.8
    ))
    sound_hist.update_layout(
        title={
            'text': f'🔊 Sound Level Distribution<br><sub>Threshold: {noise_threshold} dB | Samples: {len(sound_filtered):,}</sub>',
            'font': {'size': 20, 'color': '#2c3e50', 'family': 'Arial'}
        },
        xaxis_title='Sound Level (dB)',
        yaxis_title='Frequency',
        showlegend=False,
        hovermode='x',
        plot_bgcolor='rgba(248, 249, 252, 0.5)',
        paper_bgcolor='white',
        font=dict(family='Arial', size=12, color='#2c3e50'),
        margin=dict(t=80, b=60, l=60, r=40)
    )
    
    # Distance histogram
    distance_df = df[df['sensor_type'] == 'DISTANCE']
    
    distance_hist = go.Figure()
    distance_hist.add_trace(go.Histogram(
        x=distance_df['value'],
        nbinsx=30,
        name='Distance',
        marker=dict(
            color='#3498db',
            line=dict(color='#2980b9', width=1)
        ),
        opacity=0.8
    ))
    distance_hist.update_layout(
        title={
            'text': f'📏 Distance Distribution<br><sub>Samples: {len(distance_df):,}</sub>',
            'font': {'size': 20, 'color': '#2c3e50', 'family': 'Arial'}
        },
        xaxis_title='Distance (cm)',
        yaxis_title='Frequency',
        showlegend=False,
        hovermode='x',
        plot_bgcolor='rgba(248, 249, 252, 0.5)',
        paper_bgcolor='white',
        font=dict(family='Arial', size=12, color='#2c3e50'),
        margin=dict(t=80, b=60, l=60, r=40)
    )
    
    # Time series chart
    time_series = go.Figure()
    
    if not sound_filtered.empty:
        time_series.add_trace(go.Scatter(
            x=sound_filtered['timestamp'],
            y=sound_filtered['value'],
            mode='lines',
            name='🔊 Sound Level',
            line=dict(color='#e74c3c', width=2.5),
            fill='tozeroy',
            fillcolor='rgba(231, 76, 60, 0.1)',
            hovertemplate='<b>Sound</b><br>Time: %{x}<br>Level: %{y:.2f} dB<extra></extra>'
        ))
    
    if not distance_df.empty:
        time_series.add_trace(go.Scatter(
            x=distance_df['timestamp'],
            y=distance_df['value'],
            mode='lines',
            name='📏 Distance',
            line=dict(color='#3498db', width=2.5),
            fill='tozeroy',
            fillcolor='rgba(52, 152, 219, 0.1)',
            yaxis='y2',
            hovertemplate='<b>Distance</b><br>Time: %{x}<br>Distance: %{y:.2f} cm<extra></extra>'
        ))
    
    time_series.update_layout(
        title={
            'text': '📈 Sensor Data Over Time<br><sub>Real-time trend analysis with dual-axis comparison</sub>',
            'font': {'size': 24, 'color': '#2c3e50', 'family': 'Arial'}
        },
        xaxis=dict(
            title='Time',
            showgrid=True,
            gridcolor='rgba(200, 200, 200, 0.2)',
            zeroline=False
        ),
        yaxis=dict(
            title='Sound Level (dB)',
            title_font=dict(color='#e74c3c', size=14),
            tickfont=dict(color='#e74c3c'),
            showgrid=True,
            gridcolor='rgba(231, 76, 60, 0.1)',
            zeroline=False
        ),
        yaxis2=dict(
            title='Distance (cm)',
            title_font=dict(color='#3498db', size=14),
            tickfont=dict(color='#3498db'),
            overlaying='y',
            side='right',
            showgrid=False,
            zeroline=False
        ),
        hovermode='x unified',
        legend=dict(
            x=0.01,
            y=0.99,
            bgcolor='rgba(255, 255, 255, 0.9)',
            bordercolor='rgba(0, 0, 0, 0.1)',
            borderwidth=1,
            font=dict(size=12)
        ),
        plot_bgcolor='rgba(248, 249, 252, 0.5)',
        paper_bgcolor='white',
        font=dict(family='Arial', size=12, color='#2c3e50'),
        margin=dict(t=100, b=60, l=70, r=70)
    )
    
    # Traffic Intensity Pie Chart
    traffic_intensity_fig = go.Figure()
    if 'traffic_intensity' in traffic_analysis:
        intensity = traffic_analysis['traffic_intensity']
        traffic_intensity_fig.add_trace(go.Pie(
            labels=['🔴 High Traffic (≥85dB)', '🟡 Medium Traffic (70-85dB)', '🟢 Low Traffic (<70dB)'],
            values=[intensity['high'], intensity['medium'], intensity['low']],
            marker=dict(colors=['#e74c3c', '#f39c12', '#27ae60']),
            hole=0.4,
            textinfo='label+percent',
            textfont=dict(size=11),
            textposition='outside'
        ))
        traffic_intensity_fig.update_layout(
            title={
                'text': '🚦 Traffic Intensity Classification<br><sub>Based on sound level thresholds</sub>',
                'font': {'size': 18, 'color': '#2c3e50', 'family': 'Arial'},
                'x': 0.5,
                'xanchor': 'center'
            },
            showlegend=True,
            legend=dict(
                orientation='v',
                yanchor='middle',
                y=0.5,
                xanchor='left',
                x=1.1,
                font=dict(size=11)
            ),
            paper_bgcolor='white',
            font=dict(family='Arial', size=11, color='#2c3e50'),
            margin=dict(t=80, b=40, l=40, r=180),
            height=380
        )
    else:
        traffic_intensity_fig.update_layout(
            annotations=[{'text': 'No traffic data', 'xref': 'paper', 'yref': 'paper',
                         'showarrow': False, 'font': {'size': 16, 'color': '#95a5a6'}}],
            paper_bgcolor='white',
            height=380
        )
    
    # Hourly Pattern Chart
    hourly_pattern_fig = go.Figure()
    if 'hourly_data' in traffic_analysis and traffic_analysis['hourly_data']:
        hours = sorted(list(traffic_analysis['hourly_data'].keys()))
        values = [traffic_analysis['hourly_data'][h] for h in hours]
        
        hourly_pattern_fig.add_trace(go.Bar(
            x=hours,
            y=values,
            marker=dict(
                color=values,
                colorscale='RdYlGn_r',
                showscale=True,
                colorbar=dict(title='dB', len=0.7, y=0.5)
            ),
            text=[f'{v:.1f}dB' for v in values],
            textposition='outside',
            textfont=dict(size=10),
            hovertemplate='<b>Hour %{x}:00</b><br>Avg Sound: %{y:.2f} dB<extra></extra>'
        ))
        
        hourly_pattern_fig.update_layout(
            title={
                'text': '⏰ Hourly Traffic Pattern<br><sub>Average sound level by hour of day</sub>',
                'font': {'size': 18, 'color': '#2c3e50', 'family': 'Arial'},
                'x': 0.5,
                'xanchor': 'center'
            },
            xaxis=dict(
                title='Hour of Day',
                dtick=1,
                showgrid=True,
                gridcolor='rgba(200, 200, 200, 0.2)',
                range=[-0.5, 23.5]
            ),
            yaxis=dict(
                title='Average Sound Level (dB)',
                showgrid=True,
                gridcolor='rgba(200, 200, 200, 0.2)'
            ),
            plot_bgcolor='rgba(248, 249, 252, 0.5)',
            paper_bgcolor='white',
            font=dict(family='Arial', size=12, color='#2c3e50'),
            margin=dict(t=80, b=60, l=60, r=100),
            showlegend=False,
            height=380
        )
    else:
        hourly_pattern_fig.update_layout(
            annotations=[{'text': 'No hourly data', 'xref': 'paper', 'yref': 'paper',
                         'showarrow': False, 'font': {'size': 16, 'color': '#95a5a6'}}],
            paper_bgcolor='white',
            height=380
        )
    
    return sound_stats_html, distance_stats_html, traffic_analysis_html, sound_hist, distance_hist, traffic_intensity_fig, hourly_pattern_fig, time_series, last_update_msg

if __name__ == '__main__':
    print("🚀 Starting Analysis Dashboard...")
    print("📊 Dashboard will be available at: http://127.0.0.1:8051")
    print("🔄 Auto-refreshes every 10 seconds (faster updates!)")
    print("🎯 Features: Noise threshold filtering, historical data analysis, traffic patterns")
    app.run(debug=True, port=8051, host='0.0.0.0')
