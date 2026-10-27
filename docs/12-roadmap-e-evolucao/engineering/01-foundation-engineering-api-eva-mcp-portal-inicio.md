# Portal Engenharia + EVA — Plano inicial de implementação (Foundation 001)

> **Status:** PLANNED / IMPLEMENTATION_PENDING  
> **Data:** 2026-10-27  
> **Coordenação:** EVA — Architecture / Coordination  
> **Baseline inspecionada:** `main` @ `4bb987ee41e861f16a19a4fcaa5021a91b246ce6`  
> **Natureza:** plano de implementação, **não** evidência de código implementado, teste ou deploy.

## 1. Objetivo e escopo aprovado

Primeiro incremento vertical: construir a fundação de **`engineering-api`**, **EVA / `mcp-engineering`** e **`plugins/engineering`**, entregando **apenas a página Início** do Portal Engenharia integrada ao host corporativo e composta com `@delpi/plugin-ui`.

- `engineering-api`: backend/BFF proprietário da experiência e composição do Portal, sem assumir autoridade de LMP/TOTVS, produto/BOM, desenhos ou outras fontes oficiais.
- EVA: inteligência de Engenharia em Application/Domain com contratos independentes de provider e protocolo.
- `mcp-engineering`: adapter de interoperabilidade da EVA, **não** source of truth, autorização, workflow corporativo ou approval authority. O Portal não deverá depender de MCP como único meio de obter dados.
- `plugins/engineering`: MFE integrado ao Portal e Core; somente a página Início funcional nesta onda. Usa componentes públicos do `@delpi/plugin-ui`.

Não implementar nesta onda: Sala de interação, Minhas tarefas completas, LMPs completas, Biblioteca de desenhos, geração CAD, publicações, approvals, writes de domínio, expansão de MCP para outras áreas ou cutover.

## 2. Referências e fatos inventariados

- [Playbook — Portal Engenharia](./PLAYBOOK-MODULO-ENGENHARIA.md): jornadas, separação de owner, basePath alvo `/apps/engineering`, TopBar e sequência E0 → fundação → Início.
- [Design de Arquitetura de Informação e UX](./DESIGN-IA-ENGENHARIA.md): TopBar `Início → Visão geral → Sala de interação → Minhas tarefas → LMPs → Ajuda`.
- [Catálogo do plugin-ui](../../../../plugins/plugin-ui/docs/component-catalog.md): factories e componentes visuais compartilhados (TopBar, PageHero, NavigationCard, WorklistItem, AlertQueue, EmptyState, ScreenLoading, etc.).
- `api-delpi/app/interface/http/routes/engineering/engineering_router.py` e `api-delpi/app/composition/engineering_composer.py`: contratos/use cases de LMP e outras capacidades já existentes; não transferir regras ou acesso direto ao MFE.
- `.cursor/rules/platform-architecture-boundaries.mdc` e `.cursor/rules/mfe-own-api-no-direct-api-delpi.mdc`: boundaries e proibição de MFE com API própria acessar `api-delpi` diretamente.
- O inventário inicial da árvore do monorepo não encontrou diretórios raiz `engineering-api/`, `mcp-engineering/` ou `plugins/engineering/`. Confirmar novamente em HEAD antes de criar arquivos.

**Classificação:** documentos e caminhos encontrados = PROVEN no repositório; existência operacional, contratos completos, permissões e deploy das três novas frentes = TO_INVENTORY; incremento = PLANNED.

## 3. Arquitetura e ownership

```text
Keycloak (identidade) + Core (apps, RBAC, governança) + Portal (host)
                     |
               plugins/engineering
                 (Início/MFE)
                     |
                engineering-api
            (BFF, AuthZ, composição)
                /           \
        Domain APIs      EVA Application
       (ex.: api-delpi)       |
                         mcp-engineering
                       (adapter para outros
                       consumidores autorizados)
```

A ligação lógica com EVA precisa de contrato próprio; o BFF não deve depender de internals do MCP. Domain APIs e sistemas oficiais continuam donos dos dados e das regras. DÉLIA poderá futuramente consumir capabilities EVA governadas, sem dependência desta primeira entrega.

### Invariantes

1. `plugins/engineering` não chama `api-delpi`, `commercial-api`, arquivos privados ou banco diretamente.
2. `engineering-api` não importa Domain/Application de outros bounded contexts nem duplica regras LMP/TOTVS.
3. Domain/Application EVA não dependem de HTTP, FastAPI, DB, LLM SDK, MCP SDK ou CAD SDK.
4. MCP discovery, JWT claims, UI, model output e tool metadata não são AuthZ.
5. Backend-first/fail-closed; permissões e resource scope verificados no owner correspondente.
6. Reads preservam escopo e provenance; writes, aprovação e publicação ficam fora da onda.
7. Aplicar Abstraction Gate antes de introduzir portas, registries, stores ou engines.

## 4. Bounded implementation steps

### F0 — Reancoragem e inventory gate

- Inspecionar `HEAD`, working tree/`git status` do ambiente de execução, authorities de `.cursor/rules`, manifest e padrões dos MFEs/APIs maduros, configurações de gateway/Core, testes, CI e deploy.
- Mapear owner → source → consumer → contract → AuthN/AuthZ → error/limits → evidence para a composição inicial.
- Confirmar se existem implementações equivalentes e registrar decisões/ledger. Nenhum novo banco/vector store sem necessidade provada.

**Saída:** source/ownership map, contratos candidatos, RQ/AC revisados, evidência da baseline.

### F1 — engineering-api foundation

