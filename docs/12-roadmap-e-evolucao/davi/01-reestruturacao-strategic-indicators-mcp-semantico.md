# DAVI V2 — Plano mestre de reestruturação: Strategic Indicators + MCP semântico + ações governadas

> **Status:** PLANNED / ARCHITECTURE_DECISION_REQUIRED. Documento de planejamento; **não autoriza implementação, mudança de OAuth ou deploy**.
> **Data:** 2026-11-06.
> **Sponsor / direção de produto:** centralizar a orquestração DAVI junto à API de Indicadores Estratégicos, mantendo a API DELPI como fonte autoritativa consumida por contrato, padronizando tools semânticas e habilitando alterações de indicadores/metas e futuras ações governadas.
> **Authority:** `docs/12-roadmap-e-evolucao/davi/README.md`, regras `.cursor`, contratos dos domain owners, documentação de integração e evidência runtime. Este plano é subordinado a essas fontes.
> **Snapshot consultado:** `docs/12-roadmap-e-evolucao/davi/README.md` e `api-delpi/docs/integrations/openai-plugin-mcp.md` na branch padrão, 2026-11-06. HEAD/working tree/deployed SHA **não integralmente validados**; revalidar antes de qualquer execução.

## 1. Resultado de produto desejado

O DAVI será a interface inteligente de consulta, explicação, composição e, quando explicitamente autorizado, preparação/execução de alterações sobre indicadores e outras capacidades aprovadas da DELPI.

Objetivos independentes:
1. **Realocação física/operacional:** avaliar migração do adapter/runtime MCP DAVI hoje hospedado em `api-delpi` para o contexto da API de Indicadores Estratégicos (nome, diretório, deploy e owner técnico exatos = **TO_INVENTORY**).
2. **Continuidade cross-API:** manter acesso às capacidades operacionais aprovadas da `api-delpi`, por contratos estáveis, sem acoplamento por imports internos ou banco compartilhado.
3. **Interface semântica MCP:** alinhar a superfície de tools ao padrão corporativo (nomes propostos `read`, `knowledge` e eventuais outras ferramentas), sem confundir verbo/tool com capability, autorização ou catálogo mecânico.
4. **Ações de negócio governadas:** permitir casos de uso de ajuste de metas e CRUD específico quando ratificados pelo owner; futuramente outras APIs, somente após gates próprios.
5. **Conhecimento e inteligência:** preservar e migrar, somente se autorizado por ownership e evidência, as diretivas, explicações, mapeamento semântico e proveniência hoje utilizadas pelo DAVI; não transformar memória, prompt ou conteúdo do agent em fonte operacional.

Não objetivo: migrar dados ou regras proprietárias da API DELPI para Strategic Indicators, habilitar CRUD genérico, expor SQL/HTTP arbitrário, construir segundo RBAC, promover ao vivo sem testes ou quebrar conectores existentes.

## 2. Current evidence / baseline de comparação

| Item | Estado | Evidência / ressalva |
|---|---|---|
| MCP DAVI sediado em `api-delpi`, resource `/apps/api-delpi/mcp` | PROVEN documental | Integration runbook; revalidar runtime |
| Tools produtivas `discover_delpi_information` e `execute_delpi_information` | PROVEN documental | Runbook e DAVI README; discovery atual necessita refresh |
| `search_products` | PROVEN documental como operação atrás de discover→execute | Não supor tool dedicada |
| Broker READ com catálogo e allowlist governada | PROVEN documental | README indica v30, 94 elegíveis (índice live 97); reconciliar contagem com código/deploy |
| Layering drift `external_capabilities → composition` | RESOLVED documental | `DAVI-ARCH-RUNTIME-001`; conferir testes atuais |
| OAuth end-user, PKCE e AuthZ final do backend owner | PROVEN documental como modelo atual | Qualquer mudança de resource/client exige migration/negative testing |
| Hosting real da API Strategic Indicators, rotas, ownership, contratos e CRUD de metas | TO_INVENTORY | Não inferir de nome da API |
| Equivalência semântica de `read` / `knowledge` em MCPs irmãos | TO_INVENTORY | Inventariar schemas, semântica, versionamento, limites, consentimento e clients |
| Novo MCP DAVI em Strategic Indicators | TARGET | Não implementado por este documento |
| Escrita de metas e CRUD cross-API via DAVI | TARGET | NÃO autorizado até owner/security/contract/ACT gate |

