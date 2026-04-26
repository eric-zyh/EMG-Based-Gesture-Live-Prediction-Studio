#include <Arduino.h>

/*
  EMGesture serial sender

  This sketch matches the current Python GUI's preferred timed CSV protocol:

    t_ms,adc0,voltage0
    t_ms,adc0,voltage0,adc1,voltage1

  Notes:
  - Baud rate must stay at 115200 to match the desktop app defaults.
  - This sketch defaults to dual-channel output on A0 + A1.
  - Set ENABLE_A1 to false if you want single-channel output on A0 only.
  - If ENABLE_A1 is true, make sure a second sensor is actually wired to A1;
    otherwise the second channel will float and produce garbage/noise values.
  - Adjust VREF / ADC_MAX for boards that do not use a 10-bit 0-5 V ADC.
    Example: many ESP32 boards should use ADC_MAX = 4095 and VREF = 3.3.
*/

const unsigned long BAUD_RATE = 115200UL;
const unsigned long SAMPLE_INTERVAL_US = 5000UL;  // 200 Hz

const uint8_t A0_PIN = A0;
const uint8_t A1_PIN = A1;
const bool ENABLE_A1 = true;

const float VREF = 5.0f;
const float ADC_MAX = 1023.0f;

unsigned long lastSampleUs = 0;

float adcToVoltage(int adcValue) {
  return (static_cast<float>(adcValue) / ADC_MAX) * VREF;
}

void printHeader() {
  Serial.println("# EMGesture serial source");
  Serial.println("# baud: 115200");
  if (ENABLE_A1) {
    Serial.println("# channels: A0 A1");
    Serial.println("# format: t_ms,adc0,voltage0,adc1,voltage1");
  } else {
    Serial.println("# channels: A0");
    Serial.println("# format: t_ms,adc0,voltage0");
  }
}

void setup() {
  Serial.begin(BAUD_RATE);
  pinMode(A0_PIN, INPUT);
  if (ENABLE_A1) {
    pinMode(A1_PIN, INPUT);
  }

  delay(250);
  printHeader();
  lastSampleUs = micros();
}

void loop() {
  const unsigned long nowUs = micros();
  if (nowUs - lastSampleUs < SAMPLE_INTERVAL_US) {
    return;
  }

  // Step forward by the target interval so the sampling cadence stays close
  // to the requested rate even if one loop iteration runs a little late.
  lastSampleUs += SAMPLE_INTERVAL_US;
  if (nowUs - lastSampleUs > SAMPLE_INTERVAL_US) {
    lastSampleUs = nowUs;
  }

  const unsigned long tMs = millis();
  const int adc0 = analogRead(A0_PIN);
  const float voltage0 = adcToVoltage(adc0);

  Serial.print(tMs);
  Serial.print(",");
  Serial.print(adc0);
  Serial.print(",");
  Serial.print(voltage0, 4);

  if (ENABLE_A1) {
    const int adc1 = analogRead(A1_PIN);
    const float voltage1 = adcToVoltage(adc1);
    Serial.print(",");
    Serial.print(adc1);
    Serial.print(",");
    Serial.print(voltage1, 4);
  }

  Serial.println();
}
