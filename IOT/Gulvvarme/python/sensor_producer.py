import serial
from kafka import KafkaProducer
import time
import json

# --- Configuration ---
ARDUINO_PORT = "COM5"
ARDUINO_BAUD = 9600

KAFKA_BROKER = "10.0.0.200:9092"
KAFKA_TOPIC = "sensor-data"

# --- Location tag ---
LOCATION = "Bedroom"

# Kafka Producer Setup
producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Serial initialisation
arduino = serial.Serial(ARDUINO_PORT, ARDUINO_BAUD, timeout=1)
time.sleep(2)

print(f"Streaming data from Arduino on {ARDUINO_PORT} to Kafka topic '{KAFKA_TOPIC}'")

try:
    while True:
        line = arduino.readline().decode('utf-8').strip()
        if line:
            if "," in line:
                parts = line.split(",")
            else:
                parts = line.split()

            if len(parts) == 3:
                try:
                    temps = [float(p) for p in parts]
                    
                    # --- sanity check ---
                    if all(0 <= t <= 50 for t in temps):
                        data = {
                            "sensor1": temps[0],
                            "sensor2": temps[1],
                            "sensor3": temps[2],
                            "location": LOCATION
                        }
                        print(f"Sending to Kafka: {data}")
                        producer.send(KAFKA_TOPIC, data)
                    else:
                        print(f"Discarding out-of-range reading: {temps}")
                        
                except ValueError:
                    print(f"Invalid numeric data from Arduino: {line}")
            else:
                print(f"Unexpected line format from Arduino: {line}")

except KeyboardInterrupt:
    print("Stopping producer...")

finally:
    arduino.close()
    producer.flush()
    producer.close()
