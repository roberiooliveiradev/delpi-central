# Plano de validação — ESP32-C3 Super Mini / Production Pulse

> **Status:** plano de evidência. Um item que depende de hardware/LAN e não foi realmente executado deve ser classificado `INCONCLUSIVE/PENDENTE`, nunca `PASS`.
>
> **Pai:** [`ESP32C3-SUPER-MINI-MASTER-PLAN.md`](./ESP32C3-SUPER-MINI-MASTER-PLAN.md)

## Overview

Provar em camadas que o port C3 preserva contratos, autenticação e OTA do Minha DELPI e que as mudanças específicas de hardware funcionam no ESP32-C3 Super Mini V1601 real, separando build/testes automatizados de bancada, LAN e atualização OTA live.

## Princípio de evidência

```text
source/static
→ compile/build
→ API unit/contract/integration
→ USB bench
→ LAN/device HTTP
→ Production Pulse BFF
→ OTA live
→ verify-final do objetivo original
```

Nenhuma camada inferior autoriza alegar a superior.

## Matriz de ambientes

| Ambiente | Prova possível |
|---|---|
| repo/CI | contratos, driver registry, auth negatives, OTA family isolation |
| Arduino compile | compatibilidade Core 3.3.11, tamanho binário, partition layout |
| ESP32-C3 USB | boot, MAC, pins, LED, reset reason, serial |
| hotspot 2,4 GHz | associação/reconnect/reason code |
| LAN DELPI | DHCP, IP/gateway, API device, BFF→device |
| Minha DELPI + storage OTA | publish/link/job/download/report/reboot |

## Evidências a preservar

Para cada sessão live registrar, sem secrets:

- data/hora;
- board e core;
- firmware family/version;
- tamanho do `.bin` e partition layout;
- STA MAC;
- SSID testado, sem password;
- IP/gateway/channel/RSSI quando disponível;
- passos realizados;
- resultado PASS/FAIL/INCONCLUSIVE;
- trecho mínimo de Serial relevante, com tokens redigidos;
- versão instalada antes/depois de OTA.

---

# E1 — Baseline estático, builds e contratos automatizados

## E1.S1 — Compilar firmware C3 no perfil que será gravado

**Objetivo**  
Provar que o mesmo target/settings documentado gera o binário candidato.

**Requisitos cobertos**  
RQ-01, RQ-05, RQ-08, RQ-10, RQ-21.

**Fazer**

- usar ESP32C3 Dev Module + Arduino Core 3.3.11;
- CPU 160 MHz; flash 4 MB; QIO; flash 80 MHz; upload 115200;
- selecionar `Minimal SPIFFS`/`min_spiffs` e registrar a configuração efetiva;
- compilar `firmware/esp32c3_counter_v1/esp32c3_counter_v1.ino`;
- registrar sketch size e `.bin` gerado;
- guardar a linha/config de build suficiente para reproduzir o artefato.

**Não fazer**

- não usar uma configuração para USB e outra para gerar OTA sem registrar diferença;
- não usar `No OTA` ou `Huge APP` sem dual slots;
- não inferir sucesso OTA só do compile.

**Evidência**  
O artefato que entra no catálogo deve corresponder ao target real; build diferente invalida provenance da validação.

**Dependências**  
Firmware E1-E5 implementados.

**Teste**

Compilação limpa no perfil documentado. Se `arduino-cli` estiver instalado, registrar o comando/FQBN e board options exatos resolvidos pelo ambiente; se a bancada usar Arduino IDE, registrar screenshots/texto do perfil e compile output no evidence da execução.

**Pronto quando**  
Existe `.bin` reproduzível e seu perfil exato está registrado.

**Commit sugerido**  
Nenhum; validação não gera commit sem correção real.

## E1.S2 — Provar partition table efetiva

**Objetivo**  
Confirmar que a imagem inicialmente gravada possui `otadata`, `ota_0` e `ota_1` e espaço suficiente.

**Requisitos cobertos**  
RQ-10, RQ-21.

**Fazer**

- inspecionar a partition table efetivamente resolvida pelo Core 3.3.11/build;
- registrar nomes, offsets e tamanhos de `otadata`, `ota_0`, `ota_1`;
- comparar tamanho do firmware com o menor app slot;
- registrar margem absoluta e percentual;
- conferir que a imagem USB usada no device corresponde a esse layout.

**Não fazer**

