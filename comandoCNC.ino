#include <AccelStepper.h>
#include <GFButton.h>

GFButton botaoX(24); // digitalRead(botaoX) 0 caso apertado; 1 caso aberto
GFButton botaoY(22);

long xMax = 500 + 700 + 200 +200 + 80;
long yMax = 1000 + 500 + 200 + 200;
long posX = 0;
long posY = 0;

bool reiniciar = false;

bool reiniciarX = false;
unsigned long ultResetX = 0;

bool reiniciarY = false;
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

void stepY(long d) {
  stepperY1.move(d);
  stepperY2.move(d);
}

void paraX() {
  reiniciarX = false;
  Serial.println("parou X");
  stepperX.stop();
  return;
}

void paraY() {
  reiniciarY = false;
  Serial.println("parou Y");
  stepperY1.stop();
  stepperY2.stop();
  return;
}

void andaPara( long x, long y) {
  if ((posX + x) > xMax) {
    x = xMax - posX;
    posX = xMax;
  } else posX += x;
  if ((posY + y) > yMax) {
    y = yMax - posY;
    posY = yMax;
  } else posY += y;
  
  stepperX.move(x);
  stepY(y);
  
  return;
}

void reinicia() {
  reiniciar = true;
  reiniciarX = true;
  reiniciarY = true;
  return;
}

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);

  stepperX.setMaxSpeed(250);
  stepperX.setAcceleration(1000);

  stepperY1.setMaxSpeed(250);
  stepperY1.setAcceleration(1000);
  
  stepperY2.setMaxSpeed(250);
  stepperY2.setAcceleration(1000);

  botaoX.setPressHandler(paraX);
  botaoY.setPressHandler(paraY);
}

void loop() {

  botaoX.process();
  botaoY.process();

  // if (stepperX.distanceToGo() != 0) {}
  // if (stepperY1.distanceToGo() != 0) {}

  stepperX.run();
  stepperY1.run();
  stepperY2.run();

  // Logica de reiniciar a CNC para a posição inicial
  if (reiniciar) {

    if (reiniciarX) {
      if (millis()-ultResetX > 50){
        stepperX.move(-50);
        ultResetX = millis();
      }
    }

    if (reiniciarY) {
      if (millis()-ultResetY > 50){
        stepY(-50);
        ultResetY = millis();
      }
    }
  
    if ((!reiniciarX) && (!reiniciarY)) {
      Serial.println("parou");
      reiniciar = false;
      posX = 0;
      posY = 0;
      // stepperX.setCurrentPosition(0);
      // stepperY1.setCurrentPosition(0);
      // stepperY2.setCurrentPosition(0);
    }

  }

  if (Serial.available() > 0) {
    String texto = Serial.readStringUntil('\n');
    texto.trim();

    if (texto == "reinicia") {
      Serial.println(texto);
      reinicia();
      texto = "";
    }
    if (texto.startsWith("anda")) { // enviar: anda XXXX YYYY (aceitando negativos)
      Serial.println(texto);
      texto = texto.substring(5);
      long x;
      long y;
      if (texto[0] == '-'){
        x = texto.substring(0,5).toInt();
        texto = texto.substring(1);
      }
      else { 
        x = texto.substring(0,4).toInt();
      }
      texto = texto.substring(5);
      if (texto[0] == '-') {
        y = texto.substring(0,5).toInt();
        texto = texto.substring(1);
      }
      else {
        y = texto.substring(0,4).toInt();
      }
      andaPara(x,y);
      texto = "";
    }
  }
}
