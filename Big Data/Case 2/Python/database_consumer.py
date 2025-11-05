from kafka import KafkaConsumer
import psycopg2

KAFKA_BROKER = "0.0.0.0:9092"  # Linux VM's Kafka broker
TOPIC = "arduino-data"  # Kafka topic for Arduino data

# PostgreSQL connection
conn = psycopg2.connect(
    host="localhost",
    database="arduino_data",
    user="sascha",
    password="Kode1234!"
)
cur = conn.cursor()
conn.autocommit = True  # Ensure that each query is executed

# DEBUG
# cur.execute("SELECT current_database(), current_schema(), session_user, current_user;")
# print(cur.fetchone())

# Set up Kafka consumer
consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=[KAFKA_BROKER],
    auto_offset_reset='earliest',
    value_deserializer=lambda m: m.decode('utf-8')
)

# Inserts each received numerical data point into PostgreSQL database
for message in consumer:
    try:
        reading = int(float(message.value))  # Force int to match table
        print("Inserting:", reading)
        cur.execute("INSERT INTO public.arduino_readings (volume) VALUES (%s);", (reading,))
        conn.commit()
    except Exception as e:
        print("Error inserting:", e)
