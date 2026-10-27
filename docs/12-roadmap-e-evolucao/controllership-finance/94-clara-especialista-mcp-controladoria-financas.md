# Documento 94 — CLARA · Especialista MCP em Controladoria & Finanças

**Estado:** identidade e intenção funcional **APROVADAS** pelo usuário/PO ·
arquitetura executável **TARGET** · `IMPLEMENTATION_AUTHORIZED=YES`
para as capacidades do GO `CF-PROC0072-CLARA-COMPLETE-001` (D01–D05
decididas); G2/G3 seguem externos.
**Natureza:** especificação de governança e arquitetura. Nenhum servidor
MCP, tool, endpoint, banco, migration, permission ou deploy existia na
escrita original; a primeira fatia foi implementada em `41fdcf65e1`.
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

**Decisão PO posterior (24/10/2026, `CLARA-D01=B`):** a CLARA poderá executar pelo chat atos como **validar, rejeitar e concluir** com **aval explícito por operação** do usuário autenticado que detenha essa capacidade no Portal. O MCP é um canal de delegação, não uma entidade que valida ou conclui por iniciativa própria. A confirmação do usuário não substitui autorização efetiva do Core, escopo, vínculo, business rules, versão e auditoria. A [regra de IA, doc 14](./14-seguranca-rbac-auditoria-e-ia.md), foi revisada formalmente para distinguir execução delegada de decisão autônoma. **Runtime permanece não autorizado.**

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

## 10. Registro decisório CLARA-D01=B e decisões técnicas ainda abertas

| ID | Tema | Decisão / condição | Estado |
|---|---|---|---|
| **CLARA-D01** | Paridade das operações do Portal, incluindo ações sensíveis no chat | **OPÇÃO B APROVADA PELO PO EM 24/10/2026:** PREPARE/ACT delegado pode validar, rejeitar, concluir e executar demais operações **que o mesmo usuário já poderia executar na UI/BFF**, com confirmação humana explícita por ação, audit e verificação de resultado. A autorização final continua na BFF/Core. [Doc 14 §IA](./14-seguranca-rbac-auditoria-e-ia.md) atualizado. | `PO_APPROVED / DESIGN_ONLY`; nenhuma ACT sensível criada |
| **CLARA-D02** | Hospedagem MCP na API dona ou serviço separado | (A) `/mcp` owner-local na `controllership-finance-api` (padrão comprovado TÉO/VISTA, recomendado); (B) serviço separado via BFF. Não escolher por preferência antes de gate. | `DECIDED=A` (gate transversal CLARA-COMPLETE-001) |
| **CLARA-D03** | Delegação OAuth/MCP até api-delpi | (A) mesmo token quando audience compatível; (B) token exchange; (C) identidade validada pela BFF e S2S próprio. Inventário de Keycloak/segurança antes de decidir. | `DECIDED=C` (BFF valida identidade + cadeia S2S vigente; gate transversal CLARA-COMPLETE-001) |
| **CLARA-D04** | PREPARE/ACT governado | (A) aplicar padrão TÉO local no owner C&F (recomendado); (B) extrair compartilhado só com consumidor real adicional. Não importar `governed_writes` do domain alheio. | `DECIDED=A` (padrão TÉO local no owner C&F; gate transversal CLARA-COMPLETE-001) |
| **CLARA-D05** | Primeira fatia da CLARA | (A) DISCOVERY+READ+ANALYSIS sobre contratos existentes da BFF (recomendado); (B) aguardar P1–P6. Isto é faseamento, **não** limita capacidade final aprovada. | `DECIDED=A` (DISCOVERY+READ+ANALYSIS primeiro; PREPARE/ACT só para capacidades existentes; gate transversal CLARA-COMPLETE-001) |

### 10.1 Contrato de confirmação da ação delegada (TARGET aprovado funcionalmente)

