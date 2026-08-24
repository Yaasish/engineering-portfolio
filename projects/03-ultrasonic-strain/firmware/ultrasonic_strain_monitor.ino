/*
  Portfolio reconstruction of an HY-SRF05 acquisition sketch.

  Hardware:
    - Arduino Uno R3
    - HY-SRF05 ultrasonic sensor

  Output format:
    time_ms,distance_mm

  Strain is calculated off-board so the reference length and calibration
  assumptions remain explicit in the analysis step.
*/

const byte TRIGGER_PIN = 13;
const byte ECHO_PIN = 12;
const unsigned long SAMPLE_INTERVAL_MS = 100;
const unsigned long ECHO_TIMEOUT_US = 30000;
const byte MEDIAN_SAMPLES = 5;

unsigned long lastSampleMs = 0;

float readDistanceMm() {
  digitalWrite(TRIGGER_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIGGER_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIGGER_PIN, LOW);

  const unsigned long durationUs = pulseIn(ECHO_PIN, HIGH, ECHO_TIMEOUT_US);
  if (durationUs == 0) {
    return -1.0;
  }

  // Round-trip speed of sound at approximately 20 C: 0.343 mm/us.
  return durationUs * 0.343f / 2.0f;
}

void sortAscending(float values[], byte count) {
  for (byte i = 1; i < count; ++i) {
    const float key = values[i];
    byte j = i;
    while (j > 0 && values[j - 1] > key) {
      values[j] = values[j - 1];
      --j;
    }
    values[j] = key;
  }
}

float readMedianDistanceMm() {
  float samples[MEDIAN_SAMPLES];
  byte validCount = 0;

  while (validCount < MEDIAN_SAMPLES) {
    const float distance = readDistanceMm();
    if (distance > 0.0) {
      samples[validCount++] = distance;
    }
    delay(15);
  }

  sortAscending(samples, MEDIAN_SAMPLES);
  return samples[MEDIAN_SAMPLES / 2];
}

void setup() {
  pinMode(TRIGGER_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  Serial.begin(115200);
  Serial.println("time_ms,distance_mm");
}

void loop() {
  const unsigned long now = millis();
  if (now - lastSampleMs < SAMPLE_INTERVAL_MS) {
    return;
  }
  lastSampleMs = now;

  const float distanceMm = readMedianDistanceMm();
  Serial.print(now);
  Serial.print(',');
  Serial.println(distanceMm, 2);
}

