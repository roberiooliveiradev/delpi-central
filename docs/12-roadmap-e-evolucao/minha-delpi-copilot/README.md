# Minha DELPI Copilot

> **Status:** `PLANNED / NOT_STARTED`  
> **Decisão de produto:** **aplicação nova e standalone**  
> **Visão:** **um único Copilot para escritório, reuniões e chão de fábrica**  
> **Próxima etapa:** **C0.S0 — Platform/Media/Device/Biometric/OT Rebaseline Inventory**  
> **Ordem executável:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
> **Boundary standalone:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
> **Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)  
> **Biometric/Human Observation:** [`54-biometric-identity-and-human-observation-governance.md`](./54-biometric-identity-and-human-observation-governance.md)  
> **Baseline da plataforma:** [`51-platform-integration-baseline.md`](./51-platform-integration-baseline.md)  
> **Estrutura/Bootstrap:** [`52-standalone-repository-and-bootstrap-plan.md`](./52-standalone-repository-and-bootstrap-plan.md)  
> **Arquitetura/design patterns:** [`49-architecture-and-design-patterns-standard.md`](./49-architecture-and-design-patterns-standard.md)  
> **Prompt do Cursor:** [`23-prompt-cursor-execucao.md`](./23-prompt-cursor-execucao.md)  
> **Ledger:** [`evidence/execution-ledger.md`](./evidence/execution-ledger.md)

## 1. Decisão fundamental

O **Minha DELPI Copilot não é uma expansão do Minha DELPI Chat**.

```text
Minha DELPI Chat                 Minha DELPI Copilot
-----------------------------    ------------------------------
plugins/minha-delpi-chat         novo MFE próprio
minha-delpi-ai-api               nova API própria
runtime/persistência do Chat     runtime/persistência próprios
release do Chat                  release próprio

                 SEM DEPENDÊNCIA DE RUNTIME
```

O Copilot será construído **do zero até 100%**, preservando as fundações corporativas da Minha DELPI: Portal, Core API, Keycloak, Gateway, Manifest, Module Federation, `plugin-ui` e APIs de domínio.

O código do Chat pode ser consultado como referência técnica durante inventário, mas não pode virar dependency, base class, proxy, database authority ou migration path do Copilot.

## 2. North Star ampliado

> **Minha DELPI Copilot é a interface inteligente entre as pessoas e a operação da DELPI. Está presente no escritório e na fábrica, entende texto, voz, imagem, vídeo, documentos, contexto operacional e dados empresariais; pode reconhecer usuários conhecidos sob governança explícita e compreender padrões observáveis de trabalho; ajuda pessoas a entender, decidir, executar e aprender, preservando permissões, evidências, segurança, privacidade e governança.**

```text
PERGUNTAR  → entender, pesquisar, explicar, analisar
FAZER      → navegar, consultar, criar, alterar, aprovar, executar
ACOMPANHAR → monitorar, detectar, alertar, reagir
TRABALHAR  → investigar, colaborar, planejar, acompanhar, concluir
APRENDER   → transformar experiência validada em conhecimento governado
```

## 3. Presença e acesso

A direção do produto é permitir que o **entry point do Copilot esteja amplamente disponível aos usuários autenticados da Minha DELPI**, conforme rollout e permissão de acesso ao próprio Copilot.

Isso não significa acesso universal a dados ou ações.

```text
Copilot disponível
+
permissões efetivas do usuário
+
contexto atual
+
capability/policy/risk
=
comportamento realmente disponível
```

Invariante:

```text
Copilot effective capabilities ⊆ user effective capabilities
```

Biometria pode ajudar a reconhecer quem é um usuário conhecido, mas:

```text
biometric match
!= authenticated session
!= Core permission
!= Business Action authorization
```

## 4. Quatro surfaces, um produto

```text
GLOBAL      → painel lateral/contextual no Portal
WORKSPACE   → página completa para análise/trabalho prolongado
MEETING     → reunião assistida com voz, dados e mídia autorizada
FRONTLINE   → operador/posto/máquina com voz, câmera e UI simplificada
```

Todas usam:

```text
uma Copilot API
um Copilot MFE
uma identidade de produto
Core/RBAC
Policy/Decision Gate
Evidence
Durable Work
```

Não existem agentes/backends separados por departamento ou surface.

## 5. Owners alvo

```text
minha-delpi-copilot-api/          → backend/runtime inteligente independente
plugins/minha-delpi-copilot/      → MFE React/Vite independente e suas surfaces
portal/                           → Shell/host/navegação/contexto global
core-api/                         → apps/rotas/RBAC/governança/user authority
keycloak                          → identidade/SSO
gateway/                          → entrada/routing
plugins/plugin-ui/                → design system compartilhado
APIs de domínio                   → dados e regras de negócio
OT/domain systems                 → machine/process truth e safety owners
infra/                            → compose/deploy/env/network/storage
```

Nomes finais são congelados em C0; a arquitetura física recomendada está em `52`.

## 6. Arquitetura resumida

