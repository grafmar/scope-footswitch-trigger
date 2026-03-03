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

// --- Combo State ---
bool comboActive = false;
bool comboLongSent = false;
unsigned long comboStartTime = 0;

void setup() {
  pinMode(BTN1_PIN, INPUT_PULLUP);
  pinMode(BTN2_PIN, INPUT_PULLUP);
  Serial.begin(115200);
}

void handleButton(Button &b, const char *shortMsg, const char *longMsg) {
  bool reading = digitalRead(b.pin);

  if (reading != b.lastReading) {
    b.lastDebounceTime = millis();
    b.lastReading = reading;
  }

  if ((millis() - b.lastDebounceTime) > DEBOUNCE_MS) {
    if (reading != b.stableState) {
      b.stableState = reading;

      if (b.stableState == LOW) {
        b.pressed = true;
        b.longSent = false;
        b.pressTime = millis();
      } else {
        if (b.pressed && !b.longSent && !comboActive) {
          Serial.println(shortMsg);
        }
        b.pressed = false;
      }
    }
  }

  // Long press (nur wenn kein Combo läuft)
  if (b.pressed && !b.longSent && !comboActive) {
    if (millis() - b.pressTime >= LONGPRESS_MS) {
      Serial.println(longMsg);
      b.longSent = true;
    }
  }
}

void handleCombo() {

  // Beide stabil gedrückt?
  bool bothPressed = (b1.stableState == LOW && b2.stableState == LOW);

  // Start Combo
  if (bothPressed && !comboActive) {
    comboActive = true;
    comboLongSent = false;
    comboStartTime = millis();

    // Einzel-Long Events blockieren
    b1.longSent = true;
    b2.longSent = true;
  }

  // Während Combo aktiv
  if (comboActive) {

    // Einer losgelassen -> Combo beenden
    if (!bothPressed) {

      if (!comboLongSent) {
        Serial.println("BBS");   // Short Combo
      }

      comboActive = false;
    }
    else {
      // Long Combo
      if (!comboLongSent &&
          (millis() - comboStartTime >= LONGPRESS_MS)) {

        Serial.println("BBL");
        comboLongSent = true;
      }
    }
  }
}

void loop() {
  handleButton(b1, "B1S", "B1L");
  handleButton(b2, "B2S", "B2L");

  handleCombo();
}