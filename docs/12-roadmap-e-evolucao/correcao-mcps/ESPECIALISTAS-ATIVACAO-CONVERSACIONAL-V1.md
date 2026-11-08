# DELPI — SPECIALIST CONVERSATION ACTIVATION V1

**Data:** 2026-11-08 · **Escopo:** ativação conversacional dos 7 especialistas MCP

## 1. Inventário — o que cada camada pode fazer (evidência)

| Camada | Pode | Não pode |
|---|---|---|
| **MCP (`get_context`)** | Entregar ficha completa (`character`: identity, personality_summary, communication, expertise, appearance_summary, conduct, relationships, coexistence) + capabilities + availability | Alterar a personalidade/memória do modelo host; criar estado entre especialistas; conceder permissões |
| **GPT Builder (Instructions)** | Regras de ativação: detectar menção → chamar `get_context` → adaptar tom/estilo com base na ficha retornada; política de separação entre especialistas | Executar código, persistir estado cross-chat, invocar outro GPT |
| **ChatGPT host** | Reter contexto da conversa (memória de sessão), invocar múltiplos conectores MCP no mesmo chat (quando configurados no GPT) | Delegar entre GPTs distintos; "chamar" um GPT dentro de outro |
| **Backend** | Ficha canônica, AuthZ, capabilities governadas | Qualquer coisa na apresentação/persona do host |

**Verdade arquitetural:** o ChatGPT não delega entre GPTs. "Chama o TÉO" só funciona quando o GPT da conversa **já está conectado ao MCP do TÉO** (ou a vários MCPs simultaneamente). A adaptação de persona é feita **pelo modelo a partir da ficha retornada** — não é troca de agente, é escopo conversacional.

## 2. Contrato de ativação (fluxo lógico)

```text
USER INTENT ("chama o TÉO")
  → SPECIALIST RESOLUTION    (nome/alias → MCP correspondente)
  → CANONICAL PROFILE DISCOVERY (get_context → character)
  → AUTHORIZED CAPABILITY DISCOVERY (catálogo/capabilities efetivas)
  → SCOPED CONVERSATIONAL ADAPTATION (modelo adota identidade/tom/regras
    da ficha — sem misturar outros especialistas)
  → SPECIALIST RESPONSE (resposta no estilo da ficha, só capabilities reais)
```

Regras: ficha = contexto narrativo/operacional, **nunca** autorização;
capabilities descobertas ≠ capacidades executáveis (backend AuthZ final);
troca de especialista = nova chamada `get_context` do MCP alvo — identidade
anterior é descartada, nunca mesclada.

## 3. Instructions compactas (GPT Builder — dentro do limite)

```text
ESPECIALISTAS DELPI — ativação: quando o usuário nomear um especialista
(TÉO, VISTA, CLARA, CAIO, SURI, EVA, DAVI), chame get_context do MCP
correspondente e adote a identidade, tom e regras do campo `character`.
Identifique-se como o especialista apenas durante a participação pedida.
Nunca invente capacidades fora do catálogo retornado; nunca afirme que
outro agente executou algo sem chamada real de tool. Ao trocar de
especialista, descarte o anterior — nunca misture identidades. Ao voltar
ao modo normal, retome o comportamento padrão do GPT.
```

## 4. Playbook (Knowledge do GPT — detalhe)

```text
ATIVAÇÃO: nome/alias → MCP:
  TÉO → transformometro (get_context section="catalog")
  VISTA → tv-dashboard (get_context action="catalog")
  CLARA → controllership-finance (get_context topic="persona")
  CAIO → commercial (get_context)
  SURI → supplies (get_context action="catalog")
  EVA → engineering (get_context)
  DAVI → api-delpi (get_context action="context")

COMPORTAMENTO: usar `character.identity` (nome/acrônimo), `communication`
(idioma/tom/verbose), `personality_summary`, `conduct` (limites de humor,
answer_first), `expertise` (especialidades). Apresentação inicial curta;
depois responda direto, sem eco narrativo repetido.

PARTICIPAÇÃO CONJUNTA ("chama TÉO e DAVI"): chame get_context de cada MCP
em sequência, responda em blocos identificados por especialista —
nunca funda as duas fichas numa persona.

SAÍDA: "volta ao normal" / outro especialista chamado → descarte a ficha
ativa; recarregue se novo especialista for pedido.

PROIBIDO: usar ficha para autorizar ação; sugerir capability `planned`/
`unavailable` como disponível; anunciar execução não realizada; expor
detalhes internos (handlers, endpoints privados, segredos).
```

## 5. Configuração manual (GPT Builder)

1. Cada especialista já tem seu próprio GPT+MCP — "chama o TÉO" funciona
   **no GPT do TÉO** sem configuração extra (ficha já chega via get_context).
2. **Modo multi-especialista (opcional):** criar um GPT "DELPI Especialistas"
   conectando os MCPs necessários + Instructions §3 + Playbook §4 como
   Knowledge. Limites reais: quantidade de conectores e orçamento de
   contexto do host — começar com 2–3 especialistas mais usados.
3. Não reimportar OpenAPI, não alterar Knowledge de dados, não criar tools.

## 6. Aceite conversacional (TEST_NOT_RUN — manual)

| Prompt | Esperado |
|---|---|
| "Chama o TÉO aqui para nos ajudar." | `get_context` TÉO chamado; resposta em persona TÉO |
| "TÉO, o que você acha desse processo?" | Contexto TÉO mantido na sessão, tom coerente |
| "Agora chama a SURI." | Nova `get_context` SURI; identidade TÉO descartada |
| "SURI, avalie os riscos em suprimentos." | Só capabilities SURI reais do catálogo |
| "Chama TÉO e DAVI para analisar." | Duas `get_context`; blocos separados por especialista |
| "Pode voltar ao ChatGPT normal." | Modo padrão retomado |

## 7. Status

| Camada | Status |
|---|---|
| Fonte canônica de ficha (7/7 `get_context` → `character`) | **PASS** (verificado runtime) |
| Contrato de ativação (definição) | **PASS** (este documento) |
| Instructions compactas | **DEFINIDO** (manual paste) |
| Playbook Knowledge | **DEFINIDO** (manual paste) |
| GPT Builder config | `TEST_NOT_RUN` — ação manual |
| Aceite conversacional | `TEST_NOT_RUN` |
