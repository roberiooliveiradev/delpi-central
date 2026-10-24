# Documento 94 — CLARA · Especialista MCP em Controladoria & Finanças

**Estado:** identidade e intenção funcional **APROVADAS** pelo usuário/PO ·
arquitetura executável **TARGET** · `IMPLEMENTATION_AUTHORIZED=NO`.
**Natureza:** especificação de governança e arquitetura. Nenhum servidor
MCP, tool, endpoint, banco, migration, permission ou deploy foi criado.
**Baseline de inventário:** HEAD `348809fa82` (2026-10-24).

Legenda de estado usada neste documento: `CURRENT` (existe no HEAD,
verificado em código) · `TARGET` (comportamento desejado, sem
implementação) · `PLANNED` (dependente de decisão/gate) ·
`DECISION_REQUIRED` (escolha material em aberto).

---

## 1. Identidade aprovada

**CLARA — Especialista em Controladoria & Finanças da Minha DELPI.**

Acrônimo oficial: **C**ontroladoria, **L**eitura, **A**nálise,
**R**esultados e **A**companhamento.

| Atributo | Valor |
|---|---|
| Produto atendido | Portal Controladoria & Finanças (`controllership-finance`) |
| Primeira funcionalidade | Central de Fechamento |
| Primeiro processo | PROC-0072 — Gestão do Fechamento Mensal da Controladoria |
| Família | especialistas MCP da Minha DELPI (TÉO, DAVI, VISTA) |

A identidade não está sujeita a renomeação ou reinterpretação.

## 2. Objetivo e posicionamento

A CLARA é o **adaptador de acesso inteligente** do Portal Controladoria &
Finanças para clientes MCP/assistentes de IA. Ela **não é um novo sistema
de domínio**: não possui regras de fechamento próprias, não acessa bancos
diretamente e não substitui a BFF, o Core ou os owners canônicos.

**Princípio fundamental (aprovado):**

> A CLARA vê o que o usuário autorizado pode ver e executa as operações
> que esse usuário está autorizado a executar, respeitando o contexto, as
> regras de negócio e as confirmações exigidas.

Equivalência de capacidades = **equivalência de autorização**, não
execução automática. Confirmações, validações humanas e pré-condições
exigidas pela operação no Portal são preservadas integralmente.

## 3. Inventário da plataforma MCP (CURRENT — verificado no HEAD)

### 3.1 Fundação compartilhada `shared/delpi_mcp`

Pacote de conformidade (não framework de domínio) consumido pelos
especialistas existentes:

| Módulo | Responsabilidade |
|---|---|
| `tool_validation`, `conformance`, `protocol` | validação wire das tool definitions, namespaces DELPI, política de versão de protocolo |
| `resource_contract` | OAuth + RFC 9728 protected-resource metadata, challenge, audience/scope |
| `transport` | path canônico `/mcp`, lifespan, transport security (DNS-rebinding) |
| `auth` | gate de transporte: proíbe internal service token na superfície de dados do usuário, valida Bearer via `delpi_auth`, audience exata, scopes — **nunca** permissão de negócio |
| `identity` | snapshot read-only do contexto estabelecido por `delpi_auth` |
| `errors`, `tool_metadata` | montagem de `CallToolResult`, vocabulário de erro com redaction, **taxonomia congelada `DISCOVERY / READ / ANALYSIS / PREPARE / ACT`** |

Regra declarada no código: *metadata descreve semântica — nunca autoriza
execução; a AuthZ do backend permanece autoritativa.* Direção de
dependência: `delpi_mcp` → `delpi_auth`, nunca para domínios de apps
(teste `test_no_domain_imports`).

### 3.2 Especialistas existentes

