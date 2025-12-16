#include <EEPROM.h>

const int LDR_PIN = A0;

// EEPROM addresses
const int ADDR_DARK      = 0; // uint16_t
const int ADDR_BRIGHT    = 2; // uint16_t
const int ADDR_THRESHOLD = 4; // uint16_t

uint16_t darkBaseline;
uint16_t brightBaseline;
uint16_t threshold;

uint16_t readCalibratedRaw() {
    return analogRead(LDR_PIN);
}

long mapToFullRange(uint16_t raw, uint16_t b, uint16_t d) {
    if (b > d) { uint16_t t = b; b = d; d = t; }
    long mapped = map(raw, d, b, 0, 1023);
    return constrain(mapped, 0, 1023);
}


void loadCalibration() {
    Serial.print("Loading calibration... ");
    EEPROM.get(ADDR_DARK, darkBaseline);
    EEPROM.get(ADDR_BRIGHT, brightBaseline);
    EEPROM.get(ADDR_THRESHOLD, threshold);

    Serial.print("Calibration loaded.");
}

void setup() {
    Serial.begin(9600);
    loadCalibration();
}

void loop() {
    uint16_t raw = readCalibratedRaw();

    long mapped = mapToFullRange(raw, brightBaseline, darkBaseline);
    long mappedThreshold = mapToFullRange(threshold, brightBaseline, darkBaseline);
    Serial.print("brightBaseline=");
    Serial.print(brightBaseline);
    Serial.print(" darkBaseline=");
    Serial.print(darkBaseline);

    const char* state = (mapped < mappedThreshold) ? "BRIGHT" : "DARK";

    Serial.print(" raw=");
    Serial.print(raw);
    Serial.print("  mapped=");
    Serial.print(mapped);
    Serial.print("  state=");
    Serial.println(state);

    delay(200);
}
