# Playbook — Inventário técnico Protheus: RPO, SmartClient/WebApp e canais de inspeção (POC 18/11/2026)

> **TASK:** `EVA-TOTVS-RPO-SMARTCLIENT-AUTOMATION-FEASIBILITY-01`
> **Escopo executado:** `READ_ONLY_FEASIBILITY / ENVIRONMENT_DISCOVERY / NO_ERP_WRITE / NO_RPO_COMPILE / NO_DEPLOY`
> **Objetivo:** comprovar quais canais o Devin consegue usar para inventariar
> rotinas/funções compiladas no RPO e abrir sessão SmartClient, fundamentando
> uma futura capacidade de inventário técnico TOTVS consumível por agente.

Este playbook registra **apenas evidência live medida**. Toda coleta é
read-only, sem credenciais no documento e sem escrita no ERP.

---

## 1. Mapa de superfície live (RQ-01)

Probe TCP/HTTP executado a partir do host Devin (visto pelo broker como
`192.168.1.34`). Portas verificadas por conexão efetiva:

| Host | Porta | Serviço identificado | Protocolo | Estado |
|---|---|---|---|---|
| 192.168.1.231 | 8061 | REST Protheus **PRD** (`/restall`) | HTTP | `PROVEN_LIVE` |
| 192.168.1.231 | 3389 | RDP (Windows) | RDP | `PROVEN_LIVE` |
| 192.168.1.232 | 1450 | **TOTVS Broker HTTP Balance** → SmartClient WebApp | HTTPS | `PROVEN_LIVE` |
| 192.168.1.232 | 4321 | **SmartClient WebApp direto** do appserver | HTTP | `PROVEN_LIVE` |
| 192.168.1.232 | 5555 | SmartClient TCP (binário proprietário) | TCP binário | `PROVEN_LIVE` (porta) |
| 192.168.1.232 | 8080 | **ADVPL WSDL/SOAP catalog** (`WSINDEX.apw`) | HTTP | `PROVEN_LIVE` |
| 192.168.1.232 | 3389 | RDP (Windows) | RDP | `PROVEN_LIVE` |
| 192.168.1.232 | 445/139 | SMB | SMB | `PROVEN_LIVE` (porta) |
| 192.168.1.232 | 22 | SSH | — | **fechada** |
| 192.168.1.233 | 8701 | REST Protheus **TST01** (`/rest`) | HTTP | `PROVEN_LIVE` |
| 192.168.1.233 | 5555 | SmartClient TCP | TCP binário | `PROVEN_LIVE` (porta) |
| 192.168.1.233 | 3389 | RDP | RDP | `PROVEN_LIVE` |
| 192.168.1.233 | 445 | SMB | SMB | `PROVEN_LIVE` (porta) |
| 192.168.1.233 | 1450/4321/8080 | WebApp/SOAP | — | **fechadas** |

**Versões capturadas live (banners oficiais):**

- Appserver/broker: `24.3.1.5 guapor win64 rel-dbg 46783` (build 11/02/2026) —
  header `Server` e página de erro do broker.
- WebApp: `Build 7.00.240223P`, `Versão 10.2.0-RC10`
  (header `X-Server-Version`/`X-Server-Build` em `:4321` e tela de parâmetros).
- WS host: `ADVPL WSDL Server 1.110216` (header `XAPWSBUILD` em `:8080`).

**Nota HTTP×HTTPS na 1450:** `http://…:1450` aceita TCP e **fecha sem resposta**
(empty reply) — a entrada correta é **HTTPS**.

---

## 2. SmartClient WebApp (RQ-03)

### 2.1 Sequência de acesso reproduzível

```bash
# 1) obter cookie do broker (obrigatório — sem ele responde
#    "error in access to broker / MISSING COOKIE FOR BROKER")
curl -sk -c /tmp/cj.txt "https://192.168.1.232:1450/"

# 2) carregar a página de parâmetros iniciais
curl -sk -b /tmp/cj.txt "https://192.168.1.232:1450/webapp/"
# → "TOTVS WebApp - Parâmetros Iniciais"
```

