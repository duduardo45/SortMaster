#include <AccelStepper.h>

int botaoX = 24; // digitalRead(botaoX) 0 caso apertado; 1 caso aberto
int botaoY = 22;


bool reiniciar = false;
int confia = 0;
unsigned long ultReset = 0;

int pinSTEPx = 2;
int pinDIRx = 5;

AccelStepper stepper(AccelStepper::DRIVER, pinSTEPx, pinDIRx);
void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  stepper.setMaxSpeed(200);
  stepper.setAcceleration(200);
}

void loop() {

  if (stepper.distanceToGo() == 0)
    {

    }
    stepper.run();

  if (reiniciar) {
    if (digitalRead(botaoX) == 0) {
      confia++;
      if (confia > 2){
        reiniciar = false;
      }
    }
    while (digitalRead(botaoX) == 1) {
      confia = 0;
      if (millis()-ultReset > 200){
        stepper.move(-50);
        ultReset = millis();
      }
    }
  }

  if (Serial.available() > 0) {
    String texto = Serial.readStringUntil('\n');
    texto.trim();
    if (texto == "anda"){
      Serial.println(texto);
      stepper.move(500);
      texto = "";
    }
    if (texto == "desanda"){
      Serial.println(texto);
      stepper.move(-100);
      texto = "";
    }
    if (texto == "reinicia") {
      Serial.println(texto);
      reiniciar = true;
    }
    Serial.println(digitalRead(botaoX));
  }
  
}