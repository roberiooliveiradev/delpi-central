# Plano de implementação — firmware ESP32-C3 Super Mini

> **Status:** plano executável; revalidar regras/código antes de cada `E*.S*`.
>
> **Pai:** [`ESP32C3-SUPER-MINI-MASTER-PLAN.md`](./ESP32C3-SUPER-MINI-MASTER-PLAN.md)

## Overview

Criar `esp32c3_counter_v1` a partir do firmware ESP8266 V2 atual, preservando protocolo HTTP, configuração, token e OTA, enquanto substitui somente responsabilidades específicas da plataforma/hardware e adiciona os diagnósticos e I/Os da Super Mini V1601.

## Evidências de ownership

- `firmware/esp8266_counter_v2/esp8266_counter_v2.ino` é o firmware irmão vigente e já contém o fluxo completo que deve ser preservado.
- A `production-pulse-api` consome o device por contrato HTTP, não por internals do sketch.
- `device_http_support.py` envia `X-Device-Token` nas chamadas do BFF quando configurado.
- O contrato OTA atual já é pull-based; esta entrega não cria novo canal.

## Invariantes

1. Servidor permanece na porta 80.
2. Endpoints `/api/*` existentes não são renomeados/removidos.
3. Campos existentes do status mantêm nome e semântica.
4. `cfg.apiToken` e `X-Device-Token` permanecem.
5. `INPUT_2` não altera `counter` nesta versão.
6. Sinais de máquina jamais acionam factory reset físico.
7. Nenhuma senha/token/artifact token é exibido.
8. OTA continua usando `/device-ota/*` da `production-pulse-api`.

## Delta de contrato

Classificação: **ADDITIVE + implementação de novo driver/hardware**.

Campos novos previstos em `/api/status`:

```json
{
  "input1": 1,
  "input2": 1
}
```

Semântica: nível lógico bruto, `0 = LOW/ativo`, `1 = HIGH/inativo`. Consumidores antigos podem ignorá-los.

Nenhum endpoint novo é necessário.

---

# E1 — Baseline C3, build e identidade

## E1.S1 — Criar a família de firmware C3 a partir da V2

**Objetivo**  
Criar a pasta/sketch/README do C3 preservando a estrutura funcional da V2 e substituindo apenas includes/APIs específicos de ESP8266.

**Requisitos cobertos**  
RQ-01, RQ-02, RQ-08, RQ-09, RQ-16.

**Fazer**

- criar `docs/12-roadmap-e-evolucao/production-pulse/firmware/esp32c3_counter_v1/`;
- criar `esp32c3_counter_v1.ino` tendo a V2 como base de comportamento;
- usar identificadores novos em inglês;
- trocar bibliotecas de plataforma por `WiFi.h`, `WebServer.h`, `ESPmDNS.h`, `HTTPClient.h`, `WiFiClient.h`, `Update.h`, `EEPROM.h` e headers ESP32 estritamente necessários;
- manter `DeviceConfig` e persistência de `ssid`, `password`, `apiToken`, `debounceMs`, `otaBaseUrl`, `branch`;
- manter servidor HTTP na porta 80 e rotas existentes;
- definir família/versão `esp32c3_counter_v1` / `esp32c3_counter_v1.0.0`;
- documentar no README o perfil de build: ESP32C3 Dev Module, core 3.3.11, 160 MHz, flash 4 MB, QIO, 80 MHz, upload 115200, esquema OTA validado em E4.S2.

**Não fazer**

- não alterar o sketch ESP8266 para compartilhar código prematuramente;
- não criar framework/HAL novo;
- não renomear JSON/rotas;
- não adicionar secrets reais ao sketch/README.

**Evidência**  
A V2 contém o pipeline funcional completo. O port é responsabilidade do firmware; não exige novo endpoint para representar o novo MCU.

**Dependências**  
Nenhuma.

**Teste**

- compilar o sketch no perfil alvo com Arduino Core 3.3.11;
- conferir ausência de includes `ESP8266*`/`Updater.h` específicos do firmware anterior;
- positive: build C3 fecha sem alterar contrato das rotas;
- sibling: sketch ESP8266 permanece byte-for-byte fora do diff desta subetapa;
- negative: nenhum secret literal real aparece nos novos arquivos.