1. Usuário autenticado solicita uma operação concreta no chat; CLARA resolve a capacidade específica da **mesma BFF que serve a UI** e apresenta `quem / recurso / competência / versão / ação / impactos / motivo exigido`. Texto genérico como "pode fazer tudo" não vale como confirmação.
2. PREPARE **não modifica** estado de domínio e entrega uma proposta vinculada à identidade real, escopo, objeto, versão, efeitos e expiração. Reutilizar o padrão testado TÉO/VISTA sem copiar use cases/domains alheios.
3. Usuário **confirma explicitamente aquela operação**. Sem aval → nenhuma ACT. A confirmação é intenção/consentimento; **não concede RBAC nem substitui validação do backend**.
4. ACT verifica novamente Core effective permission (fresca para escrita), tipo de principal humano, ownership/resource_scope, elegibilidade (incluindo validator/reviewer/administrator), business rules, snapshot da versão, concorrência, idempotência e invariantes; grava apenas pela `controllership-finance-api` e audita `mcp/clara` com ator/correlação.
5. Após ACT, o serviço lê e verifica a pós-condição real; erro, timeout, rejeição, conflito, proposta expirada ou estado inconclusivo não viram sucesso afirmado.

**Exemplos vinculantes:** (i) Joici pode anexar e depois validar um PDF quando for elegível às duas ações, mas há duas confirmações/eventos independentes e `ATTACHED != VALIDATED`; (ii) rejeição exige motivo/histórico; (iii) concluir competência exige todos os critérios P5, sem reduzir `MONTHLY_CLOSING_COMPLETED` a confirmação no chat; (iv) Contabilidade/DRE é destinatária de leitura/download futuro, **não** tem capacidade de validar ou aprovar na primeira versão; (v) sacramentação ERP é externa ao Portal V1, portanto **não é ACT delegável** enquanto não houver capacidade autorizada e contrato expresso.

**Nenhuma tool de escrita ainda existia quando D01 foi aprovada.** D02–D05 foram decididas pelo PO na rodada única do GO `CF-PROC0072-CLARA-COMPLETE-001` (D02=A, D03=C, D04=A, D05=A). `IMPLEMENTATION_AUTHORIZED=YES` para as capacidades deste GO — G2/G3 seguem externos.

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
| RQ-CLARA-13 | Validar, rejeitar e concluir como usuário delegado | nenhuma alteração em PREPARE; confirmação humana **específica** a cada ação/objeto/versão; ACT só na BFF com Core efetivo, ownership, role do validador e business rules, depois auditoria/postcondition |
| RQ-CLARA-14 | Sem elevação de privilégio por consentimento no chat | usuário sem capacidade da UI recebe negação ainda que confirme; DRE read-only não valida/rejeita/conclui; proposal de outro ator, expirada ou stale não executa |

## 12. Estratégia de testes (TARGET)

- Conformidade `shared/delpi_mcp` (tool validation, protocol, resource
  metadata, transport auth) — mesmo runner dos especialistas existentes.
- Segurança: service token rejeitado; audience/scope ausente → challenge;
  usuário sem `access` → zero tools de dados; `rbac_unavailable` → 503.
- Paridade Portal↔CLARA por tool (positivo + irmão + negativo).
- Contratos: envelope da BFF preservado; erros tipados (`scope_unavailable`).
- Escrita (quando houver): PREPARE sem side effect; ACT idempotente;
  concorrência otimista; pós-condição.
- **Consentimento humano e paridade sensível:** três matrizes mínimas **validar, rejeitar, concluir**, cada uma com positive (ator elegível, confirmação por recurso), sibling (outro recurso/versão/competência), negative (sem consentimento, wrong actor, permission revogada, reviewer inelegível, prazo expirado, stale version, Core/owner indisponível, business state inválido). Verificar audit e read-after-write.
- **Separar upload e validação:** mesmo ator Joici pode efetuar ambas se autorizado; nunca autoaceite pelo upload. Conclusão mensal só após critérios P5 e evidencia de pós-condição; download DRE sem aceite.

## 13. Gates de implementação

1. **D01=B já decidida pelo PO em 24/10/2026:** confirmar que doc 14, doc 93 e RQ/AC de ações sensíveis permanecem alinhados; não pedir nova escolha para esta decisão.
2. Resolver D02/D04/D05 com owners; inventariar D03 com segurança/Keycloak. Design de OAuth/capabilities e contrato de confirmação ainda requer gate.
3. Gate transversal de arquitetura, segurança, contratos, qualidade e delivery **antes de implementar MCP ou tools**; autorização separada por fatia.
4. Fatia inicial de DISCOVERY/READ/ANALYSIS só após GO próprio, independentemente de D01=B.
5. PREPARE/ACT só depois da respectiva operação UI/BFF existir e estar homologada, da confirmação e auditoria serem contratadas e de GO **por capability**. A decisão funcional não autoriza runtime genérico.

