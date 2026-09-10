# Plano de implementação — API, driver e compatibilidade OTA do ESP32-C3

> **Status:** plano executável; revalidar regras/código antes de cada `E*.S*`.
>
> **Pai:** [`ESP32C3-SUPER-MINI-MASTER-PLAN.md`](./ESP32C3-SUPER-MINI-MASTER-PLAN.md)

## Overview

Registrar `esp32c3_counter_v1` no bounded context Production Pulse sem duplicar o protocolo HTTP do contador, preservar a regressão do ESP8266 e provar que vínculo/job OTA respeitam `driver_key`, mantendo a API como autoridade final.

## Ledger local

| Requisito | Cobertura |
|---|---|
| RQ-02 contratos HTTP existentes | E1/E2 |
| RQ-07 token atual | E1/E2/E3 |
| RQ-08 OTA existente | E3 |
| RQ-09 família isolada | E2/E3 |
| RQ-19 boundary MFE→BFF | E4 |
| RQ-21 validação por camada | E5 |

## Evidências e decisões

**FATO.** `Esp8266CounterDriver` concentra protocolo HTTP, capabilities e parsing de identidade.

**FATO.** `device_http_support.py` já centraliza base URL, timeout, `X-Device-Token`, GET/POST e parsing compartilhado.

**FATO.** `DeviceDriverRegistryService` separa definição declarativa de implementação registrada.

**FATO.** `FirmwareUpdateJobService.create_job()` só inclui device quando `device.driver_key == firmware.driver_key`.

**FATO.** `DeviceFirmwareLinkService._assert_compatible()` é autoridade do vínculo e rejeita `firmwareLinkIncompatible`.

**DECISÃO.** Não duplicar toda a lógica Python para o C3. Extrair somente o protocolo de contador que passa a ter dois consumidores reais, preservando wrappers de hardware/driver distintos.

**DECISÃO.** Não alterar schema ou `DeviceOtaService` para repetir uma compatibilidade já garantida na criação de vínculo/job, salvo evidência de bypass real durante execução.

## CURRENT → TARGET

```text
CURRENT
esp8266_counter_v1
  → Esp8266CounterDriver
  → device_http_support
  → ESP8266 /api/*

TARGET
esp8266_counter_v1 ──┐
                     ├→ protocolo HTTP counter compartilhado
esp32c3_counter_v1 ──┘
                     → device_http_support
                     → device /api/*

firmware link/job
  → continua validando driver_key no backend
```

## Estado antes × depois

| Caso | Antes | Depois | Deve mudar? |
|---|---|---|---|
| ESP8266 poll/commands | funcional | funcional | não |
| C3 poll/commands | inexistente | funcional via novo driver | sim |
| capabilities counter | ESP8266 | iguais semanticamente no C3 | adição |
| OTA ESP8266→C3 | sem C3 | rejeitado por driver mismatch | sim, novo negativo |
| OTA C3→ESP8266 | sem C3 | rejeitado por driver mismatch | sim, novo negativo |
| MFE compatibility | catálogo-driven | inclui C3 via catálogo | herança |
| schema | suficiente | sem migration | não |

---

# E1 — Compartilhar protocolo HTTP do contador sem quebrar ESP8266

## E1.S1 — Extrair implementação neutra do protocolo counter

**Objetivo**  
Ter uma única implementação para paths, parsing, timeout, commands e config usados por contadores ESP8266 e ESP32-C3.

**Requisitos cobertos**  
RQ-02, RQ-07, RQ-09.

**Fazer**

- criar módulo em `production-pulse-api/production_pulse_app/infrastructure/drivers/` com nome inglês e responsabilidade explícita, por exemplo `http_counter_driver.py`;
- mover para ele a implementação neutra de `/api/contador`, `/api/status`, `/api/config`, commands, capabilities e parsing de controller identity;
- parametrizar somente `driver_key` e dependências técnicas (`timeout_seconds`, client) necessárias;
- reutilizar `device_http_support.py` para auth/header/HTTP;
- manter em `esp8266_counter_driver.py` o símbolo público `Esp8266CounterDriver` como wrapper fino configurado com `esp8266_counter_v1`;
- preservar/reexportar `parse_controller_identity` se testes/consumidores atuais importarem esse símbolo;
- manter error codes e `CommandResult` existentes.