| Especialista | Host (owner API) | Superfície | Evidência |
|---|---|---|---|
| TÉO | `transformometro-api` (`tm_app/interface/mcp/`) | processos, AS-IS, diagnóstico; PREPARE/ACT governado (`governed_writes`: proposal handle HMAC opaco, corpo server-side, `PROPOSAL_ACTOR_MISMATCH/EXPIRED/STALE`, `OUTCOME_VERIFICATION_FAILED`) | `test_teo_mcp_write_governance.py`, `test_teo_mcp_prepare_contract.py`, `test_teo_portal_parity.py` |
| DAVI | `api-delpi` (`app/interface/mcp/`) | descoberta e consulta governada de dados DELPI | `test_davi_mcp_platform_conformance.py`, doc `davi/README.md` |
| VISTA | `tv-dashboard-api` | painéis operacionais e modelos de dados | `test_mcp_platform_conformance.py` |

**Padrão observado:** cada especialista é hospedado **dentro da API owner
do seu domínio**, como superfície `/mcp` adicional, reutilizando
`shared/delpi_mcp` e o próprio contrato OAuth (`oauth_contract.py`,
`resource_metadata.py`). Não existe servidor MCP genérico/central.

### 3.3 Superfície atual da `controllership-finance-api` (CURRENT)

| Rota | Classe candidata | Owner upstream |
|---|---|---|
| `GET /viewer-context` | READ | Core (effective permissions via middleware) |
| `GET /closing/financial-settlements` | READ | api-delpi `/financeiro/settlements/*` |
| `GET /closing/financial-settlements/summary` | READ | api-delpi |
| `GET /closing/stock-inventory` | READ | api-delpi `/financeiro/stock-inventory` |

**Não existe nenhuma operação de escrita** na BFF hoje. Portanto as
classes PREPARE/ACT da CLARA são integralmente `TARGET` e dependem de
contratos governados do Portal que ainda não foram implementados (P1–P6,
docs 08–13, 37).

## 4. Responsabilidades e boundaries (TARGET)

```
Cliente MCP / Assistente IA
  → CLARA MCP surface                 (adaptador: discovery, tool binding,
                                       explicação, conformidade delpi_mcp)
  → integração governada
  → controllership-finance-api        (contratos do Portal, autorização do
                                       produto, regras e pós-condições)
  → owners autorizados:
       Core API                       (identidade, RBAC, effective permissions)
       api-delpi                      (SQL e regras canônicas TOTVS/Protheus)
       strategic-indicators-api       (metas e indicadores)
       outros bounded contexts        (seus próprios dados e operações)
```

| Componente | É responsável por | Não é responsável por |
|---|---|---|
| CLARA | expor capacidades do Portal como tools; explicar/analisar retornos; conduzir PREPARE→confirmação→ACT | regras de negócio, autorização final, SQL, persistência de domínio |
| `controllership-finance-api` | contratos do Portal, AuthZ fail-closed, validação, idempotência, concorrência, pós-condição, auditoria | identidade/RBAC (Core), regras TOTVS (api-delpi) |
| Core API | identidade, effective permissions | regras do Portal |
| api-delpi | dados e regras TOTVS | permissões do Portal |

Proibido: acesso direto da CLARA a banco de qualquer serviço; importar
`domain`/`application` de outro contexto; duplicar fórmulas canônicas
(ex.: divergência P3, CPV vivo, status do snapshot SB9).

## 5. Segurança e autorização

### 5.1 Regras (consistentes com doc 14 e ADR-010)

- JWT identifica e contextualiza; **não é a autoridade final** de
  permissões. O backend resolve effective permissions pelo **Core**.
- Autorização fail-closed em toda tool:
  `capability AND resource_scope/ownership AND business_rule`.