**Pronto quando**  
O novo sketch compila no target C3, mantém a lista de endpoints e não altera o firmware ESP8266.

**Commit sugerido**  
`feat: cria base do contador para ESP32-C3 sem alterar contratos`

## E1.S2 — Tornar STA MAC a fonte única de identidade

**Objetivo**  
Gerar MAC operacional e controller code a partir da interface Wi-Fi Station, com representação idêntica no status, HTML e Serial.

**Requisitos cobertos**  
RQ-03, RQ-04.

**Fazer**

- executar `WiFi.mode(WIFI_STA)` antes de resolver a identidade;
- obter explicitamente os bytes do Wi-Fi Station MAC usando a API ESP32 de MAC para `ESP_MAC_WIFI_STA` e armazená-los em uma única representação canônica em memória;
- produzir `stationMacAddress` no formato `XX:XX:XX:XX:XX:XX`;
- produzir `controllerCode` no formato `ESP32C3-XXXXXXXXXXXX`, derivado dos mesmos bytes, uppercase e sem separadores;
- continuar emitindo `codigoControlador`, `controllerCode` e `equipamento` com o mesmo `controllerCode`;
- registrar `MAC WIFI STA - ENVIAR PARA TI: ...` no boot;
- mDNS deve continuar derivado da identidade estável e sanitizada, sem criar segunda identidade.

**Não fazer**

- não usar base MAC/AP MAC/Bluetooth MAC;
- não chamar `ESP.getChipId()`;
- não calcular MAC de uma fonte e controller code de outra;
- não criar migration: `controller_code VARCHAR(64)` já comporta o valor.

**Evidência**  
O backend trata controller code como string de até 64 caracteres e aceita os aliases atuais. O requisito operacional de DHCP exige a interface Station.

**Dependências**  
E1.S1.

**Teste**

- compile gate da API usada para `ESP_MAC_WIFI_STA` no core 3.3.11;
- positive live em E6: Serial, `/api/status` e HTML exibem exatamente o mesmo STA MAC;
- sibling: aliases de controller code continuam iguais;
- negative: nenhuma representação de AP/base MAC é exposta como `mac`.

**Pronto quando**  
Existe uma única fonte de bytes STA para todas as superfícies de identidade.

**Commit sugerido**  
`feat: usa MAC Wi-Fi Station como identidade do ESP32-C3`

---

# E2 — Rádio e reconexão Wi-Fi

## E2.S1 — Aplicar configuração obrigatória do rádio antes da associação

**Objetivo**  
Garantir que a Super Mini V1601 tente associação somente depois de sleep off e TX power 8,5 dBm.

**Requisitos cobertos**  
RQ-05, RQ-18.

**Fazer**

- após `WiFi.mode(WIFI_STA)` e antes de qualquer `WiFi.begin()` executar `WiFi.setSleep(false)` e `WiFi.setTxPower(WIFI_POWER_8_5dBm)`;
- concentrar essa preparação em função única de inicialização do rádio;
- verificar/registrar sucesso das configurações quando a API do core retornar status;
- registrar no Serial `WiFi sleep: disabled` e `WiFi TX power: 8.5 dBm` somente após aplicar as configurações;
- nunca reconfigurar potência no loop normal sem causa.

**Não fazer**

- não alterar potência do firmware ESP8266;
- não aplicar configuração depois de `WiFi.begin()`;
- não criar retries de radio-config em loop apertado.

**Evidência**  
A restrição é específica da variante física Super Mini V1601 testada e pertence ao firmware, não à API/MFE.

**Dependências**  
E1.S2.

**Teste**

- build C3;
- positive live: boot log confirma ordem modo STA → radio config → connect;
- sibling: segundo C3 usa o mesmo caminho sem configuração por device;
- negative: inspeção garante que não existe `WiFi.begin()` antes da preparação do rádio.

**Pronto quando**  
Toda tentativa inicial nasce após a preparação obrigatória do rádio.

**Commit sugerido**  
`fix: estabiliza rádio Wi-Fi da Super Mini em 8,5 dBm`

## E2.S2 — Implementar máquina de conexão sem tentativa concorrente

**Objetivo**  
Eliminar `WiFi.begin()` durante tentativa ativa e preservar backoff controlado.

**Requisitos cobertos**  
RQ-06, RQ-18.

**Fazer**

