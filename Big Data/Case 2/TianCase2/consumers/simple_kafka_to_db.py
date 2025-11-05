#!/usr/bin/env python3
"""
Simple Kafka Consumer: Reads sensor data and saves to PostgreSQL
This version uses system commands to insert data, which is easier for beginners
"""
import json
import sys
import subprocess
from datetime import datetime, timezone
from kafka import KafkaConsumer

# ---- Settings ----
BOOTSTRAP = "localhost:9092"  # Where Kafka is running
TOPIC = "sensors"             # Which topic to read from
GROUP_ID = "db_writer"        # Consumer group name

def save_to_database(message, kafka_info):
    """
    Save sensor reading to database using psql command
    This is simpler than using Python database drivers
    """
    try:
        # Parse timestamp with proper PostgreSQL format
        try:
            if 'ts' in message and message['ts']:
                # Convert timestamp to PostgreSQL format (remove timezone suffix)
                ts_str = message['ts'].replace('Z', '').replace('+00:00', '')
                # Parse and reformat to simple timestamp
                parsed_ts = datetime.fromisoformat(ts_str.split('+')[0])
                event_time = parsed_ts.strftime('%Y-%m-%d %H:%M:%S')
            else:
                event_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        except:
            # Fallback to current time if parsing fails
            event_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Current timestamp for received_at
        received_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        sql = f"""
            INSERT INTO readings 
            (sensor_type, value, event_ts, device_id, topic, partition, kafka_offset, received_at)
            VALUES 
            ('{message['type']}', {message['value']}, '{event_time}', 'arduino_001', 
             '{kafka_info['topic']}', {kafka_info['partition']}, {kafka_info['offset']}, 
             '{received_time}');
        """

        # Run the SQL command using the current user (no sudo) — we created
        # a Postgres role matching the Linux user 'tian', so psql will use peer auth.
        cmd = ['psql', '-d', 'traffic_db', '-c', sql]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"💾 Saved: {message['type']}={message['value']} at {event_time}")
        else:
            print(f"❌ Database error: {result.stderr}")

    except Exception as e:
        print(f"❌ Error saving data: {e}")

def main():
    print("🚀 Starting Simple Kafka Consumer...")
    print(f"📖 Reading from topic '{TOPIC}' and saving to database")
    print("💡 This version uses simple database commands")

    # Create Kafka consumer
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP,
        group_id=GROUP_ID,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='latest',  # Start from newest messages
        enable_auto_commit=True
    )

    print("✅ Consumer ready! Waiting for messages...")
    print("💡 Tip: Press Ctrl+C to stop")

    try:
        for message in consumer:
            # Get the sensor data
            sensor_data = message.value

            # Get Kafka information
            kafka_info = {
                'topic': message.topic,
                'partition': message.partition,
                'offset': message.offset
            }

            print(f"📨 Received: {sensor_data}")

            # Save to database
            save_to_database(sensor_data, kafka_info)

    except KeyboardInterrupt:
        print("\n🛑 Stopping consumer...")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        consumer.close()
        print("👋 Consumer stopped")

if __name__ == "__main__":
    main()
