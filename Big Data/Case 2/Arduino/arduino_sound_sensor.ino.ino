void setup() {
  Serial.begin(9600);  // open serial port
}

void loop() {
  int sensorValue = analogRead(A0);  // reads 0–1023 (in practice never below 24)
  Serial.println(sensorValue);  // print sensor readings
  delay(250);  // 4 readings per second
}
