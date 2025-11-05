import threading
import pandas as pd
from datetime import datetime, timedelta
import psycopg2
from confluent_kafka import Consumer
from dash import Dash, dcc, html, Input, Output
import plotly.express as px

# Database configuration
DB_CONFIG = {
    'dbname': 'arduino_data',
    'user': 'sascha',
    'password': 'Kode1234!',
    'host': 'localhost',
    'port': 5432
}

# Kafka configuration
KAFKA_CONF = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'arduino-dashboard',
    'auto.offset.reset': 'latest'  # Prioritise new incoming data; no queue
}

# Volume data is sent as a numerical number between ~24 and 1023. 
# The upper threshold (arbritrary definition of 'too loud') has been set at the numerical value of 1000.
THRESHOLD = 1000

# DataFrame for live-data capture
if 'live_df' not in globals():
    live_df = pd.DataFrame(columns=['timestamp', 'volume'])


# Starts a thread for a Kafka consumer to receive arduino data for visualisation
def kafka_consumer_thread():
    global live_df
    consumer = Consumer(KAFKA_CONF)  # Initialise consumer
    consumer.subscribe(['arduino-data'])  # Subscribe to the 'arduino-data' topic
    print("Kafka consumer thread started")
    while True:
        msg = consumer.poll(timeout=1.0)
        if msg is None or msg.error():
            continue
        try:
            volume = int(msg.value().decode('utf-8'))  # Numerical value as observed by the Arduino
            timestamp = datetime.now()  # Current timestamp
            new_row = pd.DataFrame({'timestamp':[timestamp],'volume':[volume]})  # Construct new row with data for insertion into DataFrame
            live_df = pd.concat([live_df, new_row], ignore_index=True).tail(500)  # Concatenate new data onto DataFrame
        except Exception as e:
            print("Kafka decoding error:", e)

# If the consumer thread can't be found, start a new one
if 'consumer_thread' not in globals():
    consumer_thread = threading.Thread(target=kafka_consumer_thread, daemon=True)
    consumer_thread.start()


# Queries the PostgreSQL database for historical data within a user-specified timespan
def load_historical_data(start_time: datetime, end_time: datetime):
    conn = psycopg2.connect(**DB_CONFIG)
    query = f"""
        SELECT timestamp, volume
        FROM arduino_readings
        WHERE timestamp BETWEEN '{start_time}' AND '{end_time}'
        ORDER BY timestamp ASC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

'''
This function performs a data analysis. 
It determines:
    * the amount of threshold breaches; incoming numerical value reports exceeding the chosen threshold of 1000;
    * the duration of time spent above the the threshold;
    * and the percentage of total measured time spent above the threshold.
'''
def analyse_threshold(df, threshold=THRESHOLD):
    if df.empty:
        return 0, timedelta(0), 0.0
    df = df.sort_values('timestamp')
    df['above'] = df['volume'] > threshold
    df['change'] = df['above'].ne(df['above'].shift())
    df['group'] = df['change'].cumsum()
    groups = df[df['above']].groupby('group')
    
    count = len(groups)
    duration = timedelta(0)
    
    for _, g in groups:
        if len(g) > 1:
            duration += g['timestamp'].iloc[-1] - g['timestamp'].iloc[0]
    
    total_time = df['timestamp'].iloc[-1] - df['timestamp'].iloc[0]
    percentage = (duration / total_time * 100) if total_time.total_seconds() > 0 else 0.0
    
    return count, duration, percentage

# Dash app for data visualisation
app = Dash(__name__)
app.config.suppress_callback_exceptions = True

# HTML-like dashboard design
app.layout = html.Div([
    html.H1("Arduino Dashboard"),

    # Live data display
    html.H2("Live Data"),
    dcc.Graph(id='live-graph'),
    html.Div(id='live-stats', style={'fontSize': '18px', 'marginBottom': '30px'}),

    # Historical controls (date fields with time inputs)
    html.Div([
        html.Label("Start Date & Time:"),
        dcc.DatePickerSingle(id='start-date', date=(datetime.now() - timedelta(days=1)).date()),
        dcc.Input(id='start-time', type='text', value='00:00:00', placeholder='HH:MM:SS'),
        html.Label("End Date & Time:"),
        dcc.DatePickerSingle(id='end-date', date=datetime.now().date()),
        dcc.Input(id='end-time', type='text', value=datetime.now().strftime("%H:%M:%S"), placeholder='HH:MM:SS')
    ], style={'display':'flex', 'gap':'10px', 'align-items':'center'}),

    # Historical data display
    html.H2("Historical Data"),
    dcc.Graph(id='historical-graph'),
    html.Div(id='historical-stats', style={'fontSize': '18px'}),

    dcc.Interval(id='interval', interval=1000, n_intervals=0)
])


# For updating historical data display 
@app.callback(
    [Output('historical-graph', 'figure'),
     Output('historical-stats', 'children')],
    [Input('start-date', 'date'),
     Input('start-time', 'value'),
     Input('end-date', 'date'),
     Input('end-time', 'value')]
)
# -//- 
def update_historical(start_date, start_time, end_date, end_time):
    try:
        start_dt = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M:%S")
        end_dt = datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M:%S")
    except Exception:
        start_dt = datetime.now() - timedelta(days=1)
        end_dt = datetime.now()

    df = load_historical_data(start_dt, end_dt)
    if df.empty:
        return px.line(title="No historical data in this range"), "No data available."

    count, duration, percentage = analyse_threshold(df)
    fig = px.line(df, x='timestamp', y='volume', title="Historical Data")
    fig.add_hline(y=THRESHOLD, line_dash="dot", line_color="red")

    stats_text = f"Threshold breaches: {count} | Total time above {THRESHOLD}: {duration} | {percentage:.1f}% of time above threshold"
    return fig, stats_text


# For updating live data display
@app.callback(
    [Output('live-graph', 'figure'),
     Output('live-stats', 'children')],
    Input('interval', 'n_intervals')
)
# -//-
def update_live(n):
    global live_df
    if live_df.empty:
        return px.line(title="Waiting for live data..."), "Awaiting readings..."

    count, duration, percentage = analyse_threshold(live_df)
    fig = px.line(live_df, x='timestamp', y='volume', title="Live Data (last 500 readings)")
    fig.add_hline(y=THRESHOLD, line_dash="dot", line_color="red")

    stats_text = f"Threshold breaches: {count} | Total time above {THRESHOLD}: {duration} | {percentage:.1f}% of time above threshold"
    return fig, stats_text


# Run the app
if __name__ == '__main__':
    print("Registered callbacks:", app.callback_map.keys())
    app.run(debug=False, use_reloader=False)
