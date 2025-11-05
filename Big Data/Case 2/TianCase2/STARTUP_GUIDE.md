# 🚀 Startup Guide - Unified Traffic Dashboard

## 📁 Project Structure
```
TrafficManagement/
├── producers/
│   └── arduino_to_kafka.py          # Arduino → Kafka producer
├── consumers/
│   ├── simple_kafka_to_db.py        # Kafka → PostgreSQL consumer  
│   └── dashboard/                   # Web Dashboard Folder
│       ├── unified_dashboard.py     # ⭐ Main: Live + Analysis (Port 8052)
│       ├── live_dashboard.py        # Standalone: Live only (Port 8050)
│       └── analysis_dashboard.py    # Standalone: Analysis only (Port 8051)
├── db/                              # Database scripts
└── *.md                            # Documentation files
```

##  Dashboard Options

### **Option 1: Unified Dashboard **
**Single dashboard with sidebar navigation**
- Port: **8052**
- Features: Live View + Analysis View with toggle
- Updates: Live (1s) / Analysis (10s)

### **Option 2: Standalone Dashboards (My old version)**
**Separate dashboards for specific use**
- `live_dashboard.py`: Port **8050** - Real-time Kafka only
- `analysis_dashboard.py`: Port **8051** - Historical DB analysis only


## ⚡ Quick Start

### 0. Prerequisites
**Ensure these are running:**
```bash
# PostgreSQL database
sudo systemctl status postgresql
# Should show "active (running)"

# Kafka broker
cd ~/Downloads/kafka_2.13-4.1.0
bin/kafka-server-start.sh config/server.properties
# Should show "started (kafka.server.KafkaServer)"
```

### 1️⃣ Start Data Pipeline
Open **3 terminal windows**:

```bash
# Terminal 1: Arduino → Kafka Producer
cd /home/tian/H4/TrafficManagement/producers
python arduino_to_kafka.py
#  Should show: "Sent: SOUND -> 68, DISTANCE -> 11"

# Terminal 2: Kafka → Database Consumer
cd /home/tian/H4/TrafficManagement/consumers
python simple_kafka_to_db.py
#  Should show: "Saved to database: SOUND=68, DISTANCE=11"

# Terminal 3: Unified Dashboard (RECOMMENDED)
cd /home/tian/H4/TrafficManagement/consumers/dashboard
python unified_dashboard.py
#  Should show: "Dash is running on http://0.0.0.0:8052"
```

### 2️⃣ Open Unified Dashboard
```bash
# In browser, navigate to:
http://localhost:8052

# Showing:
# - Left sidebar with "📡 Live View" and "📊 Analysis View" buttons
# - Main content area showing selected view
# - Auto-refreshing data
```

### 3️⃣ Toggle Between Views
- **Live View**: Click "📡 Live View" - Real-time sensor waveform (updates every 1 second)
- **Analysis View**: Click "📊 Analysis View" - Historical statistics and charts (updates every 10 seconds)

## 🌊 Unified Dashboard Features

### **📡 Live View**
- **Real-time sensor waveform** (last 60 data points)
- **1-second refresh rate** from Kafka stream
- **Live message counter** showing total messages received
- **Current sensor values** in gradient cards
- **Color-coded traces**: 🔊 Sound (orange), 📏 Distance (blue)
- **Single Y-axis** display (0-250 range for both sensors)

### **📊 Analysis View**
- **Historical database analysis** (1-48 hours of data)
- **10-second auto-refresh**
- **Noise filtering** with adjustable threshold (0-100 dB)
- **Statistical cards**: Mean, median, std dev, min, max
- **Traffic pattern analysis**: Low/Medium/High intensity classification
- **Multiple visualizations**:
  - Distribution histograms
  - Time series charts
  - Traffic intensity pie charts
  - Hourly activity bar charts

### **🎨 User Interface**
- **Sidebar navigation** for easy view switching
- **Responsive design** with modern gradient styling
- **Smooth transitions** between views
- **Professional card layouts** with shadows and animations
- **Color-coded sensors** throughout the interface

## 🔧 Troubleshooting

### **Problem: "Connection refused" on port 8052**
```bash
# Check if dashboard is running
ps aux | grep unified_dashboard

# Start the unified dashboard
cd /home/tian/H4/TrafficManagement/consumers/dashboard
python unified_dashboard.py
```

### **Problem: Live View shows no data**
```bash
# 1. Check if Kafka is running
ps aux | grep kafka
# Should show kafka process

# 2. Check if producer is sending data
cd /home/tian/H4/TrafficManagement/producers
python arduino_to_kafka.py
# Should show: ✅ Sent: SOUND -> 68, DISTANCE -> 11

# 3. Check Arduino connection
ls /dev/ttyUSB* /dev/ttyACM*
# Should list Arduino device (e.g., /dev/ttyUSB0)
```

### **Problem: Analysis View shows no data**
```bash
# Check if database consumer is running
ps aux | grep simple_kafka_to_db

# Verify database has data
psql -U tian -d traffic_db -c "SELECT COUNT(*) FROM readings;"
# Should return a number > 0

# Restart database consumer if needed
cd /home/tian/H4/TrafficManagement/consumers
python simple_kafka_to_db.py
```

## 📊 Alternative: Running Standalone Dashboards

### **Live Dashboard Only** (Port 8050)
```bash
cd /home/tian/H4/TrafficManagement/consumers/dashboard
python live_dashboard.py
# Access at: http://localhost:8050
```

### **Analysis Dashboard Only** (Port 8051)
```bash
cd /home/tian/H4/TrafficManagement/consumers/dashboard
python analysis_dashboard.py
# Access at: http://localhost:8051
```

### **For Debugging**
1. Check Terminal 1 (Producer): Is Arduino sending data?
2. Check Terminal 2 (Consumer): Is data being saved to DB?
3. Check Terminal 3 (Dashboard): Are there any error messages?
4. Check browser console (F12): Any JavaScript errors?

# Check data flow
tail -f /var/log/kafka/server.log  # Kafka logs
psql -d traffic_db -c "SELECT COUNT(*) FROM readings;"  # Database count
```


## 📊 System Architecture

```
Arduino → Serial → Kafka → Database (PostgreSQL)
   ↓                 
   📱                    → Dashboard.html
Producer                      (Browser)
(Python)                     
                          
```
