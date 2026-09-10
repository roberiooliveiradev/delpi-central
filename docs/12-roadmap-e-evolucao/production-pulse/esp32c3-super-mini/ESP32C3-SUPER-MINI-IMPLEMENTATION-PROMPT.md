# Prompt de implementação — ESP32-C3 Super Mini no Production Pulse

> **Escopo:** portar o firmware contador do Production Pulse de ESP8266 NodeMCU para ESP32-C3 Super Mini V1601 sem criar arquitetura paralela e preservando os contratos vigentes do Minha DELPI.
>
> **Plano mestre:** [`ESP32C3-SUPER-MINI-MASTER-PLAN.md`](./ESP32C3-SUPER-MINI-MASTER-PLAN.md)
>
> **Planos executáveis:**
> - [`ESP32C3-SUPER-MINI-FIRMWARE-PLAN.md`](./ESP32C3-SUPER-MINI-FIRMWARE-PLAN.md)
> - [`ESP32C3-SUPER-MINI-API-OTA-PLAN.md`](./ESP32C3-SUPER-MINI-API-OTA-PLAN.md)
> - [`ESP32C3-SUPER-MINI-VALIDATION-PLAN.md`](./ESP32C3-SUPER-MINI-VALIDATION-PLAN.md)

---

## Prompt reutilizável