```text
Usuário / Device
      ↓
Portal / Copilot Surface
      ↓
Minha DELPI Copilot MFE (federated)
      ↓
Gateway
      ↓
Minha DELPI Copilot API
  ├─ Core API / RBAC / apps/routes
  ├─ Domain APIs / OpenAPI
  ├─ Knowledge / Graph / Evidence
  ├─ LLM / Speech / Vision / Biometric adapters
  └─ Copilot-owned persistence
```

O Portal **hospeda** o Copilot; não implementa sua inteligência.

A Copilot API **orquestra**; não assume ownership das regras de negócio das outras APIs, da identidade corporativa nem da segurança industrial.

## 7. Meeting Mode

Quando liberado, Meeting Mode poderá:

- iniciar/parar captura explicitamente;
- transcrever voz;
- responder perguntas consultando dados reais e autorizados;
- usar câmera/tela quando policy/device permitirem;
- associar participante/speaker a usuário enrolled quando biometric capability estiver habilitada;
- registrar fatos, decisões e pendências;
- gerar **ata viva**;
- propor ações;
- criar Tasks/Cases/solicitações após governance;
- retomar pendências em reunião futura.

A ata distingue:

```text
transcrição
resumo
identity candidate/confirmed association
source data/evidence
decisão humana confirmada
ação candidata
ação executada/verificada
```

## 8. Frontline Mode

Frontline leva o mesmo Copilot ao trabalho operacional.

Experiência alvo:

```text
usuário autenticado
+ optional governed biometric identity assistance
+ device/posto
+ OP/operação
+ máquina
+ produto/revisão
+ voz/câmera
→ Copilot
→ procedimento/desenho/APIs/histórico/Evidence
→ orientação ou ação governada
```

Prioridades:

- large-touch UI;
- hands-free voice;
- touch/text fallback;
- câmera/imagem;
- reconhecimento de usuário conhecido quando habilitado;
- desenho/procedimento vigente;
- manutenção/qualidade contextual;
- registrar ocorrência/escalar ajuda;
- treinamento contextual;
- shared-device isolation.

## 9. Identidade biométrica e análise humana

O Copilot pode reconhecer **usuários conhecidos e enrolled** por foto/vídeo/rosto e voz conforme finalidade/policy explícitas.

Target:

```text
explicit enrollment
→ protected face/voice template
→ current sample
→ closed-set candidate match
→ confidence/policy/liveness when required
→ correctable userRef association
```

Unknown/low-confidence permanece desconhecido ou pede confirmação.

A capability pode ajudar em:

- participant attribution em Meeting;
- speaker diarization/recognition;
- shared-device identity assistance;
- associação de Evidence a participante/operador;
- continuidade contextual.

Ela **não** cria permission.

O Copilot também pode analisar padrões **objetivos e observáveis do processo**, como sequência de etapas, interação com ferramenta/máquina, repetição/retrabalho, tempos, deslocamentos relevantes ao fluxo e pedidos de ajuda.

Por default, não inferir de rosto/voz/comportamento:

- personalidade;
- honestidade/confiabilidade;
- intenção moral/lealdade;
- emoção como truth;
- saúde/diagnóstico;
- atributos sensíveis;
- aptidão profissional global;
- propensão disciplinar.

Biometria/Human Observation também não podem ser authority automática para contratação, promoção, punição, remuneração, avaliação formal, suspensão ou desligamento.

## 10. Aprendizagem do processo

O Copilot pode ajudar a capturar conhecimento tácito e experiências do processo, mas somente como **candidate knowledge**:

```text
observação/experiência
→ Evidence/context
→ candidate
→ owner/specialist review
→ eval
→ version/publish
```

Nunca:

```text
uma observação do operador
→ alteração automática do procedimento de produção
```

Também não criar perfil secreto do trabalhador como mecanismo de aprendizagem.

## 11. Segurança industrial e privacidade

Não fazem parte do default scope:

- câmera/microfone/identity recognition ocultos;
- open-world/indiscriminate facial recognition;
- emotion/personality/honesty inference;
- scoring/vigilância oculta de pessoas;
- raw audio/video/biometric templates sem purpose/retention definidos;
- decisão trabalhista automática baseada em biometria;
- visual finding tratado automaticamente como aprovação/reprovação oficial;
- free-form LLM → PLC/CNC/robô/máquina;
- Copilot substituindo safety PLC/interlocks.

Autonomia L5 empresarial **não** concede autoridade OT.

Qualquer futura atuação física requer safety gate separado, deterministic typed commands, allowlist, machine-state checks, industrial owner, interlocks independentes, autorização, test/simulation, fail-safe e audit.

## 12. Integração com o Portal

O Portal atual já suporta MFEs `federated` via `AppHost`, que resolve `remoteEntry`, carrega `mount()` e injeta `getAccessToken`, `basePath`, pathname, rotas e contexto do usuário.

O Copilot terá progressivamente:

1. **app/full page** registrado por manifesto;
2. **surface global** no Shell;
3. **Meeting surface** do mesmo MFE/runtime;
4. **Frontline surface** do mesmo MFE/runtime para devices compatíveis.

