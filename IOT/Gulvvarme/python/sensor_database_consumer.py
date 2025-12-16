from kafka import KafkaConsumer
import psycopg2
import json

# --- Configuration ---
KAFKA_BROKER = "10.0.0.200:9092"  # Your Linux VM's Kafka broker
TOPIC = "sensor-data"                  # Kafka topic from Arduino producer

# PostgreSQL connection
conn = psycopg2.connect(
    host="localhost",
    database="sensor_data",  # Your database name
    user="sascha",
    password="Kode1234!"
)
cur = conn.cursor()
conn.autocommit = True  # Ensure that each query is executed immediately

# Set up Kafka consumer
consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=[KAFKA_BROKER],
    auto_offset_reset='earliest',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))  # Parse JSON messages
)

print(f"Listening to Kafka topic '{TOPIC}' and inserting into Postgres table 'sensor_readings'...")

# Consume messages
for message in consumer:
    try:
        data = message.value
        sensor1 = float(data["sensor1"])
        sensor2 = float(data["sensor2"])
        sensor3 = float(data["sensor3"])

        print(f"Inserting: sensor1={sensor1}, sensor2={sensor2}, sensor3={sensor3}")

        cur.execute(
            "INSERT INTO sensor_readings (sensor_one, sensor_two, sensor_three, location) VALUES (%s, %s, %s, %s);",
            (data["sensor1"], data["sensor2"], data["sensor3"], data["location"])
        )

    except Exception as e:
        print("Error inserting:", e)