**Não fazer**

- não criar `if driver_key == ...` para C3 dentro de cada método;
- não duplicar paths/capabilities em dois arquivos completos;
- não mover lógica de domínio para `shared/` global;
- não alterar DTO do MFE.

**Evidência**  
Há dois drivers do mesmo protocolo HTTP e `device_http_support.py` já demonstra o boundary infra correto. A extração permanece dentro do bounded context e tem 2 consumidores reais.

**Dependências**  
Firmware E1.S1 deve ter confirmado que o C3 mantém o mesmo protocolo `/api/*`.

**Teste**

```bash
cd production-pulse-api && pytest tests/test_esp8266_counter_driver.py -q
```

- positive: ESP8266 continua lendo/configurando/comandando pelos mesmos paths;
- sibling: status aliases e error handling permanecem;
- negative: unsupported command continua `unsupported_command` e respostas inválidas continuam rejeitadas.

**Pronto quando**  
A implementação ESP8266 passa os testes sem duplicação do protocolo e nenhum contrato observável mudou.

**Commit sugerido**  
`refactor: compartilha protocolo HTTP dos contadores sem mudar o ESP8266`

---

# E2 — Registrar `esp32c3_counter_v1`

## E2.S1 — Adicionar definição declarativa do driver C3

**Objetivo**  
Disponibilizar o C3 pelo registry com a mesma semântica operacional do contador atual, mas identidade de driver distinta.

**Requisitos cobertos**  
RQ-09, RQ-19.

**Fazer**

- adicionar `esp32c3_counter_v1` em `production_pulse_app/content/device_drivers.json`;
- usar `roleKey=pulse_counter`;
- manter métrica `counter`, monotonic, primary, operatorSurface `counter_pad`, operatorEligible, poll timeout e `counterRestore` equivalentes ao ESP8266;
- manter commands `increment`, `decrement`, `reset`, `set`, `configure`, `reboot`, `factory_reset` porque continuam contratos HTTP suportados, mesmo que o hardware físico não tenha botão de decremento;
- label/description PT devem deixar explícito ESP32-C3 Super Mini / contador de golpes.

**Não fazer**

- não reutilizar chave `esp8266_counter_v1`;
- não criar capability nova só para `input2`, pois input raw é diagnóstico e não comando/métrica operacional nesta versão;
- não criar `operatorSurface` nova.

**Evidência**  
Registry declarativo é a fonte canônica de capabilities/operator surface; nova família de hardware exige driver key própria para compatibilidade OTA.

**Dependências**  
E1.S1.

**Teste**

- teste de registry deve resolver `esp32c3_counter_v1`;
- positive: capabilities do C3 equivalem às do counter atual;
- sibling: `esp8266_counter_v1` permanece inalterado;
- negative: chave desconhecida continua `unknown_driver`.

**Pronto quando**  
`GET /catalog/drivers` pode expor o C3 sem hardcode no MFE.

**Commit sugerido**  
`feat: registra família de contador ESP32-C3 no catálogo`

## E2.S2 — Registrar implementação C3 como wrapper do protocolo compartilhado

**Objetivo**  
Fazer poll/test/config/commands funcionarem para `esp32c3_counter_v1` usando a mesma implementação de protocolo.

**Requisitos cobertos**  
RQ-02, RQ-07, RQ-09.

**Fazer**

- criar `esp32c3_counter_driver.py` com wrapper fino configurado para `esp32c3_counter_v1`;
- registrar a implementação em `startup/register_device_drivers.py`;
- manter log de startup coerente com lista registrada;
- criar `tests/test_esp32c3_counter_driver.py` ou parametrizar teste compartilhado sem reduzir cobertura do teste ESP8266;
- provar paths, header token, parsing de status e commands.

**Não fazer**

- não copiar a classe inteira do ESP8266;
- não adicionar comportamento específico de LED/input ao backend driver;
- não tornar status fields novos obrigatórios ao parser.

**Evidência**  
O protocolo é idêntico e a diferença relevante para o backend é o `driver_key` de compatibilidade/registry.

