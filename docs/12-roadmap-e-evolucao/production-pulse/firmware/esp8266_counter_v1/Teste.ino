#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <EEPROM.h>
#include <string.h>

// =============================================================================
// Defaults de fábrica (primeiro boot / EEPROM vazia)
// =============================================================================
static const char* DEFAULT_WIFI_SSID = "YOUR_SSID";
static const char* DEFAULT_WIFI_PASSWORD = "YOUR_PASSWORD";
static const unsigned long DEFAULT_DEBOUNCE_MS = 100;
static const char* FIRMWARE_VERSION = "esp8266_counter_v1.1.0";
static const uint16_t EEPROM_SIZE = 512;
static const uint32_t CONFIG_MAGIC = 0x50505301;  // "PPS\x01"

#define BT_MAIS  D5
#define BT_MENOS D1

struct DeviceConfig {
  uint32_t magic;
  char ssid[33];
  char password[65];
  char apiToken[65];
  uint32_t debounceMs;
};

DeviceConfig cfg;
long contador = 0;
String codigoControlador;
ESP8266WebServer server(80);

bool estadoMais = HIGH;
bool estadoMenos = HIGH;
bool leituraAnteriorMais = HIGH;
bool leituraAnteriorMenos = HIGH;
unsigned long tempoMais = 0;
unsigned long tempoMenos = 0;

unsigned long lastWifiAttemptMs = 0;
unsigned long wifiBackoffMs = 1000;
static const unsigned long WIFI_BACKOFF_MAX_MS = 30000;
static const unsigned long WIFI_BOOT_WAIT_MS = 15000;

String montarCodigoControlador() {
  char buf[24];
  snprintf(buf, sizeof(buf), "ESP-%08X", ESP.getChipId());
  return String(buf);
}

bool apiTokenConfigured() {
  return cfg.apiToken[0] != '\0';
}

bool passwordConfigured() {
  return cfg.password[0] != '\0';
}

void enviarCors() {
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.sendHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  server.sendHeader("Access-Control-Allow-Headers", "Content-Type, X-Device-Token");
}

bool requireDeviceToken() {
  if (!apiTokenConfigured()) {
    return true;
  }
  if (!server.hasHeader("X-Device-Token")) {
    enviarCors();
    server.send(401, "application/json", "{\"error\":\"unauthorized\"}");
    return false;
  }
  String got = server.header("X-Device-Token");
  if (got != String(cfg.apiToken)) {
    enviarCors();
    server.send(401, "application/json", "{\"error\":\"unauthorized\"}");
    return false;
  }
  return true;
}

void saveConfigToEeprom() {
  cfg.magic = CONFIG_MAGIC;
  EEPROM.put(0, cfg);
  EEPROM.commit();
}

void loadConfigFromEeprom() {
  EEPROM.begin(EEPROM_SIZE);
  DeviceConfig loaded;
  EEPROM.get(0, loaded);
  if (loaded.magic != CONFIG_MAGIC) {
    memset(&cfg, 0, sizeof(cfg));
    cfg.magic = CONFIG_MAGIC;
    strncpy(cfg.ssid, DEFAULT_WIFI_SSID, sizeof(cfg.ssid) - 1);
    strncpy(cfg.password, DEFAULT_WIFI_PASSWORD, sizeof(cfg.password) - 1);
    cfg.apiToken[0] = '\0';
    cfg.debounceMs = DEFAULT_DEBOUNCE_MS;
    saveConfigToEeprom();
    return;
  }
  cfg = loaded;
  if (cfg.debounceMs == 0 || cfg.debounceMs > 60000UL) {
    cfg.debounceMs = DEFAULT_DEBOUNCE_MS;
  }
}

String jsonEscape(const String& value) {
  String out;
  out.reserve(value.length() + 8);
  for (size_t i = 0; i < value.length(); i++) {
    char c = value[i];
    if (c == '\\' || c == '"') {
      out += '\\';
    }
    if (c == '\n' || c == '\r') {
      continue;
    }
    out += c;
  }
  return out;
}