- modelar estados de conexão equivalentes a `idle`, `connecting`, `connected`, `backoff`;
- registrar handlers de eventos Wi-Fi do Arduino ESP32;
- ao iniciar tentativa, marcar `connecting` e guardar deadline;
- chamar `WiFi.begin()` somente na transição `idle/backoff → connecting`;
- em `ARDUINO_EVENT_WIFI_STA_GOT_IP`, transicionar para `connected`, resetar backoff e registrar IP/gateway/channel/RSSI;
- em `ARDUINO_EVENT_WIFI_STA_DISCONNECTED`, registrar `reason code`, encerrar tentativa e entrar em backoff;
- em timeout de conexão, cancelar/encerrar a tentativa uma única vez e entrar em backoff;
- usar backoff exponencial com teto equivalente ao V2 atual, sem retry storm;
- tratar wrap de `millis()` com diferenças unsigned, não comparações absolutas frágeis.

**Não fazer**

- não chamar `WiFi.begin()` enquanto `connecting`;
- não chamar `WiFi.disconnect()/begin()` a cada tick;
- não bloquear o loop por períodos longos;
- não esconder reason code com mensagem genérica.

**Evidência**  
O V2 atual chama `disconnect/begin` por timer; o problema observado nasce de nova configuração enquanto a STA ainda conecta.

**Dependências**  
E2.S1.

**Teste**

- build C3;
- positive live: conexão inicial e reconexão completam;
- sibling: perda de AP e restauração seguem o mesmo state machine;
- negative live: não aparece `wifi:sta is connecting, cannot set config`; reason code aparece na desconexão;
- soak curto: alternar AP/hotspot repetidamente sem aumento de frequência de attempts além do backoff.

**Pronto quando**  
Há no máximo uma tentativa em voo e todo retry nasce de estado/backoff explícitos.

**Commit sugerido**  
`fix: evita tentativas Wi-Fi concorrentes no ESP32-C3`

## E2.S3 — Fazer reconfiguração Wi-Fi reutilizar a máquina de conexão

**Objetivo**  
Impedir que `POST /api/config` contorne o state machine ao trocar SSID/senha.

**Requisitos cobertos**  
RQ-02, RQ-06, RQ-07.

**Fazer**

- preservar payload e persistência atual de `/api/config`;
- após salvar mudança de Wi-Fi, solicitar uma reconexão ao owner da máquina de conexão;
- o owner deve encerrar a sessão atual e iniciar nova tentativa somente pela transição oficial;
- responder a configuração conforme contrato atual sem vazar password/token.

**Não fazer**

- não deixar `WiFi.begin()` dentro do handler HTTP;
- não mudar nomes `ssid`, `password`, `apiToken`, `debounceMs`, `otaBaseUrl`, `branch`;
- não devolver valores de secrets.

**Evidência**  
O V2 chama `disconnect(true)` e `WiFi.begin()` diretamente no handler; no C3 isso duplicaria a origem de tentativas.

**Dependências**  
E2.S2.

**Teste**

- positive: mudar SSID dispara exatamente uma nova tentativa pelo state machine;
- sibling: alterar somente debounce/token/branch não reinicia Wi-Fi;
- negative: senha não aparece em response/log.

**Pronto quando**  
Existe uma única origem de `WiFi.begin()` em runtime.

**Commit sugerido**  
`refactor: centraliza reconexão Wi-Fi após configuração`

---

# E3 — Entradas, factory reset, backend freshness e RGB

## E3.S1 — Portar debounce para duas entradas active-low sem mudar semântica do contador

**Objetivo**  
Usar GPIO0 como pulso principal e GPIO1 como entrada reservada, contando uma única vez por acionamento estável LOW.

**Requisitos cobertos**  
RQ-11, RQ-12, RQ-13, RQ-16.

**Fazer**

- definir `INPUT_1_PIN = 0`, `INPUT_2_PIN = 1`;
- configurar entradas com pull-up conforme contrato elétrico de 3,3 V;
- representar leitura raw separada do estado debounced;
- incrementar `counter` somente na transição debounced para LOW de INPUT_1;
- não decrementar automaticamente por INPUT_2;
- manter INPUT_2 atualizado para diagnóstico;
- adicionar `input1` e `input2` ao `/api/status` como `0|1` raw;
- usar `cfg.debounceMs` existente.

**Não fazer**

