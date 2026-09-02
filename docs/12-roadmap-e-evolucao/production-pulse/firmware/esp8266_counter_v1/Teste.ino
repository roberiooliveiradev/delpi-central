#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>

// =============================
// Wi-Fi (ajuste para o ambiente)
// =============================
const char* ssid  = "YOUR_SSID";
const char* senha = "YOUR_PASSWORD";

#define BT_MAIS  D5
#define BT_MENOS D1

long contador = 0;

const unsigned long debounce = 100;

bool estadoMais = HIGH;
bool estadoMenos = HIGH;

bool leituraAnteriorMais = HIGH;
bool leituraAnteriorMenos = HIGH;

unsigned long tempoMais = 0;
unsigned long tempoMenos = 0;

// Código estável do controlador (chipId) — exibido na página e em /api/status
String codigoControlador;

ESP8266WebServer server(80);


String montarCodigoControlador() {
  // ChipId do ESP8266 em hex maiúsculo, prefixo fixo para cadastro Delpi
  char buf[24];
  snprintf(buf, sizeof(buf), "ESP-%08X", ESP.getChipId());
  return String(buf);
}


void enviarCors() {
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.sendHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  server.sendHeader("Access-Control-Allow-Headers", "Content-Type");
}


void enviarContador() {
  enviarCors();
  server.send(
    200,
    "application/json",
    "{\"contador\":" + String(contador) + "}"
  );
}


void enviarStatus() {
  enviarCors();
  String json =
    "{"
    "\"codigoControlador\":\"" + codigoControlador + "\","
    "\"controllerCode\":\"" + codigoControlador + "\","
    "\"equipamento\":\"" + codigoControlador + "\","
    "\"contador\":" + String(contador) + ","
    "\"ip\":\"" + WiFi.localIP().toString() + "\","
    "\"mac\":\"" + WiFi.macAddress() + "\","
    "\"status\":\"online\""
    "}";
  server.send(200, "application/json", json);
}


long parseContadorDoBody() {
  if (!server.hasArg("plain")) {
    return -1;
  }
  String body = server.arg("plain");
  body.replace(" ", "");

  int idx = body.indexOf("\"contador\"");
  if (idx < 0) {
    idx = body.indexOf("\"counter\"");
  }
  if (idx < 0) {
    return -1;
  }

  int colon = body.indexOf(':', idx);
  if (colon < 0) {
    return -1;
  }

  int start = colon + 1;
  while (start < (int)body.length() && (body[start] == ' ' || body[start] == '\"')) {
    start++;
  }

  int end = start;
  while (end < (int)body.length() && isDigit(body[end])) {
    end++;
  }
  if (end <= start) {
    return -1;
  }

  return body.substring(start, end).toInt();
}


String paginaPrincipal() {
  String html;
  html.reserve(3200);

  html += F(
    "<!DOCTYPE html><html lang='pt-BR'><head>"
    "<meta charset='utf-8'/>"
    "<meta name='viewport' content='width=device-width,initial-scale=1'/>"
    "<title>Production Pulse — Contador</title>"
    "<style>"
    ":root{--bg:#0f172a;--card:#1e293b;--line:#334155;--text:#e2e8f0;--muted:#94a3b8;--accent:#38bdf8;--ok:#4ade80;--btn:#334155;}"
    "*{box-sizing:border-box}"
    "body{margin:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:linear-gradient(160deg,#0f172a,#1e293b 55%,#0f172a);color:var(--text);min-height:100vh;padding:1.25rem}"
    ".wrap{max-width:28rem;margin:0 auto}"
    ".card{background:var(--card);border:1px solid var(--line);border-radius:1rem;padding:1.25rem;margin-bottom:1rem;box-shadow:0 12px 40px rgba(0,0,0,.35)}"
    ".label{font-size:.75rem;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin:0 0 .35rem}"
    ".code{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:1.35rem;font-weight:700;color:var(--accent);word-break:break-all}"
    ".hint{margin:.55rem 0 0;font-size:.85rem;color:var(--muted);line-height:1.4}"
    ".valor{font-size:2.75rem;font-weight:700;letter-spacing:-.03em;margin:.25rem 0}"
    ".row{display:flex;gap:.5rem;flex-wrap:wrap;margin-top:1rem}"
    "button{flex:1;min-width:5rem;border:0;border-radius:.65rem;padding:.7rem .9rem;font-size:1rem;font-weight:600;cursor:pointer;background:var(--btn);color:var(--text)}"
    "button.accent{background:var(--accent);color:#0f172a}"
    "button.danger{background:#7f1d1d;color:#fecaca}"
    ".meta{font-size:.8rem;color:var(--muted);margin-top:.75rem}"
    ".dot{display:inline-block;width:.55rem;height:.55rem;border-radius:50%;background:var(--ok);margin-right:.35rem;vertical-align:middle}"
    "</style></head><body><div class='wrap'>"
  );

  html += F("<div class='card'>");
  html += F("<p class='label'>Código do controlador</p>");
  html += "<div class='code' id='codigo'>" + codigoControlador + "</div>";
  html += F(
    "<p class='hint'>"
    "Use este código no cadastro do Production Pulse (campo «Código do controlador»), "
    "junto com IP e nome do dispositivo."
    "</p>"
    "<p class='meta'><span class='dot'></span>Identidade fixa do chip (não muda ao reiniciar)</p>"
    "</div>"
  );

  html += F(
    "<div class='card'>"
    "<p class='label'>Contador</p>"
    "<div class='valor'><span id='c'>0</span></div>"
    "<div class='row'>"
    "<button class='accent' onclick=\"cmd('incrementar')\">+1</button>"
    "<button onclick=\"cmd('decrementar')\">−1</button>"
    "<button class='danger' onclick=\"cmd('reset')\">RESET</button>"
    "</div>"
    "<p class='meta' id='metaIp'></p>"
    "</div>"
  );

  html += F(
    "<script>"
    "async function atualiza(){"
      "try{"
        "const r=await fetch('/api/status');"
        "const j=await r.json();"
        "document.getElementById('c').innerText=j.contador;"
        "if(j.codigoControlador){document.getElementById('codigo').innerText=j.codigoControlador;}"
        "const ip=j.ip||'';"
        "const mac=j.mac||'';"
        "document.getElementById('metaIp').innerText='IP '+ip+(mac?(' · MAC '+mac):'');"
      "}catch(e){}"
    "}"
    "async function cmd(x){"
      "await fetch('/api/'+x,{method:'POST'});"
      "atualiza();"
    "}"
    "setInterval(atualiza,500);"
    "atualiza();"
    "</script></div></body></html>"
  );

  return html;
}


