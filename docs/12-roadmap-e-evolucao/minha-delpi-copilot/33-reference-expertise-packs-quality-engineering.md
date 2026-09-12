# Minha DELPI Copilot — Packs de Referência: Qualidade e Engenharia

**Status:** referência funcional para os primeiros pilotos  
**Objetivo:** mostrar como expertise, playbooks, knowledge e multimodalidade se combinam sem criar agentes independentes.

## 1. Pack `quality-industrial`

### Finalidade

Apoiar análise de:

- não conformidade;
- reclamação de cliente;
- inspeção;
- reincidência;
- plano de ação;
- causa raiz;
- contenção;
- efetividade.

### Knowledge scopes candidatos

A validar no inventário:

- procedimentos de qualidade;
- planos de controle;
- instruções de inspeção;
- normas internas;
- histórico curado de NC/PAC;
- reclamações de clientes;
- critérios de liberação.

### Playbooks preferenciais

- `quality.root-cause`;
- `quality.8d`;
- `quality.nonconformity-triage`;
- `quality.customer-complaint-analysis`.

### Capabilities úteis

Sem fixar endpoint técnico:

- knowledge search;
- quality records read;
- action plans read/write conforme RBAC;
- artifact/report generation;
- document vision;
- comparative analysis.

### Guidance

- separar contenção de causa raiz;
- distinguir ocorrência, causa e efeito;
- não declarar causa sem evidência;
- verificar recorrência/histórico;
- explicitar evidência faltante;
- sugerir ação proporcional ao risco;
- medir efetividade quando aplicável.

## 2. Pack `product-engineering`

### Finalidade

Apoiar análise de:

- desenho técnico;
- revisão de produto;
- alteração de engenharia;
- especificações;
- tolerâncias;
- material/processo;
- impacto técnico;
- comparação de versões.

### Knowledge scopes candidatos

- normas de desenho;
- padrões internos;
- documentação de produto;
- procedimentos de alteração;
- especificações de materiais/processos;
- manuais de engenharia.

### Playbooks preferenciais

- `engineering.drawing-review`;
- `engineering.change-impact-analysis`;
- `engineering.technical-comparison`.

### Multimodal

Preferir quando houver desenho/PDF/imagem:

```text
document vision
→ drawing extraction
→ engineering interpretation
```

### Guidance

- registrar revisão/documento analisado;
- não inventar dimensão/tolerância ilegível;
- apontar ambiguidades;
- diferenciar especificação de inferência;
- correlacionar alteração com impacto quando evidência existir;
- considerar necessidade de validação humana em decisão crítica.

## 3. Composição Engenharia + Qualidade

Caso:

> "Analise este desenho e veja se ele pode explicar a não conformidade dimensional do lote."

Fluxo:

```text
1. extrair evidência do desenho
2. identificar revisão e característica relevante
3. ativar product-engineering
4. ativar quality-industrial
5. aplicar engineering.drawing-review
6. consultar inspeção/NC autorizada
7. comparar especificação x resultado medido
8. listar hipóteses suportadas
9. indicar evidências faltantes
10. sugerir próximo playbook, se aplicável
```

A conclusão deve evitar causalidade não provada.

## 4. Playbook `quality.root-cause`

Etapas de referência:

```text
RC1 definir problema
RC2 delimitar escopo/ocorrência
RC3 coletar evidências
RC4 separar sintomas de causas candidatas
RC5 estruturar hipóteses
RC6 testar hipóteses contra evidência
RC7 selecionar causa(s) suportada(s)
RC8 propor ação e verificação
```

Saída:

- problem statement;
- evidence map;
- candidate causes;
- rejected hypotheses;
- supported causes;
- missing evidence;
- next actions.

## 5. Playbook `quality.8d`

Etapas:

```text
D1 equipe/responsáveis quando aplicável
D2 descrição do problema
D3 contenção
D4 causa raiz
D5 ação corretiva
D6 implementação/verificação
D7 prevenção de recorrência
D8 conclusão/reconhecimento
```

O Copilot pode preparar um 8D preliminar com campos explicitamente marcados como faltantes.

Nenhum campo deve ser inventado para "completar" o formulário.

## 6. Playbook `engineering.drawing-review`

Etapas:

```text
E1 identificar documento/revisão
E2 extrair título/notas/material
E3 identificar características críticas
E4 identificar tolerâncias/símbolos relevantes
E5 localizar ambiguidades/regiões ilegíveis
E6 correlacionar com item/processo quando autorizado
E7 verificar documentos/normas relacionadas
E8 consolidar riscos e perguntas técnicas
```

## 7. Caso composto de referência

Usuário:

> "Analise o desenho 90264238, veja os principais riscos de qualidade, consulte se já tivemos problema semelhante e monte um 8D preliminar."

Execução alvo:

```text
attachment/entity resolution
→ document/drawing vision
→ product-engineering pack
→ quality-industrial pack
→ drawing-review playbook
→ quality historical Business Actions / knowledge
→ root-cause reasoning grounded
→ 8D draft artifact
→ gaps/limitations
```

Se uma operação de negócio adicional for necessária, aplicar RBAC/policy/confirmation normalmente.

## 8. Critérios de eval do piloto

### Positive

- desenho legível + histórico disponível;
- identifica corretamente revisão/item;
- correlaciona dados sem inventar.

### Sibling

- segundo desenho/item;
- outra não conformidade;
- outra fonte de histórico.

### Negative

- documento não técnico;
- desenho ilegível;
- usuário sem acesso a histórico;
- ausência de evidência de causa;
- prompt injection dentro do PDF.

### Cross-domain

- Engenharia + Qualidade + Suprimentos na mesma conversa.

## 9. Acceptance

O piloto só é considerado válido quando provar:

```text
SINGLE_COPILOT_IDENTITY = PASS
EXPERTISE_COMPOSITION = PASS
DRAWING_EVIDENCE_PROVENANCE = PASS
NO_CAUSALITY_HALLUCINATION = PASS
UNAUTHORIZED_DATA_BLOCKED = PASS
PLAYBOOK_GROUNDED = PASS
MULTIMODAL_NEGATIVES = PASS
```
