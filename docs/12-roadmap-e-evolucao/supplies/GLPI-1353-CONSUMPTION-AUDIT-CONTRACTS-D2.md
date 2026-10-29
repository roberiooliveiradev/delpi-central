# GLPI #1353 — D2.2 Contratos propostos da Auditoria de Consumo

> **Estado:** DRAFT / PROPOSED / NOT FROZEN — 2026-10-29.
> **Proibido interpretar este documento como OpenAPI publicado, rota implementada ou autorização de deploy.**
> **Dependências:** [D2.1 regras](./GLPI-1353-CONSUMPTION-AUDIT-BUSINESS-RULES-D2.md), [fluxo D1](./GLPI-1353-PRODUCTION-CONSUMPTION-AUDIT-FLOW-20261029.md), [ADR-009](./adr/ADR-009-product-access-and-operational-data-scope.md), [MATRIZ-BOUNDARIES](./MATRIZ-BOUNDARIES.md).

## 1. Boundaries e decisão recomendada (a ratificar)

`plugins/supplies` (MFE React) → `supplies-api` (BFF Flask, AuthZ Core-first) → `api-delpi` (read/cálculo Protheus). **Não** BFF/MFE direto ao banco Protheus, import de outro bounded context ou cópia dos estados SC2/SG1/SD4/SD3 no PG `supplies`.

A `api-delpi` detém SQL, classificação SD3, semântica do SD4, BOM histórica, vínculo de OP e resultados aritméticos. A `supplies-api` valida effective permissions, filial e recurso, compõe respostas e poderá futuramente armazenar investigação humana no próprio PG. MFE não autoriza nem calcula regra.

**Decisão proposta:** contratos dedicados `/supplies/consumption-audit/*` na api-delpi com proteção trusted-S2S existente do domínio `/supplies/*`, em vez de abrir indiscriminadamente `/production/*` e `/products/*` aos usuários do Portal. Requer revisão de implementação e segurança antes de freeze. **Não há endpoint criado.**

## 2. Contratos candidatos

| ID | Producer / path PROPOSED | Consumer | Conteúdo e garantia |
|---|---|---|---|
| C1 | `api-delpi GET /supplies/consumption-audit/orders` | supplies-api | lista paginada, período, filial explícita, estado e contagem de linhas avaliadas |
| C2 | `api-delpi GET /supplies/consumption-audit/orders/{op}` | supplies-api | detalhe com OP, operações, componentes, BOM histórica, SD4, SD3 classificada, evidências e limites |
| C3 | `api-delpi GET /supplies/consumption-audit/components` | supplies-api | consulta inversa por componente, com OP/operação de origem e paginação |
| C4 | `supplies-api GET /consumption-audit/*` | MFE | projeção de C1–C3, escopo Core, loading/partial/fail-closed |
| C5 | `supplies-api POST/PATCH /consumption-audit/investigations` | MFE futuro | investigação, responsável, justificativa, decisão e trilha; **fora do MVP** |

**E12 preservada:** `/supplies/safety-stock/consumption-analysis/*` é produto×período, não OP×operação. Não substituí-la nem declarar implementação BFF/MFE já existente.

## 3. Semântica de entrada candidata

- `branch`: obrigatório e validado em `01|02`; escopo “Todas” somente como composição explicitamente autorizada de 01+02, **não** filial universal.
- `op`: chave de 11 posições, preservar zeros à esquerda; validar pertencimento/visibilidade à filial.
- `period_start`, `period_end`: formato de data explícito e limite a homologar; **qual data da OP** filtra o conjunto (emissão, apontamento, baixa, encerramento) ainda depende de D2.
- `page`, `page_size`: paginação bounded, proposta de máximo 200, sujeita a teste de performance.
- `component`, `operation`, `classification`: filtros opcionais com esquema e semântica pendentes.
- `structure_as_of`: proposta `op|today`; **default `op` apenas após fechar a referência temporal**. Não publicar `today` como verdade histórica.

## 4. Esquema conceitual de resposta C2 (não é OpenAPI)

```json
{
  "branch": "01",
  "production_order": "24884201006",
  "order": {
    "product_code": "50226108",
    "planned_qty": 0.125,
    "produced_qty_sc2": 0,
    "pointed_qty_sh6": 0.125,
    "unit": "MI",
    "closed": false,
    "production_status_conflict": true
  },
  "operations": [
    {
      "operation": "01",
      "work_center": "CT-23",
      "execution_state": "unknown",
      "components": [
        {
          "component_code": "10010030",
          "unit": "MT",
          "bom_reference_date": "2026-10-20",
          "theoretical_qty_preliminary": 80.75,
          "sd4_original_qty": 80.75,
          "sd4_open_qty": 0,
          "sd4_derived_consumed_qty": 80.75,
          "sd3_eligible_consumption_qty": 80.75,
          "classification": "reconciled",
          "confidence": "partial",
          "movement_evidence": [
            {"document": "220039841", "kind": "production_consumption", "quantity": 80.75},
            {"document": "220039839", "kind": "warehouse_transfer", "quantity": 0.64}
          ]
        }
      ]
    }
  ],
  "completeness": "partial",
  "unresolved": ["operation_execution_event", "automatic_issue_causality", "sc2_sh6_discrepancy"]
}
```