## 14. Evidências e próximos passos

Evidências deste documento: `shared/delpi_mcp/*` (docstrings e testes),
`transformometro-api/tm_app/interface/mcp/*`,
`tm_app/application/governed_writes/*`, `api-delpi/app/interface/mcp/*`,
`tv-dashboard-api` conformance test,
`controllership-finance-api/.../routes/*`, docs 14, 23, 88, 91, 93.

**Estado:** D01=B, D02=A, D03=C, D04=A, D05=A decididas. Primeira fatia implementada em `41fdcf65e1` (V011 + `/mcp` owner-local + knowledge base própria + PREPARE/ACT governado para capacidades já existentes na BFF). Gate transversal fechado para este escopo; G2 humano e G3 operador permanecem externos.

## 15. Decisão posterior vinculante — CLARA batch, Keycloak e ChatGPT (25/10/2026)

**[Documento 106](./106-clara-batch-ssh-keycloak-chatgpt-go-e-gates.md) é a authority posterior para múltiplas operações com mínima interação, intenção autenticada atestada ou confirmação consolidada quando necessária, e auditoria por ação.** Substitui o requisito histórico de confirmação conversacional isolada *por operação*, não o requisito de consentimento comprovável, autorização Core, ownership/scope e invariantes C2. Os parágrafos anteriores de D01 e §10.1 sobre confirmação individual devem ser lidos como **SUPERSEDED pela aprovação do lote**. A solução física de atestação permanece DECISION_REQUIRED no gate de segurança. A implementação ACT anterior tem correções pendentes (claim antes do efeito, single-use concorrente, snapshot fail-closed e read-back independente) e deve permanecer desabilitada/fail-closed em produção até PASS. Keycloak e deploy só após G2 humano e G3 Operador SSH.


### Adendo — consentimento por desafio e apresentação completa (V014)

O consentimento consolidado deixa de ser inferido da idade do JWT
(`iat`) e passa a ser um **artefato verificável**
(`clara_consent_challenge`, V014): emitido no PREPARE, aprovado uma
única vez pela superfície confiável do Portal e consumido na
transação de claim — binding exato de ator, lote/proposta,
`plan_hash` e versão (Documento 106, Adendo 4; R-CLARA-01).

A página de consentimento passa a exibir **apresentação funcional
completa** de cada operação — descrição em português, recurso,
efeito, motivo, dependências e impedimentos — gerada por
`operation_presentation.py` a partir do plano selado persistido
(nunca reconstruída no frontend; R-CLARA-02). Operações que o
servidor não consegue apresentar com clareza são exibidas como
bloqueadas e não podem ser autorizadas implicitamente.


---

## Adendo — sincronização de corpus (CF-PROC0072-MONTHLY-OPEN-PROD-CLARA-004)

O manifest do corpus (`corpus_manifest.AUTHORIZED_SOURCES`) foi ampliado de 52 para 55 fontes autorizadas, incluindo os documentos 111 (evidência de smoke autenticado), 112 (decisões UX + inventário + DR-C1 resolvido) e 113 (plano canônico com GO do PO). Conhecimento funcional vigente que o corpus passa a representar:

- Selecionar mês de referência **não** abre fechamento (consulta ≠ operação formal).
- `access` efetivo abre o fechamento **sem** checklist publicado e sem documentos — lista vazia é estado legítimo, não erro; `no_published_template` deixou de ser regra vigente de abertura.
- Abertura é idempotente e auditada (`opened_without_template`); não conclui P2/P3/P5 por vacuidade.
- Itens publicados depois da abertura **não** entram retroativamente (re-snapshot pendente — DR-C3).
- DRE continua TARGET — não descrever como capacidade operacional.
- Nenhuma tool ACT de abertura existe — a CLARA não abre fechamentos por conta própria.

---

## Adendo — Visão geral V0.2 do Fechamento mensal (CF-PROC0072-OVERVIEW-UX-004)

