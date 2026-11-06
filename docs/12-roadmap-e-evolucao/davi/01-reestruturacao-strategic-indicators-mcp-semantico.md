# DAVI V2 — Plano mestre de evolução do MCP semântico e integração de fontes

> **Status:** PRODUCT_DIRECTION_ACCEPTED / IMPLEMENTATION_PENDING. Revisão consolidada em 2026-11-06.
> **Documento único de execução/decisão desta iniciativa.** Atualizar este arquivo nas próximas fases em vez de criar planos paralelos; histórico recuperável por Git.
> **Direção corrigida:** DAVI **permanece no contexto técnico `api-delpi`** e no MCP/resource atuais. Prioridade 1 = padronizar as tools semânticas sem regressão. Prioridade 2 = permitir consumo governado de Strategic Indicators, quando houver contratos e segurança aprovados. **Não transferir o DAVI para Strategic Indicators nem criar container, MCP ou BFF SQL novo nesta fase.**
> **Authority:** `docs/12-roadmap-e-evolucao/davi/README.md`, regras `.cursor`, contratos dos owners, Core API/governança, evidências runtime. Documento de plano não é prova de deploy e não autoriza implementação antes dos gates.
> **Snapshot:** repositório/documentação consultados em 2026-11-06; HEAD local, working tree, code-path e SHA de deploy ainda exigem validação no Cursor antes de código.

## 1. Decisões congeladas nesta revisão

1. DAVI continua como especialista em dados/informações DELPI, com seu módulo/adapter MCP atualmente hospedado em `api-delpi`; **não migrar código ou domínio para API Strategic Indicators**.
2. Manter, por enquanto, `mcp-api-delpi`, `END_USER_ACCOUNT`, OAuth Authorization Code + PKCE S256 e `https://minhadelpi.com.br/apps/api-delpi/mcp`. Sem renomear client, resource ou ingress em produção por organização.
3. Refatorar a **surface MCP** seguindo invariantes reais de MCPs irmãos: `get_context`, `read`, `knowledge` prioritárias, `analyze` depois, `execute` e `delete` apenas por capabilities ACT aprovadas. Não é obrigatório publicar seis tools sem semântica funcional.
4. Preservar a operação atual do DAVI para usuários existentes, suas consultas, allowlists, candidate tokens, SQL SELECT canônico, end-user identity, context budget, provenance e backend AuthZ.
5. Strategic Indicators é **futura fonte / bounded context**; DAVI poderá consumir capabilities autorizadas por contrato estável, sem import de internals nem acesso direto ao banco da API vizinha.
6. **Core API permanece responsável pela governança de acesso aos aplicativos e permissões da plataforma**. Ter acesso ao DAVI **não concede** acesso a Strategic Indicators. A API/owner de Indicadores Estratégicos deve exigir o contexto/permissões efetivas da Core API, além das regras de negócio pertinentes ao owner, em cada consulta ou alteração. Sem autorização efetiva para o aplicativo/escopo correspondente, resultado é **deny/fail-closed**, inclusive para READ, knowledge sensível, PREPARE e ACT.
7. **Sem segundo RBAC local DAVI**: MCP metadata, tool discovery, OAuth scopes, Agent instructions, claims isoladas, frontend ou Memory não autorizam negócio. A avaliação efetiva ocorre no boundary canônico do backend por usuário e recurso; o desenho de propagação/validação cross-API continua TO_INVENTORY.
8. Ajuste de metas/CRUD de Indicadores Estratégicos = TARGET posterior, em capabilities específicas, com PREPARE/ACT, AuthZ, policy, idempotência, OCC quando aplicável, auditoria e postcondition. Não habilitar executor de escrita genérico.
9. Container DAVI próprio, mudança de Keycloak client ou hosting, segundo MCP, mudança de domínio físico, nova BFF SQL: **DEFERRED**. Só reabrir mediante evidência de isolamento, escalabilidade, ownership ou operação e ADR própria.
10. Manter **este arquivo** como plano mestre. Evidências técnicas podem permanecer nos runbooks canônicos de seus donos, mas decisões, fases, gaps e aceite desta iniciativa devem ser atualizados aqui, não espalhados por novos roadmaps.

