const unsigned long INTERVAL_US = 1000;
unsigned long lastSample = 0;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(500000);
  analogReadResolution(14);
  lastSample = micros();
}

void loop() {
  // put your main code here, to run repeatedly:
  if (micros() - lastSample >= INTERVAL_US) {
    lastSample += INTERVAL_US;
    Serial.println(analogRead(A0));
  }
}
