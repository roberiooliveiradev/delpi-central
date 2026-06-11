# Playbook — Especialista em Correção de Texto no Minha DELPI Chat IA

**Projeto:** Minha DELPI Chat IA  
**Habilidade nativa:** correção, revisão e melhoria textual no chat comum  
**Status implementação:** Fases **1–6** (snapshot) + lousa bidirecional + regressão — maio/2026  
**Código:** `ChatTextCorrectionIntentService`, `ChatTextCorrectionCanvasService`, `ChatTextCorrectionPreferenceService`, `ChatTextCorrectionQualityValidator`, `ChatTextCorrectionMetricsService`, `ChatTextCorrectionTurnService`, policy `text-correction.md`, `run_text_correction_validation.sh`, `run_chat_text_correction_homologation.sh`

**Objetivo:** fazer o chat corrigir textos com qualidade profissional, preservando sentido, tom, intenção e contexto do usuário.

**Regra central:** correção boa = texto correto + sentido preservado + tom adequado + zero invenção.

**Arquitetura:** [`docs/architecture/chat-intelligence-base.md`](../../architecture/chat-intelligence-base.md) — inteligência no chat base; ver também [`playbook_assistente_administrativo_textos_minha_delpi_chat.md`](./playbook_assistente_administrativo_textos_minha_delpi_chat.md) (modo administrativo/textual) e [**Playbook 14** — typos no composer](../playbook-14-corretor-digitacao-chat.md) (distinto desta habilidade LLM).

### Distinção — correção de texto vs typos no composer

| Necessidade | Playbook |
|-------------|----------|
| «Corrija / revise / melhore este parágrafo» | **Este documento** — `text_correct_*` via LLM |
| Erro ao digitar «estouque do produto…» | [**Playbook 14**](../playbook-14-corretor-digitacao-chat.md) — chip pré-envio determinístico |

---

## 1. Objetivo

A correção de texto deve ser uma **habilidade nativa do chat comum**, sem depender de agente específico, API operacional, RAG ou consulta externa.

O usuário deve poder pedir:

- Corrija este texto.
- Revise a ortografia.
- Melhore a pontuação.
- Deixe mais claro.
- Corrija sem mudar meu estilo.
- Corrija e mostre o que mudou.
- Reescreva de forma mais profissional.
- Deixe mais simples.
- Deixe mais formal.
- Verifique se esse texto está bom.

E o chat deve responder com uma versão corrigida, natural e pronta para uso.

---

## 2. Regra principal

Se o usuário pedir correção de texto, o chat deve **corrigir o texto**, não consultar ERP, não acionar action e não mudar o sentido original.

**Exemplo**

| Usuário | Resposta esperada | Não fazer |
|---------|-------------------|-----------|
| Corrija: o estoque esta baixo | O estoque está baixo. | Consultar estoque |

---

## 3. Quando ativar a habilidade

Ativar quando a mensagem contiver intenções como:

- corrigir; revisar; ajustar; melhorar; reescrever; pontuar;
- verificar português; arrumar gramática;
- deixar claro; deixar formal; deixar simples;
- revisar texto; revisar e-mail; corrigir comunicado;
- melhorar mensagem; transformar em texto profissional.

**Exemplos de pedido**

- Corrija esse texto mantendo o sentido.
- Revise a gramática deste comunicado.
- Deixe esse parágrafo mais profissional.
- Corrija apenas os erros.
- Melhore a clareza, mas mantenha meu estilo.
- Mostre uma versão corrigida e explique as alterações.

**Detecção (hoje):** `ChatTextTaskIntentService.classify` → categoria `correct`; `is_pure_text_task` → estágio `text_task` sem tools (ver `ChatIntentRouterService`).

---

## 4. Tipos de correção

Evoluir **`ChatTextTaskIntentService`** ou extrair **`ChatTextCorrectionIntentService`** para classificar subtarefas de correção (`textTask.type = "correction"`).

