#include <WiFiS3.h>
#include <ArduinoHttpClient.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <LiquidCrystal_I2C.h>

// --- Wi-Fi ---
const char* ssid = "Lab-ZBC";  // net
const char* password = "Prestige#PuzzledCASH48!";  // xubwuk23 or whatever

// --- Server (SPLIT, as required) ---
const char* serverHost = "10.101.129.170";  // 10.0.0.200
const int   serverPort = 5000;
const char* serverPath = "/sensor";
const char* LOCATION   = "Bathroom";

const char* ca_cert = \
"-----BEGIN CERTIFICATE-----\n"
"MIIDaTCCAlGgAwIBAgIUQHL5N8UcWR3lpTi0Vwf3RWMVC6QwDQYJKoZIhvcNAQEL\n"
"BQAwXTELMAkGA1UEBhMCREsxEjAQBgNVBAgMCVNvbWVTdGF0ZTERMA8GA1UEBwwI\n"
"U29tZUNpdHkxDjAMBgNVBAoMBU15T3JnMRcwFQYDVQQDDA4xMC4xMDEuMTI5LjE3\n"
"MDAeFw0yNTEyMTUwOTIzNDJaFw0yNjEyMTUwOTIzNDJaMF0xCzAJBgNVBAYTAkRL\n"
"MRIwEAYDVQQIDAlTb21lU3RhdGUxETAPBgNVBAcMCFNvbWVDaXR5MQ4wDAYDVQQK\n"
"DAVNeU9yZzEXMBUGA1UEAwwOMTAuMTAxLjEyOS4xNzAwggEiMA0GCSqGSIb3DQEB\n"
"AQUAA4IBDwAwggEKAoIBAQDOniDL0Tz5DFOMsOT6PncsXALsMOyBdDNif1gOVu5N\n"
"QRWYM/usX2LagsSpShp5K3PAQUUUH5fj0VzgMCFIhCAi1/o28i+4bSvqV5PL6zWP\n"
"9mPoa9RyjKMe28KZdm0uMxi3GmJaYabxlxH/Xy+CTimdbuPrPxtKHTsT2C47hF+C\n"
"buAs6s1Fq6TM5PF92lz31XQCse1/NcZXLVGw11DR1Q4IStYKtrEaNK4zANBNAED4\n"
"eBBf3XtpMvglxddmQ/67kKDCsUD+xclfOmuwHruJy2TrLZvMuCco6YN1ZeEovW+0\n"
"Noy1hmsrEL5AX7WrCxIHoZ5N6eGNY8A77B2nEXdfAOfRAgMBAAGjITAfMB0GA1Ud\n"
"DgQWBBQ5/06oyMLdKw1s54+IiYgsoC71FDANBgkqhkiG9w0BAQsFAAOCAQEABLVj\n"
"uqtJR2WO319Y5Q648CF+gG8KUjOV7gscTQ9dHNC+ailkfDXRnjYShpQXMo6aEC6F\n"
"UAk06+V/hxFUQGFNyDsTF9XwbW1yWp9fZvBYdrPa0PJ9/Xs0RYOMldmrTS8bJX1l\n"
"3sZ4Iut2RunfXIV9WLbGySap/gVK5K/wzgL81RIudedmvC438nt8gL3vfIUlMjlf\n"
"BOAMSi68SnmYpkkJF3PLUXJcjEwbOZI3YCwvyTaXGs5nnK0qtgmi1P9LVgiNNXga\n"
"UZVnT2MNZMgIEhtQIZ6xKAhSdoBLn+YSFNSDMJ7rCqk23nSNId63ElHPbIvX/Zjj\n"
"QYeNfA+R/uIqp5yr/Q==\n"
"-----END CERTIFICATE-----\n";


// --- HTTPS client ---
WiFiSSLClient sslClient;
HttpClient http(sslClient, serverHost, serverPort);

// --- OneWire ---
#define ONE_WIRE_BUS 2
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

// --- Display ---
LiquidCrystal_I2C lcd(0x27, 16, 2);

// --- Sensor addresses ---
DeviceAddress sensor1 = { 0x28, 0x44, 0xD1, 0x86, 0x00, 0x00, 0x00, 0xF4 };
DeviceAddress sensor2 = { 0x28, 0x55, 0xFD, 0x82, 0x00, 0x00, 0x00, 0x4F };
DeviceAddress sensor3 = { 0x28, 0xB5, 0x7B, 0x6A, 0x00, 0x00, 0x00, 0x64 };

void setup() {
  Serial.begin(9600);

  sslClient.setCACert(ca_cert);

  Serial.print("Resolving hostname: ");
  Serial.println(serverHost);
  IPAddress ip;
  if (WiFi.hostByName(serverHost, ip)) {
      Serial.print("Resolved IP: ");
      Serial.println(ip);
  } else {
      Serial.println("Could not resolve hostname");
  }

  sensors.begin();
  sensors.setResolution(sensor1, 12);
  sensors.setResolution(sensor2, 12);
  sensors.setResolution(sensor3, 12);

  lcd.init();
  lcd.backlight();

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
}

void loop() {
  sensors.requestTemperatures();

  float t1 = sensors.getTempC(sensor1);
  float t2 = sensors.getTempC(sensor2);
  float t3 = sensors.getTempC(sensor3);

  // --- Reject invalid readings ---
  if (
    t1 < 0 || t1 > 50 ||
    t2 < 0 || t2 > 50 ||
    t3 < 0 || t3 > 50
  ) {
    Serial.print("Bunk readings. ");
    delay(2000);
    return;
  }

  // --- LCD ---
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

  // --- Serial (still useful for debugging) ---
  Serial.print(t1, 2);
  Serial.print(",");
  Serial.print(t2, 2);
  Serial.print(",");
  Serial.println(t3, 2);

  // --- HTTPS POST ---
  if (WiFi.status() == WL_CONNECTED) {
    String payload = "{";
    payload += "\"sensor1\":" + String(t1, 2) + ",";
    payload += "\"sensor2\":" + String(t2, 2) + ",";
    payload += "\"sensor3\":" + String(t3, 2) + ",";
    payload += "\"location\":\"" + String(LOCATION) + "\"";
    payload += "}";

    Serial.print("Begin request... \n");
    http.beginRequest();
    Serial.print("Posting to server path:\n");
    Serial.print(serverPath);
    http.post(serverPath);
    http.sendHeader("Content-Type", "application/json");
    http.sendHeader("Content-Length", payload.length());
    Serial.print("Begin body... \n");
    http.beginBody();
    Serial.print("Printing payload: \n");
    Serial.print(payload);
    http.print(payload);
    http.endRequest();

    Serial.print("Sent request. \n");

    // Drain response
    while (http.available()) {
      http.read();
    }
  } else {
    Serial.print("Not connected. \n");
  }

  delay(2000);
}