**Atenção:** os arquivos históricos anexados ao ChatGPT Project descrevem uma V1 menor e um drift em aberto. O README e runbook mais recentes do repositório registram broker de duas tools e drift resolvido. Não usar o snapshot antigo como contrato de migração; reconciliar com HEAD e live antes da execução.

## 3. Separação crítica: hosting versus autoridade

Duas decisões distintas exigem ratificação:

- **Hosting/entrypoint:** onde opera o MCP, sua composição, discovery, OAuth resource, deploy, logs e lifecycle.
- **Authority/ownership:** quem é dono de cada indicador, meta, produto, estoque ou outra informação e quem efetua AuthZ e grava alterações.

Arquitetura-alvo conceitual, **sujeita ao gate de boundary/owner**:

```text
Workspace Agent DAVI / provider
  -> App / OAuth end-user
  -> DAVI MCP semantic adapter (hosting candidate: Strategic Indicators API)
  -> orchestration/resolution bounded by authorized capability
       |-> Strategic Indicators authoritative contract/use case
       |      -> its own business AuthZ -> indicator/target source
       |-> API DELPI stable service contract
       |      -> api-delpi business AuthZ -> operational source
       |-> other owner contracts, only when separately approved
  -> bounded response + provenance + completeness
```

Se o MCP residir fisicamente em Strategic Indicators, **separar orquestração cross-domain de regras do domínio de indicadores**. O produto DAVI não se torna owner de API DELPI, de dados de outros bounded contexts ou de tabelas de terceiros. Avaliar se hospedar um orchestrator de múltiplos domínios dentro de um owner de KPIs é realmente o menor boundary correto; alternativa de manter interface owner-neutral com integração por contratos precisa ser comparada, sem construir serviço novo prematuramente.

## 4. Decisões pendentes de arquitetura (ADRs antes do código)

| ID | Questão | Gate |
|---|---|---|
| ADR-01 | Boundary real do hosting: módulo owner-local Strategic Indicators, adapter separado ou manutenção do hosting atual? | owners, consumers, contratos, deployment lifecycle, security, Abstraction Gate |
| ADR-02 | Novo MCP resource/OAuth: URL, client, audiences, scopes, callback, coexistência/rollback | Security + provider compatibility |
| ADR-03 | Modelo de `read` / `knowledge`: tools físicas, discovery/execute, contratos, parâmetros, limites, conteúdo de conhecimento | Inventário dos MCPs existentes + consumer e eval |
| ADR-04 | Knowledge owner: quais assets DAVI são directives/UX, quais são documentação, quais são dados de domínio, como versionar/freshness/provenance? | Classificação + access + owner |
| ADR-05 | Ações/CRUD em Strategic Indicators: casos de uso explícitos, owner de metas, permissions, policy, PREPARE/ACT | Ratificação domain/security |
| ADR-06 | Cross-API actor propagation e policy: modelo de end-user delegation/claims, menor privilégio, erro, auditoria | AuthZ por owner; nunca token de service account para user parity |
| ADR-07 | Compatibilidade/retirada: clients atuais, legacy Actions, dual run, cutover e rollback | Release + aceite |

Nenhum ADR é aprovado apenas pelo texto deste plano.

## 5. Workstreams e fases (ordem executável por dependência, não pela ordem da solicitação)

### Fase 0 — Inventário e rebaseline obrigatório (P0)

**Saída:** `DAVI-V2-INVENTORY-REPORT` com HEAD e owner map.

