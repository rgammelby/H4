#!/usr/bin/env python3
import json, sys
from datetime import datetime, timezone
from kafka import KafkaProducer
import serial

# ---- Settings ----
SERIAL_PORT = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyACM0"  # change if needed
BAUD = 9600
BOOTSTRAP = "localhost:9092"
TOPIC = "sensors"

def parse_line(line):
    # Expect "DISTANCE,7" or "SOUND,67"
    try:
        k, v = line.strip().split(",", 1)
        return {"type": k, "value": int(v)}
    except:
        return None  # ignore malformed lines

def main():
    # Kafka producer: send JSON
    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP,
        value_serializer=lambda d: json.dumps(d).encode("utf-8"),
        linger_ms=5,
        retries=3,
    )

    # Open serial
    ser = serial.Serial(SERIAL_PORT, BAUD, timeout=2)
    print(f"Reading {SERIAL_PORT} @ {BAUD} → Kafka topic '{TOPIC}'")
    try:
        while True:
            raw = ser.readline().decode(errors="ignore") # Read "DISTANCE,7"
            if not raw:
                continue
            msg = parse_line(raw) # Convert to {"type": "DISTANCE", "value": 7}
            if not msg:
                continue
            msg["ts"] = datetime.now().isoformat()  # Use local timezone
            producer.send(TOPIC, msg) # Send to Kafka topic
            print("Produced:", msg)
    except KeyboardInterrupt:
        pass
    finally:
        ser.close()
        producer.flush()
        producer.close()

if __name__ == "__main__":
    main()