- não contar continuamente enquanto INPUT_1 permanece LOW;
- não atribuir comando a INPUT_2 nesta versão;
- não usar GPIO2/8/9 ou 20/21 para substituir os pinos definidos;
- não ligar lógica industrial diretamente ao MCU; README deve registrar isolamento 3,3 V.

**Evidência**  
O contador atual já implementa debounce por mudança estável; o port deve preservar essa semântica e remover somente o segundo botão de decremento físico.

**Dependências**  
E1.S1.

**Teste**

- positive live: HIGH→LOW estável em INPUT_1 incrementa uma vez;
- sibling: novo HIGH→LOW após retornar HIGH incrementa novamente;
- negative: LOW contínuo não repete contagem; INPUT_2 LOW não altera counter;
- status: níveis raw acompanham multímetro/jumper/opto de bancada.

**Pronto quando**  
INPUT_1 mede pulsos, INPUT_2 é somente diagnóstico e ambos têm raw status inequívoco.

**Commit sugerido**  
`feat: adiciona duas entradas isoladas ao contador ESP32-C3`

## E3.S2 — Remover factory reset físico dos sinais de máquina

**Objetivo**  
Impedir perda de configuração causada por combinações legítimas de INPUT_1/INPUT_2.

**Requisitos cobertos**  
RQ-02, RQ-20.

**Fazer**

- não portar `checkFactoryResetHold()` baseado em dois GPIOs de entrada;
- preservar `restoreFactoryConfig()` e `POST /api/factory-reset` autenticado;
- preservar reboot autenticado;
- documentar no README que a família C3 v1 não possui gesto físico de factory reset nos sinais industriais.

**Não fazer**

- não criar combinação/hold GPIO0+GPIO1;
- não selecionar strapping pin adicional como botão permanente nesta entrega;
- não remover factory reset remoto autenticado.

**Evidência**  
D5+D1 eram botões do NodeMCU; GPIO0/GPIO1 passam a representar máquina. O significado físico mudou e copiar o gesto seria regressão de segurança operacional.

**Dependências**  
E3.S1.

**Teste**

- positive: endpoint autenticado executa factory reset;
- sibling: reboot autenticado permanece;
- negative live: INPUT_1+INPUT_2 LOW por >10 s não apaga config nem reinicia por factory reset;
- negative auth: token ausente/incorreto não executa reset.

**Pronto quando**  
Não existe caminho de factory reset acionado por estados dos sinais industriais.

**Commit sugerido**  
`fix: impede factory reset por sinais de máquina no ESP32-C3`

## E3.S3 — Definir freshness do Minha DELPI sem quebrar `/api/contador`

**Objetivo**  
Manter timestamp de último contato autenticado com backend para alimentar diagnóstico/LED.

**Requisitos cobertos**  
RQ-07, RQ-14, RQ-15.

**Fazer**

- criar um único owner `lastBackendContactMs` e helper de freshness;
- quando qualquer rota protegida validar `X-Device-Token`, registrar contato;
- em `/api/contador`, manter acesso público, mas se o header estiver presente e igual a `cfg.apiToken`, registrar contato sem exigir o header;
- após chamadas outbound autenticadas bem-sucedidas à `production-pulse-api`, como OTA check/report, registrar contato;
- definir constante nomeada para janela de freshness e documentá-la;
- visita a `/` e `/api/contador` sem token não atualiza freshness.

**Não fazer**

- não tornar `/api/contador` obrigatoriamente autenticado;
- não considerar Wi-Fi conectado equivalente a backend OK;
- não copiar checks de `millis()` para múltiplos consumidores.

**Evidência**  
O client HTTP do BFF já inclui `X-Device-Token` em GET quando token está cadastrado, permitindo detecção passiva compatível.

**Dependências**  
E1.S1.

**Teste**

- positive: poll com token correto marca backend recente;
- sibling: OTA check 2xx marca backend recente;
- negative: browser público sem token não marca; token inválido não marca;
- expiry: após janela, freshness torna-se false e novo contato válido recupera true.

**Pronto quando**  
“Minha Delpi OK” significa contato autenticado recente, não mera conectividade Wi-Fi.

**Commit sugerido**  
`feat: rastreia contato autenticado recente com o Minha DELPI`

## E3.S4 — Centralizar o LED RGB por estado operacional