Conhecimento funcional vigente sobre a organização da aba **Visão geral** (implementado; homologação visual do PO pendente):

- A Visão geral responde: qual mês está em acompanhamento, situação do fechamento, o que precisa de atenção, quais atividades executar, se a etapa da Controladoria pode concluir e se o pacote pode ser enviado.
- Os três indicadores significam: **Bloqueios** = condições impeditivas de conclusão derivadas do fechamento; **Divergências** = domínios de conciliação com divergência monetária — «—» quando uma fonte está indisponível (nunca zero); **Documentos a tratar** = métrica ainda sem contrato do owner P2 — «—» até definição.
- «O que precisa de atenção» lista situações reais traduzidas dos códigos do backend — a CLARA não deve reproduzir códigos técnicos crus (ex.: `p3_source_unavailable:P7`) ao usuário, e sim a mensagem humana («Fonte P7 indisponível»).
- Os eixos Estoque, Documentos e Pacote DRE são independentes: «Sem exigências cadastradas» (aberto sem checklist) é estado normal, não erro.
- **Concluir** a etapa da Controladoria é derivado pelo sistema quando as condições são atendidas — não existe ação de concluir na interface. **Enviar** o pacote documental é operação separada, na página de pacotes, com confirmação humana. Nunca confundir conclusão com envio.
- Atividade recente exibe somente eventos reais de auditoria P3 do mês; feed completo de eventos e métrica «Documentos a tratar» seguem pendentes de contrato (`TO_INVENTORY`).

## Adendo — Visão geral V0.3: linguagem simples (CF-PROC0072-OVERVIEW-UX-REWORK-005)

Refinamento de apresentação da Visão geral do Fechamento mensal — a estrutura V0.2 é mantida; a CLARA deve responder sobre ela em português simples:

- **Indicadores:** «O que falta resolver» (situações que impedem a conclusão — clique localiza a lista), «Divergências» (diferenças encontradas nas conferências — abre Relatórios e divergências) e «Documentos a tratar» (contagem ainda indisponível — `—`). `—` significa **indisponível**, nunca zero confirmado.
- **O que precisa de atenção:** lista de situações reais em linguagem simples (ex.: «Conferência do mês ainda não finalizada», «Não foi possível consultar o relatório P7»). Com mais de quatro itens, o botão «Mostrar todas as N situações» expande a lista na própria página — o usuário não é enviado a uma listagem parcial.
- **Eixos:** «Conferência do estoque» (situação + próximo passo), «Documentos do mês» (exigidos/aguardando/aceitos; «Nenhum documento exigido» é normal) e «Documentos para a Contabilidade» (prontos para envio vs já enviados para revisão).
- **«Não há um conjunto de documentos para envio definido neste mês»** significa ausência de conjunto configurado — NÃO que documentos estejam apenas aguardando preparação.
- **Atividades recentes:** últimos registros reais das conferências do mês (auditoria P3, até cinco). Ainda não cobre todas as áreas — histórico completo é evolução futura.
- **Concluir ≠ Enviar:** «Concluir fechamento» mostra o estado e o que falta (conclusão é derivada pelo sistema — sem botão); «Enviar documentos à Contabilidade» mostra a situação do conjunto e leva à página de gerenciamento, onde o envio exige confirmação.
- Códigos técnicos (`p3_cutoff_not_confirmed`, `no_applicable_packages` etc.) nunca aparecem no texto principal — servem apenas para diagnóstico/auditoria. Código desconhecido aparece como «Existe uma situação pendente que precisa ser verificada».

## Adendo — Documentos e interações V0.2 (CF-PROC0072-DOCUMENTS-UX-006)

A segunda aba do Fechamento mensal está implementada — a CLARA deve descrevê-la em português simples:

