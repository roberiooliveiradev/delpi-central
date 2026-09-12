# Minha DELPI Copilot — Decision Gates e What-if Simulation

**Status:** arquitetura proposta  
**Objetivo:** tornar decisões e mudanças sensíveis proporcionais ao risco e permitir simular cenários antes de agir.

## 1. De confirmation booleana para Decision Gate

Nem toda ação deve usar a mesma confirmação.

O gate deve considerar:

```text
sensitivity
financial impact
scope/volume
reversibility
confidence/evidence quality
user role
policy
business criticality
```

## 2. Tipos conceituais

```text
NO_GATE
→ reads e ações visuais de baixo risco

ACKNOWLEDGE
→ usuário toma ciência

CONFIRM
→ confirmação simples de write

REVIEW_AND_CONFIRM
→ preview estruturado + impacto + evidências

APPROVAL_WORKFLOW
→ um ou mais aprovadores humanos

BLOCK
→ operação não permitida
```

## 3. DecisionGateV1

```json
{
  "gateId": "uuid",
  "type": "review_and_confirm",
  "subject": "Atualizar preço do item X",
  "risk": "high",
  "impactSummary": {},
  "evidenceRefs": [],
  "argumentsHash": "...",
  "expiresAt": "..."
}
```

Mudança material em argumentos, policy ou evidence invalida o gate anterior.

## 4. Approval

Para operações que exigem múltiplas pessoas:

```text
prepared
→ pending_approval
→ approved | rejected | expired
→ revalidate
→ execute
```

A aprovação não substitui autorização server-side no momento da execução.

## 5. What-if / Simulation

Antes de determinadas decisões, o Copilot pode construir uma simulação sem persistir alterações.

Exemplos:

- “E se adiarmos essa OP em três dias?”;
- “Se priorizarmos este pedido, quais outros serão afetados?”;
- “Se o fornecedor atrasar mais cinco dias, onde haverá ruptura?”;
- “Qual o impacto de aumentar o estoque de segurança?”;
- “O que muda se rejeitarmos esta proposta?”.

## 6. SimulationV1

```json
{
  "simulationId": "uuid",
  "baselineRefs": [],
  "assumptions": [],
  "inputs": {},
  "modelRef": "...",
  "outputs": {},
  "evidenceRefs": [],
  "limitations": [],
  "createdAt": "..."
}
```

Simulação deve declarar premissas; não apresentar projeção como fato.

## 7. Fontes de cálculo

Preferência:

1. API/use case de simulação do domínio;
2. regras determinísticas versionadas;
3. modelos analíticos/otimização governados;
4. LLM apenas para interpretar, estruturar cenários e explicar resultados — não para inventar números.

## 8. Simulate → Apply

Quando existir operação real correspondente:

```text
simulate
→ review
→ decision gate
→ apply via Business Action
→ verify outcome
```

Não reaproveitar resultado simulado como autorização para write.

## 9. Evidence e confiança

Toda simulação relevante precisa diferenciar:

- baseline observado;
- input fornecido pelo usuário;
- premissa assumida;
- cálculo/modelo;
- resultado projetado;
- limitações.

## 10. Casos prioritários

- produção/capacidade/priorização;
- suprimentos/estoque/fornecedor;
- financeiro/crédito/cash flow quando houver modelos aprovados;
- comercial/preço/margem quando houver regra owner;
- qualidade/risco de contenção/processo;
- manutenção/janelas e impacto produtivo.

## 11. Segurança

- simulação não deve executar write escondido;
- dados usados respeitam RBAC;
- regras financeiras/industriais críticas devem possuir owner;
- modelos/versões precisam de auditabilidade;
- premissas sensíveis não devem vazar em logs.

## 12. Testes

- baseline correto;
- premissa explícita;
- cálculo determinístico reproduzível;
- modelo indisponível;
- input fora de faixa;
- conflito de dados;
- usuário sem acesso a uma fonte;
- apply exige gate novamente;
- mudança de baseline invalida resultado stale quando material.

## 13. Gate

What-if só entra como feature de decisão quando houver modelo/cálculo governado suficiente para produzir impacto verificável. Caso contrário, o Copilot deve apresentar análise qualitativa como hipótese, não “simulação”.