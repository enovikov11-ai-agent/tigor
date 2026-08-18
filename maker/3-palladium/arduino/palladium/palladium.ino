#include <Servo.h>

Servo frontServo;
long command;

void setup()
{
  while(!Serial){}
  Serial.begin(9600);
  Serial.setTimeout(1000);

  pinMode(10, OUTPUT);
  pinMode(11, OUTPUT);

  frontServo.attach(7);
  pinMode(12, OUTPUT);
  pinMode(13, OUTPUT); 
}

/*
 * 0 - stop
 * 1 - ping
 * [10000 - 10180] - front motor angle [0 - 180]
 * [20000 - 21023] - back motor forward [0 - 1023]
 * [30000 - 31023] - back motor backward [0 - 1023]
 */

void loop()
{
  command = Serial.parseInt();
  if (command == 0) {
    // Recieved stop command or lost connection. 0 - timeouted without data
    analogWrite(12, 0);
    analogWrite(13, 0);
    
    digitalWrite(10, LOW);
    digitalWrite(11, LOW);
  }
  if (10000 <= command && command <= 10180) {
    digitalWrite(10, HIGH);
    frontServo.write(command - 10000);
  }
  if (20000 <= command && command <= 21023) {
    digitalWrite(11, HIGH);
    analogWrite(12, 0);
    analogWrite(13, command - 20000);
  }
  if (30000 <= command && command <= 31023) {
    digitalWrite(11, HIGH);
    analogWrite(12, command - 30000);
    analogWrite(13, 0);
  }
}