- **Cartões:** cada documento exigido (da lista definida para o mês) vira um cartão «Exigido»; arquivos anexados só àquele mês viram cartões «Adicional». Não existe tabela principal.
- **Pesquisa e filtro:** pesquisar por nome e filtrar por situação (aguardando documento, com ajuste solicitado, com arquivo enviado, conferido) ficam na URL — a troca de mês e o retorno do detalhe preservam o contexto.
- **Documento adicional:** arquivo anexado somente àquele fechamento. Não vira exigência geral, não se torna obrigatório nos meses seguintes e não altera fechamentos concluídos.
- **Detalhe do documento:** aberto pelo cartão ou por deep link `…/documents/{ref}`. Mostra prévia do arquivo, versões (a anterior fica preservada ao enviar nova versão), download autorizado, solicitações/decisões reais e histórico auditável (anexação, versão, download, cancelamento).
- **Solicitações de ajuste:** são decisões reais registradas pelos revisores, com motivo e comentário. «Abrir conversa» leva ao detalhe do documento, onde também existe a conversa livre (ver adendo U9 abaixo).
- **Anexo ≠ validação ≠ liberação:** arquivo enviado (`ATTACHED`) não significa conferido nem liberado para a Contabilidade/DRE. Uma resposta não encerra a solicitação automaticamente.
- Estado vazio («Nenhum documento exigido para este fechamento») é normal, não erro.


## Adendo — Conversa documental U9 (CF-PROC0072-DOCUMENT-INTERACTIONS-008, 27/10/2026)

A conversa livre por documento está **implementada** — a CLARA deve descrevê-la em português simples:

- **Início proativo:** a Controladoria autorizada pode iniciar a conversa de qualquer documento acessível do Fechamento mensal, mesmo sem nenhuma mensagem ou solicitação anterior da Contabilidade/DRE. Não é preciso «esperar a DRE perguntar».
- **Onde fica:** no detalhe do documento (deep route `…/documents/{ref}`), na coluna direita «Conversa sobre o documento» — PDF e versões à esquerda, conversa à direita, histórico abaixo.
- **Persistência real:** cada mensagem é gravada no backend com autor e data do servidor e permanece disponível ao recarregar a página, trocar de aba ou voltar depois. Não existem mensagens fictícias em estado de tela.
- **Sem efeito colateral:** uma mensagem **não** valida o documento, **não** encerra solicitação de ajuste, **não** envia pacote e **não** libera arquivo para a Contabilidade. Responder não é um ato formal — os atos formais continuam sendo a validação do item (P2) e a revisão do pacote (P5).
- **Audiência interna:** neste momento a conversa é somente da Controladoria. A Contabilidade/DRE **não** visualiza mensagens nem arquivos não liberados — o acesso dela ao fio depende de um gate futuro de audiência/liberação que ainda não existe. A CLARA não deve afirmar que a DRE lê a conversa.
- **Documento cancelado:** a conversa continua acessível e pode receber mensagens — a remoção lógica do arquivo não apaga o contexto da discussão.
- **Confiabilidade do envio:** se o envio falhar, o texto é preservado para nova tentativa; tentativas repetidas não criam mensagens duplicadas (deduplicação por chave idempotente do servidor).
- **Sem tempo real:** as mensagens aparecem na tela após a confirmação do envio; não há notificação, contador de não-lidas nem atualização ao vivo (WebSocket) — a CLARA não deve prometer esses recursos.
- **Escopo da CLARA:** não existe tool MCP para ler ou escrever mensagens — a CLARA conhece o funcionamento, mas não participa da conversa.


## Adendo — Refinamento visual do detalhe (CF-PROC0072-DOCUMENT-DETAIL-UX-009, 27/10/2026)

O detalhe do documento foi refinado — a CLARA deve descrever em português simples:

- **Altura da conversa:** a coluna «Conversa sobre o documento» mantém altura mínima confortável mesmo sem mensagens ou com apenas uma; a área de mensagens rola internamente e o campo de escrita permanece sempre no rodapé da coluna. No celular, PDF, conversa e histórico ficam empilhados.
- **Histórico em linha do tempo:** o histórico do documento deixou de ser uma lista simples e virou uma linha do tempo com marcos visuais — anexação, nova versão, remoção, evidência conferida e ajuste solicitado, cada um com responsável e data.
- **Downloads e mensagens fora da linha do tempo:** consultas de download e as mensagens da conversa não aparecem como eventos — a auditoria técnica completa continua registrada no sistema; a linha do tempo mostra só alterações do documento.
- **Foto e nome dos participantes:** mensagens e eventos exibem a foto oficial do perfil do autor (cadastro de pessoas do Portal). Quando a pessoa não tem foto, aparecem as iniciais do nome; quando o perfil não está disponível, aparece «Participante» — nunca um código técnico (UUID) como nome.
- **Mensagem ≠ evento:** a conversa é discussão livre (não gera marco na linha do tempo nem validação); a linha do tempo registra alterações materiais do documento. Finalidades diferentes, as duas preservadas.
- **Escopo da CLARA:** a CLARA não lê mensagens, não lê a linha do tempo e não vê fotos — descreve o funcionamento, sem tool MCP nova.


