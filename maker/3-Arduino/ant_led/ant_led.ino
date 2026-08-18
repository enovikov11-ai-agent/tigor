long command;
int brightness = 0;

void setup() {
  pinMode(4, OUTPUT);
  pinMode(5, OUTPUT);
  pinMode(6, OUTPUT);
  pinMode(7, OUTPUT);
  digitalWrite(4, 1023);
  digitalWrite(7, 1023);
}

void setLed(bool isEnabled) {
  if(isEnabled) {
    digitalWrite(5, 1023);
    digitalWrite(6, 1023);
  } else {
    digitalWrite(5, 0);
    digitalWrite(6, 0);
  }
}

void setBrightness(int brightness) { // from 0 to 100
  for(int j = 0; j < 1000; j++){
    setLed(true);
    delayMicroseconds(brightness);
    setLed(false);
    delayMicroseconds(100 - brightness);  
  }
}

void loop() {
  for(int i = 0; i < 100; i++){
    setBrightness(i);
  }
}
