# Playbook 05 — Feedback e melhoria contínua

> **Status (31/05/2026):** [Parcial — ver STATUS](./STATUS_ROADMAP_MELHORIAS.md).


## Objetivo

Transformar feedback dos usuários em melhoria contínua real do Minha DELPI Chat IA.

O chat já possui thumbs up/down e motivos de feedback. Este playbook propõe expandir isso para diagnóstico, métricas, correção de problemas e priorização de melhorias.

---

## Princípio central

> Feedback não é só avaliação; é dado operacional para melhorar o chat.

Cada feedback negativo deve ajudar a responder:

- O que falhou?
- Em qual agente?
- Em qual intenção?
- Qual action foi usada?
- A resposta perdeu contexto?
- Faltou fonte?
- O formato foi ruim?
- O chat chamou a rota errada?
- O problema foi conteúdo, UX ou permissão?

---

## Tipos de feedback

## Feedback positivo

Indica:

- resposta útil;
- formato bom;
- action correta;
- contexto mantido;
- texto bem escrito;
- fonte correta;
- próximo passo útil.

## Feedback negativo

Deve ser categorizado.

Motivos atuais:

- Dado incorreto.
- Não respondeu.
- Faltou fonte.
- Formato ruim.
- Muito longo.
- Muito curto.
- Consulta errada.

## Motivos adicionais recomendados

- Perdeu contexto.
- Usou produto errado.
- Não seguiu instrução.
- Chamou API sem necessidade.
- Não chamou API quando deveria.
- Texto ficou ruim.
- Tradução ruim.
- Mudou o sentido.
- Botões não ajudaram.
- Resultado incompleto.
- Erro de permissão confuso.
- Resposta inventou informação.

---

## Fluxo ideal de feedback negativo

1. Usuário clica thumbs down.
2. UI mostra motivos.
3. Usuário escolhe motivo.
4. Sistema agradece.
5. Se possível, oferece ação corretiva.

### Exemplo

Usuário marca:

> Perdeu contexto.

Resposta:

> Obrigado pelo aviso. Quer que eu refaça usando a última consulta como contexto?

Botões:

- Refazer com contexto anterior.
- Escolher produto.
- Limpar contexto.
- Reportar problema.

---

## Modelo de dados recomendado

```json
{
  "messageId": "uuid",
  "sessionId": "uuid",
  "agentKey": "agente-produtos",
  "rating": -1,
  "reason": "lost_context",
  "intent": "supplier_lookup",
  "actionPath": "/products/{code}/suppliers",
  "usedMemory": true,
  "usedRag": false,
  "usedTool": true,
  "presentationType": "table",
  "createdAt": "datetime"
}
```

---

## Feedback por contexto

## Operacional

Motivos importantes:

- dado incorreto;
- consulta errada;
- faltou parâmetro;
- não respeitou período;
- usou produto errado;
- resultado incompleto.

## Textual

Motivos importantes:

- texto não ficou claro;
- tom inadequado;
- mudou sentido;
- tradução ruim;
- muito longo;
- muito formal/informal.

## RAG

Motivos importantes:

- fonte errada;
- faltou fonte;
- documento desatualizado;
- resposta sem base;
- não encontrou documento.

## UX

Motivos importantes:

- botões ruins;
- tela poluída;
- tabela ruim;
- gráfico confuso;
- próxima ação ausente.

---

## Ações corretivas por motivo

| Motivo | Ação sugerida |
|---|---|
| Perdeu contexto | Reexecutar com contexto anterior |
| Consulta errada | Mostrar opções de consulta |
| Faltou fonte | Reconsultar com RAG/fonte |
| Formato ruim | Oferecer tabela/gráfico/resumo |
| Muito longo | Criar versão curta |
| Muito curto | Detalhar |
| Texto ruim | Reescrever com tom escolhido |
| Tradução ruim | Revisar tradução |
| Dado incorreto | Reexecutar e abrir diagnóstico |
| Não respondeu | Reformular pergunta guiada |

---

## Dashboard de melhoria

Criar painel com:

- total de feedbacks;
- taxa positiva/negativa;
- motivos mais comuns;
- agentes com maior erro;
- actions com maior erro;
- perguntas mais problemáticas;
- taxa de perda de contexto;
- taxa de consulta errada;
- score de qualidade textual;
- score de RAG.

---

## Métricas principais

| Métrica | Objetivo |
|---|---|
| CSAT por resposta | Qualidade geral |
| Feedback negativo por agente | Detectar agente ruim |
| Consulta errada | Melhorar roteamento |
| Perdeu contexto | Melhorar memória |
| Faltou fonte | Melhorar RAG |
| Formato ruim | Melhorar presenter |
| Texto ruim | Melhorar skill textual |
| Botões não ajudaram | Melhorar interatividade |

---

## Ciclo de melhoria

### Diário

- revisar erros críticos;
- verificar actions com falhas;
- olhar feedback “dado incorreto”.

### Semanal

- agrupar motivos;
- priorizar correções;
- ajustar prompts/policies;
- ajustar suggestions;
- adicionar testes.

### Mensal

- revisar agentes;
- revisar knowledge;
- revisar métricas;
- planejar melhorias.

---

## Uso em testes

Cada bug reportado por feedback deve virar um teste.

Exemplo:

Feedback:

> Perdeu contexto após estoque.

Criar teste:

```text
1. estoque do produto 10080001
2. agora fornecedores
Esperado: usar produto 10080001
```

---

## Admin debug

Adicionar no painel:

- intent detectada;
- action escolhida;
- parâmetros usados;
- memória usada;
- RAG usado;
- sources;
- tempo de cada etapa;
- suggestions geradas;
- feedback recebido.

---

## Feedback positivo também importa

Se um chip tem muito uso e feedback positivo, ele deve virar padrão.

Se um agente tem alto feedback positivo, seu prompt pode servir de modelo.

Se uma resposta textual tem alto feedback positivo, usar como exemplo few-shot.

---

## Resposta ao usuário

Após feedback positivo:

> Obrigado! Isso ajuda a melhorar o chat.

Após feedback negativo:

> Obrigado pelo aviso. Vou registrar esse ponto para melhoria.

Se houver ação corretiva:

> Quer que eu tente corrigir agora?

---

## Resumo executivo

O feedback deve fechar o ciclo de melhoria do chat. Cada thumbs down precisa indicar o tipo de falha, alimentar métricas, gerar testes e orientar correções. O objetivo é transformar uso real em evolução contínua.
