/* 
  Elven Lantern — Arduino sketch with toggle switch
  - LDR on A0
  - LED (PWM) on D9
  - Toggle switch on D2 (press once = ON, press again = OFF)
  - Uses calibration baselines stored in EEPROM at addresses 0 (dark), 2 (bright), 4 (threshold)
  Behaviour:
    - Darker than threshold -> LED brightness increases as it gets darker
    - Brighter than threshold -> LED at minimum brightness
    - Smoothing applied to avoid flicker
*/

#include <EEPROM.h>

const int LDR_PIN = A0;
const int LED_PIN = 9;
const int SWITCH_PIN = 2;

const int ADDR_DARK      = 0;
const int ADDR_BRIGHT    = 2;
const int ADDR_THRESHOLD = 4;

uint16_t darkBaseline;
uint16_t brightBaseline;
uint16_t thresholdVal;

const uint8_t PWM_MIN = 0;
const uint8_t PWM_MAX = 255;
const float SMOOTH_ALPHA = 0.12f;
float smoothPWM = 0.0f;

// toggle state
bool lampOn = false;
bool lastSwitchState = HIGH;  // switch is INPUT_PULLUP: HIGH when unpressed

void loadCalibration() {
  EEPROM.get(ADDR_DARK, darkBaseline);
  EEPROM.get(ADDR_BRIGHT, brightBaseline);
  EEPROM.get(ADDR_THRESHOLD, thresholdVal);
}

uint16_t readAverage(uint8_t samples = 16, uint8_t delayMs = 5) {
  uint32_t sum = 0;
  for (uint8_t i = 0; i < samples; ++i) {
    sum += analogRead(LDR_PIN);
    delay(delayMs);
  }
  return (uint16_t)(sum / samples);
}

// Map raw -> 0..255 so that raw=0 -> max LED, raw >= thresholdVal -> min LED
int mapDarkToPWM(uint16_t raw) {
  if (raw >= thresholdVal) return PWM_MIN;

  // Scale 0..thresholdVal -> PWM_MAX..PWM_MIN
  long mapped = map((long)raw, 0, (long)thresholdVal, PWM_MAX, PWM_MIN);
  if (mapped < PWM_MIN) mapped = PWM_MIN;
  if (mapped > PWM_MAX) mapped = PWM_MAX;
  return (int)mapped;
}

void setup() {
  pinMode(LED_PIN, OUTPUT);
  pinMode(SWITCH_PIN, INPUT_PULLUP);
  Serial.begin(9600);
  loadCalibration();

  Serial.print(F("Loaded baselines: dark=")); Serial.print(darkBaseline);
  Serial.print(F("  bright=")); Serial.print(brightBaseline);
  Serial.print(F("  threshold=")); Serial.println(thresholdVal);

  smoothPWM = 0.0f;
}

void loop() {
  // --- Toggle switch logic ---
  bool currentSwitchState = digitalRead(SWITCH_PIN);
  if (lastSwitchState == HIGH && currentSwitchState == LOW) {
    // switch pressed: flip lamp state
    lampOn = !lampOn;
  }
  lastSwitchState = currentSwitchState;

  if (!lampOn) {
    // lamp off: gently ramp down
    smoothPWM = smoothPWM * (1.0f - SMOOTH_ALPHA);
    analogWrite(LED_PIN, (int)smoothPWM);
    delay(40);
    return;
  }

  // lamp is on: read sensor, compute PWM
  uint16_t raw = readAverage(8, 3);
  int targetPWM = mapDarkToPWM(raw);

  // exponential smoothing
  smoothPWM = (SMOOTH_ALPHA * (float)targetPWM) + ((1.0f - SMOOTH_ALPHA) * smoothPWM);

  analogWrite(LED_PIN, (int)(smoothPWM + 0.5f));

  // optional debug output
  Serial.print(F("raw=")); Serial.print(raw);
  Serial.print(F("  pwm_target=")); Serial.print(targetPWM);
  Serial.print(F("  pwm_smoothed=")); Serial.print((int)(smoothPWM + 0.5f));
  Serial.print(F("  lampOn=")); Serial.println(lampOn ? "YES" : "NO");

  delay(120);
}