**Dependências**  
E2.S1.

**Teste**

```bash
cd production-pulse-api && pytest tests/test_esp8266_counter_driver.py tests/test_esp32c3_counter_driver.py -q
```

- positive: C3 poll/test/config/commands usam os endpoints esperados;
- sibling: ESP8266 continua passando o mesmo corpus;
- negative: token ausente no cadastro gera headers vazios sem inventar credencial; HTTP 4xx/timeout continua traduzido pelo support existente.

**Pronto quando**  
O registry possui implementação para ambas as chaves e os contratos irmãos têm regressão.

**Commit sugerido**  
`feat: liga o driver ESP32-C3 ao protocolo de contador existente`

---

# E3 — Provar isolamento OTA e vínculo no backend

## E3.S1 — Cobrir vínculo explícito compatível/incompatível entre famílias

**Objetivo**  
Provar que um firmware ESP8266 não pode ser vinculado a device C3 e vice-versa, mantendo API como autoridade final.

**Requisitos cobertos**  
RQ-09, RQ-19.

**Fazer**

- estender `tests/test_firmware_link_api.py` e/ou testes do `DeviceFirmwareLinkService` com firmwares publicados contendo `driver_key` das duas famílias;
- testar vínculo C3→firmware C3;
- testar rejeição C3→firmware ESP8266;
- testar rejeição ESP8266→firmware C3;
- manter semântica `assignedFirmwareKey` somente para vínculo explícito.

**Não fazer**

- não adicionar compatibilidade hardcoded no MFE;
- não gerar edge por match de capability;
- não duplicar validação em controller se service já é owner.

**Evidência**  
`DeviceFirmwareLinkService._assert_compatible()` já é o owner da decisão e retorna `firmwareLinkIncompatible`.

**Dependências**  
E2.S2.

**Teste**

```bash
cd production-pulse-api && pytest tests/test_firmware_link_api.py -q
```

**Pronto quando**  
Casos cruzados falham no backend e caso C3 correto cria `assignedFirmwareKey` esperado.

**Commit sugerido**  
`test: protege vínculo OTA entre famílias ESP8266 e ESP32-C3`

## E3.S2 — Cobrir elegibilidade de job OTA por `driver_key`

**Objetivo**  
Provar que jobs/campanhas não selecionam hardware de família errada mesmo com filtro/family semelhante.

**Requisitos cobertos**  
RQ-08, RQ-09.

**Fazer**

- estender `tests/test_firmware_ota_api.py` ou teste específico de job service;
- publicar firmware C3 com `firmware_key=esp32c3_counter_v1` e `driver_key=esp32c3_counter_v1`;
- criar devices ESP8266 e C3 na mesma filial;
- provar que job C3 cria target somente C3;
- provar que seleção explícita de device id ESP8266 para firmware C3 termina em `noEligibleDevices` quando nenhum C3 elegível;
- repetir simetricamente para firmware ESP8266 quando útil como sibling.

**Não fazer**

- não relaxar igualdade de `driver_key` para aceitar apenas `roleKey=pulse_counter`;
- não mover seleção para frontend;
- não adicionar campo DB novo para plataforma de hardware nesta entrega.

**Evidência**  
`FirmwareUpdateJobService.create_job()` já exige igualdade do driver do device e firmware; teste novo congela o guardrail para a família C3.

**Dependências**  
E3.S1.

**Teste**

```bash
cd production-pulse-api && pytest tests/test_firmware_ota_api.py -q
```

**Pronto quando**  
Nenhum target cruzado é criado e o happy path C3 continua produzindo job/target autorizado.

**Commit sugerido**  
`test: impede campanhas OTA cruzadas entre ESP8266 e ESP32-C3`

## E3.S3 — Preservar o canal device OTA sem duplicar compatibilidade

**Objetivo**  
Garantir que `DeviceOtaService` continue autenticando e servindo apenas targets previamente autorizados, sem introduzir segunda regra de família.

**Requisitos cobertos**  
RQ-07, RQ-08, RQ-09.

**Fazer**

