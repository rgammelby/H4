import serial
from kafka import KafkaProducer
import time

# --- Configuration ---
ARDUINO_PORT = "COM4"          # Chosen USB port
ARDUINO_BAUD = 9600            # Standard baud rate (transfer speed, bytes per second) for Arduino sketch

KAFKA_BROKER = "10.101.129.170:9092"  # Linux VM Kafka broker IP
KAFKA_TOPIC = "arduino-data"          # Topic for sending and receiving arduino data

# Kafka Producer Setup
producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    value_serializer=lambda v: str(v).encode('utf-8')
)

# Initialise the chosen USB port
arduino = serial.Serial(ARDUINO_PORT, ARDUINO_BAUD, timeout=1)
time.sleep(2)  # Wait for Arduino to reset to avoid errors from immediate data streaming

print(f"Streaming data from Arduino on {ARDUINO_PORT} to Kafka topic '{KAFKA_TOPIC}'")

# Reads from chosen USB port
try:
    while True:
        line = arduino.readline().decode('utf-8').strip()
        if line:  # If an output is present, send to Kafka topic
            print(f"Read from Arduino: {line}")
            producer.send(KAFKA_TOPIC, line)
except KeyboardInterrupt:
    print("Stopping producer...")
finally:
    arduino.close()
    producer.flush()
    producer.close()