## 2. Modelo de autoridade e arquitetura

```text
Workspace Agent DAVI
  -> App / user OAuth -> MCP DAVI (continua hospedado em api-delpi)
  -> semantic capability selection + bounded adapter
       |-> API DELPI canonical use cases / policies
       |     -> authoritative AuthZ + operational sources
       |-> FUTURE stable Strategic Indicators API contract
             -> Core API platform app/permission governance (canonical)
             -> Strategic Indicators owner business AuthZ/rules
             -> authoritative indicator and target data
```

**Atenção:** o diagrama expressa responsabilidade, não uma ordem HTTP necessariamente sequencial. Inventariar se a API de Indicadores utiliza Core resolver, middleware, claims canônicas ou outro mecanismo oficial; não duplicar a verificação na camada DAVI e não confiar apenas numa consulta inicial de permissões. **Core governa acesso da plataforma; o owner de domínio executa sua AuthZ final de negócio**. Checagens devem acontecer na operação efetiva, não apenas em `get_context`.

Exemplo negativo obrigatório: usuário A possui acesso ao DAVI, mas não ao aplicativo Strategic Indicators. Se ele solicitar KPI/meta via DAVI, o backend deverá negar qualquer leitura, alteração ou inferência de valor protegido. Os READs da API DELPI que o ator já tem direito de acessar não são automaticamente revogados por essa negativa. Usuário B autorizado a indicadores só vê o escopo efetivamente permitido (filial, área, indicador, ação, conforme contrato do owner).

## 3. Baseline conhecido e lacunas

| Elemento | Evidência / status |
|---|---|
| DAVI MCP atual hospedado em `api-delpi`, resource e client atuais | PROVEN documental, runtime recheck PENDING |
| Tools atuais `discover_delpi_information` e `execute_delpi_information` | PROVEN provider discovery desta sessão e documentação |
| `search_products` atrás do broker, não tool dedicada | PROVEN documental |
| Broker READ, HMAC candidate token, allowlists e projections | PROVEN documental; código/deploy atual TO_INVENTORY |
| README descreve allowlist v30, 94 elegíveis e índice live 97 | Snapshot documental; reconciliar source e provider |
| `execute_readonly_sql` em `POST /data/sql` via broker e validador canônico | PROVEN documental; não criar novo BFF/SQL executor |
| Layering drift `Application → Composition Root` | RESOLVED documental (`DAVI-ARCH-RUNTIME-001`); regressão recheck pendente |
| Strategic Indicators: owner, contratos, permissões Core e resolvers | TO_INVENTORY; **integração não implementada por este plano** |
| Schema detalhado e diferenças das tools semânticas dos outros MCPs | TO_INVENTORY; nomes/descrições descobertos nesta sessão |
| Segundo usuário / negative business AuthZ, rate policy, rollout amplo | PENDING conforme documentação; revalidar |
| Nova interface DAVI, conexão cross-API e writes | TARGET / TEST_NOT_RUN |

A documentação mais atual do repo prevalece sobre snapshots antigos anexados ao Project para retratar source; **runtime só se prova em runtime/provider**.

## 4. Inventário das tools dos MCPs irmãos — provider discovery de 06/11/2026

| MCP | get_context | read | analyze | knowledge | execute | delete | extra | total |
|---|---|---|---|---|---|---|---|---|
| CAIO | SIM | SIM | SIM | SIM | SIM | SIM | — | 6 |
| CLARA | SIM | SIM | SIM | SIM | SIM | SIM | — | 6 |
| EVA | SIM | SIM | SIM | SIM | SIM | SIM | — | 6 |
| SURI | SIM | SIM | SIM | SIM | SIM | NAO | — | 5 |
| TÉO | SIM | SIM | SIM | SIM | SIM | SIM | `helpdesk_upload_attachment` | 7 |
| VISTA | SIM | SIM | SIM | SIM | SIM | SIM | — | 6 |
| DAVI | NAO | NAO | NAO | NAO | NAO | NAO | `discover_delpi_information`, `execute_delpi_information` | 2 |

Esta matriz prova **somente nomes e descrições anunciados ao ChatGPT nesta sessão**, não uso funcional nem implantação de cada ação. Ausência de tool física não prova ausência da capacidade subjacente.