- adicionar/ajustar fixtures C3 aos testes do canal `/device-ota/*`;
- provar check C3 autenticado, artifact token associado ao mesmo device, reports e versão instalada;
- documentar que compatibilidade já é decidida na criação do vínculo/job; `DeviceOtaService` trabalha com target autorizado;
- somente alterar `DeviceOtaService` se execução revelar um bypass real comprovado; isso deve ser registrado como `EXECUTION_DRIFT` antes do diff.

**Não fazer**

- não criar `if firmwareKey.startswith("esp32")`;
- não duplicar `driver_key` check em cada report/download sem evidência de bypass;
- não logar artifact token/device token.

**Evidência**  
`DeviceOtaService` valida token contra o device, artifact token contra o mesmo device e status aberto do target. O target nasce do service de job já compatível.

**Dependências**  
E3.S2.

**Teste**

```bash
cd production-pulse-api && pytest tests/test_firmware_ota_api.py -q
```

- positive: C3 recebe metadata/artefato do target correto e reporta updated;
- sibling: ESP8266 continua o fluxo existente;
- negative: token errado/ausente, target de outro device e late report continuam rejeitados.

**Pronto quando**  
O canal OTA C3 reutiliza as mesmas invariantes de autenticação/target existentes.

**Commit sugerido**  
`test: cobre canal OTA do ESP32-C3 sem duplicar regra de família`

---

# E4 — Verificar consumidores MFE e documentação

## E4.S1 — Provar que o MFE é catálogo-driven para o novo driver

**Objetivo**  
Evitar mudança antecipatória no MFE e confirmar que `esp32c3_counter_v1` aparece pelos contratos existentes.

**Requisitos cobertos**  
RQ-19.

**Fazer**

- revisar `FirmwareLinksPage`, `FirmwareDeviceLinkCanvas`, `firmwareLinkGraph.ts`, cadastro/driver selectors e `productionPulseKit.structural.test.ts`;
- provar que famílias compatíveis são derivadas do catálogo/`compatibleDriverKeys` e que driver list vem de `/catalog/drivers`;
- registrar resultado da verificação no PR/execução;
- se hardcode material impedir C3, classificar `EXECUTION_DRIFT`, atualizar este plano e corrigir a fonte canônica com teste antes de prosseguir.

**Não fazer**

- não adicionar lista C3 manual ao frontend sem evidência;
- não alterar Connection Mode, edges ou `assignedFirmwareKey`;
- não chamar api-delpi.

**Evidência**  
A regra Admin Hub e utilitários atuais já definem compatibilidade catálogo-driven; mudança de driver deve ser herança quando esse pipeline estiver intacto.

**Dependências**  
E2.S1.

**Teste**

```bash
cd plugins/production-pulse && npm run test && npm run build
```

A execução desse gate é obrigatória se houver qualquer diff MFE; sem diff, pelo menos os testes estruturais relevantes devem ser usados como evidência quando ambiente permitir.

**Pronto quando**  
O C3 não exige hardcode no browser e o boundary MFE→production-pulse-api permanece.

**Commit sugerido**  
Sem commit se verificação confirmar herança. Se houver drift comprovado, mensagem específica ao fix real.

## E4.S2 — Sincronizar documentação canônica afetada

**Objetivo**  
Documentar driver, firmware e guardrails C3 sem transformar plano em contrato concorrente.

**Requisitos cobertos**  
RQ-01, RQ-09, RQ-10, RQ-21.

**Fazer**

- atualizar `DEVICE-DRIVERS.md` com `esp32c3_counter_v1` depois que o registry estiver implementado;
- adicionar README do firmware com pins, active LOW, radio config, partition profile, first-flash e segurança de secrets;
- atualizar documentação OTA vigente somente onde a realidade mudou; não perpetuar header histórico `não implementado` como autoridade quando código prova o contrário;
- revisar `HELP-CONTENT.md`/`PP_HELP` para determinar se texto de controller code específico do ESP8266 virou enganoso; atualizar apenas conteúdo realmente afetado.

**Não fazer**

- não copiar o plano inteiro para `DEVICE-DRIVERS.md`;
- não registrar P1/P2 como entregue;
- não dizer que hardware foi homologado antes do live test.