- `git fetch origin`, `git rev-parse HEAD`, `git rev-parse origin/main`, `git status --short`; conferir SHA de deploy por serviço.
- Ler `.cursor` transversal e DAVI README; mapear diretorios reais de `api-delpi`, Strategic Indicators e MCPs irmãos (inclusive TÉO/VISTA); distinguir modules/contexts/deploys.
- Inventariar duas tools DAVI atuais, schemas, metadados OAuth, candidate tokens, source allowlists e mecanismos de knowledge/intelligence.
- Inventariar `read`, `knowledge`, `analyze`, `get_context` ou similares nos MCPs irmãos **sem assumir nomes/semântica universais**.
- Mapear consumers, clients, testes, snapshots, docs, deploy pipeline, ingress, secrets, observabilidade, UI/provider config e aplicações impactadas.
- Inventariar contratos/capacidades da API Strategic Indicators: leitura, metas, mutações, restrições, versionamento, auditoria, owner e permissões reais.
- Reconciliar allowlist/contagens no código, no deploy e no provider; registrar `PROVEN/TO_INVENTORY` e `PASS/FAIL/PENDING/INCONCLUSIVE/TEST_NOT_RUN/STALE_EVIDENCE`.
- Reportar divergências entre premissas e implementação como `EXECUTION_DRIFT`; parar mudanças onde houver conflito de authority.

**Exit:** evidência objetiva suficiente para avaliar ADR-01 a ADR-07. **Sem código de runtime nesta fase.**

### Fase 1 — Product/source capability ratification (P0)

Para cada necessidade, registrar business question, owner, source of truth, consumer, READ/PREPARE/ACT, grain, request/response/errors, classification, allowlist, paginação, provenance/freshness, authorization, observability e critérios de aceite.

Pacotes candidatos (não capabilities aprovadas):
- A: consultar indicadores estratégicos, períodos, fórmulas, metas, evidências e significado;
- B: explicar desvio de indicador com dados operacionais obtidos por contratos da API DELPI;
- C: pesquisar produtos/estoque e outros READs DAVI existentes, mantendo projeções e isolamento;
- D: consultar conhecimento governado sobre indicadores, definições, owner e metodologia;
- E: PREPARE de alteração de meta com diff/impacto/política;
- F: ACT de alteração de meta, com postcondition autoritativa;
- G: outras operações de criar/editar/excluir indicadores, quando comprovadamente suportadas e aprovadas.
  
**Exit:** Capability Decisions aprovadas por Product + domain owners + Security; nenhuma rota/tool definida apenas por existência técnica.

### Fase 2 — Blueprint de MCP semântico (P1)

- Definir semantic purpose de `read` e `knowledge`: por exemplo, consulta de dados autorizados versus consulta de conhecimento governado; **sem congelar** nomes e contratos antes de avaliar padrão real.
- Se `read` for broker, impor seleção por catálogo elegível, consultas pequenas, argumentos fechados, escopo do ator, projeção allowlisted, tokens de candidatos bound, paginação/completeness e limites de contexto.
- Se `knowledge` existir, permitir somente conteúdo approved/authorized, versioned/freshness/provenance, protegido contra prompt injection; conhecimento não fornece business permissions nem valores operacionais atuais.
- Separar discovery/planning de execução quando necessário; `read` não pode executar ACT.
- Definir tools adicionais somente para intent semântico com contratos e usuários reais; não mapear automaticamente cada endpoint nem disponibilizar CRUD/execute universal.
- Fazer adapter/provider independente do Domain/Application; construir contract tests e evals de recuperação, tool selection, recusa e não regressão.

**Exit:** ADR-03/04 e spec versionado de tool surface, com análise de compatibilidade do broker atual.

### Fase 3 — Strategic Indicators contract & cross-API integration (P1)

- Implementar/adaptar apenas os owner contracts aprovados.
- Conectar a API DELPI por seu boundary público/estável autorizado, sem imports cross-context de application/domain e sem acessar diretamente banco/TOTVS.
- Preservar a identidade do usuário e a AuthZ final **em cada API dona**; validar audience/token exchange/delegation conforme desenho aprovado, nunca confiar em header livre do Agent.
- Evitar duplicar lógica de KPI, cálculo de meta, regras Protheus ou autorização no adapter MCP.
- Projetar resultados model-safe com owner, source, período, unidade, completude, timestamp e limitações aplicáveis.
- Criar testes de isolamento entre usuários e entre contexts, timeout, falha parcial, retry e não vazamento de dados.

**Exit:** integração contratual em ambiente de teste, sem migrar provider/cutover.

### Fase 4 — Hosting/entrypoint migration (P1, condicionada ao ADR-01/02)