**Objetivo**  
Representar Wi-Fi, backend e OTA com uma única máquina visual, sem writes de GPIO espalhados.

**Requisitos cobertos**  
RQ-14, RQ-15, RQ-18.

**Fazer**

- definir `LED_R_PIN=4`, `LED_G_PIN=5`, `LED_B_PIN=6`;
- considerar cátodo comum: HIGH liga canal;
- criar enum/estado visual central e uma função única que materializa RGB/blink;
- prioridade: failure/auth > OTA > Wi-Fi connecting/offline > Wi-Fi connected/backend freshness;
- estados: boot/offline vermelho sólido; connecting/backoff vermelho piscando; connected antes de contato recente azul sólido; healthy verde sólido; backend stale azul piscando; OTA amarelo/laranja piscando; falha/auth vermelho rápido;
- timers non-blocking com `millis()`.

**Não fazer**

- não espalhar `digitalWrite` de regra por OTA/auth/Wi-Fi handlers;
- não usar `delay()` para blink no loop;
- não atribuir GPIO reservado.

**Evidência**  
O V2 já possui estado de LED simples; o C3 agrega mais sinais e precisa de um único owner para evitar prioridades conflitantes.

**Dependências**  
E2.S2, E3.S3.

**Teste**

- positive live: cada estado principal produz o padrão definido;
- sibling: recuperação de backend troca azul piscando → verde sem reboot;
- negative: estado OTA/failure não é sobrescrito por callback Wi-Fi concorrente.

**Pronto quando**  
Só o renderer central escreve nos três GPIOs e prioridades são determinísticas.

**Commit sugerido**  
`feat: centraliza sinalização RGB do estado do dispositivo`

---

# E4 — OTA e particionamento

## E4.S1 — Portar a gravação OTA sem alterar o protocolo do backend

**Objetivo**  
Adaptar watchdog/update primitives para ESP32-C3 preservando check, artifact token, progresso, reports e reboot.

**Requisitos cobertos**  
RQ-08, RQ-09, RQ-18.

**Fazer**

- manter os paths `/device-ota/check`, `/device-ota/artifacts/{artifactToken}`, `/device-ota/report`;
- preservar `controllerCode`, `branch`, `targetId`, `status`, `installedFirmwareVersion`, bytes/progress;
- substituir chamadas watchdog específicas de ESP8266 por abordagem compatível com ESP32 core 3.3.11, sem alimentar watchdog inexistente por API legada;
- usar `Update.begin`, stream/write, `Update.end`, `Update.isFinished` conforme APIs ESP32 compiladas;
- preservar timeout finito do HTTP e progress throttle;
- manter falha de report intermediário não-fatal para download já iniciado, como V2;
- atualizar estado OTA central para Serial/RGB sem logar `artifactToken`;
- reiniciar somente após update concluído.

**Não fazer**

- não criar OTA push;
- não mudar auth do device;
- não implementar SHA verify/secure boot/anti-rollback nesta etapa;
- não registrar artifact token em log.

**Evidência**  
`DeviceOtaService` e firmware V2 já definem o contrato. O delta pertence à primitive de flash/watchdog do MCU.

**Dependências**  
E2.S2, E3.S4.

**Teste**

- build C3;
- positive API/live em plano de validação: checking→downloading→applying→updated→reboot;
- sibling: check sem update retorna ao loop sem alterar counter/config;
- negative: HTTP/download/update failure reporta `failed` quando existe target e mantém segredo redigido.

**Pronto quando**  
O firmware C3 fala exatamente o canal OTA existente e compila sem APIs watchdog ESP8266.

**Commit sugerido**  
`feat: porta o fluxo OTA existente para ESP32-C3`

## E4.S2 — Fixar e provar o layout OTA de 4 MB

**Objetivo**  
Garantir que a primeira gravação USB produza um layout com duas app partitions utilizáveis por OTA e capacidade maior que o binário.

**Requisitos cobertos**  
RQ-10, RQ-21.

**Fazer**

- documentar no README o esquema selecionado `Minimal SPIFFS`/`min_spiffs` para o core 3.3.11;
- durante build, capturar a tabela de partições efetivamente usada, não apenas o label da IDE;
- provar presença de `otadata`, `ota_0`, `ota_1`;
- registrar tamanho de cada app slot e tamanho final do binário;
- estabelecer aceite `binary_size < min(ota_0_size, ota_1_size)` com margem operacional documentada;
- documentar que `No OTA` e `Huge APP` sem dual OTA são proibidos para a imagem inicial;
- manter a mesma configuração em builds OTA subsequentes.