String extractJsonString(const String& body, const char* key) {
  String needle = String("\"") + key + "\"";
  int idx = body.indexOf(needle);
  if (idx < 0) {
    return String();
  }
  int colon = body.indexOf(':', idx + needle.length());
  if (colon < 0) {
    return String();
  }
  int start = colon + 1;
  while (start < (int)body.length() && (body[start] == ' ' || body[start] == '\t')) {
    start++;
  }
  if (start >= (int)body.length() || body[start] != '"') {
    return String();
  }
  start++;
  String out;
  while (start < (int)body.length()) {
    char c = body[start++];
    if (c == '\\' && start < (int)body.length()) {
      out += body[start++];
      continue;
    }
    if (c == '"') {
      break;
    }
    out += c;
  }
  return out;
}

bool extractJsonULong(const String& body, const char* key, unsigned long& value) {
  String needle = String("\"") + key + "\"";
  int idx = body.indexOf(needle);
  if (idx < 0) {
    return false;
  }
  int colon = body.indexOf(':', idx + needle.length());
  if (colon < 0) {
    return false;
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
    return false;
  }
  value = body.substring(start, end).toInt();
  return true;
}

long parseContadorDoBody() {
  if (!server.hasArg("plain")) {
    return -1;
  }
  String body = server.arg("plain");
  unsigned long value = 0;
  if (extractJsonULong(body, "contador", value) || extractJsonULong(body, "counter", value)) {
    return (long)value;
  }
  return -1;
}

void enviarContador() {
  enviarCors();
  server.send(200, "application/json", "{\"contador\":" + String(contador) + "}");
}

void enviarStatus() {
  if (!requireDeviceToken()) {
    return;
  }
  enviarCors();
  bool wifiOk = WiFi.status() == WL_CONNECTED;
  String json =
    "{"
    "\"codigoControlador\":\"" + codigoControlador + "\","
    "\"controllerCode\":\"" + codigoControlador + "\","
    "\"equipamento\":\"" + codigoControlador + "\","
    "\"contador\":" + String(contador) + ","
    "\"ip\":\"" + WiFi.localIP().toString() + "\","
    "\"mac\":\"" + WiFi.macAddress() + "\","
    "\"status\":\"online\","
    "\"firmwareVersion\":\"" + String(FIRMWARE_VERSION) + "\","
    "\"uptimeMs\":" + String(millis()) + ","
    "\"freeHeap\":" + String(ESP.getFreeHeap()) + ","
    "\"rssi\":" + String(wifiOk ? WiFi.RSSI() : 0) + ","
    "\"wifiConnected\":" + String(wifiOk ? "true" : "false") +
    "}";
  server.send(200, "application/json", json);
}

void enviarConfig() {
  if (!requireDeviceToken()) {
    return;
  }
  enviarCors();
  bool wifiOk = WiFi.status() == WL_CONNECTED;
  String json =
    "{"
    "\"ssid\":\"" + jsonEscape(String(cfg.ssid)) + "\","
    "\"passwordSet\":" + String(passwordConfigured() ? "true" : "false") + ","
    "\"apiTokenSet\":" + String(apiTokenConfigured() ? "true" : "false") + ","
    "\"debounceMs\":" + String(cfg.debounceMs) + ","
    "\"wifiConfigured\":" + String(wifiOk ? "true" : "false") +
    "}";
  server.send(200, "application/json", json);
}

void aplicarConfigPost() {
  if (!requireDeviceToken()) {
    return;
  }
  if (!server.hasArg("plain")) {
    enviarCors();
    server.send(400, "application/json", "{\"error\":\"empty_body\"}");
    return;
  }

  String body = server.arg("plain");
  bool wifiChanged = false;
  bool touched = false;

  String newSsid = extractJsonString(body, "ssid");
  if (newSsid.length() > 0) {
    strncpy(cfg.ssid, newSsid.c_str(), sizeof(cfg.ssid) - 1);
    cfg.ssid[sizeof(cfg.ssid) - 1] = '\0';
    wifiChanged = true;
    touched = true;
  }

  String newPassword = extractJsonString(body, "password");
  if (body.indexOf("\"password\"") >= 0) {
    strncpy(cfg.password, newPassword.c_str(), sizeof(cfg.password) - 1);
    cfg.password[sizeof(cfg.password) - 1] = '\0';
    wifiChanged = true;
    touched = true;
  }

  String newToken = extractJsonString(body, "apiToken");
  if (body.indexOf("\"apiToken\"") >= 0) {
    strncpy(cfg.apiToken, newToken.c_str(), sizeof(cfg.apiToken) - 1);
    cfg.apiToken[sizeof(cfg.apiToken) - 1] = '\0';
    touched = true;
  }

  unsigned long debounce = 0;
  if (extractJsonULong(body, "debounceMs", debounce)) {
    if (debounce < 1UL) {
      debounce = 1UL;
    }
    if (debounce > 60000UL) {
      debounce = 60000UL;
    }
    cfg.debounceMs = debounce;
    touched = true;
  }

  if (!touched) {
    enviarCors();
    server.send(400, "application/json", "{\"error\":\"no_fields\"}");
    return;
  }

  saveConfigToEeprom();

  if (wifiChanged) {
    WiFi.disconnect(true);
    delay(100);
    WiFi.begin(cfg.ssid, cfg.password);
  }

  enviarConfig();
}

