#include <EEPROM.h>

const int LDR_PIN = A0;
const int SAMPLES = 20;
const unsigned long PRINT_INTERVAL = 300; // ms

// EEPROM addresses (2 bytes each)
const int ADDR_DARK     = 0; // uint16_t
const int ADDR_BRIGHT   = 2; // uint16_t
const int ADDR_THRESHOLD= 4; // uint16_t

uint16_t darkBaseline;
uint16_t brightBaseline;
uint16_t threshold;

unsigned long lastPrint = 0;

uint16_t readAverage() {
  uint32_t sum = 0;
  for (int i = 0; i < SAMPLES; ++i) {
    sum += analogRead(LDR_PIN);
    delay(5);
  }
  return (uint16_t)(sum / SAMPLES);
}

void loadCalibration() {
  EEPROM.get(ADDR_DARK, darkBaseline);
  EEPROM.get(ADDR_BRIGHT, brightBaseline);
  EEPROM.get(ADDR_THRESHOLD, threshold);
}

void saveCalibration() {
  EEPROM.put(ADDR_DARK, darkBaseline);
  EEPROM.put(ADDR_BRIGHT, brightBaseline);
  EEPROM.put(ADDR_THRESHOLD, threshold);
}

void printHelp() {
  Serial.println(F("Commands:"));
  Serial.println(F("  B  -> capture current reading as BRIGHT baseline"));
  Serial.println(F("  D  -> capture current reading as DARK baseline"));
  Serial.println(F("  C  -> compute & save threshold = (bright+dark)/2"));
  Serial.println(F("  R  -> reset calibration to defaults"));
  Serial.println(F("  P  -> print current calibration values"));
  Serial.println(F("  H  -> this help"));
}

void setup() {
  Serial.begin(115200);
  while (!Serial) { /* wait for terminal on some boards */ }

  loadCalibration();
  Serial.println(F("LDR calibration sketch started."));
  printHelp();
  Serial.println();

  Serial.print(F("Loaded: dark=")); Serial.print(darkBaseline);
  Serial.print(F("  bright=")); Serial.print(brightBaseline);
  Serial.print(F("  threshold=")); Serial.println(threshold);
}

void loop() {
  // handle serial commands
  if (Serial.available()) {
    char c = Serial.read();
    if (c == 'B' || c == 'b') {
      brightBaseline = readAverage();
      Serial.print(F("Captured BRIGHT = ")); Serial.println(brightBaseline);
    } else if (c == 'D' || c == 'd') {
      darkBaseline = readAverage();
      Serial.print(F("Captured DARK = ")); Serial.println(darkBaseline);
    } else if (c == 'C' || c == 'c') {
      threshold = (uint16_t)(((uint32_t)brightBaseline + (uint32_t)darkBaseline) / 2);
      Serial.print("brightBaseline: ");
      Serial.print(brightBaseline);
      Serial.print("\ndarkBaseline: ");
      Serial.print(darkBaseline);
      saveCalibration();
      Serial.print(F("\nComputed & saved THRESHOLD = ")); Serial.println(threshold);
    } else if (c == 'R' || c == 'r') {
      darkBaseline = 800;
      brightBaseline = 50;
      threshold = (brightBaseline + darkBaseline) / 2;
      saveCalibration();
      Serial.println(F("Calibration reset to defaults and saved."));
    } else if (c == 'P' || c == 'p') {
      Serial.print(F("Current: dark=")); Serial.print(darkBaseline);
      Serial.print(F("  bright=")); Serial.print(brightBaseline);
      Serial.print(F("  threshold=")); Serial.println(threshold);
    } else if (c == 'H' || c == 'h') {
      printHelp();
    }
    while (Serial.available()) Serial.read();
  }

  // periodic reading + mapping
  unsigned long now = millis();
  if (now - lastPrint >= PRINT_INTERVAL) {
    lastPrint = now;
    uint16_t val = readAverage();

    // map val to 0..1023 using measured extremes, brightBaseline = higher value
    long mappedVal = map(val, brightBaseline, darkBaseline, 1023, 0);
    mappedVal = constrain(mappedVal, 0, 1023);

    // map to 0..100% for convenience
    int percent = (int)((mappedVal * 100L) / 1023L);

    // threshold mapping
    long mappedThreshold = map(threshold, brightBaseline, darkBaseline, 1023, 0);
    mappedThreshold = constrain(mappedThreshold, 0, 1023);
    const char* state = (mappedVal >= mappedThreshold) ? "BRIGHT" : "DARK";

    Serial.print(F("raw=")); Serial.print(val);
    Serial.print(F("  mapped=")); Serial.print(mappedVal);
    Serial.print(F("  %=")); Serial.print(percent);
    Serial.print(F("  state=")); Serial.print(state);
    Serial.print(F("  (thr=")); Serial.print(threshold);
    Serial.print(F(", bright=")); Serial.print(brightBaseline);
    Serial.print(F(", dark=")); Serial.print(darkBaseline);
    Serial.println(F(")"));
  }
}