Padrões observados:
- `get_context`: contexto, catálogo, entidade/ação, versão, schema on demand; discovery nunca é AuthZ.
- `read`: READ por entidade e ação fechadas, filtros, identificação e paginação allowlisted; source e owner AuthZ.
- `analyze`: análises tipadas com evidência, provenance e distinção fato/cálculo/inferência/recomendação; sem side effect.
- `knowledge`: guias, corpus/itens versionados e, onde existente, `search|get|sources`; não substitui fonte operacional atual.
- `execute`: ações de escrita governadas; políticas de PREPARE/ACT, consentimento e replay **diferem entre owners**, portanto não copiar mecanicamente.
- `delete`: destruição separada em cinco MCPs, geralmente proposta selada e confirmação segura.
- TÉO usa tool dedicada de upload por binding especializado: seis nomes comuns **não** impõem interface rígida.

**A investigar em código:** input/output schemas, envelopes, errors, pagination, contracts, permission checks, provider compatibility, taxas e limites, versioning e observabilidade de cada family.

## 5. Tool surface alvo DAVI (por ondas)

| Wave | Tool | Responsabilidade e gate |
|---|---|---|
| W1 | `get_context` | Descoberta limitada do catálogo e schemas sem conceder permissão; disponibilidades reais, por ator, sem expor detalhes protegidos indevidamente |
| W1 | `read` | Consultas semânticas autorizadas; **preservar regras do broker atual** (candidate token e allowlists, SQL SELECT via backend, field projections, paging/completeness, no arbitrary SQL/HTTP) |
| W1 | `knowledge` | Orientação/metodologia governada com owner, versão, fonte, classificação, provenance e tratamento anti-injection; knowledge não é dado operacional live |
| W2 | `analyze` | Análises específicas e reprodutíveis quando houver caso, owner e contrato; sem SQL livre disfarçado |
| W3+ | `execute` | ACT específico e autorizado, inicialmente somente após capability aprovada; PREPARE != ACT |
| W3+ | `delete` | Exclusões destrutivas específicas e raras, com confirmação verificável e authoritative postcondition |

Não registrar `execute/delete` vazios por aparência de padronização. Nome de tool não é permission nem capability. `read` não pode executar SQL mutável nem permitir bypass de seus fluxos internos. `get_context` pode substituir a descoberta externa para o modelo, mas a escolha do candidato técnico e a validação de execução não podem ser simplesmente removidas.

## 6. Sequência de implementação controlada

### Fase 0 — Rebaseline e inventário técnico (PRÓXIMA, READ-ONLY)

- Cursor: `git fetch origin`; `git rev-parse HEAD`; `git rev-parse origin/main`; `git status --short`; `git branch --show-current`, deployed SHA/fingerprint quando acessível.
- Ler README DAVI, `.cursor` arquitetura, security, contracts, MCP, testing e context budget; runbook `api-delpi/docs/integrations/openai-plugin-mcp.md`.
- Inventariar código das duas tools DAVI: rota, schemas, HMAC candidate tokens, allowlist, projections, SQL SELECT, throttling, intelligence/knowledge, consumers, constraints e testes.
- Inspecionar código/docs dos MCPs CAIO, CLARA, EVA, SURI, TÉO e VISTA; comparar contratos, não só nomes.
- Mapear golden prompts/casos reais e baseline de latência, compatibilidade, erros e isolamento de usuários.
- Entregar `DAVI-V2-SEMANTIC-TOOLS-INVENTORY-001` com evidência, opções para W1, impacto em contrato e risco. **Não implementar runtime.**

**Exit:** architecture review + spec W1 aceitos, source/owner/consumers identificados. Se premissa invalidada, `EXECUTION_DRIFT`.

### Fase 1 — Contratos semânticos W1 e UX de transição

- Desenhar `get_context`, `read`, `knowledge` com schema mínimo, erros tipados, atores, bounds, output, provenance e segurança.
- Definir se `read` faz resolução/discovery interna do catálogo atual, usa tokens bound ou envelope equivalente; nunca bypass.
- Classificar o conhecimento existente (persona/directives, docs, data domain, provider prompt); atribuir owner e freshness.
- Definir testes de golden queries, eval de seleção de tools, contexto e não regressão.
- Manter `discover_delpi_information` e `execute_delpi_information` durante piloto; se coexistência causar ambiguidade, validar switchover versionado com rollback e consumer proof.
- Mudanças pequenas por contrato/teste, sem alterar OAuth/client/resource, SQL owner ou backend AuthZ.