| Subintenção | Descrição | Status |
|-------------|-----------|--------|
| `text_correct_basic` | Ortografia, acentos, concordância e pontuação | **Concluída** |
| `text_correct_preserve_style` | Corrigir mantendo estilo original | **Concluída** |
| `text_correct_formal` | Corrigir e deixar mais formal | **Concluída** |
| `text_correct_clear` | Corrigir e melhorar clareza | **Concluída** |
| `text_correct_simple` | Corrigir e simplificar linguagem | **Concluída** |
| `text_correct_professional` | Corrigir com tom corporativo | **Concluída** |
| `text_correct_explain` | Corrigir e explicar alterações | **Concluída** |
| `text_correct_compare` | Mostrar antes/depois | **Concluída** |
| `text_rewrite` | Reescrever mantendo sentido | **Concluída** |
| `text_review_quality` | Avaliar se o texto está adequado | **Concluída** |

---

## 5. Pipeline recomendado

```
Mensagem do usuário
  → ChatTextTaskIntentService (tarefa textual / correction)
  → ChatTextCorrectionIntentService (subtipo)
  → extrair texto a corrigir (pedido, lousa ou anexo)
  → ChatTextCorrectionPromptSupplementService + policies
  → LLM (estágios text_task + text_correction, sem tools)
  → ChatTextCorrectionAnswerGuardService + QualityValidator
  → metadata textTask + chips; lousa: canvasOpen atualizado quando há conteúdo
```

**Não usar em correção textual pura:** action, RAG, SQL, API operacional, consulta externa.

**Turno misto:** se o usuário pedir consulta operacional **e** correção na mesma frase, `is_mixed_text_and_operational` — tools primeiro, texto depois (`ChatTextTaskComposerService`).

---

## 6. Modos de resposta

### 6.1 Correção simples

**Pedido:** Corrija este texto:

**Resposta ideal:**

```text
Segue a versão corrigida:

[texto corrigido]
```

Sem explicação longa (já previsto em `administrative-writing.md`).

### 6.2 Correção preservando estilo

**Pedido:** Corrija sem mudar meu estilo.

Corrigir somente: ortografia, acentuação, concordância, pontuação, fluidez mínima. Não transformar texto simples em texto excessivamente formal.

### 6.3 Correção com explicação

**Pedido:** Corrija e explique o que mudou.

```markdown
## Versão corrigida

[texto corrigido]

## Principais ajustes

- Corrigi acentuação em...
- Ajustei concordância em...
- Melhorei a pontuação em...
```

### 6.4 Antes e depois

```markdown
## Antes

[texto original]

## Depois

[texto corrigido]

## O que mudou

- ...
```

### 6.5 Correção profissional

**Pedido:** Corrija e deixe mais profissional.

- Remover informalidades;
- Melhorar clareza;
- Tom respeitoso, sem exagero de formalidade;
- Preservar intenção.

---

## 7. Política de preservação de sentido

**Corrigir não é inventar, ampliar ou alterar a intenção do usuário.**

| Pode | Não pode |
|------|----------|
| Corrigir erros; melhorar pontuação; ajustar concordância | Inventar fatos; adicionar promessas; criar prazos |
| Melhorar fluidez; reduzir ambiguidade | Mudar destinatário; alterar números/códigos |
| Trocar expressões inadequadas | Modificar nomes próprios sem pedido |
| Organizar frases | Transformar reclamação em aprovação |
| | Suavizar cobrança firme sem pedido; tornar agressivo sem pedido |

---

## 8. Regras para nomes, códigos e termos técnicos

Preservar exatamente:

- nomes de pessoas e empresas;
- códigos de produto, cliente e DELPI;
- siglas, medidas, datas, valores;
- números de pedido; nomes de arquivos; termos técnicos.

**Exemplo**

| Usuário | Resposta |
|---------|----------|
| Corrija: o produto 10080001 esta com divergencia na BOM | O produto 10080001 está com divergência na BOM. |

Não trocar `10080001` nem substituir `BOM` por outro termo.

---

## 9. Template interno de resposta

### Correção padrão

```text
Segue a versão corrigida:

[texto corrigido]
```

### Correção com tom profissional

```text
Segue uma versão corrigida e mais profissional:

[texto corrigido]
```

### Correção com explicação

Ver §6.3.

### Texto com ambiguidade

```text
Segue uma versão corrigida:

[texto corrigido]

Observação: mantive o sentido original, mas o trecho “[trecho]” pode ser interpretado de mais de uma forma.
```

