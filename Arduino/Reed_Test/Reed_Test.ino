const int led = 13;
const int reed = 7;
const int control = 5;

int doorState; //0 = open, 1 = closed
int state;

void setup()
{
  pinMode(led, OUTPUT);
  pinMode(control, OUTPUT);
  pinMode(reed, INPUT_PULLUP);
  state = 0;
  doorState = digitalRead(reed);
  //Wait for door to close
  while(doorState == LOW)
  {
    delay(500);
    doorState = digitalRead(reed);
  }
}

void loop()
{  
  doorState = digitalRead(reed);

  switch(state)
  {
    case 0:
      if(doorState == LOW)
        state = 1;
      break;
    case 1:
      digitalWrite(led, HIGH);
      if(doorState == HIGH)
        state = 2;
      break;
    case 2:
      digitalWrite(control, HIGH);
      delay(1000);
      digitalWrite(control, LOW);
      delay(500);
      digitalWrite(led, LOW);
      state = 0;
      break;
  }
   delay(50);
}
