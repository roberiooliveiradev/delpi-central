# DAVI V2 — Inventário inicial das surfaces MCP semânticas

> **Data:** 2026-11-06
> **Status:** INVENTORY_PARTIAL / PROPOSAL_ONLY; nenhuma mudança de runtime autorizada.
> **Método:** discovery das ferramentas expostas nesta sessão ChatGPT pelos conectores dos especialistas. Isto prova **provider tool discovery nesta sessão**, não o estado completo do source/deploy, de contratos internos, nem o sucesso de chamadas de negócio. HEAD, working tree e deploy SHA exigem revalidação antes do brief de implementação.
> **Relacionados:** [baseline DAVI](README.md) e [roadmap de reestruturação](01-reestruturacao-strategic-indicators-mcp-semantico.md).

## 1. Direção priorizada

O DAVI permanece conectado ao MCP atual da API DELPI durante esta onda. Objetivo **prioritário**: alinhar a **surface de tools semânticas** ao padrão observado nos outros especialistas, mantendo as capacidades existentes e sua continuidade operacional. A integração com Strategic Indicators virá por contrato governado, em onda posterior. Migração de hosting/container, rename de resource/client Keycloak, novo BFF SQL e separação de runtime ficam **DEFERRED / TO_INVENTORY**; não são pré-requisitos da padronização.

Não criar um MCP adicional somente para trocar nomenclatura. Não duplicar o executor SQL: o README DAVI registra que `execute_readonly_sql` já passa pelo broker de duas tools e pelo contrato canônico de `api-delpi`. Validar no código e no runtime antes de generalizar.

## 2. Matriz de descoberta das tools (evidência desta sessão)

| Especialista | get_context | read | analyze | knowledge | execute | delete | Outras | Total |
|---|---|---|---|---|---|---|---|---|
| CAIO | SIM | SIM | SIM | SIM | SIM | SIM | — | 6 |
| CLARA | SIM | SIM | SIM | SIM | SIM | SIM | — | 6 |
| EVA | SIM | SIM | SIM | SIM | SIM | SIM | — | 6 |
| SURI | SIM | SIM | SIM | SIM | SIM | NAO | — | 5 |
| TÉO | SIM | SIM | SIM | SIM | SIM | SIM | helpdesk_upload_attachment | 7 |
| VISTA | SIM | SIM | SIM | SIM | SIM | SIM | — | 6 |
| DAVI | NAO | NAO | NAO | NAO | NAO | NAO | discover_delpi_information; execute_delpi_information | 2 |

**Significado:** `NAO` indica ausência daquela tool da surface disponível **nesta sessão**, não ausência de lógica equivalente ou impossibilidade de implementação. Não confundir tool anunciada com AuthZ, ação de negócio aprovada ou prova de execução.

## 3. Semântica recorrente observada

- **get_context:** descoberta do escopo/contexto e catálogo de entidades/ações/schemas (por exemplo CAIO/EVA requerem consulta inicial; CLARA expõe actor/catalog/schema/persona). Contexto é dica de disponibilidade, jamais autorização.
- **read:** leitura via vocabulário fechado (tipicamente `entity + action`, filtros e paginação allowlisted). Sem URL/método/SQL arbitrário; owner AuthZ ao executar.
- **analyze:** análise tipada, fundamentada, não persistente. CAIO/EVA qualificam OBSERVED/CALCULATED/INFERRED/UNKNOWN; outras usam rótulos FACT/CALCULATION/RECOMMENDATION ou classes de preview.
- **knowledge:** consulta de orientação/conhecimento versionado e governado, com diferentes contratos de `search/get/sources` ou guias por tópico. Nunca fonte operacional live ou autoridade.
- **execute:** escrita governada. Modelos variam por risco: chamadas diretas autorizadas, PREPARE/COMMIT, propostas seladas, idempotência, auditoria e read-back.
- **delete:** superfície separada para destruição em CAIO, CLARA, EVA, TÉO e VISTA; confirmação segura e autorização final são próprias de cada owner.
- **specialized adapter:** TÉO dispõe de `helpdesk_upload_attachment` porque arquivo requer binding/protocolo especial; isso demonstra que seis tools não constituem limite rígido.

**Não padronizar apenas os nomes.** Inventariar schemas, envelopes, erros, limites, consentimento e compatibilidade antes de propor um contrato DAVI concreto.

## 4. DAVI atualmente observado

Tools físicas:
- `discover_delpi_information`: recebe intenção de leitura e devolve `candidate_token` opaque para candidatas elegíveis.
- `execute_delpi_information`: executa candidato da descoberta, com token; não aceita URL/path/method/operationId/SQL arbitrário. Backend AuthZ permanece final.

