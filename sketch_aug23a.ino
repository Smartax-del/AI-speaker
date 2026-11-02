const int BUTTON_PIN = 2;
const int PIN_R = 9;
const int PIN_G = 10;
const int PIN_B = 11;
const int POT_PIN = A0;
const int BUZZER_PIN = 8;

int lastButtonState = HIGH;
int lastPotValue = -1;

enum LedMode { SOLID, BLINK };
LedMode ledMode = SOLID;
int ledR = 0, ledG = 0, ledB = 255;
unsigned long lastBlinkTime = 0;
bool blinkOn = true;
const unsigned long BLINK_INTERVAL = 300;

unsigned long lastPotSend = 0;
const unsigned long POT_SEND_INTERVAL = 200;

void applyColor(int r, int g, int b) {
  analogWrite(PIN_R, r);
  analogWrite(PIN_G, g);
  analogWrite(PIN_B, b);
}

void setSolid(int r, int g, int b) {
  ledMode = SOLID;
  ledR = r; ledG = g; ledB = b;
  applyColor(r, g, b);
}

void setBlink(int r, int g, int b) {
  ledMode = BLINK;
  ledR = r; ledG = g; ledB = b;
  blinkOn = true;
  lastBlinkTime = millis();
  applyColor(r, g, b);
}

void updateBlink() {
  if (ledMode == BLINK) {
    unsigned long now = millis();
    if (now - lastBlinkTime >= BLINK_INTERVAL) {
      blinkOn = !blinkOn;
      lastBlinkTime = now;
      applyColor(blinkOn ? ledR : 0, blinkOn ? ledG : 0, blinkOn ? ledB : 0);
    }
  }
}

void playAlarm() {
  for (int i = 0; i < 5; i++) {
    digitalWrite(BUZZER_PIN, HIGH);
    delay(150);
    digitalWrite(BUZZER_PIN, LOW);
    delay(150);
  }
}

void setup() {
  Serial.begin(9600);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(PIN_R, OUTPUT);
  pinMode(PIN_G, OUTPUT);
  pinMode(PIN_B, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  setSolid(0, 0, 255);
}

void loop() {
  int currentButtonState = digitalRead(BUTTON_PIN);
  if (currentButtonState != lastButtonState) {
    Serial.println(currentButtonState == LOW ? "PRESS" : "RELEASE");
    lastButtonState = currentButtonState;
  }

  unsigned long now = millis();
  if (now - lastPotSend >= POT_SEND_INTERVAL) {
    int potValue = analogRead(POT_PIN);
    if (abs(potValue - lastPotValue) > 5) {
      Serial.print("VOL:");
      Serial.println(potValue);
      lastPotValue = potValue;
    }
    lastPotSend = now;
  }

  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();

        if (command == "READY") {
      setSolid(0, 0, 255);       // синий — покой
    } else if (command == "LISTEN") {
      setSolid(255, 40, 0);      // жёлтый — слушаю
    } else if (command == "THINK") {
      setBlink(0, 0, 255);       // мигающий синий — думаю
    } else if (command == "SPEAK") {
      setSolid(0, 255, 0);       // зелёный — говорю
    } else if (command == "ERROR") {
      setBlink(255, 0, 0);       // мигающий красный — ошибка
    } else if (command == "ALARM") {
      playAlarm();
    }
  }

  updateBlink();
  delay(10);
}