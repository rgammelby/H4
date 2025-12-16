#include <Wire.h>

void setup() {
  Wire.begin();
  Serial.begin(9600);

  Serial.println("Scanning I2C bus...");

  for (uint8_t addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() == 0) {
      Serial.print("Found device at 0x");
      Serial.println(addr, HEX);
      delay(10);
    }
  }

  Serial.println("Scan complete.");
}

void loop() {
}