---

## 10. Validador de qualidade

**Serviço alvo:** `ChatTextCorrectionQualityValidator`

Validar a resposta antes de entregar (ou no guard pós-LLM).

| Check | Descrição |
|-------|-----------|
| Texto corrigido | Há versão utilizável na resposta |
| Sentido preservado | Sem inversão de intenção |
| Sem informação nova | Sem fatos/prazos inventados |
| Códigos e nomes | Preservados (regex/heurística) |
| Tom respeitado | Alinhado ao subtipo |
| Explicação proporcional | Não explicar demais em modo simples |
| Pontuação natural | pt-BR |
| Pronto para copiar | Formato limpo |

---

## 11. Exemplos práticos

### Exemplo 1 — Correção simples

**Usuário:** Corrija: segue em anexo os documento solicitado  

**Resposta:** Seguem em anexo os documentos solicitados.

### Exemplo 2 — Concordância

**Usuário:** Corrija: os item foi enviado ontem  

**Resposta:** Os itens foram enviados ontem.

### Exemplo 3 — Texto profissional

**Usuário:** Melhore: preciso que você mande isso logo porque estamos atrasados  

**Resposta:** Poderia, por gentileza, nos enviar essa informação o quanto antes? Precisamos dela para evitar impacto no andamento do processo.

### Exemplo 4 — Preservar estilo

**Usuário:** Corrija sem mudar muito: Robério, segue os arquivo que você pediu  

**Resposta:** Robério, seguem os arquivos que você pediu.

### Exemplo 5 — Correção com explicação

**Usuário:** Corrija e explique: nos vai enviar o pedido amanhã  

**Resposta:**

## Versão corrigida

Nós vamos enviar o pedido amanhã.

## Ajustes realizados

- Corrigi “nos” para “nós”.
- Mantive o sentido original da frase.

---

## 12. Interatividade após correção

Após corrigir, exibir chips (alvo: `personality_playbook.json` → `textCorrectionFollowUpChips`):

- Deixar mais formal
- Deixar mais curto
- Deixar mais claro
- Mostrar alterações
- Transformar em e-mail
- Transformar em comunicado
- Traduzir para inglês
- Colocar na lousa
- Copiar texto

**MFE:** atalho «Escrever ou corrigir texto» com `{{textContent}}` (`onboarding.json`); botão copiar e chips quando `textTask.type === correction` (`ChatMessageList.tsx`).

---

## 13. Integração com lousa/canvas

Comandos suportados:

- Corrija o texto da lousa.
- Reescreva a lousa de forma mais profissional.
- Deixe o texto da lousa mais claro.
- Mostre uma versão curta da lousa.
- Traduza o texto da lousa.
- Transforme a lousa em comunicado.

**Fluxo:** texto → lousa → correção → atualização da lousa → refinamentos (histórico no canvas).

**Implementado:** `ChatTextCorrectionCanvasService` lê `canvasOpen` do histórico (`ChatCanvasContentService.find_active_canvas`), injeta no prompt e, após o LLM, emite novo `canvasOpen` com a versão corrigida (`textCorrectionCanvasUpdate` / `canvasUpdated` nas métricas).

Reutilizar `ChatCanvasIntentService` / `ChatCanvasContentService` sem duplicar lógica de correção no agente.

---

## 14. Integração com anexos

Quando o usuário anexar documentos:

- corrigir texto do documento;
- revisar gramática; resumir; reescrever;
- extrair pendências;
- transformar em e-mail ou comunicado;
- traduzir.

**Documento extenso:**

> O documento é extenso. Posso começar corrigindo por seção ou gerar uma versão revisada dos principais trechos.

Instrução anexo: `ChatTextTaskComposerService.attachment_text_task_instruction`.

---

## 15. Memória de preferência textual

Lembrar na sessão (alvo: `ChatTextCorrectionPreferenceService` + `ai_chat_session_memory`):

- Sempre corrija sem explicar.
- Sempre mostre antes e depois.
- Sempre deixe mais formal.
- Sempre mantenha meu estilo.
- Sempre entregue só a versão final.

**Exemplo**