- Criar serviço apenas se inventário confirmar ausência/equivalência não reutilizável; seguir padrões canônicos de APIs de domínio da plataforma.
- Bootstrap, configuração segura, health/readiness, observabilidade/correlation e testes de inicialização.
- Definir contrato **read-only** de composição do Início com resultados parciais (`partial_sources`), timeout e erros diferenciados; não fabricar KPIs/contagens.
- Port/gateway para primeira fonte autorizada (LMP candidata pela presença dos use cases existentes), sem acesso direto pelo MFE.
- Integração Core AuthZ real, com casos positive/sibling/negative e escopo de recursos.

### F2 — EVA Application + mcp-engineering foundation

- Definir primeira capability EVA de **leitura/análise assistida** somente após confirmar source, consumer, policy e dados de avaliação; LMP é candidata, não promessa de análise produtiva.
- Separar input estruturado, recuperação autorizada, análise, evidence/provenance, limitações, erros e outputs candidatos.
- Implementar adapter MCP mínimo e catálogo semântico bounded; nenhuma publicação/escrita ou exposição de internals do Chat.
- Evals adequadas ao caso: grounding, unsupported claims, casos negativos, permission boundaries, falha do upstream e task outcome.
- Sem reutilizar Chat como backend runtime; inventário legado é referência.

### F3 — plugins/engineering / página Início

- Manifest/Module Federation, host, app/route registration e RBAC via contratos canônicos do Core.
- BasePath alvo `/apps/engineering`, F5, back/forward e deep links.
- Reutilizar `@delpi/plugin-ui`; não copiar `TopBar`, chrome visual ou lógica de autorização.
- TopBar planejada: **Início → Visão geral → Sala de interação → Minhas tarefas → LMPs → Ajuda**; fora de escopo desta onda, rotas não devem fingir páginas concluídas.
- Home prioriza atenção pessoal, tarefas, LMPs críticas/recentes, menções/salas, catálogo de ferramentas e atividade recente **quando contratos confiáveis existirem**. Sem contrato, exibir estados honestos, não métricas fictícias.
- Espaço/entry point EVA claramente identificado como capacidade assistida e condicionado a capability/AuthZ real.
- Estados loading, empty, error, forbidden e partial; acessibilidade, desktop/mobile, tema claro/escuro e ajuda coerente.

### F4 — integração e aceite

- Verificar contrato MFE → engineering-api → fonte autorizada, e capability EVA → adapter MCP, com limites e provenance.
- Testar smoke no host federado, positive/sibling/negative, degradação parcial, compatibilidade, autenticação e autorização.
- Residual search para bypass `api-delpi`, duplicação, imports cross-context, secrets e regressão no kit.
- Registrar testes no SHA exato, outcome evidence, diffs, riscos e residuals em `EVA EXECUTION REPORT`. Sem autoaprovação nem deploy declarado apenas por build verde.

## 5. Requisitos e critérios de aceite (provisórios até F0)

| Requisito | Critério mínimo |
|---|---|
| RQ-ENG-001 — Foundation engineering-api | AC-ENG-001: serviço inicializável, health/readiness, configuração, erros, observabilidade e tests; sem bypass de Domain APIs |
| RQ-ENG-002 — Contrato de Início | AC-ENG-002: resposta read-only com provenance e degradação parcial; AuthZ positiva/negativa e downstream fake |
| RQ-EVA-001 — Fronteira EVA/MCP | AC-EVA-001: Domain/Application independentes de MCP/LLM/provider; adapter com catálogo mínimo e contrato explícito |
| RQ-EVA-002 — Primeira análise assistida | AC-EVA-002: grounded output, source/revision/limitations, fail-closed, testes/evals e ausência de claim não suportada |
| RQ-PORTAL-001 — MFE federado | AC-PORTAL-001: manifest, Core/Portal, basePath/deep link, kit-first e sem acesso direto a api-delpi |
| RQ-PORTAL-002 — Página Início | AC-PORTAL-002: componentes do kit, conteúdo conforme disponibilidade real, loading/empty/error/forbidden/partial, responsividade/acessibilidade |
| RQ-INT-001 — Fluxo integrado | AC-INT-001: contrato/autorização/observabilidade testados ponta a ponta, testes no SHA e outcome evidence |

## 6. Gates e riscos

- **ARCHITECTURE_DECISION_REQUIRED:** novo owner, nova source of truth, novo bounded context além dos dois explicitamente propostos, mudança de authority ou alteração cross-cutting.
- Confirmar integração Core (app id, permissions, manifest) e gateway antes de fixar nomes de operações, endpoints e scopes.
- Não estabelecer o nome `mcp-engineering` como autoridade funcional: é nome do adapter/serviço de interoperabilidade.
- Não prometer dados da Home antes da fonte e policy serem comprovadas.
- Não abrir banco específico, infraestrutura de IA ou filas sem RQ/consumer demonstrado.
- Deploy e feature flags seguem política operacional do repositório; esta documentação **não autoriza** bypass de gates de segurança nem a exposição de funcionalidades incompletas.

## 7. Coordenação e handoffs

- **EVA — Foundation / Inventory**: F0 e prova de fatos/ownership.
- **EVA — Backend / Domain / Application**: F1 e separação Domain/Application em F2.
- **EVA — MCP / APIs / Interoperability**: adapter MCP/contratos em F2.
- **Portal Engenharia — Frontend / MFE / UX**: F3.
- **EVA — Security / AuthZ / Governance** e **EVA — Integration / Acceptance / Evals**: revisão transversal F4.
- **EVA — Architecture / Coordination**: reconciliar RQ/AC, aprovar decisões e emitir veredicto `ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE`.

**Próximo bounded step autorizado:** executar F0 e entregar inventário factual + contrato inicial revisável para F1–F3. Implementação e aceite dependem de evidência; não presumir runtime.
