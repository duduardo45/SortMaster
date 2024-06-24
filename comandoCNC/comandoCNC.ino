#include <AccelStepper.h>
#include <GFButton.h>
#include <Servo.h>

GFButton botaoX(32); // digitalRead(botaoX) 0 caso apertado; 1 caso aberto
GFButton botaoY(22);

long xMax = 500 + 700 + 200 + 200 + 80;
long yMax = 1000 + 500 + 200 + 200;
long posX = 0;
long posY = 0;

bool dentro_de_caixa = false;
bool bomba_ligada = false;

typedef struct
{
  int n_caixa;
  long x;
  long y;
} Caixa;

int qtd_registros = 0;
Caixa guardadores[4];

int velStd = 600;

int vel = velStd;

bool reiniciar = false;
bool reiniciar2 = false;
unsigned long para_reiniciar = 0;

bool reiniciarX = false;
unsigned long ultResetX = 0;

bool reiniciarY = false;
unsigned long ultResetY = 0;

bool pega_ativo = false;
unsigned long pega_delay = 0;
int pega_fase_ativa = 0;
int pega_n_c = -1;
long pega_x;
long pega_y;

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
int pinoServo = 11;
int cima = 50;
int baixo = 180;

const int relayPin = 44; // Pino do relé conectado ao Arduino

void stepY(long d)
{
  stepperY1.move(d);
  stepperY2.move(d);
}

void paraX()
{
  reiniciarX = false;
  Serial.println("parou X");
  stepperX.stop();
  return;
}

void paraY()
{
  reiniciarY = false;
  Serial.println("parou Y");
  stepperY1.stop();
  stepperY2.stop();
  return;
}

void andaPara(long x, long y)
{
  if ((posX + x) > xMax)
  {
    x = xMax - posX;
    posX = xMax;
  }
  else
    posX += x;
  if ((posY + y) > yMax)
  {
    y = yMax - posY;
    posY = yMax;
  }
  else
    posY += y;

  stepperX.move(x);
  stepY(y);

  return;
}

void moveCNC(long x, long y)
{
  if (dentro_de_caixa)
  {
    return;
  }
  if (x > xMax)
  {
    x = xMax;
  }
  if (y > yMax)
  {
    y = yMax;
  }
  long mx, my;
  mx = x - posX;
  my = y - posY;
  andaPara(mx, my);
  return;
}

void troca_velocidade(int spd)
{
  stepperX.setMaxSpeed(spd);
  stepperY1.setMaxSpeed(spd);
  stepperY2.setMaxSpeed(spd);
  vel = spd;
  return;
}

void bomba()
{
  if (bomba_ligada)
  {
    digitalWrite(relayPin, HIGH);
    bomba_ligada = false;
  }
  else
  {
    digitalWrite(relayPin, LOW);
    bomba_ligada = true;
  }
}

void reinicia()
{
  reiniciar = true;
  reiniciarX = true;
  reiniciarY = true;
  return;
}

void mexe_cabeca(int angulo)
{
  cabeca.write(angulo);
  // Serial.print(angulo);
  return;
}

void fim_do_reinicia()
{
  reiniciar = false;
  posX = 0;
  posY = 0;
  if (vel == velStd)
  {
    troca_velocidade(50);
    andaPara(100, 100); // PRECISA DAR TEMPO DISSO EXECUTAR ANTES DE REINICIAR DE NOVO
    reiniciar2 = true;
    para_reiniciar = millis();
  }
  else if (vel == 50)
    troca_velocidade(velStd);
}

void registra_caixa(int n, long x, long y)
{
  Caixa c;
  c.n_caixa = n;
  c.x = x;
  c.y = y;
  guardadores[qtd_registros] = c;
  qtd_registros++;
  return;
}

void reinicia_caixas()
{
  qtd_registros = 0;
  return;
}

int acha_caixa(int n)
{ // retorna o indice no vetor, e -1 caso não ache
  int n_da_caixa;
  for (int i = 0; i < qtd_registros; i++)
  {
    n_da_caixa = guardadores[i].n_caixa;
    if (n == n_da_caixa)
      return i;
  }
  return -1;
}

void entra_sai_caixa()
{ // mexe a cabeca da CNC adentro e afora das caixas usando o andaPara
  if (dentro_de_caixa)
  {
    andaPara(0, -300);
    dentro_de_caixa = false;
  }
  else
  {
    andaPara(0, 300);
    dentro_de_caixa = true;
  }
  return;
}

void pega_e_guarda(Caixa c, long x, long y)
{
  // testa se a coordenada esbarra nas caixas
  if (pega_y > yMax - 300)
    pega_y = yMax - 300;
  unsigned long t = millis();
  if ((pega_fase_ativa == 0))
  {
    moveCNC(x, y); // vai até o objeto
    pega_delay = t;
    pega_fase_ativa = 1;
  }
  else if ((pega_fase_ativa == 1) && (t - pega_delay >= 6000))
  {
    mexe_cabeca(baixo); // abaixa a cabeca
    pega_delay = t;
    pega_fase_ativa = 2;
  }
  else if ((pega_fase_ativa == 2) && (t - pega_delay >= 1000))
  {
    bomba(); // liga a bomba para pegar o objeto
    pega_delay = t;
    pega_fase_ativa = 3;
  }
  else if ((pega_fase_ativa == 3) && (t - pega_delay >= 1000))
  {
    mexe_cabeca(cima); // sobe a cabeca
    pega_delay = t;
    pega_fase_ativa = 4;
  }
  else if ((pega_fase_ativa == 4) && (t - pega_delay >= 1000))
  {
    moveCNC(c.x, c.y); // vai até a coordenada da caixa
    pega_delay = t;
    pega_fase_ativa = 5;
  }
  else if ((pega_fase_ativa == 5) && (t - pega_delay >= 6000))
  {
    entra_sai_caixa(); // entra na caixa
    pega_delay = t;
    pega_fase_ativa = 6;
  }
  // mexe_cabeca(baixo); // (opcional) desce a cabeca
  else if ((pega_fase_ativa == 6) && (t - pega_delay >= 3000))
  {
    bomba(); // desliga a bomba
    pega_delay = t;
    pega_fase_ativa = 7;
  }
  // mexe_cabeca(cima); // (condicional) sobe a cabeca
  else if ((pega_fase_ativa == 7) && (t - pega_delay >= 1000))
  {
    entra_sai_caixa(); // sai da caixa
    pega_delay = t;
    pega_fase_ativa = 8;
  }
  else if ((pega_fase_ativa == 8) && (t - pega_delay >= 3000))
  {
    pega_fase_ativa = 0;
    pega_ativo = false;
    Serial.println("pega terminado");
  }
  return;
}