**Exit:** tool surface W1 validada localmente e no provider, com resultados comparáveis e usuários autorizados/negativos; deprecar legacy apenas se consumer impact aprovado.

### Fase 2 — Análises semânticas

- Inventariar quais análises possuem consumidores e contrato real.
- Incorporar `analyze` com provas de amostragem/completude, cálculo, métricas, escopo e rotulagem de incerteza.
- Evitar promover cálculos de negócio do owner para DAVI.

**Exit:** análise específica aceita; não exigir publicação da tool sem capability.

### Fase 3 — Strategic Indicators como nova source (FUTURO)

- Ratificar necessidades, owner humano/técnico, source of truth, API stable contract, consumers, field allowlist, freshness, classificação e budgets.
- Inventariar Core API: app access, permission resolver, vínculo entre usuário, escopo e capability, como Strategic Indicators aplica Core governance e sua própria business AuthZ.
- **Teste negativo inegociável:** usuário autenticado autorizado no DAVI mas SEM acesso a Strategic Indicators obtém deny em `read`, `knowledge` protegida, `analyze`, PREPARE e ACT relativos a indicadores. Deny em outras combinações de escopo e ações também.
- Escolher integração por HTTP/contrato estável ou mecanismo oficial aprovado; nunca importar domain/application de Strategic Indicators para `api-delpi` nem acessar banco direto.
- Validar propagação da identidade end-user, audience/delegation, fail-closed, proteção contra confused deputy e cross-user privilege inheritance.
- Integrar somente capabilities READ ratificadas; preservar consultas DELPI existentes.

**Exit:** positive e negative AuthZ e provider calls comprovados para fonte Strategic Indicators, com proveniência e sem regressão.

### Fase 4 — PREPARE / ACT e alterações de metas (FUTURO, GATE INDEPENDENTE)

- Ratificar individualmente cada ação (ex.: ajustar meta), sem CRUD genérico, com authority owner, payload, permission e escopo da Core API e backend.
- `PREPARE`: preview/diff, verificação de target/version e policy, sem persistir.
- `ACT`: authenticated user, Core platform permission + owner final business AuthZ, policy/consent verificável, idempotência, OCC quando aplicável, audit/correlation e authoritative postcondition.
- `delete` somente se owner suportar política destrutiva explícita e confirmação confiável.
- Testes positivos/negativos por usuário e ação, bypass, replay, staleness, conflito de versão e rollback.

**Exit:** cada capability ACT aceita individualmente. `2xx` ou tool discovery não provam negócio.

### Fase 5 — Avaliar extração física, novos MCPs e container (DEFERRED)

Somente se evidência comprovar benefício real de deployment/escala/isolamento/ownership. Não mover DAVI do `api-delpi` por mera nomenclatura. Qualquer novo MCP resource, OAuth client, audiences, callback e plugin exigirá ADR, migração, live evidence, pilot e rollback; não é parte desta iniciativa atual.

## 7. Sequência de dependências

```text
F0 inventário
 -> F1 W1 semantic tools (get_context/read/knowledge) + regression
 -> F2 analyze por caso concreto
 -> F3 Strategic Indicators READ via contratos + Core AuthZ
 -> F4 ACT metas por capability governada
 -> F5 container/MCP/keycloak re-evaluation somente se justificado
```

F2 e F3 podem ser ajustadas na ordem após review; F3 requer foundation de segurança, não necessariamente todas as análises. Sempre diff pequeno, deploy controlado e evidência.

## 8. Guardrails e acceptance gates

