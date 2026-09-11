#include <WiFi.h>
#include <WebServer.h>
#include <ESPmDNS.h>
#include <HTTPClient.h>
#include <WiFiClient.h>
#include <Update.h>
#include <EEPROM.h>
#include <esp_mac.h>
#include <esp_wifi.h>
#include <esp_system.h>
#include <string.h>

// =============================================================================
// Factory defaults (first boot / empty EEPROM) — placeholders only, no secrets
// =============================================================================
static const char* DEFAULT_WIFI_SSID = "YOUR_SSID";
static const char* DEFAULT_WIFI_PASSWORD = "YOUR_PASSWORD";
static const unsigned long DEFAULT_DEBOUNCE_MS = 100;
static const char* FIRMWARE_VERSION = "esp32c3_counter_v1.1.0.0";
// OTA pair identity: V1 green / V2 red (HTML accent + BACKEND_OK RGB).
static const bool VERSION_THEME_IS_RED = false;
static const uint16_t EEPROM_SIZE = 512;
static const uint32_t CONFIG_MAGIC = 0x50504331;  // "PPC1" — distinct from ESP8266 PPS\x02

// Opto-isolated machine inputs (active LOW, INPUT_PULLUP). 3.3 V logic side only.
#define INPUT_1_PIN 0
#define INPUT_2_PIN 1

// External RGB common-cathode: HIGH = channel on (external ~220 Ω per channel).
#define LED_R_PIN 4
#define LED_G_PIN 5
#define LED_B_PIN 6

struct DeviceConfig {
  uint32_t magic;
  char ssid[33];
  char password[65];
  char apiToken[65];
  uint32_t debounceMs;
  char otaBaseUrl[129];  // e.g. http://host/apps/production-pulse-api (no trailing slash)
  char branch[8];        // filial EN "01" / "02"
};

DeviceConfig cfg;

// Persisted outside DeviceConfig (own magic) so Wi-Fi/token layout stays compatible.
static const uint32_t VERSION_HISTORY_MAGIC = 0x50505648;  // "PPVH"
static const int VERSION_HISTORY_EEPROM_OFFSET = 400;

struct VersionHistory {
  uint32_t magic;
  char previousFirmwareVersion[48];
  char lastOtaTargetVersion[48];  // Pulse version string from last successful OTA
};

VersionHistory versionHistory;

long contador = 0;

// Single STA identity source (resolved after WiFi.mode(WIFI_STA)).
uint8_t stationMacBytes[6] = {0};
String stationMacAddress;   // XX:XX:XX:XX:XX:XX
String controllerCode;      // ESP32C3-XXXXXXXXXXXX
String codigoControlador;   // alias — same value as controllerCode

WebServer server(80);

// Input debounce (INPUT_1 increments; INPUT_2 diagnostic only).
bool input1Stable = HIGH;
bool input2Stable = HIGH;
bool input1LastRaw = HIGH;
bool input2LastRaw = HIGH;
unsigned long input1DebounceMs = 0;
unsigned long input2DebounceMs = 0;
int input1RawLevel = 1;
int input2RawLevel = 1;

// Wi-Fi connection state machine — sole owner of WiFi.begin().
enum WifiConnState {
  WIFI_SM_IDLE = 0,
  WIFI_SM_CONNECTING = 1,
  WIFI_SM_CONNECTED = 2,
  WIFI_SM_BACKOFF = 3
};

volatile WifiConnState wifiConnState = WIFI_SM_IDLE;
volatile bool wifiGotIpFlag = false;
volatile bool wifiDisconnectedFlag = false;
volatile uint8_t wifiDisconnectReason = 0;
bool wifiReconnectRequested = false;
unsigned long wifiAttemptStartMs = 0;
unsigned long wifiBackoffUntilMs = 0;
unsigned long wifiBackoffMs = 1000;
static const unsigned long WIFI_BACKOFF_MAX_MS = 30000;
static const unsigned long WIFI_CONNECT_TIMEOUT_MS = 20000;

// Backend freshness (authenticated contact with Minha DELPI / production-pulse-api).
unsigned long lastBackendContactMs = 0;
static const unsigned long BACKEND_FRESHNESS_MS = 120000UL;  // 2 minutes

// Auth / OTA / RGB
bool authErrorLatched = false;
unsigned long authErrorUntilMs = 0;
unsigned long lastOtaCheckMs = 0;
bool otaInProgress = false;
bool otaCheckRequested = false;
unsigned long otaIntervalJitterMs = 0;
unsigned long otaErrorBackoffMs = 0;
unsigned long lastPeriodicStatusMs = 0;
unsigned long rgbLastToggleMs = 0;
bool rgbBlinkPhase = false;

static const unsigned long AUTH_ERROR_HOLD_MS = 5000;
static const unsigned long OTA_CHECK_INTERVAL_MS = 60000;   // 60 s base pull
static const unsigned long OTA_JITTER_MAX_MS = 15000;       // 0–15 s jitter
static const unsigned long OTA_ERROR_BACKOFF_MIN_MS = 60000;
static const unsigned long OTA_ERROR_BACKOFF_MAX_MS = 300000;
static const unsigned long OTA_FIRST_CHECK_MS = 60000;      // 1 min after boot
static const uint32_t OTA_MIN_FREE_HEAP = 20000;
static const unsigned long PERIODIC_STATUS_MS = 10000;
static const unsigned long RGB_BLINK_SLOW_MS = 500;
static const unsigned long RGB_BLINK_FAST_MS = 100;
static const unsigned long RGB_BLINK_OTA_MS = 350;

enum RgbVisualState {
  RGB_OFFLINE = 0,
  RGB_CONNECTING = 1,
  RGB_WIFI_OK_BACKEND_STALE = 2,
  RGB_BACKEND_OK = 3,
  RGB_AUTH_ERROR = 4,
  RGB_OTA_IN_PROGRESS = 5
};

// =============================================================================
// Helpers
// =============================================================================

bool apiTokenConfigured() {
  return cfg.apiToken[0] != '\0';
}

bool passwordConfigured() {
  return cfg.password[0] != '\0';
}

bool isBackendFresh() {
  if (lastBackendContactMs == 0) {
    return false;
  }
  return (millis() - lastBackendContactMs) < BACKEND_FRESHNESS_MS;
}