- não aceitar o texto “Minimal SPIFFS” como única evidência;
- não estimar slot pelo consumo reportado da IDE;
- não publicar candidato maior que o menor slot.

**Evidência**  
Dual OTA depende do layout de flash, não da existência da biblioteca `Update`.

**Dependências**  
E1.S1.

**Teste**

```text
ASSERT otadata exists
ASSERT ota_0 exists
ASSERT ota_1 exists
ASSERT ota_0.size == ota_1.size (ou documentar diferença real)
ASSERT firmware.bin.size < min(ota_0.size, ota_1.size)
```

**Pronto quando**  
Todos asserts têm evidência do build real.

**Commit sugerido**  
Nenhum.

## E1.S3 — Executar regressão API/BFF e family isolation

**Objetivo**  
Provar contratos e compatibilidade antes de usar hardware live.

**Requisitos cobertos**  
RQ-02, RQ-07, RQ-08, RQ-09, RQ-19, RQ-21.

**Fazer**

```bash
cd production-pulse-api && pytest tests -q
```

Se MFE foi alterado:

```bash
cd plugins/production-pulse && npm run test && npm run build
```

Quando materiais ao diff, executar gates de arquitetura de `test-and-commit.mdc` contra a base correta.

- conferir especificamente casos ESP8266↔C3 de link/job OTA;
- conferir auth negativa do device OTA;
- conferir regressão do `Esp8266CounterDriver`.

**Não fazer**

- não pular suite completa porque testes específicos passaram;
- não classificar falha externa sem evidência.

**Evidência**  
A API é autoridade de compatibilidade/segurança; hardware live não substitui contract tests.

**Dependências**  
API/OTA E1-E4 implementados.

**Teste**  
Comandos acima.

**Pronto quando**  
Suites obrigatórias passam ou falhas não relacionadas estão comprovadamente classificadas; qualquer falha do escopo bloqueia E2+.

**Commit sugerido**  
Nenhum, salvo fix necessário.

---

# E2 — Bancada USB: boot, identidade e secrets

## E2.S1 — Validar boot log, chip e identidade STA

**Objetivo**  
Provar no hardware real que o MAC enviado à TI é o Wi-Fi Station MAC e é a única identidade usada.

**Requisitos cobertos**  
RQ-03, RQ-04, RQ-18.

**Fazer**

- gravar o build validado em E1 no ESP32-C3 real;
- abrir Serial a 115200;
- capturar family/version, chip/revision, reset reason, STA MAC, controller code, SSID, radio config, branch, heap e status token/OTA;
- comparar `controllerCode` com `ESP32C3-` + STA MAC sem `:`;
- consultar `/api/status` com token e comparar `mac`/aliases;
- abrir HTML local e comparar MAC/controller code.

**Não fazer**

- não compartilhar o valor do token na evidência;
- não aceitar MAC semelhante: deve ser igualdade exata entre superfícies.

**Evidência**  
O erro anterior de DHCP ocorreu por interface MAC incorreta; igualdade é requisito operacional.

**Dependências**  
E1 concluído.

**Teste**

```text
Serial STA MAC == /api/status.mac == HTML STA MAC
controllerCode == "ESP32C3-" + remove_colons(Serial STA MAC)
codigoControlador == controllerCode == equipamento
```

**Pronto quando**  
As igualdades acima são observadas em placa real.

**Commit sugerido**  
Nenhum.

## E2.S2 — Fazer negative secret scan da superfície real

**Objetivo**  
Provar que credenciais configuradas não aparecem em Serial/HTML/status público.

**Requisitos cobertos**  
RQ-07, RQ-17, RQ-18.

**Fazer**

- configurar valores de teste conhecidos para password/apiToken;
- capturar boot/runtime Serial e HTML source;
- verificar `/api/status` e `/api/config` conforme auth;
- pesquisar pelos valores secretos conhecidos nos captures;
- confirmar que token aparece apenas como `configurado/não configurado`.

**Não fazer**

- não armazenar secrets reais de produção no evidence;
- não incluir artifact token de uma execução OTA.

**Evidência**  
Segurança exige teste negativo de redaction, não apenas inspeção do código.

**Dependências**  
E2.S1.

**Teste**

```text
ASSERT test_wifi_password not in serial_capture
ASSERT test_api_token not in serial_capture
ASSERT test_wifi_password not in html_source
ASSERT test_api_token not in html_source
```