- A CLARA **não cria nem exige permission própria**: nenhuma permission
  por tool MCP, página, botão, endpoint, CRUD, filial ou unidade. Ela
  herda exatamente o conjunto de permissions do contrato do Portal.
  `CURRENT` (manifest 1.0.0 + teste estrutural): somente
  `controllership-finance.access` e `controllership-finance.manage`;
  `MANAGE` não implica `ACCESS`. Nota: o [doc 91](./91-ciclo3-contabilidade-acesso-documentos-historicos-gate.md)
  registra a direção aprovada pelo PO de uma permission específica para
  Contabilidade/DRE, com criação **ADIADA** e dependente de gate
  transversal. Se e quando esse contrato do Portal mudar, a CLARA herda a
  mudança por equivalência — sem permission MCP adicional.
- Audience/scope OAuth da superfície MCP são **binding de transporte**
  (padrão `delpi_mcp.auth`), nunca permissão de negócio.
- A CLARA **não possui identidade administrativa privilegiada**, não
  concede permissões e não eleva privilégios. Internal service tokens são
  proibidos na superfície de dados do usuário (já imposto por
  `delpi_mcp.auth`).
- Filial, unidade, competência e ownership são dimensões de contexto e
  escopo de recurso. Autenticado ≠ autorizado a qualquer recurso.
- Isolamento entre usuários: proposals e contextos vinculados ao ator
  (cf. `PROPOSAL_ACTOR_MISMATCH` do TÉO).
- Secrets/tokens nunca em prompts, respostas, logs comuns ou docs.

### 5.2 Delegação até a api-delpi (`TO_INVENTORY`)

Hoje a BFF delega o Bearer humano + credencial S2S própria
(`X-Delpi-Service-Authorization`, cliente `controllership-finance-api`,
ADR-010) e a api-delpi impõe scope de dataset fail-closed
(`scope_unavailable`). Não está verificado se o token OAuth emitido para
a audience MCP é aceito na mesma cadeia de delegação (audience/scopes
distintos). Ver **CLARA-D03**.

## 6. Padrões de interação

Taxonomia: a congelada da plataforma (`shared/delpi_mcp.tool_metadata`).
Nenhuma classe nova.

| Classe | Comportamento TARGET | Estado |
|---|---|---|
| DISCOVERY | listar as capacidades do Portal **que o usuário efetivamente possui** (derivadas das effective permissions + feature availability), não um catálogo estático | TARGET |
| READ | consultar estados, dados, documentos, pendências, históricos e evidências autorizados — mapeamento 1:1 com contratos da BFF | 4 contratos `CURRENT` na BFF; tools `TARGET` |
| ANALYSIS | interpretar retornos, apontar anomalias/divergências, resumir, orientar — distinguindo **fato (dado do owner)**, **hipótese** e **recomendação** | TARGET |
| PREPARE | montar alteração governada: escopo, parâmetros, impactos, riscos; **não persiste business state**; emite handle opaco vinculado a ator/versão | TARGET (reutilizar padrão TÉO, ver CLARA-D04) |
| ACT | executar operação explicitamente solicitada e autorizada; confirmação conforme política; revalida AuthZ/escopo/estado no backend; idempotência e concorrência otimista; verifica pós-condição real; audita | TARGET — sem contratos de escrita na BFF hoje |

Toda operação de escrita será executada **pela BFF**, nunca pela CLARA; a
CLARA apenas invoca o contrato governado com a identidade do usuário.

## 7. Invariantes do fechamento (preservadas, não reimplementadas)

```
STOCK_CLOSED != PACKAGE_SENT != MONTHLY_CLOSING_COMPLETED
ATTACHED != VALIDATED
CANCELLED != DELETED
CANCELLED != NOT_APPLICABLE
MANAGE_APPROVAL != EVIDENCE_VALIDATION
```

- Finalizar ≠ enviar; `PACKAGE_SENT` tem histórico imutável.
- Erro ou ausência da fonte **não** significa zero (ex.: `source_missing`
  do stock-inventory é exibido como indisponibilidade).
