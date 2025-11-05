// --- Pin setup ---
// Ultrasonic
#define TRIG_PIN A1
#define ECHO_PIN A2

// KY-037 Sound Sensor (Analog output)
#define SOUND_PIN A0   // AO pin of KY-037

void setup() {
  Serial.begin(9600);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  Serial.println("Simulation started: Distance + Sound values...");
}

void loop() {
  // --- Distance ---
  long duration = getDistanceDuration();
  int distance = durationToCm(duration);

  if (distance <= 0) {
    Serial.println("DISTANCE,ERROR");
  } else {
    Serial.print("DISTANCE,");
    Serial.println(distance);
  }

  // --- Sound ---
  int soundValue = analogRead(SOUND_PIN);
  Serial.print("SOUND,");
  Serial.println(soundValue);

  // Small delay to keep output readable (adjust if you want faster/slower data)
  delay(1000);
}

// --- Helper functions ---
long getDistanceDuration() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  return pulseIn(ECHO_PIN, HIGH, 30000); // microseconds
}

int durationToCm(long durationMicros) {
  if (durationMicros == 0) return 0;     // no echo detected
  int cm = (int)(durationMicros * 0.034 / 2.0);
  if (cm > 4000) return 0;                // out of range
  return cm;
}