**Usuário:** Daqui para frente, quando eu pedir correção, entregue só a versão final.

**Chat:** Combinado. Nesta conversa, quando você pedir correção, vou entregar apenas a versão final corrigida.

(Padrão análogo a `ChatEmailPreferenceService` / `emailWriting`.)

---

## 16. Regras de tom

| Tom pedido | Comportamento |
|------------|---------------|
| Simples | Frases curtas e diretas |
| Formal | Linguagem corporativa e respeitosa |
| Profissional | Claro, polido e objetivo |
| Executivo | Direto, estratégico, sem excesso |
| Cordial | Educado e leve |
| Firme | Claro e assertivo, sem agressividade |
| Técnico | Preserva termos técnicos e precisão |

---

## 17. O que evitar

1. Corrigir e mudar o sentido.
2. Inventar contexto.
3. Adicionar promessas.
4. Alterar números ou códigos.
5. Substituir nomes próprios.
6. Explicar demais quando o usuário pediu «só corrija».
7. Formalidade excessiva sem pedido.
8. Suavizar cobrança firme sem solicitação.
9. Responder com análise em vez de versão corrigida.
10. Acionar API operacional em correção textual pura.

---

## 18. Prompt interno sugerido

Policy alvo: `app/domain/prompt_policies/text-correction.md` (especialização de `administrative-writing.md`).

```text
Você é um especialista em correção e revisão de textos em português brasileiro.

Sua função é corrigir ortografia, gramática, pontuação, concordância, clareza e fluidez,
preservando o sentido original do usuário.

Regras obrigatórias:
1. Se o usuário pedir apenas correção, entregue a versão corrigida sem explicações longas.
2. Preserve nomes próprios, códigos, datas, valores, medidas, siglas e termos técnicos.
3. Não invente fatos, prazos, compromissos, cargos ou informações.
4. Não altere o sentido original do texto.
5. Adapte o tom apenas quando o usuário pedir.
6. Se o usuário pedir explicação, liste os principais ajustes.
7. Se houver ambiguidade, corrija o possível e indique a dúvida.
8. Use português brasileiro natural e profissional.
9. Não acione API, RAG ou ferramentas operacionais em correções textuais puras.
10. Após corrigir, ofereça opções de refinamento quando a interface permitir.
```

Registrar em `PromptPolicyService` quando o subtipo `correction` estiver ativo.

---

## 19. Metadata recomendada

```json
{
  "textTask": {
    "type": "correction",
    "subtype": "text_correct_basic",
    "source": "user_message",
    "preserveMeaning": true,
    "preserveStyle": false,
    "tone": "professional",
    "changedMeaningRisk": false,
    "containsTechnicalTerms": true,
    "suggestions": [
      "Deixar mais formal",
      "Mostrar alterações",
      "Transformar em e-mail"
    ]
  },
  "textCorrectionFollowUpSuggestions": [
    { "label": "Deixar mais formal", "query": "deixe o texto anterior mais formal" }
  ],
  "textCorrectionQuality": { "passed": true, "checks": [] }
}
```

---

## 20. Feedback específico

Motivos em `personality_playbook.json` (alvo):

| Código | Descrição |
|--------|-----------|
| `text_correction_changed_meaning` | Mudou o sentido |
| `text_correction_over_corrected` | Corrigiu demais |
| `text_correction_under_corrected` | Corrigiu de menos |
| `text_correction_style_lost` | Não preservou meu estilo |
| `text_correction_artificial` | Texto ficou artificial |
| `text_correction_too_formal` | Formal demais |
| `text_correction_too_informal` | Informal demais |
| `text_correction_missed_error` | Não corrigiu erro importante |
| `text_correction_altered_code` | Alterou código ou nome |
| `text_correction_over_explained` | Explicou demais |
| `text_correction_under_explained` | Faltou explicar alterações |

---

## 21. Testes de regressão

| Artefato | Conteúdo |
|----------|----------|
| `tests/unit/test_text_correction_skill.py` | Casos C1–C12 |
| `tests/fixtures/chat_intelligence_regression_cases.py` | `TEXT_CORRECTION_*_CASES` |
| `tests/unit/domain/services/test_chat_text_correction_intelligence_regression.py` | Regressão parametrizada |
| `scripts/smoke_text_task_routing.py` | Roteamento `correct` sem tools |
| `scripts/run_text_correction_validation.sh` | Suite unit + smoke |