- Resultado preliminar ≠ final.
- IA não aprova, valida nem finaliza **por inferência**.
- Conciliação P3: `DIVERGENCIA = ENTRADAS_SAIDAS - P7 - H02`; paridade
  somente com divergência exatamente R$ 0,00; tolerância `NONE`. A CLARA
  **interpreta** o resultado entregue pelo owner — não recalcula.
- Ciclo 2: SB9/`MV_ULMES` ≠ homologação (doc 86, doc 88 C3-D05).

## 8. Relação com TÉO, DAVI e VISTA

| Especialista | Domínio | Relação com a CLARA |
|---|---|---|
| TÉO | processos, AS-IS, diagnóstico, evidências do Transformômetro | fonte de proveniência do PROC-0072; a CLARA não replica tools do TÉO |
| DAVI | descoberta/consulta governada de dados DELPI (api-delpi) | a CLARA não consulta TOTVS por fora da BFF nem reexpõe tools do DAVI |
| VISTA | painéis operacionais | sem sobreposição |
| CLARA | processos, recursos, operações e informações do Portal C&F | — |

Integração entre especialistas somente por contrato explícito,
autorizado e justificado (`PLANNED`, nenhuma prevista nesta fase).

## 9. Auditoria, observabilidade e resiliência (TARGET)

- Toda ACT gera evento de auditoria da BFF (actor, timestamp,
  competência, unidade, entidade, before/after, reason, correlation — doc
  14 §Auditoria), com marcação do canal `mcp/clara`.
- Logs estruturados com correlation ID ponta a ponta; redaction de
  detalhes (padrão `delpi_mcp.errors`).
- Downstream indisponível → erro tipado honesto (`503`/`502` mapeados como
  na BFF atual), **nunca** resposta vazia ou zero; RBAC indisponível →
  fail-closed.
- Sem retry em escrita não idempotente; timeouts herdados da BFF.

## 10. Decisões abertas — `DECISION_REQUIRED`

| ID | Questão | Evidência | Opções | Recomendação (não decidida) |
|---|---|---|---|---|
| **CLARA-D01** | Conciliar "executa o que o usuário pode executar" com doc 14 §IA ("IA não pode autorizar, validar, rejeitar, sacramentar, concluir, enviar, alterar configuração") | doc 14 linhas 222–240 vigentes | (A) atos de julgamento humano (validar, rejeitar, aprovar, sacramentar, finalizar, enviar pacote, alterar configuração) permanecem **fora** do ACT via MCP — apenas UI; ACT cobre operações operacionais. (B) ACT permitido para todos os atos do usuário, como delegado, com confirmação explícita obrigatória e auditoria de canal — exige revisão formal do doc 14 | **A** para a primeira fase — preserva a regra vigente; B só por decisão explícita do PO que altere o doc 14 |
| **CLARA-D02** | Hospedagem da superfície MCP | TÉO/DAVI/VISTA embutidos na API owner (§3.2) | (A) superfície `/mcp` dentro da `controllership-finance-api` (padrão da plataforma); (B) serviço MCP separado chamando a BFF por HTTP | **A** — segue o padrão real, evita novo deploy/credencial |
| **CLARA-D03** | Cadeia de delegação do token MCP até api-delpi | §5.2 | (A) mesmo token OAuth delegado (exige audience compatível); (B) token exchange; (C) BFF resolve identidade e mantém S2S próprio | `TO_INVENTORY` com owner de segurança/Keycloak antes de escolher |
| **CLARA-D04** | Mecanismo PREPARE/ACT | `governed_writes` do TÉO é local ao `tm_app` | (A) replicar o padrão no owner C&F; (B) extrair para shared quando houver 2º consumidor real | A agora; B somente com 2+ consumidores (regra de shared code) |
| **CLARA-D05** | Escopo da primeira fatia | BFF só tem READ | (A) DISCOVERY+READ+ANALYSIS sobre os 4 contratos atuais; (B) aguardar contratos P1–P6 | **A** — valor imediato, zero escrita |

Nenhuma recomendação acima está implementada ou aprovada.

