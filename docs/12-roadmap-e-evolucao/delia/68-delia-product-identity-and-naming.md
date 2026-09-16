# DÉLIA — Identidade, Nome e Convenções de Produto

**Status:** product naming authority  
**Produto:** **DÉLIA**  
**Expansão:** **DELPI · Ecossistema de Ligações, Inteligência e Automação**  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Product target:** [`24-product-specification.md`](./24-product-specification.md)

> Este arquivo é authority transversal de naming e **não** integra a sequência temática `53–66`.

## 1. Decisão de nome

O nome oficial de produto e persona é:

> **DÉLIA**

A sigla comunica diretamente o papel da solução:

```text
D  DELPI
E  Ecossistema
L  Ligações
I  Inteligência
A  Automação
```

“Ligações” representa tanto a essência da DELPI no setor de conexões elétricas quanto a função da plataforma de conectar pessoas, dados, aplicações, processos, máquinas, conhecimento e fontes externas.

## 2. Posicionamento

DÉLIA não é apenas um chatbot nem um produto denominado genericamente “Copilot”.

Definição de produto:

> **DÉLIA é a inteligência operacional da Minha DELPI: conecta pessoas, dados, aplicações, processos, máquinas e fontes externas; entende contexto, pesquisa, analisa, prevê, decide dentro de políticas, coordena execução, verifica resultados, comunica e aprende de forma governada.**

## 3. Uso do nome

### User-facing

Sempre preferir:

```text
DÉLIA
DÉLIA — Inteligência da Minha DELPI
DÉLIA — Ecossistema de Ligações, Inteligência e Automação
```

Evitar como nome principal de produto:

```text
Minha DELPI Copilot
DELPI Copilot
Copilot DELPI
```

“Copilot” pode continuar aparecendo somente quando identificar token legado (`LEGACY_TOKEN`), referência histórica ou contexto explícito de migração. Não é a marca final do produto nem namespace técnico ativo pós-aceite de C0.S1.

## 4. C0.S1 naming freeze candidate (PLANNED / FROZEN_CANDIDATE)

**Status:** `CANDIDATE_FOR_ARCHITECTURE_REVIEW` — **não** aceito; **não** autoriza C0.S2; **não** é `FOUNDATION_FREEZE`.

O namespace documental canônico permanece:

```text
docs/12-roadmap-e-evolucao/delia/
```

### 4.1 Product identity

```text
PRODUCT_NAME = DÉLIA
PRODUCT_EXPANSION = DELPI · Ecossistema de Ligações, Inteligência e Automação
TECHNICAL_SLUG = delia
DISPLAY_NAME = DÉLIA
```

“Copilot” deixa de ser namespace técnico **ativo** para novos assets da DÉLIA após aceite de C0.S1. Referências `minha-delpi-copilot*` podem permanecer somente quando explicitamente `HISTORICAL` | `LEGACY_TOKEN` | `SUPERSEDED` | `REFERENCE_ONLY`.

### 4.2 Final technical names (freeze candidate)

```text
DÉLIA API repository path     = delia-api/
DÉLIA API service name        = delia-api
DÉLIA API container name      = delpi-delia-api
DÉLIA MFE repository path     = plugins/delia/
DÉLIA MFE service name        = delia
DÉLIA MFE container name      = delpi-delia
Core app / manifest id        = delia
MFE base path                 = /apps/delia
MFE remote entry target       = /apps/delia/assets/remoteEntry.js
API Gateway base path         = /apps/delia-api/
DÉLIA logical persistence ns  = delia
DÉLIA migration root          = delia-api/migrations/
```

Classification: `PLANNED / FROZEN_CANDIDATE` until architecture acceptance. Não prova runtime.

### 4.3 Rationale (convention, not evidence)

```text
monorepo APIs        → <product>-api          (ex.: commercial-api)
MFEs                 → plugins/<product>      (ex.: plugins/commercial)
containers           → delpi-<service>        (ex.: delpi-commercial-api)
Gateway APIs         → /apps/<service>-api/
federated assets     → /apps/<app>/assets/remoteEntry.js
product identity     → DÉLIA / technical slug delia
minha-delpi-copilot* → temporary planning token (SUPERSEDED as active target)
```