- Mover/implantar adapter somente após prova da vantagem de hosted Strategic Indicators; **não** apenas mover diretório mantendo imports indevidos.
- Mapear antiga→nova configuração: MCP URL/resource, nome técnico, plugin manifest, OAuth client, issuer/audiences, PKCE/callback, secrets, ingress, DNS/Origin, session manager, health, dashboards, runbooks, URLs de consumidores.
- Preferir implantação paralela com contrato versionado e reconexão controlada; não retirar `/apps/api-delpi/mcp` até provar migração e rollback.
- Revalidar provider tools/list e chamadas end-user no destino; comparar output e AuthZ ao comportamento anterior.
- Garantir estratégia para sessões/conectores já vinculados e compatibilidade de clients.

**Exit:** staging e piloto privado PASS, com rollback ensaiado e rastreio de configuração.

### Fase 5 — Governed write: metas e CRUD específico (P2; gate separado)

- Inventariar owner real, recursos e regras para **cada** caso: alterar meta, criar indicador, editar fórmula, excluir indicador etc.; não inferir operações pelo nome CRUD.
- Separar `READ` de `PREPARE` (validação, diff, versão, impactos, preview sem persistência) e `ACT` (efeito persistente).
- Exigir authenticated actor, final owner business AuthZ, policy/confirmation, idempotency key, optimistic concurrency/version (quando aplicável), auditoria/correlation, limites e authoritative read-after-write/postcondition.
- Para exclusão: inventariar soft delete, dependências, histórico, restauração, policy adicional, retenção e impossibilidade de reversão.
- Para outros contexts: repetir integralmente o gate; não obter permissão por herança do acesso ao MCP.
- Negative tests: usuário sem permissão, escopo/filial incorreto, versão conflitante, duplicata de requisição, stale confirmation, payload adulterado, token inválido, fail-closed.

**Exit:** capability ACT individualmente aceita; 2xx, tool discovery ou confirmação do Agent isolados **não** provam resultado de negócio.

### Fase 6 — Provider UX, release e decommission (P2)

- Revalidar provider UI/connector, schemas e refresh/reconnect; atualizar Agent directives somente após live tools/contratos provados.
- Executar matrix de regressão para todos os usos DAVI acordados: consultas de produtos, estoque, explicação de indicadores, knowledge, casos de erro e outputs.
- Executar ladder: source → local tests → public HTTP → OAuth discovery → connection → initialize → tools/list → provider discovery → authenticated call → projection → negative business AuthZ → Agent preview → deploy fingerprint.
- Exigir piloto com segundo usuário de autorização diferente, decisão formal de rate/abuse policy, auditoria/telemetria sem secrets e plano de compartilhamento.
- Atualizar README DAVI, runbooks do novo owner, docs da API DELPI e migration guide; só então retirar recursos legados mediante evidência de ausência de consumidores.

**Exit:** go-live autorizado e decommission separado, nunca por inferência.

## 6. Dependências / prioridades

```text
Fase 0 Inventory
   -> Fase 1 Capability + owner/security ratification
      -> ADRs (hosting, semantic tools, OAuth, knowledge)
         |-> Fase 2 semantic-tool design
         |-> Fase 3 cross-API contracts
         |     -> Fase 4 hosting migration (if accepted)
         |-> Fase 5 write capabilities (independent gated track)
         -> Fase 6 release/retirement after verified evidence
```

A mudança da superfície das tools e a migração física **não precisam compartilhar o mesmo release**. Preferir diffs independentes e rollback por fatia.

## 7. No-regression contract

Preservar, até mudança aprovada:
- searches e READs governados já utilizados pelo DAVI, incluindo broker `discover_delpi_information` / `execute_delpi_information`;
- output allowlists, completude, paginação, limits e error handling existentes;
- identity = end-user, sem autoridade herdada entre usuários;
- backend owner AuthZ e source-of-truth boundaries;
- GPT Actions como bridge legada, sem expansão oportunista;
- instruções/knowledge do Agent como UX, nunca fonte live ou autorização;
- compatibilidade dos consumidores ativos, ou cutover explícito e testado.

Definir golden queries e evidências before/after; regressão funcional ou de segurança bloqueia cutover.