## 11. Requisitos e critérios de aceite

Prefixo `RQ-CLARA-*` (livre no ledger canônico doc 23; ingressar no
ledger quando aprovado o gate de design).

| RQ | Requisito | AC |
|---|---|---|
| RQ-CLARA-01 | Discovery das capacidades reais | lista apenas tools cujos contratos o usuário pode invocar; sem `access` → nenhuma tool de dados |
| RQ-CLARA-02 | Consulta de recursos autorizados | toda READ passa pela BFF; recurso fora de escopo → 403 tipado retransmitido |
| RQ-CLARA-03 | Equivalência de capabilities | para cada tool, resultado == contrato da BFF para o mesmo usuário (teste de paridade, padrão `test_teo_portal_parity`) |
| RQ-CLARA-04 | AuthZ de leitura e escrita no backend | metadata/classe nunca autoriza; remover permission no Core nega imediatamente (respeitado stale ≤900s de reads) |
| RQ-CLARA-05 | Isolamento entre usuários | proposal de A não executa com token de B (`ACTOR_MISMATCH`) |
| RQ-CLARA-06 | Preservação de regras de negócio | nenhuma fórmula canônica no adaptador; testes provam passthrough |
| RQ-CLARA-07 | Confirmação de operações sensíveis | ACT sem handle PREPARE válido → `PROPOSAL_REQUIRED`; handle expirado/stale → recusa |
| RQ-CLARA-08 | Auditoria e rastreabilidade | toda ACT gera evento com canal `mcp/clara` e correlation |
| RQ-CLARA-09 | Indisponibilidade downstream | 5xx/timeout → erro honesto; nunca vazio/zero |
| RQ-CLARA-10 | Comunicação honesta | respostas distinguem fato/hipótese/recomendação; `source_missing` não vira 0 |
| RQ-CLARA-11 | Verificação de pós-condição | ACT só reporta sucesso após leitura da pós-condição (`OUTCOME_VERIFICATION_FAILED` caso contrário) |
| RQ-CLARA-12 | Sem permission própria da CLARA | diff de manifest/Core da fatia CLARA não adiciona código de permission; conjunto efetivo == contrato vigente do Portal |

## 12. Estratégia de testes (TARGET)

- Conformidade `shared/delpi_mcp` (tool validation, protocol, resource
  metadata, transport auth) — mesmo runner dos especialistas existentes.
- Segurança: service token rejeitado; audience/scope ausente → challenge;
  usuário sem `access` → zero tools de dados; `rbac_unavailable` → 503.
- Paridade Portal↔CLARA por tool (positivo + irmão + negativo).
- Contratos: envelope da BFF preservado; erros tipados (`scope_unavailable`).
- Escrita (quando houver): PREPARE sem side effect; ACT idempotente;
  concorrência otimista; pós-condição.

## 13. Gates de implementação

1. Decisões CLARA-D01..D05 explícitas do PO/arquiteto.
2. Inventário de delegação (D03) com owner de segurança.
3. Gate transversal (arquitetura, segurança, contratos, qualidade,
   delivery) antes de qualquer código.
4. Fatia 1 (se D05=A): DISCOVERY/READ/ANALYSIS sobre contratos `CURRENT`.
5. PREPARE/ACT somente após contratos de escrita do Portal existirem e
   D01 decidido.

## 14. Evidências e próximos passos

Evidências deste documento: `shared/delpi_mcp/*` (docstrings e testes),
`transformometro-api/tm_app/interface/mcp/*`,
`tm_app/application/governed_writes/*`, `api-delpi/app/interface/mcp/*`,
`tv-dashboard-api` conformance test,
`controllership-finance-api/.../routes/*`, docs 14, 23, 88, 91, 93.

**Próximo passo delimitado:** decisão do PO sobre CLARA-D01, D02 e D05;
em seguida inventário D03. Nenhuma implementação decorre deste documento.
