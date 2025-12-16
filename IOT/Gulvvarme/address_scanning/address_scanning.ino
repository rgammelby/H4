#include <OneWire.h>

#define ONE_WIRE_BUS 2  // D0, or whichever pin you chose
OneWire oneWire(ONE_WIRE_BUS);

void setup() {
  Serial.begin(9600);
  Serial.println("Beginning scan...");

  byte addr[8];
  oneWire.reset_search();

  while (oneWire.search(addr)) {
    Serial.print("Found device: ");
    for (byte i = 0; i < 8; i++) {
      if (addr[i] < 16) Serial.print("0");
      Serial.print(addr[i], HEX);
      if (i < 7) Serial.print(" ");
    }
    Serial.println();

    if (OneWire::crc8(addr, 7) != addr[7]) {
      Serial.println("CRC is invalid.");
    }
  }

  Serial.println("Scan finished.");
}

void loop() {
}