**Pronto quando**  
Nenhum valor secreto de teste aparece nas superfícies não autorizadas.

**Commit sugerido**  
Nenhum.

---

# E3 — Wi-Fi association e reconnect

## E3.S1 — Validar associação com radio settings antes do begin

**Objetivo**  
Reproduzir a condição de rede relevante e provar associação estável com 8,5 dBm/sleep off.

**Requisitos cobertos**  
RQ-05, RQ-06, RQ-18.

**Fazer**

- testar hotspot Windows 2,4 GHz WPA2 e, quando acessível, `Delpi-Desenvolvimento`;
- confirmar no boot log que sleep off/TX 8,5 dBm são aplicados antes de conexão;
- registrar associação, DHCP, IP, gateway, channel e RSSI;
- manter observação suficiente para detectar disconnect loop imediato.

**Não fazer**

- não alterar potência durante o teste para “achar” um valor melhor sem novo requisito;
- não concluir sobre LAN DELPI apenas com hotspot.

**Evidência**  
O hardware V1601 mostrou `AUTH_EXPIRE` em potência normal e conexão estável a 8,5 dBm nos testes preliminares relatados.

**Dependências**  
E2.

**Teste**

- positive: associa, autentica, recebe DHCP e permanece conectado no cenário executado;
- sibling: repetir no segundo C3 quando disponível;
- negative diagnostic: se desconectar, reason code deve aparecer.

**Pronto quando**  
Cada ambiente executado possui resultado e evidência, e não há claim para ambiente não testado.

**Commit sugerido**  
Nenhum.

## E3.S2 — Validar tentativa única, backoff e recuperação

**Objetivo**  
Provar que uma perda de rede não cria `WiFi.begin()` concorrente e recupera automaticamente.

**Requisitos cobertos**  
RQ-06, RQ-14, RQ-18.

**Fazer**

- com device conectado, desligar hotspot/AP ou tornar rede indisponível;
- observar disconnect reason e backoff;
- manter rede ausente por múltiplas janelas de retry;
- restaurar AP;
- observar conexão e reset do backoff;
- repetir ciclo algumas vezes;
- verificar padrões RGB offline/connecting/connected.

**Não fazer**

- não reiniciar MCU manualmente entre perda/recuperação;
- não chamar endpoint de reboot para mascarar reconnect.

**Evidência**  
A correção só é provada se a state machine recuperar sem concorrência real.

**Dependências**  
E3.S1.

**Teste**

```text
ASSERT serial does not contain "sta is connecting, cannot set config"
ASSERT disconnect event contains reason
ASSERT attempts respect backoff
ASSERT AP restoration eventually reaches connected without MCU reboot
```

**Pronto quando**  
Os asserts são comprovados em hardware real.

**Commit sugerido**  
Nenhum.

## E3.S3 — Validar mudança de SSID/config sem bypass do reconnect owner

**Objetivo**  
Provar que configuração Wi-Fi remota troca de rede sem disparar begin concorrente.

**Requisitos cobertos**  
RQ-02, RQ-06, RQ-07.

**Fazer**

- chamar `/api/config` autenticado alterando SSID/password para rede de teste válida;
- observar uma única sequência de desconexão/reconexão;
- alterar somente debounce/branch em outra chamada e confirmar que Wi-Fi não reinicia;
- restaurar configuração de bancada.

**Não fazer**

- não logar password usado;
- não testar com credencial de produção na evidência.

**Teste**

- positive: alteração Wi-Fi conecta à nova rede;
- sibling: mudança não-Wi-Fi não reconecta;
- negative: nenhuma mensagem de config concorrente.

**Pronto quando**  
Handler config não cria uma segunda origem de tentativa observável.

**Commit sugerido**  
Nenhum.

---

# E4 — Entradas digitais e proteção contra reset acidental

## E4.S1 — Validar INPUT_1 por pulso e held-low

**Objetivo**  
Provar um incremento por acionamento, não por nível mantido.

**Requisitos cobertos**  
RQ-11, RQ-12, RQ-13.

**Fazer**

- iniciar com INPUT_1 HIGH;
- acionar opto/jumper de bancada para LOW por período maior que debounce;
- retornar HIGH;
- repetir N vezes conhecidas;
- manter LOW continuamente por período muito maior que debounce;
- comparar counter esperado e raw status.

**Teste**

```text
counter_after_N_pulses - counter_before == N
held_LOW_after_first_transition adds == 1, not repeated increments
/api/status.input1 == electrical raw level
```

