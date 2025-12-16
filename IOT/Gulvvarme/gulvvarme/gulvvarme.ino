#include <OneWire.h>
#include <DallasTemperature.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// --- Bus + devices ---
#define ONE_WIRE_BUS 2   // Your chosen data pin (D0 in your sketch)

OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

// --- Display ---
LiquidCrystal_I2C lcd(0x27, 16, 2);   // Adjust address if needed

// --- Device addresses (fill these after scanning) ---
DeviceAddress sensor1 = { 0x28, 0x44, 0xD1, 0x86, 0x00, 0x00, 0x00, 0xF4 };
DeviceAddress sensor2 = { 0x28, 0x55, 0xFD, 0x82, 0x00, 0x00, 0x00, 0x4F };
DeviceAddress sensor3 = { 0x28, 0xB5, 0x7B, 0x6A, 0x00, 0x00, 0x00, 0x64 };

// --- Helper ---
void printAddress(DeviceAddress deviceAddress) {
  for (uint8_t i = 0; i < 8; i++) {
    if (deviceAddress[i] < 16) Serial.print("0");
    Serial.print(deviceAddress[i], HEX);
  }
}

void setup() {
  Serial.begin(9600);

  sensors.begin();
  sensors.setResolution(sensor1, 12);
  sensors.setResolution(sensor2, 12);
  sensors.setResolution(sensor3, 12);

  lcd.init();
  lcd.backlight();

  /*Serial.println("Found sensor addresses:");
  Serial.print("1: "); printAddress(sensor1); Serial.println();
  Serial.print("2: "); printAddress(sensor2); Serial.println();
  Serial.print("3: "); printAddress(sensor3); Serial.println();*/
}

void loop() {
  sensors.requestTemperatures();

  float t1 = sensors.getTempC(sensor1);
  float t2 = sensors.getTempC(sensor2);
  float t3 = sensors.getTempC(sensor3);

  // --- Send to LCD ---
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("1:");
  lcd.print(t1, 1);
  lcd.print("C  2:");
  lcd.print(t2, 1);

  lcd.setCursor(0, 1);
  lcd.print("3:");
  lcd.print(t3, 1);
  lcd.print("C");

  // --- Send to Serial for Python producer ---
  Serial.print(t1, 2);
  Serial.print(",");
  Serial.print(t2, 2);
  Serial.print(",");
  Serial.println(t3, 2);

  delay(2000);
}