Workspace Context e Platform Commands atravessam contratos tipados; autorização continua em Core/domain owners.

## 13. Princípios não negociáveis

1. Copilot API própria; nenhum endpoint do Chat é requisito de funcionamento.
2. Copilot MFE próprio; nenhum source import de `plugins/minha-delpi-chat`.
3. Persistência/migrations próprias; nenhuma tabela do Chat é authority.
4. Core/RBAC continua authority de permissões e identidade corporativa materializada.
5. Domain APIs continuam authority de dados/regras.
6. Business Actions são OpenAPI-first.
7. Portal continua authority de navegação/hosting.
8. `plugin-ui` é o design system compartilhado.
9. Um único Copilot; Expertise/Playbooks especializam sem agentes departamentais.
10. Entity/Evidence/Decision/Workflow/Event usam foundations compartilhadas.
11. Business Graph conecta referências e não replica bancos.
12. Durable Work reutiliza executors canônicos.
13. Chain-of-thought não é persistida/exposta.
14. Clean Architecture + Ports & Adapters + DDD pragmático conforme `49`.
15. Voice/image/video/biometric signals são modalidades/contexto, não bypass de permission.
16. Contexto industrial reutiliza WorkspaceContext + EntityRef.
17. Data minimization é default para mídia/biometria.
18. Device identity != user identity; biometric candidate != authenticated session.
19. Process learning publica somente via governance.
20. Human Observation fica limitado a sinais observáveis do processo.
21. Copilot não é industrial safety authority.

## 14. Ordem foundation-first

```text
C0 — Platform + Architecture + Media/Privacy/Biometric/OT Foundation Freeze
→ C1 — Standalone App Bootstrap
→ C2 — Portal + Operational Context + Platform Commands
→ C3 — Intelligence Core + Multimodal/Biometric Foundations
→ C4 — Business Reads + Business Graph
→ C5 — Governed Writes + Durable Work Foundation
→ C6 — Tasks/Cases/Rooms/Inbox/Watch + Meeting/Frontline + Ecosystem/Learning
→ C7 — Advanced Realtime + Autonomy/Simulation/Model Routing/Rollout
```

Primeiro provamos boundaries e integração; depois construímos intelligence/media/biometric/work surfaces.

## 15. C0 — o que precisa congelar

```text
platform inventory
standalone boundaries
repo/service names
Gateway/Compose/Manifest contracts
Core/RBAC integration
MFE hosting contract
media/device/realtime inventory
privacy/consent/retention boundaries
biometric enrollment/template/liveness boundaries
shared-device identity/session boundary
Human Observation prohibited-inference boundary
operational context sources
OT/industrial safety boundary
shared primitives / MediaRef / biometric-ref decisions
architecture/patterns
ports/persistence boundaries
error/event/state/resilience rules
contract/conformance harness
```

C1 só inicia com `FOUNDATION_FREEZE=PASS`.

## 16. Business Actions não dependem do Chat

O Copilot implementará sua própria cadeia:

```text
OpenAPI
→ Copilot Action Catalog/index
→ allowed capabilities
→ retrieval/planner
→ schema/argument validation
→ RBAC/policy/Decision Gate
→ generic executor
→ Domain API
→ Outcome/Evidence
```

Texto, voz, Meeting ou Frontline convergem para esse mesmo pipeline. Biometric identity apenas ajuda a resolver contexto/participante; não cria action authority.

## 17. Documentos canônicos

| Documento | Papel |
|---|---|
| `16` | única ordem de implementação |
| `17` | owners/primitives/contracts |
| `20` | testes/gates |
| `21` | state/persistence/media/biometric refs |
| `23` | prompt mestre Cursor |
| `25` | requisitos `CP-*` |
| `49` | architecture/design patterns |
| `50` | boundary standalone |
| `51` | baseline factual Portal/Core/APIs/MFEs |
| `52` | estrutura física/bootstrap |
| `53` | multimodal/Meeting/Frontline/industrial safety |
| `54` | biometric identity/Human Observation governance |
| ledger | estado/evidence executável |

Specs temáticas detalham comportamento, mas não podem contradizer authorities acima.

## 18. Relação com documentos antigos de migração de agents

Qualquer trecho que trate o Copilot como migração de `AgentSpecializationService`, `userActivatedAgent`, `softAgentHandoff`, `agent_id` ou sessions do Chat está **SUPERSEDED / OUT_OF_SCOPE**.

O Copilot novo simplesmente não nasce com essas dependências.

## 19. Primeiro passo

Abrir `23-prompt-cursor-execucao.md` e executar **somente C0.S0**.

C0.S0 é inventário/evidence, agora incluindo media/device/privacy/frontline/biometric/OT. Não cria planner, RAG, biometric runtime, Meeting, Frontline, Graph, Case, Watch ou Model Router.

O primeiro runtime após Foundation Freeze será o **bootstrap standalone**: API + MFE + auth + Core + Gateway + Compose + Manifest + Portal federated mount.