**Pronto quando**  
Counter corresponde ao número de transições válidas e não ao tempo em LOW.

**Commit sugerido**  
Nenhum.

## E4.S2 — Validar INPUT_2 como diagnóstico sem side effect

**Objetivo**  
Provar que o segundo opto está pronto fisicamente, mas não muda lógica de produção.

**Requisitos cobertos**  
RQ-11, RQ-13.

**Fazer**

- alternar INPUT_2 HIGH/LOW repetidamente;
- manter INPUT_1 estável;
- observar `/api/status.input2`;
- conferir counter antes/depois.

**Teste**

```text
input2 raw follows electrical state
counter_after == counter_before
```

**Pronto quando**  
INPUT_2 é observável e não executa nenhum comando/counter delta.

**Commit sugerido**  
Nenhum.

## E4.S3 — Validar que dois sinais LOW não executam factory reset

**Objetivo**  
Provar a remoção do gesto perigoso herdado do NodeMCU.

**Requisitos cobertos**  
RQ-20, RQ-07.

**Fazer**

- configurar um valor de bancada persistente identificável, sem secret real;
- manter INPUT_1 e INPUT_2 LOW simultaneamente por >10 s;
- retornar HIGH e verificar que configuração persiste e não houve factory reset/reboot associado;
- executar separadamente `POST /api/factory-reset` com token válido para provar que o recurso remoto continua;
- executar negativo com token inválido/ausente.

**Teste**

```text
both_inputs_low does not factory-reset
valid authenticated endpoint still factory-resets
invalid/missing token does not factory-reset
```

**Pronto quando**  
Sinais industriais não conseguem apagar configuração e o endpoint autorizado continua funcional.

**Commit sugerido**  
Nenhum.

---

# E5 — HTTP device, backend freshness e RGB

## E5.S1 — Validar compatibilidade das APIs do device

**Objetivo**  
Provar endpoints antigos no C3 com positive/negative auth.

**Requisitos cobertos**  
RQ-02, RQ-07, RQ-17.

**Fazer**

Testar no IP real:

- `GET /api/contador` sem token;
- `GET /api/status` com e sem token;
- `GET/POST /api/config` com token;
- incrementar/decrementar/reset/definir;
- reboot;
- factory reset em sessão controlada.

Exemplos de curl devem usar placeholders e `X-Device-Token: <TEST_TOKEN>`; não versionar token.

**Não fazer**

- não tornar contador público uma prova de backend freshness;
- não executar factory reset antes de registrar/restaurar config de bancada.

**Teste**

- positive: respostas mantêm shape esperado;
- sibling: commands alteram counter conforme V2;
- negative: rotas protegidas retornam 401 sem/token inválido.

**Pronto quando**  
O protocolo esperado pelo driver da API funciona no C3 real.

**Commit sugerido**  
Nenhum.

## E5.S2 — Validar definição “Minha DELPI OK” e LED

**Objetivo**  
Provar que verde depende de contato autenticado recente, não somente de Wi-Fi.

**Requisitos cobertos**  
RQ-14, RQ-15.

**Fazer**

- conectar Wi-Fi sem gerar contato backend válido: observar azul inicial;
- executar request público `/api/contador` sem token: deve permanecer sem freshness;
- executar request com token válido/BFF test probe ou aguardar poll real: observar healthy/verde;
- impedir contato backend mantendo Wi-Fi conectado até expirar freshness: observar azul piscando;
- restaurar contato: observar retorno a verde;
- provocar auth inválida em rota protegida e observar failure vermelho rápido por janela definida.

**Não fazer**

- não derrubar Wi-Fi para testar backend stale; são dimensões diferentes;
- não considerar browser HTML como backend.

**Teste**

```text
WiFi OK + no authenticated contact => blue
public counter request => still not healthy
valid authenticated BFF/device request => green
freshness expiry with WiFi still OK => blinking blue
valid contact recovery => green
```

**Pronto quando**  
As transições RGB correspondem exatamente à semântica de freshness definida.

**Commit sugerido**  
Nenhum.

---

# E6 — Integração real com production-pulse-api

## E6.S1 — Validar probe/poll BFF → C3 pela LAN

**Objetivo**  
Provar a cadeia `production-pulse-api → driver esp32c3_counter_v1 → device` na rede real.

**Requisitos cobertos**  
RQ-02, RQ-07, RQ-09, RQ-15, RQ-19, RQ-21.

