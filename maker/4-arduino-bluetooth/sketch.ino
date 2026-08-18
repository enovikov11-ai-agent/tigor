#define EN_PIN 13

void setup() {
    pinMode(EN_PIN, OUTPUT);
    digitalWrite(EN_PIN, LOW);
    while(!Serial) {}
    Serial.begin(9600);
    Serial1.begin(9600);
    digitalWrite(EN_PIN, HIGH);
}

void loop() {
    if(Serial1.available()) {
        Serial.write(Serial1.read());
    }

    if(Serial.available()) {
        Serial1.write(Serial.read());
    }
}