**Não fazer**

- não assumir ~1,9 MB sem inspecionar a tabela do pacote instalado;
- não declarar OTA pronta só porque `Update` compila;
- não trocar partition scheme entre primeira gravação e releases sem plano de migração.

**Evidência**  
O firmware já se aproxima do limite do layout menor e OTA exige slots alternados. O nome do menu não prova o binário de partição realmente aplicado.

**Dependências**  
E4.S1.

**Teste**

- compile no perfil alvo;
- inspecionar partition table gerada/usada e anexar ao registro de validação os offsets/sizes de `otadata`, `ota_0`, `ota_1`;
- comparar tamanho `.bin` com menor app slot;
- negative: build/config `No OTA`/`Huge APP` sem dois slots não pode ser classificado PASS.

**Pronto quando**  
Há evidência do layout efetivo e o binário cabe em ambos os slots com margem.

**Commit sugerido**  
`docs: fixa perfil de partições OTA da Super Mini`

---

# E5 — Status, HTML e Serial

## E5.S1 — Evoluir `/api/status` apenas de forma aditiva

**Objetivo**  
Preservar consumidores atuais e expor diagnóstico das entradas.

**Requisitos cobertos**  
RQ-02, RQ-03, RQ-04, RQ-13, RQ-17.

**Fazer**

- manter todos os campos atuais do status;
- `mac` = STA MAC canônico;
- aliases de controller iguais;
- adicionar `input1`/`input2` raw `0|1`;
- manter `firmwareVersion=esp32c3_counter_v1.0.0`;
- manter `wifiConnected`, RSSI, heap e uptime.

**Não fazer**

- não mudar tipo/nome dos campos existentes;
- não incluir token/password;
- não criar `/api/health` paralelo.

**Evidência**  
O parser da API já ignora metadata desconhecida e consome os campos legados conhecidos.

**Dependências**  
E1.S2, E3.S1.

**Teste**

- positive: response contém campos antigos + inputs;
- sibling: driver antigo continua parseando identidade/health;
- negative: ausência de token em `/api/status` continua 401 conforme contrato atual.

**Pronto quando**  
Consumidor atual consegue ler o status sem modificação obrigatória.

**Commit sugerido**  
`feat: adiciona diagnóstico das entradas ao status do C3`

## E5.S2 — Atualizar a página HTML de manutenção

**Objetivo**  
Exibir identidade e saúde operacional local sem expor credenciais.

**Requisitos cobertos**  
RQ-04, RQ-07, RQ-17.

**Fazer**

- manter HTML leve embutido;
- mostrar controller code, counter, STA MAC, IP, firmware, RSSI, Wi-Fi e estado OTA;
- mostrar token somente como configurado/não configurado se presente na UI;
- manter atualização do counter sem framework externo;
- preferir dados locais já em memória em vez de chamar endpoint protegido sem token do browser.

**Não fazer**

- não embutir apiToken em JavaScript;
- não mostrar senha/ota artifact token;
- não transformar em SPA.

**Evidência**  
A página atual é uma superfície de manutenção local simples e não deve adquirir responsabilidade do MFE.

**Dependências**  
E5.S1, E3.S4.

**Teste**

- positive live: todos os campos mínimos aparecem e correspondem ao Serial/status;
- negative: HTML source não contém password/apiToken/artifactToken.

**Pronto quando**  
A bancada consegue identificar dispositivo/rede/firmware sem acessar segredo.

**Commit sugerido**  
`feat: amplia página local de diagnóstico do ESP32-C3`

## E5.S3 — Implementar boot log e resumo periódico redigidos

**Objetivo**  
Deixar manutenção de bancada diagnosticável a 115200 sem flooding ou secrets.

**Requisitos cobertos**  
RQ-04, RQ-05, RQ-06, RQ-07, RQ-18.

**Fazer**

