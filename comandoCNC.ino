#include <AccelStepper.h>

int botaoX = 24; // digitalRead(botaoX) 0 caso apertado; 1 caso aberto
int botaoY = 22;

bool reiniciar = false;

bool reiniciarX = false;
int confiaX = 0;
unsigned long ultResetX = 0;

bool reiniciarY = false;
int confiaY = 0;
unsigned long ultResetY = 0;

int pinSTEPx = 2;
int pinDIRx = 5;

int pinSTEPy1 = 3;
int pinDIRy1 = 6;

int pinSTEPy2 = 4;
int pinDIRy2 = 7;

AccelStepper stepperX(AccelStepper::DRIVER, pinSTEPx, pinDIRx);
AccelStepper stepperY1(AccelStepper::DRIVER, pinSTEPy1, pinDIRy1);
AccelStepper stepperY2(AccelStepper::DRIVER, pinSTEPy2, pinDIRy2);



void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);

  stepperX.setMaxSpeed(200);
  stepperX.setAcceleration(200);

  stepperY1.setMaxSpeed(200);
  stepperY1.setAcceleration(200);
  
  stepperY2.setMaxSpeed(200);
  stepperY2.setAcceleration(200);
}

void loop() {

  // if (stepperX.distanceToGo() == 0)
  //   {

  //   }
    stepperX.run();
    stepperY1.run();
    stepperY2.run();

  if (reiniciar) {
    if (digitalRead(botaoX) == 0 && reiniciarX) {
      confiaX++;
      if (confiaX > 2){
        reiniciarX = false;
        stepperX.move(50);
      }
    }
    if (digitalRead(botaoY) == 0 && reiniciarY) {
      confiaY++;
      if (confiaY > 3){
        reiniciarY = false;
        stepperY1.move(50);
        stepperY2.move(50);
      }
    }
    if (digitalRead(botaoX) == 1) {
      confiaX = 0;
      if (millis()-ultResetX > 200){
        stepperX.move(-50);
        ultResetX = millis();
      }
    }
    if (digitalRead(botaoY) == 1) {
      confiaY = 0;
      if (millis()-ultResetY > 200){
        stepperY1.move(-50);
        stepperY2.move(-50);
        ultResetY = millis();
      }
    }
    // ESTÁ BUGADO AQUI; COM ESTA PARTE ACABA CEDO DEMAIS
    if (reiniciarX == false && reiniciarY == false) {
      reiniciar = false;
    }
  }

  if (Serial.available() > 0) {
    String texto = Serial.readStringUntil('\n');
    texto.trim();
    if (texto == "anda x"){
      Serial.println(texto);
      stepperX.move(500);
      texto = "";
    }
    if (texto == "desanda x"){
      Serial.println(texto);
      stepperX.move(-100);
      texto = "";
    }
    if (texto == "anda y"){
      Serial.println(texto);
      stepperY1.move(100);
      stepperY2.move(100);
      texto = "";
    }
    if (texto == "desanda y"){
      Serial.println(texto);
      stepperY1.move(-100);
      stepperY2.move(-100);
      texto = "";
    }
    if (texto == "anda"){
      Serial.println(texto);
      stepperX.move(200);
      stepperY1.move(200);
      stepperY2.move(200);
      texto = "";
    }
    if (texto == "le") {
      Serial.print("B X: ");
      Serial.println(digitalRead(botaoX));
      Serial.print("B Y: ");
      Serial.println(digitalRead(botaoY));
    }
    if (texto == "reinicia") {
      Serial.println(texto);
      reiniciar = true;
      reiniciarX = true;
      reiniciarY = true;
    }
  }
  
}