O README do DAVI registra broker governado, `search_products` atrás de discover→execute, allowlist evoluída e `execute_readonly_sql` como contrato backend SQL SELECT. Esses fatos são **documentary evidence**; contagens de allowlist e deploy precisam de rebaseline.

## 5. Surface TARGET proposta (não implementation authorization)

| Tool | Intenção DAVI | Ordem proposta | Gate |
|---|---|---|---|
| `get_context` | capabilities disponíveis, catálogo e schemas on demand com estado honesto | W1 | confirmar formato/semântica cross-MCP, segurança e context budget |
| `read` | consultas oficiais governadas, preservando current broker/allowlists | W1 | planejar discover→candidate→execute por baixo ou outro contrato sem perder safeguards |
| `knowledge` | guias DAVI e conhecimento organizacional aprovado/owner-authorized | W1 | inventariar assets, owner, index/corpus, versionamento, citations, data classification |
| `analyze` | análises específicas com provenance, cálculo, completude e incerteza | W2 | tipos de análise/consumers/outputs aprovados; sem SQL livre disfarçado |
| `execute` | ACT estritamente por capability (ex. futuras metas Strategic Indicators) | W3+ | owner/source/contract, end-user AuthZ, PREPARE/ACT, idempotência, policy, audit e postcondition |
| `delete` | exclusão destrutiva específica, se realmente necessária | W3+ | destructive policy, proposta selada, confirmação verificável, revalidação de AuthZ, rollback/retenção |

`execute` e `delete` não devem ser registrados como ferramentas ativas vazias só para completar o padrão. Mesmo `analyze` necessita capability real antes de ser exposto.

## 6. Estratégia de transição sem regressão

1. Inventariar HEAD, deploy, MCP server registration, schemas exatos e fluxos internos do broker atual.
2. Mapear consumidores e golden prompts, inclusive consultas SQL SELECT e usos cotidianos; estabelecer baseline de resultados, latência, erros e permissões.
3. Ratificar `get_context`, `read`, `knowledge` por contratos; implementar primeiro em modo aditivo/canary, preservando `discover_delpi_information` e `execute_delpi_information`.
4. Impedir bypass dos candidate tokens, output projections, schema validation, governança SQL, scopes e backend AuthZ pelo novo `read`.
5. Verificar se expor tools antigas + novas causa seleção ambígua do modelo; se causar, desenhar fase de switchover com cobertura/evals e rollback, sem retirada abrupta.
6. Provar source tests, provider tools/list, live calls end-user, second-user negative AuthZ, outputs, completeness, rate/abuse handling e agent preview.
7. Depreciar/remover nomes legados apenas após consumer inventory, evidência de paridade e cutover/rollback.
8. Integrar Strategic Indicators como capability/source family governada **depois**, por contrato estável e AuthZ do owner; sem acoplamento de internals ou migração do MCP física obrigatória.

## 7. Brief próximo — DAVI-V2-SEMANTIC-TOOLS-INVENTORY-001 (READ-ONLY)

**Cursor deve:**
- `git fetch origin`; reportar `HEAD`, `origin/main`, `git status --short`, deployed SHA e `EXECUTION_DRIFT` quando aplicável;
- ler `.cursor` transversal, DAVI README, runbooks MCP e documentação dos MCPs CAIO, CLARA, EVA, SURI, TÉO, VISTA;
- inventariar por ferramenta: owner, route, schema input/output, version, permissions, identity, field projections, errors, limits, provenance, business outcomes e source files;
- mapear implementation path de `discover_delpi_information`, `execute_delpi_information`, incluindo `execute_readonly_sql`, candidate tokens e agent intelligence assets;
- comparar os contratos das seis famílias, identificar invariantes reais e diferenças legítimas;
- gerar design mínimo para W1 e matriz de regressão; **não implementar**;
- incluir `BASE HEAD / FINAL HEAD / files inspected / tests / deployment/provider evidence / unresolved`.

**STOP CONDITIONS:** qualquer tentativa de refatorar simultaneamente OAuth/client/hostname, adicionar SQL executor, renomear recursos produtivos, abrir CRUD genérico ou implementar cross-API antes do gate específico.

## 8. Aceite deste documento

- Inventário de **nomes e propósitos** observados: PASS (provider discovery desta sessão).
- Inventário detalhado de schemas, contratos, código e deploy de todas as tools: PENDING.
- Desenho semântico W1: PROPOSAL_ONLY.
- Implementação/testes de regressão do DAVI: TEST_NOT_RUN.
- Mudança de ferramenta produtiva: NONE.