void setup() {
  Serial.begin(115200);

  pinMode(BT_MAIS, INPUT_PULLUP);
  pinMode(BT_MENOS, INPUT_PULLUP);

  codigoControlador = montarCodigoControlador();

  WiFi.begin(ssid, senha);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }

  Serial.println();
  Serial.println("WiFi conectado");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
  Serial.print("MAC: ");
  Serial.println(WiFi.macAddress());
  Serial.print("Codigo controlador: ");
  Serial.println(codigoControlador);

  server.on("/", HTTP_GET, []() {
    server.send(200, "text/html", paginaPrincipal());
  });

  server.on("/api/contador", HTTP_GET, enviarContador);
  server.on("/api/status", HTTP_GET, enviarStatus);

  server.on("/api/incrementar", HTTP_POST, []() {
    contador++;
    Serial.print("Contador: ");
    Serial.println(contador);
    enviarContador();
  });

  server.on("/api/decrementar", HTTP_POST, []() {
    contador--;
    Serial.print("Contador: ");
    Serial.println(contador);
    enviarContador();
  });

  server.on("/api/reset", HTTP_POST, []() {
    contador = 0;
    Serial.println("Contador zerado");
    enviarContador();
  });

  // Define valor absoluto — usado pela API Delpi no restore pós-queda de energia
  server.on("/api/definir", HTTP_POST, []() {
    long valor = parseContadorDoBody();
    if (valor < 0) {
      enviarCors();
      server.send(400, "application/json", "{\"erro\":\"informe contador\"}");
      return;
    }
    contador = valor;
    Serial.print("Contador definido: ");
    Serial.println(contador);
    enviarContador();
  });

  server.on("/api/definir", HTTP_OPTIONS, []() {
    enviarCors();
    server.send(204);
  });

  server.begin();
  Serial.println("Servidor iniciado");
}


void loop() {
  server.handleClient();

  bool leituraMais = digitalRead(BT_MAIS);
  if (leituraMais != leituraAnteriorMais) {
    tempoMais = millis();
  }
  if ((millis() - tempoMais) > debounce) {
    if (leituraMais != estadoMais) {
      estadoMais = leituraMais;
      if (estadoMais == LOW) {
        contador++;
        Serial.print("Contador: ");
        Serial.println(contador);
      }
    }
  }
  leituraAnteriorMais = leituraMais;

  bool leituraMenos = digitalRead(BT_MENOS);
  if (leituraMenos != leituraAnteriorMenos) {
    tempoMenos = millis();
  }
  if ((millis() - tempoMenos) > debounce) {
    if (leituraMenos != estadoMenos) {
      estadoMenos = leituraMenos;
      if (estadoMenos == LOW) {
        contador--;
        Serial.print("Contador: ");
        Serial.println(contador);
      }
    }
  }
  leituraAnteriorMenos = leituraMenos;
}