**Este JSON é um exemplo ilustrativo derivado do snapshot da OP, não resposta real de endpoint.** Os nomes/campos finais, precisão/decimal, timezone, identidade estável de ocorrências, reanálise e versionamento precisam freeze. Em produção a saída não pode apresentar `reconciled` como homologação se execução/status ou fontes exigidas forem incompletos; classificar com ressalva ou `unclassified`.

## 5. Condições de segurança e contrato

- RBAC: **apenas** `supplies.access` para leitura; `supplies.manage` para administração, sem implicar access. Core API é authority de effective permissions; JWT apenas identidade. Backend = capability AND unit/data scope AND resource scope/ownership AND business rule; fail-closed.
- Filiais 01/02 são filtros operacionais (ADR-009), **não** grants novos ou permissões por endpoint.
- Trusted-caller é autenticação S2S verificada no backend, nunca header simples autoatribuído; não ampliar indiscriminadamente para `/production/*`.
- Erros e cenários a contratualizar: 400/422 parâmetros; 401 identidade; 403 capacidade/escopo; 404 OP invisível/inexistente segundo política; 502/504 downstream; 503 Core/AuthZ indisponível. Não vazar informação entre filiais.
- Resposta precisa distinguir `complete|partial|inconclusive`, warnings e proveniência; resultados não suportados devem ser `null/unknown`, não zero.
- Não expor custo/fornecedor nem tokens ou informações de outras áreas; logs sem secrets.

## 6. Regras de cálculo que ainda NÃO são contrato congelado

- Teórico: `structure_qty_at_reference_date × reference_production_qty`; validar base de quantidade e conversões.
- Derivado SD4: `original_qty - open_qty`; pode **não** coincidir com baixa física líquida.
- Consumo SD3: somar **somente** movimentos classificados elegíveis, liquidados os estornos/retornos e com conversão validada; não somar transferências e mão de obra.
- Diferença: `eligible_consumption - theoretical_qty` apenas quando fontes completas e comparáveis; percentual depende de denominador não nulo e decisão de negócio.
- Alertas por operação dependem do estado real de apontamento/execução; SH8 demonstra cadastro e não execução.
- Operações/OPs relacionadas precisam impedir contagem dupla (D4_OPORIG, documentos compartilhados).
- `classification` proposta: `reconciled | arithmetic_difference | requires_investigation | unclassified`; não usar `irregular` ou `shortage` sem prova física/funcional.

## 7. Testes e critérios para GATE-D2 (a executar futuramente)

| Caso | Resultado exigido |
|---|---|
| Filial 01, OP de referência, cabo | SD3 consumo 80,75 e transferência 0,64 separadas; nunca 81,39 de consumo |
| Terminal em operação 02 sem execução comprovada | não abrir alerta conclusivo de falta de consumo |
| MOD216 tipo MO/HR | fora do somatório de MP |
| Documento compartilhado | linhas segregadas por filial/OP/item; sem juntar só por número do documento |
| OP relacionada por D4_OPORIG | rastrear vínculo, não duplicar baixas |
| Histórico BOM diferente da estrutura atual | cálculo por versão efetiva, sem usar “hoje” silenciosamente |
| Devolução/estorno parcial; UM diferente | resultado baseado em regra homologada ou `unclassified` |
| Execução ausente + SD4 aberto | `unclassified`/não conclusivo, não “falta física” |
| SH6 quantidade 0,125 vs SC2 QUJE 0 | conflito explícito, não conversão automática em fechamento |
| 401/403/filial inválida/Core indisponível | negar fail-closed, sem fuga de dados |
| Lista com alto volume | paginação, sem N+1 por OP×componente; limites e timeouts testados |

GATE-D2 só pode receber `ACCEPT` após decisões sobre semântica, cálculos, status e tolerâncias por owners, schemas finais e revisão security/producer-consumer. Até lá `INCONCLUSIVE` e contratos `PROPOSED`.

## 8. Riscos e decisões de produto

1. PO decidir página/rota e encaixe no roadmap; **GLPI #1353 ≠ E12**. O gate E11 precisa ser respeitado e revalidado no HEAD.
2. Joici e Michael homologar classificação, tolerâncias e valor para operação parcialmente executada.
3. PCP/owner Protheus comprovar trigger da baixa, execução por operação, SH6 × SC2, estorno/retorno e vínculos de OP.
4. Equipe de segurança aprovar o producer dedicado e AuthZ S2S sem permissão nova.
5. Implementação somente após gate, autorização explícita, HEAD/status e provas atuais.

## 9. Controle documental

- D2.1 define **o que** avaliar; D2.2 propõe **por quais contratos**, sem substituir schemas/OpenAPI reais.
- D1 continua `INCONCLUSIVE`; D2 permanece `DRAFT`.
- Mudanças materiais de semântica, owner ou contrato exigem `EXECUTION_DRIFT` e decisão explícita; jamais ajustar silenciosamente.
