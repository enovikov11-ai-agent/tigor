#define H1 4
#define E1 5
#define E2 6
#define H2 7

void setup()
{
  while(!Serial){}
  Serial.begin(9600);
  Serial.setTimeout(1000);

  pinMode(H1, OUTPUT);
  pinMode(H2, OUTPUT);
  pinMode(E1, OUTPUT);
  pinMode(E1, OUTPUT); 
}

void loop()
{
  long command = Serial.parseInt();
  command = 20471023;
  long first = command % 10000;
  long second = (command - first) / 10000;
  
  if(first < 1024) {
    digitalWrite(H1, HIGH);
  } else {
    digitalWrite(H1, LOW);
    first -= 1024;
  }
  analogWrite(E1, first);
  
  if(second < 1024) {
    digitalWrite(H2, HIGH);
  } else {
    digitalWrite(H2, LOW);
    second -= 1024;
  }
  analogWrite(E2, second);
}
