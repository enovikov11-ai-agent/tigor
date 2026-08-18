long command;

void setup() {
  while(!Serial){}
  Serial.begin(9600);

  pinMode(4, OUTPUT);
  pinMode(5, OUTPUT);
  pinMode(6, OUTPUT);
  pinMode(7, OUTPUT);

  digitalWrite(4, HIGH);
  digitalWrite(7, HIGH);
}

void loop() {
  command = Serial.parseInt();
  if(10000 <= command && command <= 11023){
    analogWrite(5, command - 10000);
    analogWrite(6, command - 10000);
  }
}