```text
Você atua como Senior/Staff Software Engineer e Arquiteto responsável pelo Minha DELPI — Production Pulse.

OBJETIVO
Portar o firmware contador atual do Production Pulse do ESP8266 NodeMCU para o ESP32-C3 Super Mini V1601, preservando a arquitetura, os contratos HTTP, a autenticação por device token, o fluxo OTA e a compatibilidade com o Minha DELPI. Adicionar somente as capacidades necessárias ao novo hardware: Wi-Fi ESP32-C3, identidade baseada no MAC Wi-Fi Station, reconexão resiliente, duas entradas opto-isoladas, LED RGB externo, diagnóstico expandido e particionamento OTA adequado.

NÃO CRIE UMA SEGUNDA ARQUITETURA DE FIRMWARE/API.
A fonte inicial do comportamento é o firmware vigente:
- docs/12-roadmap-e-evolucao/production-pulse/firmware/esp8266_counter_v2/esp8266_counter_v2.ino
- docs/12-roadmap-e-evolucao/production-pulse/firmware/esp8266_counter_v2/README.md

A família alvo é nova e isolada por hardware:
- driverKey / firmwareKey: esp32c3_counter_v1
- versão inicial: esp32c3_counter_v1.0.0
- target sketch: docs/12-roadmap-e-evolucao/production-pulse/firmware/esp32c3_counter_v1/esp32c3_counter_v1.ino

ANTES DE ALTERAR QUALQUER CÓDIGO
1. Releia as regras globais atuais:
   - .cursor/rules/development-standards-index.mdc
   - .cursor/rules/evidence-driven-execution.mdc
   - .cursor/rules/centralized-rules-first.mdc
   - .cursor/rules/clean-code-architecture-guardrails.mdc
   - .cursor/rules/english-code-identifiers.mdc
2. Para esta tarefa, carregue também as responsabilidades/regras materiais:
   - .cursor/rules/platform-architecture-boundaries.mdc
   - .cursor/rules/platform-security-identity-authorization.mdc
   - .cursor/rules/platform-api-contracts-integration.mdc
   - .cursor/rules/contract-evolution-backward-compatibility.mdc
   - .cursor/rules/http-integration-resilience.mdc
   - .cursor/rules/platform-quality-testing.mdc
   - .cursor/rules/platform-delivery-runtime-operations.mdc
   - .cursor/rules/platform-reliability-observability.mdc
   - .cursor/rules/production-pulse-admin-hub.mdc quando o MFE/compatibilidade visual forem tocados
   - .cursor/rules/test-and-commit.mdc
   - .cursor/rules/plan-execution.mdc
3. Revalide o código e os contratos atuais antes de cada E*.S*. O plano é uma hipótese estruturada de execução; regras, contratos e implementação vigentes vencem qualquer instrução que tenha sofrido drift.
4. Inspecione o working tree antes do diff e preserve alterações preexistentes.
5. Se uma premissa material estiver inválida, pare o subgrafo afetado e registre EXECUTION_DRIFT antes de replanejar.

BOUNDARY ARQUITETURAL INEGOCIÁVEL
Portal → MFE production-pulse → production-pulse-api → Postgres / IoT LAN / gateway → api-delpi → TOTVS.

- O MFE Production Pulse NUNCA chama api-delpi diretamente.
- A production-pulse-api continua owner do bounded context IoT/firmware/OTA.
- Não introduza apiDelpiUrl, API_DELPI_BASE, /apps/api-delpi ou fetch direto no browser.
- Não mova regra específica de Production Pulse para api-delpi.
- Não crie migration sem necessidade comprovada; migrations aplicadas são imutáveis.

CONTRATOS QUE DEVEM CONTINUAR COMPATÍVEIS
O ESP32-C3 deve manter o mesmo servidor HTTP na porta 80 e preservar os endpoints atuais:
- GET /
- GET /api/contador
- GET /api/status
- GET/POST /api/config
- POST /api/incrementar
- POST /api/decrementar
- POST /api/reset
- POST /api/definir
- POST /api/reboot
- POST /api/factory-reset

Preserve os nomes já consumidos pelo Minha DELPI, especialmente:
- contador
- codigoControlador
- controllerCode
- equipamento
- mac
- ip
- firmwareVersion
- uptimeMs
- freeHeap
- rssi
- wifiConnected

Novos campos diagnósticos em /api/status devem ser ADDITIVE e não podem alterar a semântica dos existentes.

IDENTIDADE E MAC
- Coloque o rádio explicitamente em WIFI_STA antes de resolver a identidade.
- O MAC canônico do dispositivo para TI/DHCP é o MAC da interface Wi-Fi Station, nunca base MAC, AP MAC ou outro endereço derivado.
- Use uma única fonte de bytes do STA MAC para gerar tanto o campo mac quanto o controllerCode.
- Formato travado, salvo evidência atual contrária: ESP32C3-XXXXXXXXXXXX, em que X é o MAC STA em hexadecimal sem separadores e em uppercase.
- Preserve os três aliases de identidade com o mesmo valor: codigoControlador, controllerCode e equipamento.
- Mostrar exatamente o mesmo STA MAC no Serial, HTML e /api/status.
- Log de boot obrigatório: MAC WIFI STA - ENVIAR PARA TI: XX:XX:XX:XX:XX:XX.

HARDWARE ALVO
- Placa: ESP32-C3 Super Mini V1601
- MCU: ESP32-C3
- Flash: 4 MB
- Arduino board: ESP32C3 Dev Module
- Espressif Arduino Core: 3.3.11
- CPU: 160 MHz
- Flash mode: QIO
- Flash frequency: 80 MHz
- Upload: 115200

WI-FI ESPECÍFICO DESTA FAMÍLIA
Depois de WiFi.mode(WIFI_STA) e antes da conexão:
- WiFi.setSleep(false)
- WiFi.setTxPower(WIFI_POWER_8_5dBm)

Valide o retorno das duas configurações quando a API permitir e registre no Serial sem expor segredo.
A limitação de 8,5 dBm pertence à família esp32c3_counter_v1 / Super Mini V1601; não altere o ESP8266 por efeito colateral.

RECONEXÃO
- Não chame WiFi.begin novamente enquanto uma tentativa anterior estiver ativa.
- Modele estados explícitos de conexão ou equivalente que garanta uma única tentativa em voo.
- Use eventos do Arduino ESP32 e capture ARDUINO_EVENT_WIFI_STA_DISCONNECTED.
- Registre o reason code da desconexão.
- Preserve backoff exponencial limitado, sem retry storm.
- Configuração Wi-Fi alterada por /api/config deve transicionar pela mesma máquina de conexão, em vez de chamar WiFi.begin fora dela.

AUTENTICAÇÃO E SEGREDOS
- Preserve cfg.apiToken e X-Device-Token.
- Não crie nova estratégia de autenticação.
- Nunca imprimir senha Wi-Fi, apiToken, artifactToken ou credencial completa em Serial, HTML, log da API ou erro.
- Exibir apenas API Token: configurado | não configurado.
- /api/contador continua compatível como leitura pública; quando houver X-Device-Token válido, o firmware pode reconhecer passivamente esse request como contato legítimo do backend sem tornar o header obrigatório.
- Rotas hoje protegidas continuam protegidas; não relaxar requireDeviceToken para facilitar o port.

DEFINIÇÃO DE “MINHA DELPI OK” PARA O LED
A production-pulse-api já envia X-Device-Token nas chamadas HTTP ao device, inclusive GET /api/contador quando existe token cadastrado. Portanto:
- registrar lastBackendContactMs quando uma chamada inbound contiver X-Device-Token válido, mesmo em /api/contador, sem tornar o token obrigatório nessa rota;
- também registrar contato em trocas outbound autenticadas com a production-pulse-api que retornem sucesso, como /device-ota/check e reports OTA;
- não considerar visita à página HTML ou request público sem token como confirmação do Minha DELPI;
- escolher a janela de freshness com constante nomeada/documentada e testar expiração/recuperação; não espalhar millis() checks pelo sketch.

ENTRADAS DIGITAIS ISOLADAS
- INPUT_1_PIN = GPIO0
- INPUT_2_PIN = GPIO1
- active LOW
- inativo = HIGH
- opto acionado = LOW
- usar pull-up de 3,3 V no lado lógico conforme hardware
- INPUT_1 é o único sinal físico que incrementa a contagem nesta versão
- INPUT_2 é reservado/diagnóstico e NÃO altera o contador
- debounce deve preservar contagem por transição estável para LOW; manter LOW não pode contar continuamente
- adicionar estados das duas entradas em /api/status de forma aditiva e documentada
- sinais industriais 12/24 V permanecem no lado isolado do opto; nenhum GPIO recebe tensão industrial

ATENÇÃO AO FACTORY RESET FÍSICO
O ESP8266 atual usa hold simultâneo dos dois botões D5+D1 para factory reset. Não transfira esse gesto para INPUT_1 + INPUT_2: no ESP32-C3 eles são sinais de máquina e uma combinação legítima não pode apagar configuração. Preserve o endpoint autenticado POST /api/factory-reset. Não invente outro pino permanente para factory reset nesta entrega.

LED RGB EXTERNO
LED de cátodo comum:
- LED_R_PIN = GPIO4
- LED_G_PIN = GPIO5
- LED_B_PIN = GPIO6
- cada canal com resistor externo ~220 Ω
- HIGH liga o canal; LOW desliga

Centralize a sinalização em um único estado visual, sem digitalWrite de regra espalhado:
- boot/sem Wi-Fi: vermelho sólido
- conectando/reconectando: vermelho piscando
- Wi-Fi conectado, sem contato backend recente: azul sólido inicialmente
- Wi-Fi + Minha DELPI recente: verde sólido
- Wi-Fi continua conectado e contato backend expirou: azul piscando
- OTA checking/downloading/applying: amarelo/laranja piscando (R+G)
- falha OTA/autenticação: vermelho rápido por janela definida

PINOS RESERVADOS
Não usar para sinais permanentes:
- GPIO2, GPIO8, GPIO9: strapping pins do ESP32-C3
- GPIO20, GPIO21: reservar para UART/debug futuro

PÁGINA HTML
Preserve a página simples do firmware e acrescente, no mínimo:
- controllerCode
- counter
- MAC Wi-Fi Station
- IP
- firmware family/version
- RSSI
- Wi-Fi state
- OTA state
- token apenas como configurado/não configurado, se exibido
Não exponha segredo nem crie SPA/framework para essa página.

SERIAL / OBSERVABILIDADE
115200 baud. No boot mostrar:
- firmware family/version
- chip model/revision
- reset reason
- MAC Wi-Fi Station com destaque para TI
- controllerCode
- SSID, nunca senha
- Wi-Fi sleep disabled
- TX power 8.5 dBm
- token configurado/não configurado
- OTA configurado/não configurado
- otaBaseUrl somente se não contiver segredo
- branch
- free heap

Na conexão mostrar IP, gateway, channel e RSSI.
Na desconexão mostrar reason code.
No OTA mostrar checking, downloading, applying, updated ou failed, sem artifactToken.
Adicionar resumo curto a cada ~60 s com uptime, estado Wi-Fi, RSSI, heap, versão e backend freshness, sem flooding.

OTA
Preserve o pipeline real existente:
GET /device-ota/check
→ artifactToken
→ GET /device-ota/artifacts/{artifactToken}
→ Update.begin/write/end
→ POST /device-ota/report downloading/applying/updated|failed
→ ESP.restart

- Adapte apenas APIs específicas de ESP8266 para ESP32-C3.
- Preserve progress byte-a-byte já implementado.
- Não implemente uma segunda OTA stack.
- Não invente push OTA.
- Não implemente P1/P2 (SHA verify no chip, semver anti-downgrade, assinatura/secure boot) nesta entrega, salvo nova decisão explícita. Esses itens continuam evolução separada nos contratos OTA vigentes.

ISOLAMENTO DE FAMÍLIA / DRIVER
Criar novo driver declarativo esp32c3_counter_v1 com a mesma semântica de pulse_counter e capabilities do contador atual.
A família OTA esp32c3_counter_v1 deve aceitar somente versões publicadas com driverKey esp32c3_counter_v1.
Preserve o ESP8266 existente.
Evite copiar toda a lógica HTTP do driver. Há dois consumidores reais do mesmo protocolo (ESP8266 counter e ESP32-C3 counter), então reutilize a implementação de protocolo no owner de infrastructure/drivers mantendo identidades de driver distintas e testes de regressão do ESP8266.

PARTICIONAMENTO OTA
- 4 MB flash com duas partições app OTA + otadata.
- Preferir o esquema do Arduino Core chamado Minimal SPIFFS / min_spiffs, desde que a versão 3.3.11 efetivamente resulte em slots OTA compatíveis com o binário.
- Não usar No OTA nem Huge APP sem OTA.
- Antes de declarar pronto, provar no artefato/partition table usada que existem ota_0, ota_1 e otadata e que o .bin cabe no menor slot com margem.
- Essa configuração precisa fazer parte da primeira gravação USB e do runbook de bancada.

MFE / ADMIN HUB
Não altere o MFE por antecipação.
Primeiro prove se o novo driver/família já aparece pelo catálogo dinâmico. Se algum hardcode impedir a nova família, corrija a fonte canônica sem duplicar compatibilidade.
Se tocar o Hub:
- preservar /apps/production-pulse/firmware-links
- compatibilidade != vínculo explícito
- sem assignedFirmwareKey = sem edge
- assignedFirmwareKey = edge sólida
- API continua autoridade final de compatibilidade
- reutilizar plugin-ui / Pp*; nenhum modal/toast/CSS paralelo
- executar productionPulseKit.structural.test.ts e build/testes MFE

VALIDAÇÃO
Backend, quando alterado:
cd production-pulse-api && pytest tests -q

MFE, somente se alterado:
cd plugins/production-pulse && npm run test && npm run build

Aplicar também os gates de arquitetura exigidos por test-and-commit.mdc quando o diff os tornar materiais.

Firmware:
- compilar com o core/board/settings alvo;
- registrar tamanho do sketch/binário;
- provar layout OTA efetivo;
- executar testes de bancada previstos no plano de validação.

Nunca declarar como validado por hardware algo que não foi executado em ESP32-C3 real/LAN real. Classifique como INCONCLUSIVE/PENDENTE quando faltar placa, rede, DHCP, hotspot ou acesso físico.

PROTOCOLO DE EXECUÇÃO
Execute os planos na ordem definida no master plan e, antes de cada E*.S*:
- revalidar regras + código + contrato + dependências + working tree;
- cumprir READY_TO_EXECUTE;
- implementar somente o escopo da subetapa;
- executar testes positive + sibling + negative previstos;
- revisar o diff adversarialmente;
- provar as pós-condições antes de liberar dependentes;
- se surgir drift material, STOP-THE-LINE no subgrafo afetado e corrigir o plano.

Commit/push somente quando houver autorização explícita conforme test-and-commit.mdc. Não interprete este prompt como autorização automática para commits de implementação.

FORMATO DE RELATO
Para cada etapa entregue registrar:
- FATO — evidência confirmada
- INFERÊNCIA — conclusão limitada
- PROPOSTA — apenas quando ainda não implementada
- PLAN_STEP
- FILES/OWNERS
- CONTRACT_CHANGE_CLASS
- TESTS EXECUTADOS e resultado real
- SECURITY NEGATIVES
- DIFF_SCOPE_REVIEW
- EXECUTION_DRIFT, se houve
- POSTCONDITIONS_PROVED
- DEPENDENTS_UNLOCKED
- PENDÊNCIAS/INCONCLUSIVE

CRITÉRIO FINAL
Antes de concluir, responda com evidência:
1. O C3 preserva os contratos HTTP e o token atuais?
2. O MAC exibido é inequivocamente o Wi-Fi Station usado para DHCP?
3. Não há WiFi.begin concorrente com tentativa ativa?
4. TX power 8.5 dBm e sleep off são aplicados antes da associação?
5. INPUT_1 conta uma vez por acionamento e INPUT_2 não conta?
6. Sinais de máquina não podem acionar factory reset por combinação/hold?
7. O RGB traduz Wi-Fi/backend/OTA sem duplicação de regra?
8. ESP8266 e ESP32-C3 não podem receber artefatos da família errada?
9. ota_0 + ota_1 + otadata existem na imagem/layout usado?
10. Nenhum token/senha/artifactToken aparece em log/HTML?
11. O MFE continua dependendo somente da production-pulse-api?
12. O ESP8266 existente continua coberto por regressão?
13. Testes locais, build e testes live foram diferenciados honestamente?
14. O objetivo original foi comprovado, não apenas os testes unitários?
```

---

## Nota de autoridade

Este prompt organiza a execução, mas **não substitui** regras `.cursor`, ADRs, contratos, schemas, código ou testes atuais. Antes de cada subetapa, a implementação vigente deve ser revalidada. Se houver divergência material, aplicar `EXECUTION_DRIFT` conforme `plan-execution.mdc` e corrigir o plano em vez de adaptar o código a uma premissa obsoleta.
