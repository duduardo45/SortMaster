#include <AccelStepper.h>
#include <GFButton.h>
#include <Servo.h>

GFButton botaoX(32); // digitalRead(botaoX) 0 caso apertado; 1 caso aberto
GFButton botaoY(22);

long xMax = 500 + 700 + 200 +200 + 80;
long yMax = 1000 + 500 + 200 + 200;
long posX = 0;
long posY = 0;

int velStd = 400;

int vel = velStd;

bool reiniciar = false;
bool reiniciar2 = false;
unsigned long para_reiniciar = 0;

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

Servo cabeca;
int pinoServo = 38;

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

void troca_velocidade(int spd) {
  stepperX.setMaxSpeed(spd);
  stepperY1.setMaxSpeed(spd);
  stepperY2.setMaxSpeed(spd);
  vel = spd;
  return;
}

void reinicia() {
  reiniciar = true;
  reiniciarX = true;
  reiniciarY = true;
  return;
}

void mexe_cabeca(int angulo){
  cabeca.write(angulo);
  return;
}

void fim_do_reinicia() {
  reiniciar = false;
  posX = 0;
  posY = 0;
  if (vel == velStd) {
    troca_velocidade(50);
    andaPara(100, 100); // PRECISA DAR TEMPO DISSO EXECUTAR ANTES DE REINICIAR DE NOVO
    reiniciar2 = true;
    para_reiniciar = millis();
  } else if (vel == 50) troca_velocidade(velStd);
}

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);

  troca_velocidade(velStd);

  stepperX.setAcceleration(1000);

  stepperY1.setAcceleration(1000);
  
  stepperY2.setAcceleration(1000);

  botaoX.setPressHandler(paraX);
  botaoY.setPressHandler(paraY);

  cabeca.attach(pinoServo);
  cabeca.write(0);
  delay(2000);
  cabeca.write(180);
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
      if (millis()-ultResetX > 20){
        stepperX.move(-50);
        ultResetX = millis();
      }
    }

    if (reiniciarY) {
      if (millis()-ultResetY > 20){
        stepY(-50);
        ultResetY = millis();
      }
    }
  
    if ((!reiniciarX) && (!reiniciarY)) {
      Serial.println("parou");
      fim_do_reinicia();
    }
  }

  if (reiniciar2) {
    if (millis()-para_reiniciar > 4000) {
      reinicia();
      reiniciar2 = false;
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
    else if(texto.startsWith("c ")){
      int ang = texto.substring(3,6).toInt();
      mexe_cabeca(ang);
      texto = ""
    }
  }
}
