from flask import Flask, request
from kafka import KafkaProducer
import json

app = Flask(__name__)

producer = KafkaProducer(
    bootstrap_servers=["localhost:9092"],
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

@app.route("/sensor", methods=["POST"])
def sensor():
    data = request.json
    print("Received:", data)
    producer.send("sensor-data", data)
    return "OK", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, ssl_context=('/home/sascha/Kafka/certs/server.crt', '/home/sascha/Kafka/certs/server.key')
)