**Evidência**  
`plugins-documentation.mdc` exige documentação durável para mudança relevante; docs canônicos devem refletir o estado implementado.

**Dependências**  
E2/E3 implementados.

**Teste**

- verificar links/paths Markdown e coerência com `device_drivers.json`;
- positive: docs identificam C3 como família distinta;
- negative: nenhuma instrução sugere firmware ESP8266 como compatível com C3.

**Pronto quando**  
Docs de driver/firmware refletem o contrato real, sem declarar itens live não testados.

**Commit sugerido**  
`docs: documenta família ESP32-C3 e fluxo OTA preservado`

---

# E5 — Verify-final API/BFF

## E5.S1 — Executar regressão completa e gates arquiteturais materiais

**Objetivo**  
Provar que adicionar C3 não quebrou ESP8266, auth, OTA, registry ou boundaries.

**Requisitos cobertos**  
RQ-02, RQ-07, RQ-08, RQ-09, RQ-19, RQ-21.

**Fazer**

```bash
cd production-pulse-api && pytest tests -q
```

Quando o diff de código/API exigir conforme `.cursor/rules/test-and-commit.mdc`, executar também os audits de arquitetura Phase 3/platform guardrails contra a base correta.

Se MFE foi alterado:

```bash
cd plugins/production-pulse && npm run test && npm run build
```

- revisar diff real por scope, duplicação, secrets e contrato;
- registrar failures como `CAUSADA_PELO_DIFF`, `PREEXISTENTE_CONFIRMADA`, `INFRA/AMBIENTE` ou `INCONCLUSIVE`;
- confirmar que não houve migration;
- confirmar que `api-delpi` não foi tocada.

**Não fazer**

- não enfraquecer testes/gates;
- não declarar CI todo verde sem executar;
- não avançar para live OTA se family isolation tests estiverem falhando.

**Evidência**  
A mudança toca registry, driver, auth HTTP e OTA compatibility; regressão completa é proporcional ao risco.

**Dependências**  
E1-E4.

**Teste**  
Comandos acima + casos cross-family de E3.

**Pronto quando**  
API completa passa no estado final e regressões/pendências estão classificadas com evidência.

**Commit sugerido**  
Sem commit exclusivo, salvo correção de regressão encontrada no verify-final.

## Rastreabilidade

| Requisito | Evidência | Decisão | Subetapa | Teste | Aceite |
|---|---|---|---|---|---|
| RQ-02 | driver atual | protocolo único | E1/E2 | driver tests | contratos iguais |
| RQ-07 | device_http_support | token preservado | E1/E3 | auth negatives | sem bypass/secret |
| RQ-08 | DeviceOtaService | reuso OTA | E3 | firmware OTA tests | fluxo existente |
| RQ-09 | job/link services | driver distinto | E2/E3 | cross-family | zero target/link cruzado |
| RQ-19 | Hub/catalog | catálogo-driven | E4 | MFE tests/build | sem hardcode/api-delpi |
| RQ-21 | quality rules | regressão completa | E5 | pytest + gates | evidência final |

## Risco residual explícito

Separar `driver_key` impede mistura entre famílias **quando o artefato é publicado com metadata correta**. O catálogo atual não prova por inspeção estática que um arquivo `.bin` rotulado como C3 foi realmente compilado para C3. Portanto, a validação de release deve associar artefato ao build reproduzível C3 e o plano live deve incluir conferência de provenance/nome/hash disponível. Não declarar proteção absoluta contra operador rotular binário errado sem um mecanismo de artifact attestation que não existe hoje e está fora desta entrega.

## Revisão adversarial

- Extraímos protocolo porque existem dois consumidores reais, ou criamos abstração especulativa? Devem existir exatamente ESP8266+C3 usando-a.
- O wrapper C3 contém regra duplicada? Deve conter apenas identidade/configuração de driver.
- O MFE recebeu hardcode de família? Deve ser não.
- Role/capability está sendo usada como compatibilidade OTA em vez de driver? Deve ser não.
- Algum job cruzado consegue nascer via `deviceIds` explícito? Teste negativo deve provar que não.
- `DeviceOtaService` ganhou uma segunda regra de compatibilidade sem bypass comprovado? Deve ser não.
