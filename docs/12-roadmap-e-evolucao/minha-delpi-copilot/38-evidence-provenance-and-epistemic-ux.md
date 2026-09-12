# Minha DELPI Copilot — Evidence, Provenance e Epistemic UX

**Status:** arquitetura proposta  
**Objetivo:** tornar análises, conclusões e recomendações auditáveis e distinguíveis entre fato, cálculo, hipótese e decisão.

## 1. Regra central

Toda conclusão material deve, quando possível, apontar para evidência verificável.

```text
claim
→ evidence refs
→ source/provenance
→ freshness
→ confidence
→ limitations
```

## 2. Tipos epistemológicos

O Copilot deve distinguir explicitamente:

```text
FACT
→ observado diretamente em fonte autorizada

CALCULATION
→ derivado matematicamente de fatos

HYPOTHESIS
→ explicação possível ainda não confirmada

CONCLUSION
→ inferência sustentada por evidência suficiente

RECOMMENDATION
→ ação sugerida a partir de fatos/conclusões/policy
```

Nunca apresentar `HYPOTHESIS` como `FACT`.

## 3. EvidenceRefV1

Contrato conceitual:

```json
{
  "evidenceId": "uuid",
  "kind": "api_fact",
  "sourceSystem": "purchase-api",
  "sourceRef": "purchase-order:450231",
  "entityRefs": [],
  "observedAt": "ISO-8601",
  "freshness": "current",
  "valueSummary": "Pedido atrasado 12 dias",
  "confidence": "authoritative"
}
```

Para documentos/desenhos:

```text
fileRef
page/sheet/region
extraction method
model/parser version quando relevante
confidence
```

## 4. ClaimV1

```json
{
  "claimId": "uuid",
  "type": "hypothesis",
  "statement": "A troca de lote pode estar associada ao aumento de refugo",
  "evidenceRefs": ["e1", "e2"],
  "confidence": 0.68,
  "limitations": ["Ainda não foi comparado o certificado do lote anterior"]
}
```

Scores numéricos só devem ser exibidos quando houver método claro; não criar falsa precisão.

## 5. UX alvo

Exemplo:

```text
Causa provável
Atraso de fornecimento

Evidências
- pedido 450231: 12 dias de atraso
- estoque atual: 0
- OP 123445: bloqueada por falta

Classificação: CONCLUSÃO
Confiança: alta
Dados consultados: 12/09/2026 15:37
Limitação: fornecedor ainda não confirmou nova data
```

O usuário deve conseguir abrir a entidade/documento fonte quando tiver permissão.

## 6. Provenance transversal

Preservar provenance durante:

```text
API result
→ normalized result
→ analysis
→ workflow
→ artifact
→ case
→ recommendation
```

Artefato gerado deve conseguir referenciar evidence usada, sem copiar secret/PII indevido.

## 7. Freshness

Definir semântica de frescor por fonte:

- `live/current` — consultado no turno;
- `snapshot` — snapshot com timestamp;
- `cached` — cache válido segundo policy;
- `stale` — pode ser usado apenas com aviso/limitação;
- `unknown` — não afirmar atualidade.

## 8. Evidence em análise multimodal

Para desenho/imagem:

- região visual;
- página/sheet;
- texto extraído;
- finding;
- método/modelo;
- confidence;
- revisão do documento.

Um finding visual importante sem localização/provenance é incompleto.

## 9. Evidence em Cases

Cases devem manter um `Evidence Board` estruturado:

```text
accepted
contested
missing
superseded
```

Nova revisão de desenho pode superseder evidência anterior sem apagar histórico.

## 10. Observabilidade

Registrar IDs e metadados, não chain-of-thought.

Devemos conseguir responder:

- quais fontes suportaram a conclusão?;
- quando foram consultadas?;
- algum dado estava stale?;
- houve hipótese sem validação?;
- qual ação foi tomada a partir dela?.

## 11. Testes

Obrigatórios:

- fato correto com sourceRef;
- cálculo rastreável aos inputs;
- hipótese rotulada;
- source indisponível;
- dado stale;
- conflito entre fontes;
- evidence revogada por RBAC;
- documento substituído por revisão nova;
- artifact preserva referências permitidas;
- resposta não inventa evidenceId/sourceRef inexistente.

## 12. Gate

Nenhuma feature de análise avançada deve ser considerada madura se não consegue separar fato/hipótese e preservar provenance das evidências materiais.