**Fazer**

- cadastrar/testar device C3 com `driver_key=esp32c3_counter_v1`, IP LAN e token correspondente;
- executar fluxo `test-probe`/teste de device existente conforme superfície atual;
- observar counter + meta identity retornados;
- permitir poll normal e confirmar readings `metrics.counter`;
- observar LED mudar para healthy por request autenticado do BFF;
- confirmar que MFE não chama device nem api-delpi diretamente.

**Não fazer**

- não alegar sucesso LAN usando somente curl no host se API/container não alcançou o device;
- não misturar diagnóstico de container/host/LAN.

**Evidência**  
A arquitetura exige BFF como owner e o driver é executado pela API, potencialmente de runtime/container diferente do browser.

**Teste**

- positive: API probe/poll retorna counter e controller identity do C3;
- sibling: device ESP8266 existente continua pollável;
- negative: token incorreto produz erro de driver/auth e não reading falsa.

**Pronto quando**  
Há evidência do request originando na production-pulse-api e chegando ao C3 real.

**Commit sugerido**  
Nenhum.

---

# E7 — OTA live end-to-end

## E7.S1 — Publicar e vincular artefato C3 corretamente identificado

**Objetivo**  
Preparar OTA sem possibilidade de seleção cruzada no fluxo normal.

**Requisitos cobertos**  
RQ-08, RQ-09, RQ-10.

**Fazer**

- usar o `.bin` gerado no build/provenance E1;
- publicar versão com `firmwareKey=esp32c3_counter_v1` e `driverKey=esp32c3_counter_v1`;
- vincular explicitamente o device C3 pela superfície `/apps/production-pulse/firmware-links` ou API canônica;
- confirmar `assignedFirmwareKey=esp32c3_counter_v1` e edge sólida;
- confirmar que firmware ESP8266 não pode ser vinculado ao C3 e inverso.

**Não fazer**

- não publicar binário sem saber de qual build veio;
- não tratar compatibilidade como vínculo;
- não editar banco manualmente.

**Teste**

- positive: link C3↔família C3;
- negative: cross-family link retorna `firmwareLinkIncompatible`;
- visual: edge só existe após vínculo explícito.

**Pronto quando**  
O target C3 aponta explicitamente para a família C3 e o artefato possui provenance do build validado.

**Commit sugerido**  
Nenhum.

## E7.S2 — Executar campanha e observar ciclo completo OTA

**Objetivo**  
Provar download, gravação no slot alternado, reports e reboot para nova versão.

**Requisitos cobertos**  
RQ-08, RQ-10, RQ-14, RQ-18, RQ-21.

**Fazer**

- instalar uma versão C3 anterior/controle e publicar versão alvo C3 diferente;
- criar job manual para o device;
- observar no Serial `checking`, `downloading`, `applying`, `updated`/reboot;
- observar RGB OTA amarelo/laranja piscando;
- observar progresso real no backend/Admin;
- após reboot, consultar `/api/status` e detalhe device para confirmar versão instalada;
- confirmar job/target terminal coerente.

**Não fazer**

- não considerar report `updated` isolado suficiente se o device não reiniciar/reportar versão alvo;
- não declarar slot OTA usado sem evidência disponível;
- não expor artifact token em captures.

**Teste**

```text
job target: authorized → downloading → applying → updated
progress uses real bytes during downloading
ESP reboots
/api/status.firmwareVersion == target version
backend installedFirmwareVersion == target version
```

**Pronto quando**  
Toda a cadeia device→API→artifact→Update→report→reboot→version reconciliation é observada.

**Commit sugerido**  
Nenhum.

## E7.S3 — Validar falhas OTA e isolamento negativo

**Objetivo**  
Provar que falhas não viram sucesso falso e família errada não gera target pelo fluxo normal.

**Requisitos cobertos**  
RQ-07, RQ-08, RQ-09, RQ-21.

**Fazer**

- executar API tests de token ausente/inválido, artifact token de outro device/expirado e late reports;
- em live, quando seguro e controlável, interromper rede durante download para observar `failed`/recuperação sem corromper firmware executável;
- confirmar que job C3 não seleciona device ESP8266 e vice-versa;
- após falha, reiniciar/recuperar rede e confirmar que device continua bootável na versão válida anterior quando o updater não concluiu.

**Não fazer**