## Adendo — Isolamento de participantes por documento (CF-PROC0072-DOCUMENT-DETAIL-UX-009-RW01, 27/10/2026)

Correção de segurança no serviço de nomes/fotos de participantes — a CLARA deve descrever a regra vigente em português simples:

- **Consulta somente dentro do documento autorizado:** nomes e fotos de participantes só podem ser consultados no contexto de um documento e de uma competência aos quais o usuário tem acesso legítimo. Ter acesso ao Portal não basta — é preciso que a pessoa consultada participe daquele documento (autor de mensagem, responsável por evento ou quem anexou o arquivo).
- **Core continua sendo a fonte oficial:** nomes e fotos continuam vindo do cadastro de pessoas do Portal (Core). A BFF da Controladoria apenas verifica o vínculo documental antes de pedir os dados ao Core — não existe cópia local de perfis nem de fotos.
- **Não existe consulta livre de avatares:** o Portal não oferece busca livre de pessoas nem de fotos pela tela de documentos. Consultar participante de outro documento ou de outra competência retorna «não encontrado», sem revelar se a pessoa ou o documento existem.
- **Fallback preservado:** quem não tem foto publicada aparece com as iniciais do nome; perfil indisponível aparece como «Participante» — nunca um código técnico (UUID) como nome.
- **Nada mudou na conversa nem no histórico:** a conversa por documento, a linha do tempo, a altura da coluna e o campo de escrita no rodapé continuam funcionando como antes — a correção foi somente na autorização.
- **Sem efeitos colaterais novos:** mensagens continuam não validando documento, não liberando arquivo para a Contabilidade e não gerando notificações; a audiência da DRE/Contabilidade na conversa continua sendo um gate futuro que não existe.
- **Escopo da CLARA:** a CLARA não consulta perfis, não resolve nomes e não acessa fotos — descreve a regra, sem tool MCP nova.


## Adendo — Relatórios e divergências na aba de relatórios (CF-PROC0072-REPORTS-UX-010, 27/10/2026)

A terceira aba «Relatórios e divergências» do Fechamento mensal virou uma bancada de análise — a CLARA deve descrevê-la em português simples:

- **Ordem da página:** primeiro os indicadores do mês, depois «O que precisa de atenção», os cartões de relatório por família, os resultados detalhados, a cobertura da matriz R01–R15 e o espaço da prévia de PDF.
- **Três tipos de situação, nunca misturados:** divergência comprovada (diferença calculada pelo sistema), fonte indisponível (a consulta não respondeu ou está parcial) e conferência não realizada (a atividade ainda não foi executada — por exemplo, a conciliação P3 exige competência aberta). A CLARA não deve tratar fonte indisponível como «sem divergência» nem como zero.
- **Famílias com consulta real hoje:** Baixas financeiras (pagamentos e recebimentos SE5) e Estoque e conciliação (posição P7 + conferência Entradas/Saídas − P7 − H02). Os resultados abrem na própria aba: primeiro o total, depois os agrupamentos e, só quando a pessoa pede («Ver detalhes»), as linhas e registros.
- **Divergência de estoque:** a diferença exibida vem da conciliação P3 calculada pelo backend (reportado − esperado, somente quando a fonte está disponível e comparável). A conciliação só é concluída com diferença de exatamente R$ 0,00 — não existe tolerância. Se P7 ou H02 estiverem indisponíveis, o estado aparece como fonte indisponível, nunca como resultado inventado.
- **Causa e correção:** quando a causa ainda não foi comprovada pelo sistema, a tela diz «A causa ainda não foi identificada». A correção é manual no TOTVS — o Portal não escreve no ERP e não executa ajuste automático; após corrigir, a pessoa revalida a conciliação no checklist P3.
- **Matriz R01–R15 não são quinze relatórios calculados:** é a lista de entregáveis do fechamento e sua cobertura de conferência — vários R-IDs são evidência manual, fonte externa ou contrato pendente, não relatórios prontos. A CLARA não deve afirmar que R01–R15 estão calculados.
- **Prévia de PDF:** o espaço existe vinculado ao relatório selecionado, mas nenhum relatório tem PDF gerado hoje — a tela informa «A prévia do PDF ainda não está disponível para este relatório». A CLARA não deve prometer PDF nem tratar PDF anexado como evidência se fosse relatório oficial.
- **Competência como mês de referência:** a aba funciona por mês selecionado; consultas de baixas e estoque não exigem fechamento aberto, mas a conciliação P3 e a cobertura da matriz exigem — nesse caso aparece «Conferência não realizada».
- **Contabilidade/DRE:** relatórios operacionais desta aba **não** são enviados à DRE — a CLARA não deve afirmar o contrário.
- **Escopo da CLARA:** não existe tool MCP para consultar divergências ou gerar PDF — a CLARA conhece o funcionamento e orienta o usuário, sem executar a análise.