O cookie `TOTVS_PROXY_SH_001` é emitido pelo **Broker HTTP Balance Server**;
a 1450 é o balanceador na frente dos appservers. A 4321 é o webapp **direto**
de uma instância (sem broker).

### 2.2 Tela de parâmetros (headless, screenshot comprovada)

- **Programa Inicial:** única opção `SIGAADV` (ambiente de desenvolvimento AdvPL).
- **Ambiente no servidor:** única opção `DELPI`.
- Nenhum módulo de negócio (`SIGAEST`, `SIGAFAT`, …) está publicado neste webapp —
  ou seja, o webapp é um ponto de entrada **de desenvolvimento**, não de operação.

### 2.3 Resultado do teste de sessão (Playwright + Chromium headless)

Após clicar `OK` (SIGAADV + DELPI), a sequência observada foi:

```
GET /webapp/<uuid>/start          → sessão alocada
wss://192.168.1.232:1450/webapp/<uuid>/ws  → WebSocket da sessão aberto
ws(s)://127.0.0.1:2601/agent?uuid=0        → ~30 tentativas consecutivas
```

**Conclusão `PROVEN_LIVE`:** o SIGAADV exige o **agente SmartClient local**
(porta 2601 no host do usuário). Sem agente instalado, a página permanece em
branco — a sessão não renderiza no navegador. O host Devin (Linux, headless)
não possui o agente; instalar é fora de escopo e exigiria aprovação.

- `SMARTCLIENT_BROWSER`: **PROVEN** — webapp carrega integralmente headless
  (Chromium via `mcr.microsoft.com/playwright` em Docker; o chromium do host
  falha por `libnspr4.so` ausente — workaround documentado).
- `SMARTCLIENT_AUTH`: **TO_INVENTORY** — a tela de login (usuário/senha) só
  aparece depois que o agente local assume a sessão; não alcançada. A conta de
  serviço REST **não foi presumida** válida para login interativo.
- `SMARTCLIENT_SESSION`: **INCONCLUSIVE/BLOCKED** — depende de agente local
  `127.0.0.1:2601` (TOTVS Monitor/SmartClient desktop).
- `DIAGNOSTIC_CENTER` / `CALL_STACK_ACCESS`: **BLOCKED** — exigem sessão
  autenticada; inacessíveis sem agente + credencial interativa.

### 2.4 Pontos de intervenção humana necessários

| Etapa | Requisito |
|---|---|
| Sessão SmartClient completa | Agente TOTVS (Monitor) instalado num host autorizado **ou** RDP em `.232/.233` (3389 aberto) |
| Autenticação | Identidade interativa aprovada (a definir; conta de serviço REST ≠ login interativo comprovado) |
| Central de Diagnóstico | Sessão autenticada + perfil que permita ferramentas de diagnóstico |

---

## 3. Inspeção do RPO (RQ-02)

Canais avaliados para consultar **funções/rotinas efetivamente compiladas**:

| Canal | Método | Resultado |
|---|---|---|
| RESTALL (`:8061` / `:8701`) | classes publicadas | `PROVEN_LIVE` para catálogo REST; **nenhuma classe de inspeção de RPO** no inventário G0-B (527/526 classes) |
| SOAP/WS (`:8080` `WSINDEX.apw`) | catálogo de serviços + status | `PROVEN_LIVE` — inventário de serviços publicados (lista abaixo); **metadados de função não expostos** |
| FWDICTIONARY/FWWSMODEL (SOAP) | consulta dicionário/modelo | `DESABILITADO` no catálogo — não invocável |
| SmartClient TCP (`:5555`) | sessão nativa | `BLOCKED` — protocolo binário proprietário, sem cliente headless |
| SIGAADV via WebApp | IDE AdvPL (Inspetor de RPO nativo) | `BLOCKED` — exige agente local (§2.3) |
| TOTVS DevStudio (VSCode ext./Eclipse TDS) | inspetor de objetos/funções | `TO_INVENTORY` — requer estação autorizada + credencial dev; não instalado |
| RPO via SMB (`:445`) | leitura do arquivo `.rpo` | `FORBIDDEN` pela task — binário proprietário, extração/decompilação proibida |
| Façade `.PRW` de inventário | WSRESTFUL read-only chamando introspecção AdvPL | `PLANNED` — exige compilação autorizada (próximo gate) |