void noteBackendContact() {
  lastBackendContactMs = millis();
}

void enviarCors() {
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.sendHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  server.sendHeader("Access-Control-Allow-Headers", "Content-Type, X-Device-Token");
}

/**
 * Optional passive freshness on public routes: valid X-Device-Token refreshes
 * lastBackendContactMs without requiring the header.
 */
void maybeNoteBackendContactFromHeader() {
  if (!apiTokenConfigured()) {
    return;
  }
  if (!server.hasHeader("X-Device-Token")) {
    return;
  }
  String got = server.header("X-Device-Token");
  if (got == String(cfg.apiToken)) {
    noteBackendContact();
  }
}

bool requireDeviceToken() {
  if (!apiTokenConfigured()) {
    return true;
  }
  if (!server.hasHeader("X-Device-Token")) {
    authErrorLatched = true;
    authErrorUntilMs = millis() + AUTH_ERROR_HOLD_MS;
    enviarCors();
    server.send(401, "application/json", "{\"error\":\"unauthorized\"}");
    return false;
  }
  String got = server.header("X-Device-Token");
  if (got != String(cfg.apiToken)) {
    authErrorLatched = true;
    authErrorUntilMs = millis() + AUTH_ERROR_HOLD_MS;
    enviarCors();
    server.send(401, "application/json", "{\"error\":\"unauthorized\"}");
    return false;
  }
  noteBackendContact();
  return true;
}

void saveConfigToEeprom() {
  cfg.magic = CONFIG_MAGIC;
  EEPROM.put(0, cfg);
  EEPROM.commit();
}


void saveVersionHistoryToEeprom() {
  versionHistory.magic = VERSION_HISTORY_MAGIC;
  EEPROM.put(VERSION_HISTORY_EEPROM_OFFSET, versionHistory);
  EEPROM.commit();
}

void loadVersionHistoryFromEeprom() {
  VersionHistory loaded;
  EEPROM.get(VERSION_HISTORY_EEPROM_OFFSET, loaded);
  if (loaded.magic != VERSION_HISTORY_MAGIC) {
    memset(&versionHistory, 0, sizeof(versionHistory));
    versionHistory.magic = VERSION_HISTORY_MAGIC;
    saveVersionHistoryToEeprom();
    return;
  }
  versionHistory = loaded;
  versionHistory.previousFirmwareVersion[sizeof(versionHistory.previousFirmwareVersion) - 1] = '\0';
  versionHistory.lastOtaTargetVersion[sizeof(versionHistory.lastOtaTargetVersion) - 1] = '\0';
}