## 8. Riscos e mitigação

| Risco | Tratamento obrigatório |
|---|---|
| API de KPIs vira proxy universal de todas as APIs | ADR-01 + Abstraction Gate + contratos estáveis por owner |
| Migração confunde hosting com domain ownership | owner/source matrix e testes cross-context |
| CRUD genérico / tool universal de escrita | capability ACT específica + backend AuthZ + confirmação/policy |
| Novo OAuth resource quebra usuários e sessions | ADR-02, staging, coexistência, reconexão controlada, rollback |
| Ferramentas `read` e `knowledge` mudam semântica sem versionamento | inventário dos MCPs irmãos, contract/eval e compatibilidade |
| Knowledge stale ou instrução injetada se passa por dado oficial | provenance, classification, sanitização e source authoritative |
| Perda das consultas DELPI e da inteligência existente | golden regression matrix, migration inventory, parity gates |
| Dual auth / token forwarding inseguro | Security review, audience/delegation, fail-closed e negative tests |
| 2xx ou testes locais confundidos com go-live | deployed SHA + provider discovery + AuthZ + postcondition |
| Integração de múltiplos contexts cria acoplamento | ports/adapters, contracts, no cross-context imports |

## 9. Governança e handoff

| Frente | Responsabilidade de revisão |
|---|---|
| Architecture / Coordination | ADR-01/02/07, boundaries, freeze, aceitação |
| Capability Expansion / Product | semantic intent, consumers, source/owner, projeções |
| Security / Identity / Privacy | OAuth, end-user, business AuthZ, privacy, ACT controls |
| Owner Strategic Indicators | contrato e autoridade de indicadores/metas (owner humano/técnico exato TO_INVENTORY) |
| API DELPI / Backend / Contracts | manter e validar contratos DELPI já existentes |
| MCP / OAuth / OpenAI Integration | tools, transport, provider, redirect/reconnect |
| Testing / Acceptance / Evals | paridade, regressão, negative tests, evidence |
| Operations / Documentation / Release | deploy, rollback, docs, decommission |

GPT define brief/review/aceite; Cursor inventaria, implementa menor diff, testa e emite evidence report; GitHub persiste contratos/docs/SHAs. Para cada fase: `BASE HEAD`, `FINAL HEAD`, arquivos alterados, testes, residual search, impacto contratual, evidência runtime/provider, gaps e status.

## 10. Próximo passo autorizado (somente leitura/inventário)

Emitir **DAVI-V2-INVENTORY-001**, sem mudanças no runtime:

1. verificar `origin/main`, HEAD, working tree e deployed SHA;
2. descobrir nome/caminho/owner da API Strategic Indicators e contratos de indicadores/metas;
3. inventariar estrutura e wiring do MCP DAVI atual e suas duas tools;
4. comparar MCPs irmãos para semântica e contratos reais de `read` / `knowledge`;
5. mapear AuthN/AuthZ, migration cost e compatibilidade provider;
6. identificar o que é conteúdo/persona/conhecimento DAVI, seu owner e sua fonte;
7. devolver opções ADR-01 (pelo menos hosting no owner Strategic Indicators vs manter boundary atual), trade-offs e sequência recomendada;
8. **STOP** se owner, source, contract ou AuthZ contradizerem o plano; registrar `EXECUTION_DRIFT`.

**Acceptance:** relatório verificável sem inferir APIs, ferramentas, permissões, operações CRUD ou deploy inexistentes. Nenhum código/recurso migrado nesta etapa.

## 11. Critérios de sucesso final (TARGET)

- DAVI consulta indicadores e os explica por evidências rastreáveis da API Strategic Indicators e de fontes operacionais autorizadas.
- Recupera informações da API DELPI sem perder os READs já aprovados e sem violar ownership.
- Oferece interface semântica consistente com padrões MCP comprovados e contratos específicos.
- Executa **somente** ações de indicadores/metas explicitamente aprovadas, com PREPARE/ACT, AuthZ negativa e postcondition.
- End-user isolation, replay/idempotency, auditing, data minimization e rollback são comprovados.
- Novo provider, deploy e consumo real estão provados, com documentação atualizada e sem divergência material de autoridade.