- não induzir power-loss durante flash sem protocolo específico de bancada e recuperação USB;
- não usar device de produção para fault injection destrutiva;
- não rotular binário cruzado manualmente como C3 para “provar” segurança sem entender o risco residual de metadata.

**Teste**

- negative contract tests da API;
- network interruption live controlada;
- boot/version after failure.

**Pronto quando**  
Falha é terminal/observável e não existe seleção cruzada no fluxo de catálogo corretamente rotulado.

**Commit sugerido**  
Nenhum.

---

# E8 — Verify-final contra o pedido original

## E8.S1 — Consolidar tabela PASS/FAIL/INCONCLUSIVE por requisito

**Objetivo**  
Validar o outcome perceptível original, não apenas suites verdes.

**Requisitos cobertos**  
RQ-01 a RQ-21.

**Fazer**

Produzir ao final da execução uma tabela:

| RQ | Resultado | Evidência | Regressão/Pendência |
|---|---|---|---|
| RQ-01 | PASS/FAIL/... | build/live ref | ... |

Confirmar explicitamente:

1. firmware C3 preserva APIs/config/token/counter/reboot/factory reset remoto;
2. MAC é STA e coincide em Serial/HTML/status/DHCP evidence quando disponível;
3. 8,5 dBm/sleep off precedem associação;
4. reconnect não gera begin concorrente e registra reason;
5. INPUT_1 conta por transição; INPUT_2 não conta;
6. dois inputs não executam factory reset;
7. RGB diferencia Wi-Fi, backend freshness, OTA e failure;
8. dual OTA partition layout é comprovado;
9. OTA end-to-end atualiza e reconcilia versão;
10. family isolation impede links/targets cruzados quando metadata está correta;
11. nenhum secret aparece em logs/HTML;
12. ESP8266 continua passando regressão;
13. MFE continua somente via `production-pulse-api`.

**Não fazer**

- não converter `INCONCLUSIVE` em PASS por confiança;
- não omitir falha porque o restante funcionou;
- não usar commit criado como evidência.

**Evidência**  
`platform-quality-testing.mdc` e `plan-execution.mdc` exigem validação do objetivo e classificação honesta das camadas não executadas.

**Dependências**  
E1-E7 conforme ambientes disponíveis.

**Teste**  
Revisão cruzada das evidências registradas + diff final + suites do estado final se código mudou durante live fixes.

**Pronto quando**  
Cada requisito material possui estado e evidência, e qualquer pendência live está explícita.

**Commit sugerido**  
Nenhum, salvo fix real de regressão.

## Rastreabilidade resumida

| Área | Positive | Sibling | Negative |
|---|---|---|---|
| identidade | STA MAC único | aliases iguais | nenhum AP/base MAC |
| Wi-Fi | associa/reconecta | segundo ambiente/device | sem begin concorrente |
| auth | token correto | BFF poll | ausente/inválido |
| inputs | INPUT_1 pulsa | múltiplos pulsos | held LOW/input2 não contam |
| factory reset | endpoint válido | reboot | inputs/invalid token não resetam |
| LED | healthy verde | recovery | public request não marca healthy |
| OTA | C3→C3 update | ESP8266 regressão | cross-family/token/failure |
| partition | dual slots | rebuild same profile | No OTA não passa |

## Risco residual

O isolamento atual do catálogo é baseado em `driver_key`/metadata, não em attestation criptográfica da arquitetura do `.bin`. Portanto, a entrega pode provar que o **fluxo normal corretamente rotulado** não cruza famílias e que o artefato C3 usado tem provenance do build C3. Impedir matematicamente um operador de subir um binário de outra arquitetura com metadata deliberadamente errada exigiria capacidade adicional de artifact validation/attestation fora do escopo atual.

## Revisão adversarial final

- O device conectou ao hotspot, mas a API no container alcança a LAN? E6 prova separadamente.
- O LED ficou verde por uma visita manual pública? E5.S2 deve rejeitar isso.
- O MAC no status veio correto, mas a TI cadastrou outro? Capturar/comparar DHCP evidence quando disponível.
- OTA reportou updated, mas voltou na versão antiga? E7 exige reconciliação pós-reboot.
- API bloqueia cross-family, mas artefato foi rotulado errado? Registrar provenance e risco residual; não prometer attestation inexistente.
- Compile usa min_spiffs, mas a placa foi gravada anteriormente com outra partition table? E1.S2/E7 só passam se a imagem inicial real tiver o layout esperado.
