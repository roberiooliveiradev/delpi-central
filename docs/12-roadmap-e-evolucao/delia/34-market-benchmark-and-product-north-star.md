# DÉLIA — Benchmark de Mercado e North Star

**Status:** `REFERENCE_ONLY` — referência estratégica, não authority de execução nem evidência DELPI  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Thematic target:** `53–68`

## 1. Objetivo

Registrar classes de capacidades usadas como referência estratégica para a DÉLIA. Este documento **não prova** tecnologia, contrato, infraestrutura, provider, licença ou capability existente na DELPI e não define sequência de implementação.

Qualquer afirmação atual sobre vendor/API/mercado exige revalidação em fonte recente no momento em que for usada para decisão concreta.

## 2. North Star

> **A DÉLIA é a camada de Continuous Operational Intelligence da Minha DELPI: percebe contexto e sinais, entende dados/processos autorizados, pesquisa, analisa, prevê/simula, decide sob políticas, prepara/executa o permitido, verifica outcomes e aprende sob governança — sem criar authority paralela.**

```text
PERCEBER
ENTENDER
PESQUISAR
ANALISAR
PREVER/SIMULAR
DECIDIR
PREPARAR/EXECUTAR
VERIFICAR
COMUNICAR
APRENDER COM GOVERNANÇA
```

## 3. Classes de referência

As categorias abaixo são referências conceituais; nomes de vendors históricos podem aparecer como exemplos de mercado, mas não são fatos arquiteturais DELPI nem recomendação de contratação/reuso.

### Enterprise AI / Operational Intelligence

Padrões de interesse:

- enterprise context/tools/actions;
- event triggers/proactivity;
- human-in-the-loop;
- model/tool governance;
- external connectors;
- personalization/memory;
- interoperability;
- centralized observability/governance.

### Automation / RPA orchestration

Padrões de interesse:

- intelligence separated from deterministic technical execution;
- APIs/robots/functions/humans as executor classes;
- queue/worker/package management;
- exception handling;
- technical result separated from verified business outcome.

Interpretação DELPI: **DÉLIA = intelligence/Policy/Decision/Work; Automation Hub = technical execution**.

### Process Intelligence

Padrões de interesse:

- process discovery;
- event-log reconstruction;
- variants/conformance/bottlenecks;
- automation opportunity detection;
- before/after measurement.

Interpretação DELPI: process evidence sem employee surveillance.

### AI Governance / Control Tower

Padrões de interesse:

- inventory/owner/risk/evals;
- health/cost/incidents;
- rollout/rollback/revoke/kill switches.

Interpretação DELPI: Control Tower é governance plane, não segundo planner nem business permission authority.

### Semantic Layer / Graph

```text
Business Graph = relações
Semantic Business Layer = significado/cálculo governado
```

Nenhum deles absorve systems of record.

### Predictive / Prescriptive / Twin

```text
Prediction != FACT
Recommendation != Authorization
Twin != Source of Truth
Simulate != Apply
```

### Edge / Offline

Interpretação DELPI: Edge governa inferência/cache/continuidade quando aprovado, sem ampliar authority e sem free-form machine actuation.

### Model Lifecycle / Marketplace

Padrões de interesse: eval, approval, deployment, drift, rollback/revoke e catálogo governado de reusable assets. Install/enable não concede permission.

### Analysis / Artifacts

Padrões de interesse: analysis sandbox isolado e Artifact Workspace versionado/provenanced.

### MCP / A2A / interoperability

Padrões de interesse: adapters/allowlists/trust lifecycle/least context; discovery nunca significa approval.

## 4. Diferenciadores target DELPI

```text
DÉLIA standalone
+ Core/Keycloak/Portal boundaries
+ Domain APIs/OpenAPI-first
+ Evidence/Policy/Decision/Work
+ Business Graph
+ Semantic Business Layer
+ Expertise/Playbooks/Knowledge
+ Personal Memory governada
+ Process Intelligence
+ Event/Decision Intelligence
+ Automation Hub boundary
+ Analysis/Artifacts
+ Predictive/Prescriptive/Twin
+ Meeting/Frontline/Edge
+ MCP/A2A interoperability
+ AI Control Tower
+ Model Lifecycle/Marketplace
```

Tudo acima é `TARGET/PLANNED` salvo quando fonte canônica/evidence classificar como `PROVEN`.

## 5. Ideias não copiadas cegamente

- departmental multi-agent sprawl;
- RPA-first quando API autoritativa existe;
- hidden worker/task surveillance;
- unrestricted browser/computer control;
- auto-trust of external tools/agents;
- generic memory misturando private/user/company state;
- graph/ontology absorvendo todos os dados/semântica;
- LLM como KPI formula authority;
- prediction como business truth;
- twin/simulation escrevendo produção diretamente;
- Edge autonomy sem central/safety boundaries;
- Marketplace install concedendo permission;
- technical AI success como business outcome;
- free-form AI→PLC/CNC/robot.

## 6. Priority ≠ implementation order

Somente `16` define dependencies e ordem C0–C7. Benchmark não antecipa fase nem cria requirement.

## 7. Benchmark rule

Disponibilidade de mercado não produz:

```text
PROVEN
PLATFORM_REUSE
NEUTRAL_SHARED_REUSE
```

Reuse/fato DELPI exige evidence real de repo/infra/owner/contract durante C0 ou fase aplicável.

## 8. Posição estratégica

DÉLIA é planejada como Continuous Operational Intelligence, não “Chat + RAG”. O valor deve vir de contexto DELPI, integração autoritativa, outcomes verificáveis, industrial/frontline capabilities governadas e safety/privacy/authority boundaries.

## 9. Regra de uso

Use este arquivo somente para benchmark/direção. Para decisões concretas, siga `16`, `50`, `17`, `49`, `51`, `52`, `21`, `20`, `25` e specs aplicáveis, sempre revalidando informação de mercado atual antes de usá-la.