### Casos mínimos

| Caso | Entrada | Esperado |
|------|---------|----------|
| C1 | Corrigir ortografia | Corrige acentos e grafia |
| C2 | Concordância | Ajusta singular/plural |
| C3 | Pontuação | Melhora vírgulas e pontos |
| C4 | Preservar código | Não altera códigos |
| C5 | Preservar nome | Não altera nomes próprios |
| C6 | Só corrigir | Não explica demais |
| C7 | Explicar alterações | Mostra ajustes principais |
| C8 | Antes/depois | Mostra comparação |
| C9 | Deixar formal | Ajusta tom corporativo |
| C10 | Manter estilo | Corrige sem reescrever demais |
| C11 | Texto técnico | Preserva siglas e unidades |
| C12 | Não chamar API | Nenhuma action operacional |

---

## 22. Roadmap de implementação

| Fase | Escopo | Status |
|------|--------|--------|
| **1 — Correção básica nativa** | Detectar intenção `correct`; não acionar tools; policies `administrative-writing.md` + `text-correction.md`; preservar códigos/nomes | **Concluída** |
| **2 — Modos de correção** | Subtipos (`text_correct_*`, `text_rewrite`, `text_review_quality`) | **Concluída** |
| **3 — Validador** | `ChatTextCorrectionQualityValidator` + guard pós-LLM | **Concluída** |
| **4 — Interatividade** | Chips `textCorrectionFollowUpSuggestions`; botão copiar no MFE | **Concluída** |
| **5 — Memória** | `ChatTextCorrectionPreferenceService`, `textCorrection` em `behaviorInstructions`, chips de contexto | **Concluída** |
| **6 — Métricas** | `textCorrectionMetrics` + `adminDebug` + `canvasUpdated` por turno | **Concluída** (agregado §23 backlog) |
| **Lousa bidirecional** | Leitura + `canvasOpen` após correção da lousa | **Concluída** |
| **Lousa/anexo (fonte)** | `source`: canvas / attachment no contexto e prompt | **Concluída** |

**Ordem sugerida:** Fase 2 (subtipos + policy dedicada) → Fase 3 → Fase 4 → Fase 5.

---

## 23. Métricas

**Por turno (implementado):** `textCorrectionMetrics` (subtipo, fonte, qualidade, `canvasUpdated`, chips).

**Agregado (backlog produto/admin):**

- quantidade de correções solicitadas;
- taxa de feedback positivo;
- feedback «mudou sentido» / «texto artificial»;
- uso de chips pós-correção;
- uso de lousa após correção;
- correções de anexos;
- tempo médio de resposta;
- taxa de reescrita solicitada;
- taxa de «só versão final».

---

## 24. Resultado esperado

Depois da implementação completa, o chat deve ser excelente em:

- corrigir português; melhorar pontuação; revisar gramática;
- ajustar concordância; preservar sentido; manter estilo quando pedido;
- explicar alterações quando solicitado; reescrever com tom profissional;
- corrigir textos da lousa e documentos anexados;
- não inventar dados; não acionar rotas operacionais indevidas.

---

## 25. Resumo executivo

A correção de texto deve ser uma **habilidade nativa e transversal** do Minha DELPI Chat IA.

O chat age como revisor profissional: corrige, melhora e organiza, mas **preserva o sentido original**.

Implementar na **camada base** (`ChatIntelligencePipelineService`, `ChatToolContextService`) — agentes e projetos **herdam** a habilidade; não duplicar lógica só no prompt de um agente.

---

## Referências

- [`playbook_escrita_emails_minha_delpi_chat.md`](./playbook_escrita_emails_minha_delpi_chat.md) — e-mails (subconjunto de tarefas textuais)
- [`playbook_assistente_administrativo_textos_minha_delpi_chat.md`](./playbook_assistente_administrativo_textos_minha_delpi_chat.md) — visão administrativa ampla
- [`../../architecture/chat-intelligence-base.md`](../../architecture/chat-intelligence-base.md)