**Resposta RQ-02:** o Devin **não consegue** consultar funções compiladas do
RPO com as ferramentas atuais — o acesso fica bloqueado no requisito de
agente local/DevStudio. O que é comprovável live hoje: **catálogo REST,
catálogo SOAP, versões de runtime e dicionário SX3 via ODBC** (G0-A).

### 3.1 Inventário SOAP capturado (`:8080`, 32 serviços)

`Status: HABILITADO` (20 — cluster fiscal/TSS/NF-e):
`FECRED`, `MANIFESTACAODESTINATARIO`, `NFECFGLOC`, `NFESBRA`, `NFESLOC`,
`NFSE001`, `RECOPI`, `SPEDADM`, `SPEDCFGNFE`, `TSSAUTHENTICATION`, `TSSGNRE`,
`TSSMANAGEREDI`, `TSSWSCONSIGNADO`, `TSSWSREINF`, `TSSWSSIGNATURE`,
`TSSWSSOCIAL`, `TSSWSSUNAT`, `WEBSERVAGRO`, `WSCPESERVICEARG`, `WSFEV1`, `WSLPEG`.

`Status: DESABILITADO` (12 — framework/dev/dicionário/EAI):
`EAISERVICE`, `FWAUTHENTICATION`, `FWDICTIONARY`, `FWHOSTCOMMUNICATION`,
`FWPORTALWEBSERVICE`, `FWWSEAI`, `FWWSECM`, `FWWSLOOKUP`, `FWWSMODEL`,
`FWWSPROTHEUSWIDGET`, `TWSSERVICE` *(+1)*.

**Corrobora G0-C:** `EAISERVICE`/`FWWSEAI` desabilitados = mais uma evidência
independente de que a infra EAI não está operacional para MATI060/SA5.

Comando reproduzível do censo:

```bash
curl -s "http://192.168.1.232:8080/" | grep -o 'WSVCNAME=[A-Z0-9_]*' | sort -u
# para cada serviço:
curl -s "http://192.168.1.232:8080/WSINDEX.apw?cOp=02&WSVCNAME=<SVC>" \
  | grep -o 'Status </td><td> [A-Z]*'
```

---

## 4. Piloto MATA010 / MATA061 (RQ-04/RQ-05)

| Informação | Fonte GitHub | REST/Runtime | Estado |
|---|---|---|---|
| MATA010 rotina | `MATA010M_DLP.PRW` versionado; handler `DLP04I01.PRW` (ExecAuto 22 campos) | `DELPIPRODUTO` POST/PUT `PROVEN_LIVE` em PRD+TST01 | `MATCH` (contrato REST); presença compilada da rotina em si = `INCONCLUSIVE` |
| MATA010 no SmartClient | — | não alcançado (agente local) | `INCONCLUSIVE` |
| MATA061 rotina | `Dmata061.prx` + `mata061_dlp.prx` (pasta `NãoCompilar/`!) | nenhum REST SA5 em 527/526 classes | `SOURCE_ONLY` |
| MATI060 adapter | `IntegDef→MATI060` em `Dmata061.prx` | `EAISERVICE`/`FWWSEAI` **DESABILITADO**; TOTVSEAI sem integrações (G0-C) | `RUNTIME_DISABLED` — confirma G0-C |
| Pontos de entrada | declarações no fonte | evidência runtime indisponível | `INCONCLUSIVE` |
| Versão compilada vs fonte | commit GitHub | build do RPO não consultável | `INCONCLUSIVE` |

`NãoCompilar/mata061_dlp.prx`: o próprio nome da pasta indica que o fonte é
referência, não necessariamente o que roda — reforça a necessidade de
inspeção de RPO para provar drift fonte×runtime.

---

## 5. Automação viável × bloqueada (RQ-06)

### Automatizável hoje (sem nova autorização)