void setup()
{
  // put your setup code here, to run once:
  Serial.begin(9600);

  troca_velocidade(velStd);

  stepperX.setAcceleration(1000);

  stepperY1.setAcceleration(1000);

  stepperY2.setAcceleration(1000);

  botaoX.setPressHandler(paraX);
  botaoY.setPressHandler(paraY);

  cabeca.attach(pinoServo);
  cabeca.write(50);

  pinMode(relayPin, OUTPUT);
  digitalWrite(relayPin, HIGH);

  registra_caixa(1, 1000, 1500);
}

void loop()
{

  botaoX.process();
  botaoY.process();

  // if (stepperX.distanceToGo() != 0) {}
  // if (stepperY1.distanceToGo() != 0) {}

  stepperX.run();
  stepperY1.run();
  stepperY2.run();

  // Logica de reiniciar a CNC para a posição inicial
  if (reiniciar)
  {

    if (reiniciarX)
    {
      if (millis() - ultResetX > 20)
      {
        stepperX.move(-100);
        ultResetX = millis();
      }
    }

    if (reiniciarY)
    {
      if (millis() - ultResetY > 20)
      {
        stepY(-100);
        ultResetY = millis();
      }
    }

    if ((!reiniciarX) && (!reiniciarY))
    {
      Serial.println("parou");
      fim_do_reinicia();
    }
  }

  if (reiniciar2)
  {
    if (millis() - para_reiniciar > 6000)
    {
      reinicia();
      reiniciar2 = false;
    }
  }

  // lógica de sequencia de ações para pegar e guardar um objeto
  if (pega_ativo)
  {
    pega_e_guarda(guardadores[pega_n_c], pega_x, pega_y);
  }

  if (Serial.available() > 0)
  {
    String texto = Serial.readStringUntil('\n');
    texto.trim();

    if (texto == "reinicia")
    {
      Serial.println(texto);
      reinicia();
      texto = "";
    }
    else if (texto.startsWith("anda"))
    { // enviar: anda XXXX YYYY (aceitando negativos)
      Serial.println(texto);
      texto = texto.substring(5);
      long x;
      long y;
      if (texto[0] == '-')
      {
        x = texto.substring(0, 5).toInt();
        texto = texto.substring(1);
      }
      else
      {
        x = texto.substring(0, 4).toInt();
      }
      texto = texto.substring(5);
      if (texto[0] == '-')
      {
        y = texto.substring(0, 5).toInt();
        texto = texto.substring(1);
      }
      else
      {
        y = texto.substring(0, 4).toInt();
      }
      moveCNC(x, y);
      texto = "";
    }
    else if (texto.startsWith("c "))
    {
      if (texto[2] == '0')
      {
        int ang = texto.substring(3, 5).toInt();
        mexe_cabeca(ang);
        texto = "";
      }
      else
      {
        int ang = texto.substring(2, 5).toInt();
        mexe_cabeca(ang);
        Serial.println(texto);
        texto = "";
      }
    }
    else if (texto.startsWith("bomba"))
    {
      bomba();
      Serial.println(texto);
      texto = "";
    }
    else if (texto.startsWith("pega"))
    { // enviar: pega C XXXX YYYY (aceitando negativos)
      Serial.println(texto);
      texto = texto.substring(5);
      pega_n_c = texto.substring(0, 1).toInt();
      pega_n_c = acha_caixa(pega_n_c);
      if (pega_n_c == -1)
      {
        Serial.println("nao existe esta caixa!");
        texto = "";
        return;
      }
      texto = texto.substring(2);
      if (texto[0] == '-')
      {
        pega_x = texto.substring(0, 5).toInt();
        texto = texto.substring(1);
      }
      else
      {
        pega_x = texto.substring(0, 4).toInt();
      }
      texto = texto.substring(5);
      if (texto[0] == '-')
      {
        pega_y = texto.substring(0, 5).toInt();
        texto = texto.substring(1);
      }
      else
      {
        pega_y = texto.substring(0, 4).toInt();
      }
      Serial.println(pega_x);
      Serial.println(pega_y);
      pega_ativo = true;
      texto = "";
    }
    else if (texto.startsWith("registra_caixa"))
    { // enviar: registra_caixa N XXXX YYYY
      Serial.println(texto);
      texto = texto.substring(15);
      int n = texto.substring(0, 1).toInt();
      texto = texto.substring(2);
      long x = texto.substring(0, texto.indexOf(' ')).toInt();
      texto = texto.substring(texto.indexOf(' ') + 1);
      long y = texto.toInt();
      registra_caixa(n, x, y);
      texto = "";
    }
  }
}