- no boot: family/version, chip model/revision, reset reason, STA MAC, controller code, SSID, radio config, token configured state, OTA configured state/base URL segura, branch, free heap;
- on connect: IP, gateway, channel, RSSI;
- on disconnect: reason code;
- OTA: checking/downloading/applying/updated/failed;
- resumo a cada ~60 s: uptime, Wi-Fi, RSSI, heap, version, backend freshness;
- centralizar redaction/formatting suficiente para não duplicar secrets.

**Não fazer**

- não imprimir password/apiToken/artifactToken;
- não imprimir o mesmo status a cada loop;
- não depender apenas do Serial para estado de domínio do backend.

**Evidência**  
O device ficará em chão de fábrica; observabilidade local reduz diagnóstico por tentativa e erro, mas não substitui API/telemetria.

**Dependências**  
E2.S2, E3.S3, E4.S1.

**Teste**

- positive live: eventos aparecem uma vez/na cadência definida;
- negative: busca no log capturado não encontra valores secretos conhecidos usados no teste;
- soak: heartbeat não causa spam entre intervalos.

**Pronto quando**  
Logs respondem qual versão/rede/estado falhou sem revelar segredo.

**Commit sugerido**  
`feat: melhora diagnóstico serial da Super Mini`

---

# E6 — Verify-final do firmware

## E6.S1 — Revalidar contrato, build e bancada antes de liberar a API/OTA integration

**Objetivo**  
Provar as pós-condições do firmware que o plano de API e validação integrada dependem.

**Requisitos cobertos**  
RQ-01 a RQ-18, RQ-20, RQ-21.

**Fazer**

- rebuild limpo no perfil documentado;
- revisar diff contra V2 para garantir que mudanças são MCU/hardware/diagnóstico necessários;
- executar matriz positive/sibling/negative do plano de validação para identidade, Wi-Fi, inputs, auth, LED e OTA basic readiness;
- registrar itens live não executados como `INCONCLUSIVE`, nunca PASS;
- conferir partition evidence.

**Não fazer**

- não alterar expected/test para acomodar bug;
- não liberar dependente com build verde se identidade/partition contract ainda não estiver provado;
- não declarar rede/hardware testados sem placa real.

**Evidência**  
`plan-execution.mdc` exige pós-condição comprovada, não apenas commit/build.

**Dependências**  
E1-E5 concluídos.

**Teste**

- compile final no mesmo profile da imagem a ser gravada;
- checklist live do `ESP32C3-SUPER-MINI-VALIDATION-PLAN.md` aplicável à bancada disponível;
- diff adversarial e secret scan.

**Pronto quando**  
O firmware é compilável, seu layout OTA está comprovado e as capacidades live executadas têm evidência, com pendências explicitamente classificadas.

**Commit sugerido**  
Sem commit exclusivo, salvo correção real encontrada no verify-final.

---

## Rastreabilidade resumida

| Requisito | Subetapas principais | Aceite |
|---|---|---|
| RQ-01/02 | E1.S1, E5.S1 | port compila e contratos permanecem |
| RQ-03/04 | E1.S2 | uma identidade STA em todas superfícies |
| RQ-05/06 | E2.S1-S3 | 8,5 dBm/sleep off + tentativa única |
| RQ-07 | E2.S3, E3.S3, E5.S2-S3 | auth preservada e redigida |
| RQ-08/09/10 | E4.S1-S2 | OTA existente + dual slots |
| RQ-11/12/13 | E3.S1 | pulse único/input2 diagnóstico |
| RQ-14/15 | E3.S3-S4 | LED baseado em contato autenticado |
| RQ-16 | E1/E3 | pinos fixos/reservados preservados |
| RQ-17/18 | E5 | manutenção HTML/Serial |
| RQ-20 | E3.S2 | sinais de máquina não resetam config |
| RQ-21 | E4.S2/E6 | automated vs live separado |

## Revisão adversarial

- Existe algum `WiFi.begin()` fora da máquina de conexão? Deve ser zero.
- Algum callback escreve diretamente no RGB? Deve ser zero fora do renderer.
- INPUT_2 consegue alterar counter? Deve ser não.
- Dois inputs LOW conseguem apagar config? Deve ser não.
- Um request público marca backend healthy? Deve ser não.
- MAC exibido pode vir de interface diferente? Deve ser não.
- Build pode usar partition scheme diferente do documentado? O verify deve detectar e bloquear PASS.
- Update failure pode deixar `otaInProgress`/LED presos? Cobrir recuperação nos testes live.