- **Business access:** usuário com acesso ao DAVI não herda acesso a Strategic Indicators. Core API governa acesso/app; backend do owner revalida business AuthZ final. Sem permissões efetivas: no protected data, no target value inference, no write.
- **Identity:** end-user token e resource binding; não usar service account para user-parity, nem confiar na existência da tool em `tools/list`.
- **Bounded exposure:** no generic SQL/HTTP/expose-all; SQL READ atual apenas por use case canônico e SqlValidator; fields/projections allowlisted e paginação/completeness explícitas.
- **Compatibility:** clientes produtivos, consumers, schemas e golden queries; rollout paralelo quando cabível, migração com rollback, sem drop abrupto do broker.
- **Knowledge:** guidance jamais autoridade, fonte live ou direito de acesso; proteger contra prompt injection.
- **Observability/security:** audit, rate policy, error handling fail-closed, redaction, no secrets.
- **Ladder:** source → local tests → public HTTP → OAuth discovery/user connection → MCP initialize/tools/list → provider discovery → authenticated call → field allowlist → negative business AuthZ (incl. Core app access) → Agent preview → deploy SHA → postcondition se ACT.
- Classificações: `PROVEN | TO_INVENTORY | PLANNED | TARGET`; execução `PASS | FAIL | PENDING | INCONCLUSIVE | TEST_NOT_RUN | STALE_EVIDENCE`; premissa invalidada `EXECUTION_DRIFT`.

## 9. Governança e documentação compacta

Este é o **único plano evolutivo principal**. A cada onda atualizar aqui: decisões, owners, fonte, contratos, checks, status, bloqueios, evidência/SHAs, mudanças de prioridade e próxima fase. Referenciar runbooks e contratos canônicos, não duplicá-los integralmente; handoff/evidence report de execução podem residir no fluxo Cursor/GitHub conforme necessário, mas **não produzir novos roadmaps paralelos**.

- GPT Architecture / Coordination: owner/boundary decisions, briefs, review/acceptance.
- Cursor: code inventory, minimal diff, testing, residual search e evidence report.
- Core API: authority de acesso/plataforma, app permissions e resolução canônica, quando aplicável.
- Strategic Indicators: authoritative indicator/target data, business use cases e final domain policy.
- API DELPI: authoritative operational sources/use cases, inclusive SQL SELECT.
- Security/Testing/Operations: OAuth/cross-API, negative tests, deployment/provenance, release.

**Não abrir nova frente cross-cutting sem voltar a Architecture / Coordination.**

## 10. Próximo brief — DAVI-V2-SEMANTIC-TOOLS-INVENTORY-001

**SCOPE:** READ-ONLY INVENTORY, nenhuma implementação.

**RQ-1:** revalidar HEAD/working tree e deployed SHA, lendo `.cursor` e as fontes canônicas.

**RQ-2:** inventariar schemas exatos `get_context/read/knowledge/analyze/execute/delete` de CAIO, CLARA, EVA, SURI, TÉO, VISTA; mapear semelhanças e diferenças justificadas de inputs, outputs, status, boundaries e auth.

**RQ-3:** mapear implementação `discover_delpi_information → candidate_token → execute_delpi_information`, catálogo, SQL read-only, intelligence, allowlist, consumidores e tests.

**RQ-4:** produzir spec proposta de W1 sem bypass, com estratégia de coexistência/cutover e matriz de golden queries/negative tests; NÃO codificar.

**RQ-5:** listar risco de integração futura Strategic Indicators via Core API (sem implementá-la), identificando os pontos de backend AuthZ e informação ainda TO_INVENTORY.

**RETURN:** BASE HEAD, FINAL HEAD, branch, working tree, files inspected, source/owner/contracts map, contract impact, tests (ou TEST_NOT_RUN), deploy/provider evidence, gaps, drift, recomendação de próximo menor diff.

**STOP:** conflito de owner, permissão ou autoridade; registrar `EXECUTION_DRIFT` e remeter à coordenação.

## 11. Critérios de sucesso (TARGET)

- DAVI segue atendendo usuários atuais sem regressão.
- Tools semânticas padronizadas com capabilities governadas e descoberta/uso comprovados.
- SQL READ existente preservado sem execução irrestrita.
- Strategic Indicators integrada futuramente somente para usuários autorizados no aplicativo e no escopo da operação, com Core API + domain backend AuthZ.
- Writes futuros usam PREPARE/ACT e pós-condição verificável, sem CRUD genérico.
- Sem migração física involuntária, sem duplicação de auth/owner e com evidências persistentes de cada onda.