void reiniciarDispositivo() {
  if (!requireDeviceToken()) {
    return;
  }
  enviarCors();
  server.send(200, "application/json", "{\"ok\":true,\"action\":\"reboot\"}");
  delay(50);
  ESP.restart();
}

void ensureWifiConnected() {
  if (WiFi.status() == WL_CONNECTED) {
    wifiBackoffMs = 1000;
    return;
  }
  unsigned long now = millis();
  if (now - lastWifiAttemptMs < wifiBackoffMs) {
    return;
  }
  lastWifiAttemptMs = now;
  WiFi.disconnect();
  WiFi.begin(cfg.ssid, cfg.password);
  if (wifiBackoffMs < WIFI_BACKOFF_MAX_MS) {
    unsigned long next = wifiBackoffMs * 2UL;
    wifiBackoffMs = next > WIFI_BACKOFF_MAX_MS ? WIFI_BACKOFF_MAX_MS : next;
  }
}

String paginaPrincipal() {
  String html;
  html.reserve(2400);
  html += F(
    "<!DOCTYPE html><html lang='pt-BR'><head>"
    "<meta charset='utf-8'/>"
    "<meta name='viewport' content='width=device-width,initial-scale=1'/>"
    "<title>Production Pulse — Contador</title>"
    "<style>"
    ":root{--bg:#0f172a;--card:#1e293b;--line:#334155;--text:#e2e8f0;--muted:#94a3b8;--accent:#38bdf8;--ok:#4ade80;}"
    "*{box-sizing:border-box}"
    "body{margin:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;"
    "background:linear-gradient(160deg,#0f172a,#1e293b 55%,#0f172a);color:var(--text);min-height:100vh;padding:1.25rem}"
    ".wrap{max-width:28rem;margin:0 auto}"
    ".card{background:var(--card);border:1px solid var(--line);border-radius:1rem;padding:1.25rem;"
    "margin-bottom:1rem;box-shadow:0 12px 40px rgba(0,0,0,.35)}"
    ".label{font-size:.75rem;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin:0 0 .35rem}"
    ".code{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:1.35rem;"
    "font-weight:700;color:var(--accent);word-break:break-all}"
    ".hint{margin:.55rem 0 0;font-size:.85rem;color:var(--muted);line-height:1.4}"
    ".valor{font-size:2.75rem;font-weight:700;letter-spacing:-.03em;margin:.25rem 0}"
    ".meta{font-size:.8rem;color:var(--muted);margin-top:.75rem}"
    ".dot{display:inline-block;width:.55rem;height:.55rem;border-radius:50%;background:var(--ok);"
    "margin-right:.35rem;vertical-align:middle}"
    "</style></head><body><div class='wrap'>"
  );
  html += F("<div class='card'>");
  html += F("<p class='label'>Código do controlador</p>");
  html += "<div class='code' id='codigo'>" + codigoControlador + "</div>";
  html += F(
    "<p class='hint'>"
    "Use este código no cadastro do Production Pulse (campo «Código do controlador»), "
    "junto com IP e nome do dispositivo. Config Wi-Fi/token: API /api/config."
    "</p>"
    "<p class='meta'><span class='dot'></span>Identidade fixa do chip (não muda ao reiniciar)</p>"
    "</div>"
  );
  html += F(
    "<div class='card'>"
    "<p class='label'>Contador</p>"
    "<div class='valor'><span id='c'>0</span></div>"
    "<p class='meta'>Atualização via GET /api/contador (público)</p>"
    "</div>"
  );
  html += F(
    "<script>"
    "async function atualiza(){"
      "try{"
        "const r=await fetch('/api/contador');"
        "if(!r.ok){return;}"
        "const j=await r.json();"
        "document.getElementById('c').innerText=j.contador;"
      "}catch(e){}"
    "}"
    "setInterval(atualiza,500);"
    "atualiza();"
    "</script></div></body></html>"
  );
  return html;
}