| Atividade | Fonte oficial | Método | Formato | Intervenção humana |
|---|---|---|---|---|
| Catálogo REST (classes/URIs/métodos) | RESTALL | form-login serviço + GET catálogo | HTML→JSON | nenhuma |
| Inventário SOAP + status | `WSINDEX.apw` (:8080) | GET catalog + por-serviço | JSON/CSV | nenhuma |
| Versões runtime (appserver/webapp/WS) | banners HTTP | GET headers | JSON | nenhuma |
| Dicionário SX3/físico | ODBC TOTVS | queries read-only (G0-A) | SQL→JSON | nenhuma |
| Programa inicial/ambientes webapp | WebApp params | Playwright headless (Docker) | screenshot+DOM | nenhuma |
| Diff PRD×TST01 catálogos | RESTALL ambos | mesma coleta ×2 | relatório | nenhuma |

### Bloqueado até autorização/dependência

| Atividade | Bloqueio | Dependência |
|---|---|---|
| Inventário de funções compiladas no RPO | sem API de inspeção | façade `.PRW` read-only **ou** DevStudio autorizado |
| Pontos de entrada ativos | idem | idem |
| Central de Diagnóstico | sessão autenticada | agente local/RDP + credencial interativa |
| Pilha de chamada/parâmetros de rotina | idem | idem |
| Drift fonte×RPO | sem metadados de build do RPO | façade ou Inspetor (DevStudio) |
| RPO via SMB | proibido pela governança | nunca — binário proprietário |

---

## 6. Arquitetura mínima candidata (RQ-08)

```
RESTALL / SOAP WSINDEX / ODBC SX3 / WebApp params / banners
        │  (coletores read-only, conta de serviço governada)
        ▼
inventário técnico versionado (JSON + timestamp + ambiente + provenance)
        │  em docs/ — NÃO é source of truth do ERP
        ▼
análise de divergência (fonte GitHub × catálogo × runtime)
        │
        ▼
relatórios/handoffs → consumidores autorizados (api-delpi, Coordination)
```

- **Owner coleta:** api-delpi (já detém credenciais governadas RESTALL/ODBC).
- **Owner dos dados:** Integrações TOTVS; inventário = fotografia, não fonte
  operacional.
- **Façade `.PRW` de inventário (opcional, próximo gate):** WSRESTFUL read-only
  no padrão `DLP04I01`/`delpiproduto`, expondo metadados de funções/pontos de
  entrada via introspecção AdvPL — resolve o gap central com aprovação mínima
  de compilação.
- **Política:** sem credencial em artefato; logs sem dados de negócio; acesso
  revogável pela conta de serviço; frequência sugerida = sob demanda + antes
  de cada gate de implementação.

---

## 7. Necessidade de agente/skill/MCP (RQ-07)

Aplicando o Abstraction Gate (menor solução adequada):

| Opção | Avaliação |
|---|---|
| **Script/CLI de inventário** | **Recomendado** — cobre 100% do bloco "automatizável hoje"; batch, auditável, sem sessão persistente |
| Capacidade de API interna | Opcional — se a consulta precisar ser online/sob demanda pelos agentes |
| Skill especializada | `PLANNED` — útil quando houver façade `.PRW` e runbook de comparação; prematuro agora |
| MCP dedicado | **Não recomendado** — inventário é batch; MCP só faria sentido após façade online com ferramentas governadas |
| Agente com acesso persistente | **Rejeitado** — task proíbe agente operacional persistente |

**Resposta:** não criar agente/skill/MCP agora. A menor capacidade correta é
o **coletor versionado** (script governado) + futura façade `.PRW` read-only
para o que hoje é `INCONCLUSIVE`.

---

## 8. Referências

- Inventário de campos SB1/SX3/SA5 (G0-A) e RESTALL (G0-B):
  `playbook-cadastro-produto-sb1-sx3-sa5.md` §§12–14
- Verificação live MATI060/TOTVSEAI (G0-C): mesma fonte §14
- Fontes: `docs/13-fontes-totvs-protheus/73. CRM/{Dmata061.prx, MATA010M_DLP.PRW, NãoCompilar/mata061_dlp.prx}`
- Ambiente/compose: `infra/README-ambiente.md`
