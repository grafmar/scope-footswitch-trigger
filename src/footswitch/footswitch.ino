#define BTN1_PIN 3
#define BTN2_PIN 4

#define DEBOUNCE_MS   30
#define LONGPRESS_MS 800

struct Button {
  uint8_t pin;
  bool stableState;
  bool lastReading;
  unsigned long lastDebounceTime;

  bool pressed;
  bool longSent;
  unsigned long pressTime;
};

Button b1 = {BTN1_PIN, HIGH, HIGH, 0, false, false, 0};
Button b2 = {BTN2_PIN, HIGH, HIGH, 0, false, false, 0};

void setup() {
  pinMode(BTN1_PIN, INPUT_PULLUP);
  pinMode(BTN2_PIN, INPUT_PULLUP);

  Serial.begin(115200);
}

void handleButton(Button &b, const char *shortMsg, const char *longMsg) {
  bool reading = digitalRead(b.pin);

  // Debounce handling
  if (reading != b.lastReading) {
    b.lastDebounceTime = millis();
    b.lastReading = reading;
  }

  if ((millis() - b.lastDebounceTime) > DEBOUNCE_MS) {
    if (reading != b.stableState) {
      b.stableState = reading;

      // Button pressed
      if (b.stableState == LOW) {
        b.pressed = true;
        b.longSent = false;
        b.pressTime = millis();
      }

      // Button released
      else {
        if (b.pressed && !b.longSent) {
          Serial.println(shortMsg);  // short press
        }
        b.pressed = false;
      }
    }
  }

  // Long press detection (while held)
  if (b.pressed && !b.longSent) {
    if (millis() - b.pressTime >= LONGPRESS_MS) {
      Serial.println(longMsg);
      b.longSent = true;
    }
  }
}

void loop() {
  handleButton(b1, "B1S", "B1L");
  handleButton(b2, "B2S", "B2L");
}