Colisão revalidada em C0.S1-T1: `delia-api/` e `plugins/delia/` **ausentes** no HEAD; sem rename de sistemas não relacionados.

### 4.4 Historical residual

```text
minha-delpi-copilot/            = HISTORICAL docs-only placeholder (não runtime)
minha-delpi-copilot-api         = SUPERSEDED active target (was temporary planned)
plugins/minha-delpi-copilot     = SUPERSEDED active target (was temporary planned)
/apps/minha-delpi-copilot*      = SUPERSEDED active target
COPILOT_API_OWN_RUNTIME etc.   = LEGACY_TOKEN (gate id; semantics = DÉLIA)
```

## 5. Persona

DÉLIA deve parecer uma inteligência corporativa confiável, objetiva e contextual.

Traços desejados:

```text
clara
objetiva
proativa sem ser invasiva
orientada a evidências
consciente de risco
capaz de admitir incerteza
contextual à DELPI
consistente entre escritório/fábrica/reuniões
```

Não antropomorfizar de forma que esconda limites, automação ou responsabilidade humana.

## 6. Voz e apresentação

Na UI:

```text
DÉLIA
Inteligência da Minha DELPI
```

Exemplos:

```text
Pergunte à DÉLIA
DÉLIA está analisando os dados autorizados
DÉLIA encontrou 3 evidências relevantes
DÉLIA preparou uma ação para sua revisão
DÉLIA executou a ação e verificou o resultado
```

Evitar frases que atribuam certeza onde existe hipótese/model output.

## 7. Relação com a Minha DELPI

```text
Minha DELPI = plataforma/ecossistema corporativo
DÉLIA       = inteligência transversal do ecossistema
```

DÉLIA é uma aplicação standalone integrada ao ecossistema, não substitui Portal/Core/Keycloak/Domain APIs.

## 8. Relação com capabilities

O nome DÉLIA cobre todas as surfaces e capabilities:

```text
Global
Workspace
Meeting
Frontline
Teams surface
Internet Research
External Connectors
Business Graph
Semantic Layer
Process Intelligence
Automation Hub
AI Control Tower
Personal Memory
Analysis Sandbox
Artifact Workspace
Predictive/Prescriptive Intelligence
Operational Twin
Edge AI
MCP/A2A
AI Marketplace/Studio
```

Não criar nomes de produto independentes para cada capability sem decisão explícita de arquitetura/produto.

## 9. Identidade visual futura

A identidade visual deve derivar da Minha DELPI e da identidade corporativa DELPI, mas com assinatura própria suficiente para reconhecer DÉLIA como inteligência transversal.

Pontos para design futuro:

```text
avatar/símbolo próprio
motion states: idle / thinking / acting / waiting / alert
voice identity when speech is enabled
clear indicators for capture/automation/autonomy
consistent presence across Portal, Teams, Meeting and Frontline
```

Não definir automaticamente voz, gênero, rosto realista ou biometria como identidade da persona.

## 10. Validação comercial/legal

Antes de lançamento público, nome, domínio, marca e identidade visual devem passar por validação jurídica/comercial de disponibilidade e eventual registro de marca.

Esta documentação congela a decisão de produto interna; não constitui parecer de disponibilidade de marca.

## 11. Regra de atualização documental

Novos documentos devem usar **DÉLIA** no título e no texto user-facing.

Documentos antigos podem manter “Copilot” somente quando necessário para `LEGACY_TOKEN`/IDs históricos, referência histórica ou contexto explícito de migração.

Durante o refinamento documental, referências residuais que usem “Copilot” como nome de produto devem ser corrigidas para **DÉLIA**. Paths/contracts ativos devem usar o freeze candidate da §4 (`delia-api` / `plugins/delia` / `/apps/delia*`) até aceite arquitetural; não criar runtime nesta etapa.
