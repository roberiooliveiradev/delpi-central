# 04 — Requisitos, contratos e critérios de aceite (candidatos)

| RQ | Necessidade | AC observável |
|---|---|---|
| RQ-01 | Identificar novo produto por fonte oficial | Nenhuma OP vira 'nova' por heurística não aprovada |
| RQ-02 | Consultar programação do Carga Máquina / OPs | Filtros semana/mês/período e unidade, com escopo autorizado |
| RQ-03 | Planejar com antecedência | Previsões têm data, origem e última atualização |
| RQ-04 | Líder aciona manualmente | Chamado vinculado à OP, auditável e idempotente |
| RQ-05 | Conciliar eventos | Previsão e solicitação manual não geram duplicidade |
| RQ-06 | Checklist por operação | Operação, produto/OP, desenho/revisão, resultado, executor e tempo registráveis |
| RQ-07 | Divergência rastreável | Encaminhamento à Engenharia e rechecagem registrados |
| RQ-08 | Conclusão governada | Sem retirada do indicador antes de completude e autorização do owner |
| RQ-09 | Pendências e reprogramação | Preserva histórico sem registrar conclusão falsa |
| RQ-10 | Segurança e resiliência | Falhas/403/stale/conflict exibidos corretamente; AuthZ backend |
| RQ-11 | Medição | Métricas com fórmula, período, fonte, owner; sem meta fictícia |

## Contratos a inventariar antes da implementação
- **Carga Máquina/OP:** owner, API oficial, modelo de OP, produto, filial, operações, previsão, mudanças e início real; leitura paginada, filtros, freshness e erros.
- **Produto novo:** campo/critério canônico, revisão, validade, quem decide e como consultar.
- **Acompanhamento/checklist:** owner real, estados, eventos, CRUD/autorização, idempotência, retenção, links às evidências e leitura.
- **Divergência/correção:** owners, escopo de acesso, eventos de mudança, trilha de auditoria e retorno ao acompanhamento.
- **Desenho:** referência/revisão oficial, operação de retirada do indicador, revisão/aprovação/publicação pelo owner competente.
- **Navegação:** Core app/route/RBAC, permissões positivas/negativas, links do Portal, ajuda e logs.

**Contrato antes do código:** request/response, erros, AuthN/AuthZ live, limites, compatibilidade, observabilidade, idempotência e postcondition; respeitar read/write, draft/publish e rollback.

## Testes candidatos
1. Eng. vê somente OPs permitidas com datas atualizadas; outra unidade bloqueada.
2. Reprogramação não cria início nem conclusão.
3. Líder autorizado aciona OP; reenvio não duplica; usuário não autorizado recebe 403.
4. Filial registra checklist e comunica conformidade/divergência à Engenharia.
5. Pendência mantém indicador; conclusão exige aprovação e owner do desenho.
6. API fora do ar mostra falha/stale sem dados inventados.
7. E2E visual e funcional, a11y, desktop/mobile, reload/deep link, testes no commit SHA.