void processarBotao(
  int pino,
  bool& estado,
  bool& leituraAnterior,
  unsigned long& tempoRef,
  long delta
) {
  bool leitura = digitalRead(pino);
  if (leitura != leituraAnterior) {
    tempoRef = millis();
  }
  if ((millis() - tempoRef) > cfg.debounceMs) {
    if (leitura != estado) {
      estado = leitura;
      if (estado == LOW) {
        contador += delta;
        Serial.print("Contador: ");
        Serial.println(contador);
      }
    }
  }
  leituraAnterior = leitura;
}

void registrarRotas() {
  const char* tokenHeader = "X-Device-Token";
  const char* headerKeys[] = {tokenHeader};
  server.collectHeaders(headerKeys, 1);

  server.on("/", HTTP_GET, []() {
    server.send(200, "text/html", paginaPrincipal());
  });

  server.on("/api/contador", HTTP_GET, []() {
    // Única rota /api pública — ver contagem sem X-Device-Token
    enviarContador();
  });
  server.on("/api/status", HTTP_GET, enviarStatus);
  server.on("/api/config", HTTP_GET, enviarConfig);
  server.on("/api/config", HTTP_POST, aplicarConfigPost);
  server.on("/api/config", HTTP_OPTIONS, []() {
    enviarCors();
    server.send(204);
  });

  server.on("/api/incrementar", HTTP_POST, []() {
    if (!requireDeviceToken()) {
      return;
    }
    contador++;
    enviarContador();
  });
  server.on("/api/decrementar", HTTP_POST, []() {
    if (!requireDeviceToken()) {
      return;
    }
    contador--;
    enviarContador();
  });
  server.on("/api/reset", HTTP_POST, []() {
    if (!requireDeviceToken()) {
      return;
    }
    contador = 0;
    enviarContador();
  });
  server.on("/api/definir", HTTP_POST, []() {
    if (!requireDeviceToken()) {
      return;
    }
    long valor = parseContadorDoBody();
    if (valor < 0) {
      enviarCors();
      server.send(400, "application/json", "{\"error\":\"informe contador\"}");
      return;
    }
    contador = valor;
    enviarContador();
  });
  server.on("/api/definir", HTTP_OPTIONS, []() {
    enviarCors();
    server.send(204);
  });
  server.on("/api/reboot", HTTP_POST, reiniciarDispositivo);
  server.on("/api/reboot", HTTP_OPTIONS, []() {
    enviarCors();
    server.send(204);
  });
}

void setup() {
  Serial.begin(115200);
  ESP.wdtEnable(8000);
  pinMode(BT_MAIS, INPUT_PULLUP);
  pinMode(BT_MENOS, INPUT_PULLUP);
  codigoControlador = montarCodigoControlador();
  loadConfigFromEeprom();

  WiFi.mode(WIFI_STA);
  WiFi.begin(cfg.ssid, cfg.password);
  lastWifiAttemptMs = millis();
  unsigned long bootStart = millis();
  while (WiFi.status() != WL_CONNECTED && (millis() - bootStart) < WIFI_BOOT_WAIT_MS) {
    delay(200);
    ESP.wdtFeed();
  }

  Serial.println();
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("WiFi conectado");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("WiFi ainda offline — reconnect no loop");
  }
  Serial.print("Codigo controlador: ");
  Serial.println(codigoControlador);
  Serial.print("apiTokenSet: ");
  Serial.println(apiTokenConfigured() ? "true" : "false");

  registrarRotas();
  server.begin();
  Serial.println("Servidor iniciado");
}

void loop() {
  ESP.wdtFeed();
  ensureWifiConnected();
  server.handleClient();
  processarBotao(BT_MAIS, estadoMais, leituraAnteriorMais, tempoMais, +1);
  processarBotao(BT_MENOS, estadoMenos, leituraAnteriorMenos, tempoMenos, -1);
}