## Adendo — Páginas contextuais de relatório V0.3 (CF-PROC0072-REPORTS-DETAIL-UX-011, 27/10/2026)

A aba «Relatórios e divergências» continua sendo a central de análise, mas o detalhe completo de cada relatório agora abre uma **página contextual própria dentro do Fechamento Mensal** — a CLARA deve explicar a diferença:

- **Aba vs página:** a aba mostra indicadores, «O que precisa de atenção» e os cartões das famílias; o cartão «Abrir relatório» leva à página do relatório (`…/closing/monthly-closing/{mês}/reports/{relatório}`). Não é uma quarta aba — o caminho «Fechamento mensal > Relatórios e divergências > {Relatório}» aparece no topo e o botão «Voltar para Relatórios e divergências» restaura o mês e a família analisada.
- **Relatórios com página hoje:** Baixas financeiras (mesma tela de Baixas, competência travada no mês, agrupamentos por natureza/tipo em tabela de colunas e «Ver registros» aplicando os filtros do grupo) e Estoque e conciliação (mesma tela do P7, com a conciliação Entradas/Saídas − P7 − H02, resumos por tipo e por armazém). As rotas antigas `closing/financial-settlements` e `closing/stock-inventory` continuam existindo.
- **PDF:** cada página tem o espaço da prévia, mas nenhum relatório possui PDF gerado — a mensagem é «A prévia do PDF ainda não está disponível para este relatório». A CLARA não deve prometer PDF nem tratar anexos de evidência como relatório oficial.
- **Divergências:** seguem vindo somente da conciliação calculada pelo backend; fonte indisponível e conferência não realizada nunca são «zero». A matriz R01–R15 continua na aba, agora recolhida como rastreabilidade técnica — não são quinze relatórios calculados.
- **Sem escrita no ERP:** correções continuam manuais no TOTVS; o Portal não ajusta dados.


## Adendo — Filtros persistentes nas páginas de relatório (CF-PROC0072-REPORTS-DETAIL-UX-011-RW01, 28/10/2026)

A navegação entre a aba e as páginas contextuais ganhou **recuperação integral de contexto** — a CLARA deve orientar o usuário sobre o que é restaurado:

- **Filtros sobrevivem a F5, link direto e voltar/avançar:** os filtros vigentes ficam na própria URL da página do relatório (visíveis na barra de endereço). Atualizar a página, colar o link em outra aba ou usar os botões voltar/avançar do navegador restaura exatamente os mesmos filtros e a mesma página de resultados — a consulta é refeita no backend com esses valores.
- **Voltar à aba preserva a análise:** «Voltar para Relatórios e divergências» retorna ao mês correto, marca a família analisada e guarda seus filtros — reabrir o mesmo relatório restaura o contexto anterior. Abrir a outra família começa limpa: filtros nunca vazam de um relatório para outro.
- **Competência sempre do mês da rota:** em Baixas, datas fora do mês selecionado são descartadas (o intervalo volta ao mês); em Estoque, o mês nem aparece nos filtros — trocar de competência no seletor do Fechamento sempre consulta dados novos, nunca reaproveita resultado de outro mês.
- **Filtros persistidos — Baixas:** pagamentos/recebimentos, data inicial/final, natureza, tipo de movimento, ordenação/direção e página de resultados. **Estoque:** filial, visão de estoque, armazém e página.
- **Limitações:** filtros de outra família não são restaurados ao trocar de relatório (comportamento intencional); valores inválidos ou malformados na URL caem nos padrões seguros; nenhum token nem valor financeiro viaja na URL — autorização continua no backend.