void rememberFirmwareTransition(const String& pulseTargetVersion) {
  strncpy(
    versionHistory.previousFirmwareVersion,
    FIRMWARE_VERSION,
    sizeof(versionHistory.previousFirmwareVersion) - 1
  );
  versionHistory.previousFirmwareVersion[sizeof(versionHistory.previousFirmwareVersion) - 1] = '\0';
  String target = pulseTargetVersion;
  target.trim();
  if (target.length() == 0) {
    target = String(FIRMWARE_VERSION);
  }
  strncpy(
    versionHistory.lastOtaTargetVersion,
    target.c_str(),
    sizeof(versionHistory.lastOtaTargetVersion) - 1
  );
  versionHistory.lastOtaTargetVersion[sizeof(versionHistory.lastOtaTargetVersion) - 1] = '\0';
  saveVersionHistoryToEeprom();
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
    cfg.otaBaseUrl[0] = '\0';
    strncpy(cfg.branch, "01", sizeof(cfg.branch) - 1);
    saveConfigToEeprom();
    return;
  }
  cfg = loaded;
  if (cfg.debounceMs == 0 || cfg.debounceMs > 60000UL) {
    cfg.debounceMs = DEFAULT_DEBOUNCE_MS;
  }
  if (cfg.branch[0] == '\0') {
    strncpy(cfg.branch, "01", sizeof(cfg.branch) - 1);
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

bool extractJsonBool(const String& body, const char* key, bool& value) {
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
  while (start < (int)body.length() && (body[start] == ' ' || body[start] == '\t')) {
    start++;
  }
  if (body.substring(start, start + 4) == "true") {
    value = true;
    return true;
  }
  if (body.substring(start, start + 5) == "false") {
    value = false;
    return true;
  }
  return false;
}

/** Prefer envelope.data payload from Production Pulse API success responses. */
String extractEnvelopeData(const String& body) {
  int dataKey = body.indexOf("\"data\"");
  if (dataKey < 0) {
    return body;
  }
  int colon = body.indexOf(':', dataKey);
  if (colon < 0) {
    return body;
  }
  int start = colon + 1;
  while (start < (int)body.length() && (body[start] == ' ' || body[start] == '\t')) {
    start++;
  }
  if (start >= (int)body.length() || body[start] != '{') {
    return body;
  }
  int depth = 0;
  for (int i = start; i < (int)body.length(); i++) {
    char c = body[i];
    if (c == '{') {
      depth++;
    } else if (c == '}') {
      depth--;
      if (depth == 0) {
        return body.substring(start, i + 1);
      }
    }
  }
  return body;
}

String urlEncodeComponent(const String& value) {
  String out;
  out.reserve(value.length() * 2);
  for (size_t i = 0; i < value.length(); i++) {
    char c = value[i];
    if ((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9')
        || c == '-' || c == '_' || c == '.' || c == '~') {
      out += c;
    } else if (c == ' ') {
      out += "%20";
    } else {
      char buf[4];
      snprintf(buf, sizeof(buf), "%%%02X", (unsigned char)c);
      out += buf;
    }
  }
  return out;
}

bool otaConfigured() {
  return cfg.otaBaseUrl[0] != '\0' && apiTokenConfigured() && cfg.branch[0] != '\0';
}

String otaBaseTrimmed() {
  String base = String(cfg.otaBaseUrl);
  while (base.endsWith("/")) {
    base.remove(base.length() - 1);
  }
  return base;
}

/** Safe OTA base for Serial/HTML: hide URL if it looks like it embeds credentials. */
String otaBaseSafeForDisplay() {
  String base = otaBaseTrimmed();
  if (base.indexOf('@') >= 0) {
    return String("(redacted)");
  }
  return base;
}

void httpEnableRedirects(HTTPClient& http) {
#if defined(HTTPC_STRICT_FOLLOW_REDIRECTS)
  http.setFollowRedirects(HTTPC_STRICT_FOLLOW_REDIRECTS);
#endif
}

// =============================================================================
// Identity (STA MAC single source)
// =============================================================================

void resolveStationIdentity() {
  esp_err_t err = esp_read_mac(stationMacBytes, ESP_MAC_WIFI_STA);
  if (err != ESP_OK) {
    Serial.print("esp_read_mac(ESP_MAC_WIFI_STA) failed: ");
    Serial.println((int)err);
    memset(stationMacBytes, 0, sizeof(stationMacBytes));
  }

  char macBuf[18];
  snprintf(
    macBuf,
    sizeof(macBuf),
    "%02X:%02X:%02X:%02X:%02X:%02X",
    stationMacBytes[0],
    stationMacBytes[1],
    stationMacBytes[2],
    stationMacBytes[3],
    stationMacBytes[4],
    stationMacBytes[5]
  );
  stationMacAddress = String(macBuf);

  char codeBuf[24];
  snprintf(
    codeBuf,
    sizeof(codeBuf),
    "ESP32C3-%02X%02X%02X%02X%02X%02X",
    stationMacBytes[0],
    stationMacBytes[1],
    stationMacBytes[2],
    stationMacBytes[3],
    stationMacBytes[4],
    stationMacBytes[5]
  );
  controllerCode = String(codeBuf);
  codigoControlador = controllerCode;
}

// =============================================================================
// Radio preparation (before any WiFi.begin)
// =============================================================================

void prepareWifiRadio() {
  bool sleepOk = WiFi.setSleep(false);
  Serial.print("WiFi sleep: disabled");
  Serial.print(" (setSleep=");
  Serial.print(sleepOk ? "ok" : "fail");
  Serial.println(")");

  bool txOk = WiFi.setTxPower(WIFI_POWER_8_5dBm);
  Serial.print("WiFi TX power: 8.5 dBm");
  Serial.print(" (setTxPower=");
  Serial.print(txOk ? "ok" : "fail");
  Serial.println(")");
}

// =============================================================================
// Wi-Fi state machine
// =============================================================================

void onWifiArduinoEvent(WiFiEvent_t event, WiFiEventInfo_t info) {
  if (event == ARDUINO_EVENT_WIFI_STA_GOT_IP) {
    wifiGotIpFlag = true;
  } else if (event == ARDUINO_EVENT_WIFI_STA_DISCONNECTED) {
    wifiDisconnectedFlag = true;
    wifiDisconnectReason = info.wifi_sta_disconnected.reason;
  }
}

void requestWifiReconnect() {
  wifiReconnectRequested = true;
}

void startWifiConnectAttempt() {
  wifiGotIpFlag = false;
  wifiDisconnectedFlag = false;
  wifiConnState = WIFI_SM_CONNECTING;
  wifiAttemptStartMs = millis();
  Serial.print("WiFi begin ssid=");
  Serial.println(cfg.ssid);
  WiFi.begin(cfg.ssid, cfg.password);
}

void scheduleWifiBackoff() {
  wifiConnState = WIFI_SM_BACKOFF;
  wifiBackoffUntilMs = millis() + wifiBackoffMs;
  Serial.print("WiFi backoff ms=");
  Serial.println(wifiBackoffMs);
  if (wifiBackoffMs < WIFI_BACKOFF_MAX_MS) {
    unsigned long next = wifiBackoffMs * 2UL;
    wifiBackoffMs = next > WIFI_BACKOFF_MAX_MS ? WIFI_BACKOFF_MAX_MS : next;
  }
}

void ensureWifiStateMachine() {
  // Drain event flags (loop context — safe for Serial / state transitions).
  if (wifiGotIpFlag) {
    wifiGotIpFlag = false;
    wifiConnState = WIFI_SM_CONNECTED;
    wifiBackoffMs = 1000;
    wifiReconnectRequested = false;
    Serial.println("WiFi GOT_IP");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
    Serial.print("Gateway: ");
    Serial.println(WiFi.gatewayIP());
    Serial.print("Channel: ");
    Serial.println(WiFi.channel());
    Serial.print("RSSI: ");
    Serial.println(WiFi.RSSI());
  }

  if (wifiDisconnectedFlag) {
    wifiDisconnectedFlag = false;
    uint8_t reason = wifiDisconnectReason;
    Serial.print("WiFi DISCONNECTED reason=");
    Serial.println(reason);
    if (wifiConnState == WIFI_SM_CONNECTED || wifiConnState == WIFI_SM_CONNECTING) {
      scheduleWifiBackoff();
    }
  }

  if (wifiReconnectRequested) {
    wifiReconnectRequested = false;
    Serial.println("WiFi reconnect requested (config change)");
    if (wifiConnState == WIFI_SM_CONNECTING || wifiConnState == WIFI_SM_CONNECTED) {
      WiFi.disconnect(false, false);
    }
    wifiBackoffMs = 1000;
    wifiConnState = WIFI_SM_IDLE;
  }

  if (wifiConnState == WIFI_SM_CONNECTED) {
    if (WiFi.status() != WL_CONNECTED) {
      scheduleWifiBackoff();
    }
    return;
  }

  if (wifiConnState == WIFI_SM_CONNECTING) {
    if ((millis() - wifiAttemptStartMs) >= WIFI_CONNECT_TIMEOUT_MS) {
      Serial.println("WiFi connect timeout");
      WiFi.disconnect(false, false);
      scheduleWifiBackoff();
    }
    return;
  }

  if (wifiConnState == WIFI_SM_BACKOFF) {
    if ((long)(millis() - wifiBackoffUntilMs) < 0) {
      return;
    }
    wifiConnState = WIFI_SM_IDLE;
  }

  // WIFI_SM_IDLE → start exactly one begin in flight.
  if (wifiConnState == WIFI_SM_IDLE) {
    startWifiConnectAttempt();
  }
}

// =============================================================================
// HTTP / OTA
// =============================================================================

bool httpExchange(
  const String& method,
  const String& url,
  const String& body,
  int& statusCode,
  String& responseBody
) {
  WiFiClient client;
  HTTPClient http;
  http.setTimeout(20000);
  httpEnableRedirects(http);
  if (!http.begin(client, url)) {
    return false;
  }
  http.addHeader("X-Device-Token", String(cfg.apiToken));
  http.addHeader("Accept", "application/json");
  if (method == "POST") {
    http.addHeader("Content-Type", "application/json");
    statusCode = http.POST(body);
  } else {
    statusCode = http.GET();
  }
  responseBody = http.getString();
  http.end();
  return statusCode > 0;
}

bool reportOtaStatus(
  const String& targetId,
  const String& status,
  const String& errorCode,
  const String& installedVersion,
  int bytesReceived = -1,
  int bytesTotal = -1,
  int progressPercent = -1
) {
  if (!otaConfigured()) {
    return false;
  }
  String url = otaBaseTrimmed() + "/device-ota/report";
  String payload = "{";
  payload += "\"controllerCode\":\"" + jsonEscape(controllerCode) + "\",";
  payload += "\"branch\":\"" + jsonEscape(String(cfg.branch)) + "\",";
  if (targetId.length() > 0) {
    payload += "\"targetId\":\"" + jsonEscape(targetId) + "\",";
  }
  payload += "\"status\":\"" + jsonEscape(status) + "\"";
  if (errorCode.length() > 0) {
    payload += ",\"errorCode\":\"" + jsonEscape(errorCode) + "\"";
  }
  if (installedVersion.length() > 0) {
    payload += ",\"installedFirmwareVersion\":\"" + jsonEscape(installedVersion) + "\"";
  }
  if (bytesReceived >= 0) {
    payload += ",\"bytesReceived\":" + String(bytesReceived);
  }
  if (bytesTotal >= 0) {
    payload += ",\"bytesTotal\":" + String(bytesTotal);
  }
  if (progressPercent >= 0) {
    payload += ",\"progressPercent\":" + String(progressPercent);
  }
  payload += "}";
  int code = 0;
  String resp;
  if (!httpExchange("POST", url, payload, code, resp)) {
    Serial.print("OTA report transport fail status=");
    Serial.println(status);
    return false;
  }
  bool ok = code >= 200 && code < 300;
  if (ok) {
    noteBackendContact();
  } else {
    Serial.print("OTA report HTTP ");
    Serial.print(code);
    Serial.print(" body=");
    Serial.println(resp);
  }
  return ok;
}

// Terminal OTA statuses (updated / failed before give-up). Best-effort ACK with
// limited retries; false still allows restart — backend reconcile covers gaps.
// ESP32: yield/delay only (no ESP8266 ESP.wdtFeed).
bool reportTerminalWithRetry(
  const String& targetId,
  const String& status,
  const String& errorCode,
  const String& installedVersion,
  int bytesReceived = -1,
  int bytesTotal = -1,
  int progressPercent = -1
) {
  const int maxAttempts = 3;
  const unsigned long backoffsMs[3] = {200UL, 400UL, 800UL};
  for (int attempt = 0; attempt < maxAttempts; attempt++) {
    if (reportOtaStatus(
          targetId, status, errorCode, installedVersion, bytesReceived, bytesTotal, progressPercent
        )) {
      return true;
    }
    Serial.print("OTA terminal report retry status=");
    Serial.print(status);
    Serial.print(" attempt=");
    Serial.println(attempt + 1);
    delay(backoffsMs[attempt]);
    yield();
  }
  return false;
}

bool applyOtaBinary(const String& artifactUrl, const String& targetId, const String& version) {
  reportOtaStatus(targetId, "downloading", "", "", 0, -1, 0);
  yield();

  WiFiClient client;
  HTTPClient http;
  // HTTPClient timeout is uint16_t ms on Arduino-ESP32 (max 65535).
  http.setTimeout(60000);
  httpEnableRedirects(http);
  if (!http.begin(client, artifactUrl)) {
    reportTerminalWithRetry(targetId, "failed", "http_begin_failed", "");
    return false;
  }
  http.addHeader("X-Device-Token", String(cfg.apiToken));
  int code = http.GET();
  if (code != HTTP_CODE_OK) {
    http.end();
    reportTerminalWithRetry(targetId, "failed", "download_http_" + String(code), "");
    return false;
  }
  int contentLength = http.getSize();
  if (contentLength <= 0) {
    http.end();
    reportTerminalWithRetry(targetId, "failed", "missing_content_length", "");
    return false;
  }
  WiFiClient* stream = http.getStreamPtr();
  if (stream == nullptr) {
    http.end();
    reportTerminalWithRetry(targetId, "failed", "download_stream_null", "");
    return false;
  }

  if (!Update.begin((size_t)contentLength)) {
    http.end();
    reportTerminalWithRetry(targetId, "failed", "update_begin_failed", "");
    return false;
  }

  const size_t BUF_SIZE = 512;
  uint8_t buf[BUF_SIZE];
  size_t written = 0;
  int lastReportedPct = -1;
  unsigned long lastReportMs = 0;
  const unsigned long REPORT_MIN_MS = 2000;
  const int REPORT_STEP_PCT = 5;
  const size_t REPORT_STEP_BYTES = 32UL * 1024UL;

  while (written < (size_t)contentLength) {
    size_t remaining = (size_t)contentLength - written;
    size_t toRead = remaining > BUF_SIZE ? BUF_SIZE : remaining;
    int n = stream->readBytes(buf, toRead);
    if (n <= 0) {
      delay(50);
      yield();
      if (!stream->connected() && stream->available() == 0) {
        break;
      }
      continue;
    }
    size_t w = Update.write(buf, (size_t)n);
    if (w != (size_t)n) {
      http.end();
      Update.end(false);
      reportTerminalWithRetry(targetId, "failed", "update_write_failed", "", (int)written, contentLength, -1);
      return false;
    }
    written += w;
    yield();

    int pct = (int)((written * 100UL) / (size_t)contentLength);
    unsigned long now = millis();
    bool stepPct = pct >= lastReportedPct + REPORT_STEP_PCT;
    bool stepBytes =
      lastReportedPct < 0 ||
      (written % REPORT_STEP_BYTES) < BUF_SIZE ||
      written == (size_t)contentLength;
    bool timeOk = (now - lastReportMs) >= REPORT_MIN_MS;
    if (written == (size_t)contentLength || ((stepPct || stepBytes) && timeOk)) {
      // Progress report uses a second short HTTP; failure must not abort flash.
      reportOtaStatus(targetId, "downloading", "", "", (int)written, contentLength, pct);
      lastReportedPct = pct;
      lastReportMs = now;
    }
  }
  http.end();

  if (written != (size_t)contentLength) {
    Update.end(false);
    reportTerminalWithRetry(targetId, "failed", "download_incomplete", "", (int)written, contentLength, -1);
    return false;
  }

  reportOtaStatus(targetId, "applying", "", "", contentLength, contentLength, 100);
  if (!Update.end(true) || !Update.isFinished()) {
    reportTerminalWithRetry(targetId, "failed", "update_end_failed", "");
    return false;
  }
  // ACK best-effort; restart regardless so we never loop on report failure.
  rememberFirmwareTransition(version);
  reportTerminalWithRetry(targetId, "updated", "", version, contentLength, contentLength, 100);
  delay(200);
  ESP.restart();
  return true;
}

void rollOtaIntervalJitter() {
  otaIntervalJitterMs = (unsigned long)random(0, (long)OTA_JITTER_MAX_MS + 1L);
}

unsigned long otaEffectiveIntervalMs() {
  unsigned long base = OTA_CHECK_INTERVAL_MS + otaIntervalJitterMs;
  if (otaErrorBackoffMs > base) {
    return otaErrorBackoffMs;
  }
  return base;
}

void noteOtaCheckSuccess() {
  otaErrorBackoffMs = 0;
  rollOtaIntervalJitter();
}

void noteOtaCheckError() {
  if (otaErrorBackoffMs == 0) {
    otaErrorBackoffMs = OTA_ERROR_BACKOFF_MIN_MS;
  } else {
    unsigned long next = otaErrorBackoffMs * 2UL;
    otaErrorBackoffMs = next > OTA_ERROR_BACKOFF_MAX_MS ? OTA_ERROR_BACKOFF_MAX_MS : next;
  }
  rollOtaIntervalJitter();
}

void solicitarOtaCheckNow() {
  if (!requireDeviceToken()) {
    return;
  }
  otaCheckRequested = true;
  enviarCors();
  server.send(202, "application/json", "{\"accepted\":true,\"action\":\"ota_check_now\"}");
}

void maybeCheckOta() {
  if (otaInProgress || !otaConfigured()) {
    return;
  }
  if (WiFi.status() != WL_CONNECTED) {
    return;
  }
  if (ESP.getFreeHeap() < OTA_MIN_FREE_HEAP) {
    return;
  }
  unsigned long now = millis();
  bool requested = otaCheckRequested;
  if (!requested) {
    if (lastOtaCheckMs == 0) {
      if (now < OTA_FIRST_CHECK_MS) {
        return;
      }
    } else if ((now - lastOtaCheckMs) < otaEffectiveIntervalMs()) {
      return;
    }
  }

  otaCheckRequested = false;
  lastOtaCheckMs = now;
  otaInProgress = true;
  Serial.println("OTA checking");

  String url = otaBaseTrimmed() + "/device-ota/check?controllerCode="
    + urlEncodeComponent(controllerCode)
    + "&branch=" + urlEncodeComponent(String(cfg.branch));
  int code = 0;
  String resp;
  if (!httpExchange("GET", url, "", code, resp) || code != HTTP_CODE_OK) {
    Serial.print("OTA check HTTP ");
    Serial.println(code);
    noteOtaCheckError();
    otaInProgress = false;
    return;
  }
  noteBackendContact();

  String dataJson = extractEnvelopeData(resp);
  bool available = false;
  if (!extractJsonBool(dataJson, "updateAvailable", available) || !available) {
    Serial.println("OTA no update");
    noteOtaCheckSuccess();
    otaInProgress = false;
    return;
  }

  String token = extractJsonString(dataJson, "artifactToken");
  String targetId = extractJsonString(dataJson, "targetId");
  String version = extractJsonString(dataJson, "version");
  if (token.length() == 0) {
    reportOtaStatus(targetId, "failed", "missing_artifact_token", "");
    noteOtaCheckError();
    otaInProgress = false;
    return;
  }

  noteOtaCheckSuccess();
  String artifactUrl = otaBaseTrimmed() + "/device-ota/artifacts/" + urlEncodeComponent(token)
    + "?controllerCode=" + urlEncodeComponent(controllerCode)
    + "&branch=" + urlEncodeComponent(String(cfg.branch));
  Serial.print("OTA applying version=");
  Serial.println(version);
  applyOtaBinary(artifactUrl, targetId, version);
  otaInProgress = false;
}

// =============================================================================
// HTTP handlers
// =============================================================================

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
  maybeNoteBackendContactFromHeader();
  enviarCors();
  String json =
    "{"
    "\"contador\":" + String(contador) + ","
    "\"hardwareUid\":\"" + controllerCode + "\","
    "\"controllerCode\":\"" + controllerCode + "\","
    "\"codigoControlador\":\"" + controllerCode + "\","
    "\"mac\":\"" + stationMacAddress + "\""
    "}";
  server.send(200, "application/json", json);
}

void enviarStatus() {
  if (!requireDeviceToken()) {
    return;
  }
  enviarCors();
  bool wifiOk = WiFi.status() == WL_CONNECTED;
  String json =
    "{"
    "\"hardwareUid\":\"" + controllerCode + "\","
    "\"codigoControlador\":\"" + controllerCode + "\","
    "\"controllerCode\":\"" + controllerCode + "\","
    "\"equipamento\":\"" + controllerCode + "\","
    "\"contador\":" + String(contador) + ","
    "\"ip\":\"" + WiFi.localIP().toString() + "\","
    "\"mac\":\"" + stationMacAddress + "\","
    "\"status\":\"online\","
    "\"firmwareVersion\":\"" + String(FIRMWARE_VERSION) + "\","
    "\"previousFirmwareVersion\":\"" + jsonEscape(String(versionHistory.previousFirmwareVersion)) + "\","
    "\"lastOtaTargetVersion\":\"" + jsonEscape(String(versionHistory.lastOtaTargetVersion)) + "\","
    "\"uptimeMs\":" + String(millis()) + ","
    "\"freeHeap\":" + String(ESP.getFreeHeap()) + ","
    "\"rssi\":" + String(wifiOk ? WiFi.RSSI() : 0) + ","
    "\"wifiConnected\":" + String(wifiOk ? "true" : "false") + ","
    "\"input1\":" + String(input1RawLevel) + ","
    "\"input2\":" + String(input2RawLevel) +
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
    "\"otaBaseUrl\":\"" + jsonEscape(String(cfg.otaBaseUrl)) + "\","
    "\"branch\":\"" + jsonEscape(String(cfg.branch)) + "\","
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

  String newOtaBase = extractJsonString(body, "otaBaseUrl");
  if (body.indexOf("\"otaBaseUrl\"") >= 0) {
    strncpy(cfg.otaBaseUrl, newOtaBase.c_str(), sizeof(cfg.otaBaseUrl) - 1);
    cfg.otaBaseUrl[sizeof(cfg.otaBaseUrl) - 1] = '\0';
    touched = true;
  }

  String newBranch = extractJsonString(body, "branch");
  if (newBranch.length() > 0) {
    strncpy(cfg.branch, newBranch.c_str(), sizeof(cfg.branch) - 1);
    cfg.branch[sizeof(cfg.branch) - 1] = '\0';
    touched = true;
  }

  if (!touched) {
    enviarCors();
    server.send(400, "application/json", "{\"error\":\"no_fields\"}");
    return;
  }

  saveConfigToEeprom();

  if (wifiChanged) {
    // Reconnect only via state machine — never WiFi.begin() in HTTP handler.
    requestWifiReconnect();
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

void restoreFactoryConfig() {
  memset(&cfg, 0, sizeof(cfg));
  cfg.magic = CONFIG_MAGIC;
  strncpy(cfg.ssid, DEFAULT_WIFI_SSID, sizeof(cfg.ssid) - 1);
  strncpy(cfg.password, DEFAULT_WIFI_PASSWORD, sizeof(cfg.password) - 1);
  cfg.apiToken[0] = '\0';
  cfg.debounceMs = DEFAULT_DEBOUNCE_MS;
  cfg.otaBaseUrl[0] = '\0';
  strncpy(cfg.branch, "01", sizeof(cfg.branch) - 1);
  saveConfigToEeprom();
}

void aplicarFactoryReset() {
  if (!requireDeviceToken()) {
    return;
  }
  restoreFactoryConfig();
  enviarCors();
  server.send(
    200,
    "application/json",
    "{\"ok\":true,\"action\":\"factory_reset\",\"note\":\"counter RAM cleared on restart\"}"
  );
  delay(80);
  ESP.restart();
}

// =============================================================================
// RGB (single owner of GPIO4/5/6 writes)
// =============================================================================

void writeRgbChannels(bool r, bool g, bool b) {
  digitalWrite(LED_R_PIN, r ? HIGH : LOW);
  digitalWrite(LED_G_PIN, g ? HIGH : LOW);
  digitalWrite(LED_B_PIN, b ? HIGH : LOW);
}

RgbVisualState resolveRgbVisualState() {
  if (authErrorLatched && (long)(millis() - authErrorUntilMs) >= 0) {
    authErrorLatched = false;
  }

  // Priority: auth/failure > OTA > connecting/offline > connected/backend freshness
  if (authErrorLatched) {
    return RGB_AUTH_ERROR;
  }
  if (otaInProgress) {
    return RGB_OTA_IN_PROGRESS;
  }
  if (wifiConnState == WIFI_SM_CONNECTING || wifiConnState == WIFI_SM_BACKOFF
      || wifiConnState == WIFI_SM_IDLE) {
    if (WiFi.status() != WL_CONNECTED) {
      if (wifiConnState == WIFI_SM_IDLE && millis() < 2000UL) {
        return RGB_OFFLINE;
      }
      return RGB_CONNECTING;
    }
  }
  if (WiFi.status() != WL_CONNECTED) {
    return RGB_OFFLINE;
  }
  if (isBackendFresh()) {
    return RGB_BACKEND_OK;
  }
  // Connected but never contacted, or freshness expired → stale (solid then blink).
  if (lastBackendContactMs == 0) {
    return RGB_WIFI_OK_BACKEND_STALE;  // solid blue until first contact
  }
  return RGB_WIFI_OK_BACKEND_STALE;    // blink blue when expired (pattern differs below)
}

void updateRgbState() {
  RgbVisualState state = resolveRgbVisualState();
  unsigned long now = millis();
  unsigned long interval = RGB_BLINK_SLOW_MS;
  bool r = false;
  bool g = false;
  bool b = false;
  bool solid = false;

  switch (state) {
    case RGB_AUTH_ERROR:
      interval = RGB_BLINK_FAST_MS;
      r = true;
      break;
    case RGB_OTA_IN_PROGRESS:
      interval = RGB_BLINK_OTA_MS;
      r = true;
      g = true;  // yellow/orange
      break;
    case RGB_CONNECTING:
      interval = RGB_BLINK_SLOW_MS;
      r = true;
      break;
    case RGB_OFFLINE:
      solid = true;
      r = true;
      break;
    case RGB_BACKEND_OK:
      solid = true;
      if (VERSION_THEME_IS_RED) {
        r = true;  // V2 brand = red (auth error uses fast blink red)
      } else {
        g = true;  // V1 brand = green
      }
      break;
    case RGB_WIFI_OK_BACKEND_STALE:
      if (lastBackendContactMs == 0) {
        // Wi-Fi OK, never contacted backend yet → solid blue
        solid = true;
        b = true;
      } else {
        // Freshness expired → blinking blue
        interval = RGB_BLINK_SLOW_MS;
        b = true;
      }
      break;
    default:
      solid = true;
      r = true;
      break;
  }

  if (solid) {
    writeRgbChannels(r, g, b);
    return;
  }

  if ((now - rgbLastToggleMs) < interval) {
    return;
  }
  rgbLastToggleMs = now;
  rgbBlinkPhase = !rgbBlinkPhase;
  if (rgbBlinkPhase) {
    writeRgbChannels(r, g, b);
  } else {
    writeRgbChannels(false, false, false);
  }
}

// =============================================================================
// Inputs
// =============================================================================

void processInput1Pulse() {
  bool leitura = digitalRead(INPUT_1_PIN);
  input1RawLevel = (leitura == LOW) ? 0 : 1;
  if (leitura != input1LastRaw) {
    input1DebounceMs = millis();
  }
  if ((millis() - input1DebounceMs) > cfg.debounceMs) {
    if (leitura != input1Stable) {
      input1Stable = leitura;
      if (input1Stable == LOW) {
        contador += 1;
        Serial.print("Contador: ");
        Serial.println(contador);
      }
    }
  }
  input1LastRaw = leitura;
}

void processInput2Diagnostic() {
  bool leitura = digitalRead(INPUT_2_PIN);
  input2RawLevel = (leitura == LOW) ? 0 : 1;
  if (leitura != input2LastRaw) {
    input2DebounceMs = millis();
  }
  if ((millis() - input2DebounceMs) > cfg.debounceMs) {
    if (leitura != input2Stable) {
      input2Stable = leitura;
      // Diagnostic only — never mutates contador.
    }
  }
  input2LastRaw = leitura;
}

// =============================================================================
// HTML maintenance page
// =============================================================================

String paginaPrincipal() {
  // Arduino IDE 1.x corrupts literal HTML closing tags in .ino — always split: "</" "tag>"
  bool wifiOk = WiFi.status() == WL_CONNECTED;
  String html;
  html.reserve(4200);
  html += "<!DOCTYPE html><html lang='pt-BR'><head>";
  html += "<meta charset='utf-8'/>";
  html += "<meta name='viewport' content='width=device-width,initial-scale=1'/>";
  html += "<title>Production Pulse - Contador V1 Verde</" "title><style>";
  html += ":root{--bg:#0b1220;--card:#111827;--line:#334155;--text:#e2e8f0;--muted:#94a3b8;--accent:#22c55e;--ok:#4ade80;}";
  html += "*{box-sizing:border-box}";
  html += "body{margin:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;";
  html += "background:linear-gradient(160deg,#052e1f,#0b1220 55%,#052e1f);color:var(--text);min-height:100vh;padding:1.25rem}";
  html += ".wrap{max-width:28rem;margin:0 auto}";
  html += ".badge{display:inline-block;padding:.2rem .55rem;border-radius:999px;border:1px solid var(--accent);";
  html += "color:var(--accent);font-size:.75rem;letter-spacing:.08em;text-transform:uppercase;margin-bottom:.75rem}";
  html += ".card{background:var(--card);border:1px solid var(--line);border-radius:1rem;padding:1.25rem;";
  html += "margin-bottom:1rem;box-shadow:0 12px 40px rgba(0,0,0,.35)}";
  html += ".label{font-size:.75rem;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin:0 0 .35rem}";
  html += ".code{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:1.15rem;";
  html += "font-weight:700;color:var(--accent);word-break:break-all}";
  html += ".hint{margin:.55rem 0 0;font-size:.85rem;color:var(--muted);line-height:1.4}";
  html += ".valor{font-size:2.75rem;font-weight:700;letter-spacing:-.03em;margin:.25rem 0}";
  html += ".meta{font-size:.8rem;color:var(--muted);margin-top:.55rem;line-height:1.5}";
  html += ".dot{display:inline-block;width:.55rem;height:.55rem;border-radius:50%;background:var(--ok);";
  html += "margin-right:.35rem;vertical-align:middle}";
  html += "</" "style></" "head><body><div class='wrap'>";
  html += "<div class='badge'>V1 · Verde · C3</" "div>";
  html += "<div class='card'>";
  html += "<p class='label'>Firmware instalado</" "p>";
  html += "<div class='code'>";
  html += FIRMWARE_VERSION;
  html += "</" "div>";
  html += "<p class='hint'>Versao em execucao (binario atual).</" "p>";
  html += "<p class='label' style='margin-top:1rem'>Versao anterior</" "p>";
  html += "<div class='code'>";
  html += (versionHistory.previousFirmwareVersion[0]
    ? String(versionHistory.previousFirmwareVersion)
    : String("— (nenhum OTA ainda)"));
  html += "</" "div>";
  html += "<p class='hint'>Gravada no chip antes do ultimo OTA bem-sucedido (permite ver se voltou a uma versao anterior).</" "p>";
  html += "<p class='label' style='margin-top:1rem'>Alvo do ultimo OTA (Pulse)</" "p>";
  html += "<div class='code'>";
  html += (versionHistory.lastOtaTargetVersion[0]
    ? String(versionHistory.lastOtaTargetVersion)
    : String("—"));
  html += "</" "div>";
  html += "<p class='hint'>Versao autorizada pelo Pulse na ultima atualizacao.</" "p>";
  html += "</" "div>";
  html += "<div class='card'>";
  html += "<p class='label'>Codigo do controlador</" "p>";
  html += "<div class='code' id='codigo'>";
  html += controllerCode;
  html += "</" "div>";
  html += "<p class='meta'>STA MAC: <span id='mac'>";
  html += stationMacAddress;
  html += "</" "span></" "p>";
  html += "<p class='meta'>IP: <span id='ip'>";
  html += (wifiOk ? WiFi.localIP().toString() : String("-"));
  html += "</" "span></" "p>";
  html += "<p class='meta'>Wi-Fi: <span id='wifi'>";
  html += (wifiOk ? "conectado" : "offline");
  html += "</" "span> | RSSI: <span id='rssi'>";
  html += String(wifiOk ? WiFi.RSSI() : 0);
  html += "</" "span></" "p>";
  html += "<p class='meta'>API Token: ";
  html += (apiTokenConfigured() ? "configurado" : "nao configurado");
  html += "</" "p>";
  html += "<p class='meta'>OTA base: ";
  html += (otaConfigured() || cfg.otaBaseUrl[0] != '\0' ? otaBaseSafeForDisplay() : String("nao configurado"));
  html += "</" "p>";
  html += "<p class='meta'>OTA state: <span id='ota'>";
  html += (otaInProgress ? "in_progress" : "idle");
  html += "</" "span></" "p>";
  html += "<p class='meta'><i class='dot'></" "i>Uptime ms: <span id='up'>0</" "span></" "p>";
  html += "</" "div>";
  html += "<div class='card'>";
  html += "<p class='label'>Contador C3</" "p>";
  html += "<div class='valor' id='c'>0</" "div>";
  html += "<p class='meta'>Atualizacao via GET /api/contador (publico)</" "p>";
  html += "</" "div>";
  html += "<script>";
  html += "async function atualiza(){";
  html += "try{";
  html += "var r=await fetch('/api/contador');";
  html += "if(!r.ok){return;}";
  html += "var j=await r.json();";
  html += "document.getElementById('c').innerText=j.contador;";
  html += "}catch(e){}";
  html += "document.getElementById('up').innerText=String(Date.now()%100000000);";
  html += "}";
  html += "setInterval(atualiza,500);";
  html += "atualiza();";
  html += "</" "script></" "div></" "body></" "html>";
  return html;
}

void registrarRotas() {
  // ESP32 Arduino Core 3.x: collectHeaders variadic.
  const char* headerKeys[] = {"X-Device-Token"};
  server.collectHeaders(headerKeys, 1);

  server.on("/", HTTP_GET, []() {
    server.send(200, "text/html", paginaPrincipal());
  });

  server.on("/api/contador", HTTP_GET, []() {
    // Unique public /api route — count without requiring X-Device-Token
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
  server.on("/api/factory-reset", HTTP_POST, aplicarFactoryReset);
  server.on("/api/factory-reset", HTTP_OPTIONS, []() {
    enviarCors();
    server.send(204);
  });
  server.on("/api/ota/check-now", HTTP_POST, solicitarOtaCheckNow);
  server.on("/api/ota/check-now", HTTP_OPTIONS, []() {
    enviarCors();
    server.send(204);
  });
}

void logPeriodicStatus() {
  unsigned long now = millis();
  if ((now - lastPeriodicStatusMs) < PERIODIC_STATUS_MS) {
    return;
  }
  lastPeriodicStatusMs = now;
  bool wifiOk = WiFi.status() == WL_CONNECTED;
  Serial.print("status uptimeMs=");
  Serial.print(now);
  Serial.print(" wifi=");
  Serial.print(wifiOk ? "1" : "0");
  Serial.print(" sm=");
  Serial.print((int)wifiConnState);
  Serial.print(" rssi=");
  Serial.print(wifiOk ? WiFi.RSSI() : 0);
  Serial.print(" heap=");
  Serial.print(ESP.getFreeHeap());
  Serial.print(" fw=");
  Serial.print(FIRMWARE_VERSION);
  Serial.print(" backendFresh=");
  Serial.print(isBackendFresh() ? "1" : "0");
  Serial.print(" in1=");
  Serial.print(input1RawLevel);
  Serial.print(" in2=");
  Serial.println(input2RawLevel);
}

void logBootBanner() {
  Serial.println();
  Serial.println("=== Production Pulse ESP32-C3 ===");
  Serial.print("firmware: ");
  Serial.println(FIRMWARE_VERSION);
  Serial.print("chip: ");
  Serial.print(ESP.getChipModel());
  Serial.print(" rev=");
  Serial.println(ESP.getChipRevision());
  Serial.print("resetReason: ");
  Serial.println((int)esp_reset_reason());
  Serial.print("MAC WIFI STA - ENVIAR PARA TI: ");
  Serial.println(stationMacAddress);
  Serial.print("controllerCode: ");
  Serial.println(controllerCode);
  Serial.print("ssid: ");
  Serial.println(cfg.ssid);
  Serial.print("apiToken: ");
  Serial.println(apiTokenConfigured() ? "configurado" : "nao configurado");
  Serial.print("ota: ");
  Serial.println(otaConfigured() ? "configurado" : "nao configurado");
  if (cfg.otaBaseUrl[0] != '\0') {
    Serial.print("otaBaseUrl: ");
    Serial.println(otaBaseSafeForDisplay());
  }
  Serial.print("branch: ");
  Serial.println(cfg.branch);
  Serial.print("freeHeap: ");
  Serial.println(ESP.getFreeHeap());
  Serial.print("BACKEND_FRESHNESS_MS: ");
  Serial.println(BACKEND_FRESHNESS_MS);
}

// =============================================================================
// setup / loop
// =============================================================================

void setup() {
  Serial.begin(115200);
  delay(200);
  randomSeed((uint32_t)esp_random());
  rollOtaIntervalJitter();

  pinMode(LED_R_PIN, OUTPUT);
  pinMode(LED_G_PIN, OUTPUT);
  pinMode(LED_B_PIN, OUTPUT);
  writeRgbChannels(true, false, false);  // solid red at boot

  pinMode(INPUT_1_PIN, INPUT_PULLUP);
  pinMode(INPUT_2_PIN, INPUT_PULLUP);
  input1LastRaw = digitalRead(INPUT_1_PIN);
  input2LastRaw = digitalRead(INPUT_2_PIN);
  input1Stable = input1LastRaw;
  input2Stable = input2LastRaw;
  input1RawLevel = (input1LastRaw == LOW) ? 0 : 1;
  input2RawLevel = (input2LastRaw == LOW) ? 0 : 1;

  loadConfigFromEeprom();
  loadVersionHistoryFromEeprom();

  WiFi.mode(WIFI_STA);
  resolveStationIdentity();
  prepareWifiRadio();
  logBootBanner();

  WiFi.onEvent(onWifiArduinoEvent);
  // First association goes through the state machine (idle → connecting → begin).
  wifiConnState = WIFI_SM_IDLE;
  ensureWifiStateMachine();

  registrarRotas();
  server.begin();
  Serial.println("Servidor iniciado");

  String mdnsHost = controllerCode;
  mdnsHost.replace(":", "-");
  mdnsHost.toLowerCase();
  if (MDNS.begin(mdnsHost.c_str())) {
    MDNS.addService("http", "tcp", 80);
    Serial.print("mDNS: http://");
    Serial.print(mdnsHost);
    Serial.println(".local");
  } else {
    Serial.println("mDNS falhou");
  }
}

void loop() {
  ensureWifiStateMachine();
  updateRgbState();
  server.handleClient();
  maybeCheckOta();
  processInput1Pulse();
  processInput2Diagnostic();
  logPeriodicStatus();
  // ESP32 mDNS does not require MDNS.update() in loop (unlike ESP8266).
}
