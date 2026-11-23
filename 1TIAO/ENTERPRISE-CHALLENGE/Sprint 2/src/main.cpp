#include <Arduino.h>

/*
 * Fleet Intelligence - Sprint 2
 * Simulacao de telemetria veicular com ESP32 (Wokwi)
 *
 * Entradas analogicas:
 *   GPIO34 - Velocidade (potenciometro)
 *   GPIO35 - RPM (potenciometro)
 *   GPIO32 - Nivel de combustivel (potenciometro)
 *   GPIO33 - Temperatura do motor (potenciometro)
 *
 * Saidas:
 *   GPIO2  - LED de alerta
 *   GPIO25 - Buzzer
 *
 * Os valores sao simulados. Nao representam sensores reais de um veiculo.
 */

const int PIN_SPEED = 34;
const int PIN_RPM = 35;
const int PIN_FUEL = 32;
const int PIN_TEMP = 33;

const int PIN_LED = 2;
const int PIN_BUZZER = 25;

const unsigned long SAMPLE_INTERVAL_MS = 1000;
unsigned long lastSample = 0;

struct Telemetry {
  int speedKmh;
  int rpm;
  int fuelPct;
  int engineTempC;
};

Telemetry readTelemetry() {
  Telemetry data;

  data.speedKmh = map(analogRead(PIN_SPEED), 0, 4095, 0, 160);
  data.rpm = map(analogRead(PIN_RPM), 0, 4095, 600, 6000);
  data.fuelPct = map(analogRead(PIN_FUEL), 0, 4095, 0, 100);
  data.engineTempC = map(analogRead(PIN_TEMP), 0, 4095, 40, 130);

  return data;
}

String detectAlerts(const Telemetry& data) {
  String alerts = "";

  if (data.speedKmh > 120) {
    alerts += "HIGH_SPEED|";
  }
  if (data.rpm > 5000) {
    alerts += "HIGH_RPM|";
  }
  if (data.fuelPct < 10) {
    alerts += "LOW_FUEL|";
  }
  if (data.engineTempC > 105) {
    alerts += "HIGH_ENGINE_TEMP|";
  }

  if (alerts.length() == 0) {
    return "NONE";
  }

  alerts.remove(alerts.length() - 1); // remove o ultimo separador |
  return alerts;
}

void setup() {

  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);

  digitalWrite(PIN_LED, LOW);
  digitalWrite(PIN_BUZZER, LOW);

  analogReadResolution(12);

  Serial.begin(115200);
  delay(500);

  // Configuração PWM do buzzer - Arduino ESP32 Core 2.x
  ledcSetup(0, 2000, 8);
  ledcAttachPin(PIN_BUZZER, 0);

  Serial.println("timestamp_ms,speed_kmh,rpm,fuel_pct,engine_temp_c,alerts");
}

void loop() {
  const unsigned long now = millis();

  if (now - lastSample >= SAMPLE_INTERVAL_MS) {
    lastSample = now;

    Telemetry data = readTelemetry();
    String alerts = detectAlerts(data);
    bool hasAlert = (alerts != "NONE");

    digitalWrite(PIN_LED, hasAlert ? HIGH : LOW);

    if (hasAlert) {
    ledcWriteTone(0, 2000);
} else {
    ledcWriteTone(0, 0);
}

    // Uma linha por amostra, pronta para copiar/exportar como CSV.
    Serial.print(now);
    Serial.print(",");
    Serial.print(data.speedKmh);
    Serial.print(",");
    Serial.print(data.rpm);
    Serial.print(",");
    Serial.print(data.fuelPct);
    Serial.print(",");
    Serial.print(data.engineTempC);
    Serial.print(",");
    Serial.println(alerts);
  }
}