## Adendo — Catálogo mestre de documentos (CF-PROC0072-DOCUMENT-CATALOG-UX-012, 28/10/2026)

Existe uma administração dedicada para **definir quais documentos são exigidos** no fechamento — a CLARA deve distinguir cadastro mestre de anexação:

- **Cadastro mestre ≠ anexação:** «Documentos do fechamento» (Administração, exige gestão) configura tipos de documento — nome, finalidade, orientações, obrigatoriedade, destino (Contabilidade, Fiscal ou uso interno) e vigência. Enviar o arquivo PDF de um mês continua na aba «Documentos e interações» da competência — cadastrar o tipo nunca exige anexo no mesmo momento.
- **Páginas completas:** cadastro e edição abrem páginas próprias (`/new`, `/{itemKey}`), nunca modal — com breadcrumb, filtros preservados na URL e retorno que restaura a consulta.
- **Vigência por competência:** «exigido a partir de» define a primeira competência cobrada (nunca retroativa); «exigido até» torna a exigência temporária — o documento deixa de ser cobrado no período seguinte. A vigência é derivada das versões publicadas do checklist mestre; situação exibida: vigente, futuro ou encerrado.
- **Histórico preservado:** cada alteração publica uma nova versão — fechamentos abertos/encerrados guardam snapshot próprio e nunca mudam retroativamente. «Encerrar exigência» é prospectivo e não exclui o documento.
- **Limites atuais:** não é pré-requisito cadastrar documentos para abrir um fechamento; se houver rascunho/revisão aberta no checklist mestre, o salvamento é recusado até ser concluído; documento excepcional de uma competência específica segue fluxo próprio (não é o catálogo); a página exclusiva para documentos recebidos da Contabilidade/DRE é fase posterior separada.


**RW01 (28/10/2026) — como as vigências realmente funcionam:**

- **Versões são conjuntos absolutos:** cada versão publicada do checklist define TODAS as exigências a partir da competência inicial. Por isso, cadastrar ou editar um documento propaga a alteração às versões futuras já publicadas — sem isso a exigência desapareceria no boundary seguinte.
- **Vencedora por competência:** a versão aplicável é a publicada com «a partir de» mais recente que não passa da competência (desempate: versão de número maior). Publicar fora de ordem cronológica é permitido e determinístico.
- **Falha intermediária:** a gravação executa várias publicações atômicas; se uma falhar, o usuário vê erro — nunca «salvo parcialmente». Repetir a operação é seguro: passos já concluídos são detectados e pulados.
- **Última exigência:** o contrato exige ao menos um item por versão — encerrar o único documento do checklist ainda não é possível (decisão de contrato pendente); um fechamento SEM nenhuma versão publicada já abre legitimamente sem documentos.

### Adendo ao catálogo — GATE-015/016 (28/10/2026)

- **Última exigência:** SUPERSEDED — DR-2 alternativa A aprovada pelo PO: encerrar o único documento é permitido via confirmação explícita (`allow_empty`), publicando versão real com zero itens (distinto de competência sem template aplicável).
- **Escrita transacional:** cadastro/edição/encerramento é UMA operação na BFF (`PUT …/documents/{item_key}/requirement`) com `base_version` (OCC) e `Idempotency-Key`; retry é seguro e replay retorna o mesmo resultado.
- **Rascunho aberto:** a operação é recusada com `catalog_draft_conflict` enquanto houver DRAFT/REVIEW — o administrador deve concluir/descartar o rascunho pela UI antes de alterar o catálogo.
- **Produção:** endpoint ativo, V017 aplicada, RBAC fail-closed verificado; primeiro cadastro real será feito pelo PO (draft v1 com 53 itens reais aguarda publicação prospectiva — `effective_from` nunca cobre competência já aberta).
