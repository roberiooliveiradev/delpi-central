# Portal de Engenharia — decisões funcionais pendentes

> **Status:** lista de decisões `NOT_READY`/`READY_BOUNDED`.  
> **Regra:** o Cursor não pode escolher silenciosamente uma opção durante a implementação.

## 1. Como usar

Cada decisão deve terminar em uma destas classificações:

```text
READY_CONFIRMED
READY_BOUNDED
NOT_READY
FORA_DO_ESCOPO_COM_ACEITE
```

Quando resolvida, atualizar este documento e o contrato afetado antes de promover a etapa correspondente.

## 2. P-01 — Uma ou várias salas por contexto

**Pergunta:** Produto/LMP/Projeto terá uma única sala canônica por contexto ou poderá ter múltiplas salas?

**Estado:** `NOT_READY`.

**Impacto:** índice único do banco, criação de sala, UX, deep links e membership.

**Gate:** resolver antes da migration física da Sala.

## 3. P-02 — Membership da Sala

**Pergunta:** quem entra automaticamente em sala contextual e quem pode adicionar/remover participantes?

Possíveis fontes a investigar: responsável da LMP, membros de equipe/grupo, criador, participantes explícitos.

**Estado:** `NOT_READY`.

**Proibição:** não assumir “todo engineering.access vê todas as salas”.

## 4. P-03 — Retenção de mensagens e anexos

Definir:

- retenção mínima/máxima;
- soft delete;
- auditoria;
- tratamento de usuário desativado;
- limpeza de anexos órfãos.

**Estado:** `NOT_READY` para produção; não bloqueia desenho documental.

## 5. P-04 — Storage de anexos da Sala

**Pergunta:** reutilizar infraestrutura de attachments da plataforma/plugins ou criar storage próprio do `engineering-api`?

**Estado:** `NOT_READY`.

**Gate:** antes de implementar upload.

## 6. P-05 — Tecnologia realtime Flask-compatible

**Pergunta:** qual mecanismo canônico deve ser usado pelo `engineering-api` sem trocar o framework Flask?

Investigar padrões atuais de WebSocket/socket/event-driven, Nginx, processo/container e dependências aprovadas.

**Estado:** `NOT_READY`.

**Proibição:** não acoplar a Sala ao `commercial-api`.

## 7. P-06 — Fontes reais de Minhas tarefas

**Pergunta:** quais owners entram no P0 da worklist?

Candidatos:

- LMP;
- Controle MP (`requests-api`);
- NC;
- outras atividades de Engenharia.

**Estado:** `READY_BOUNDED`: arquitetura do agregador está definida, catálogo P0 precisa de evidência por owner.

## 8. P-07 — Actions rápidas na worklist

**Pergunta:** quais fontes fornecem `allowed_actions` confiável e mutação autorizada?

**Estado:** `NOT_READY` por owner.

P0 pode lançar apenas deep link quando actions não forem comprovadas.

## 9. P-08 — Escopo por filial/unidade

**Pergunta:** LMPs, Produtos, documentos ou worklist precisam de unit scope explícito no Portal?

**Estado:** `NOT_READY`.

Nota: indicadores estratégicos de Engenharia são consolidados; isso não responde sozinho ao escopo operacional.

## 10. P-09 — Administração do Portal

**Pergunta:** haverá uma página administrativa P0 para gerir salas, bibliotecas, settings ou integrações?

**Estado:** `FORA_DO_ESCOPO_P0` até demanda explícita.

`engineering.administration.manage` não deve entrar no manifesto inicial sem uma superfície real.

## 11. P-10 — Política de preço/custo em Produtos

**Pergunta:** quem pode visualizar preço de compra, custo e impacto financeiro?

**Estado:** `NOT_READY`.

Proposta segura: capability sensível separada `engineering.costs.view`, sujeita a validação do Product Owner/RBAC.

## 12. P-11 — Biblioteca de desenhos: permission

**Pergunta:** desenhos devem herdar `engineering.products.access`, usar `engineering.documents.access` ou capability própria por risco?

**Estado:** `NOT_READY`.

Não criar permission própria apenas por organização visual; decidir pelo risco e população real.

## 13. P-12 — Bibliotecas FILESERVER P0

**Pergunta:** quais raízes/documentos entram no primeiro release?

Preencher para cada biblioteca:

```text
library_id
nome
raiz server-side
owner do conteúdo
extensions
profundidade
preview/download
permission
auditoria
```

**Estado:** `NOT_READY`.

Sem essa lista, implementar apenas biblioteca de desenhos já contratada pelo backend.

## 14. P-13 — Preview de Office

**Pergunta:** DOCX/XLSX/PPTX terão preview inline ou apenas download controlado no P0?

**Estado:** `READY_BOUNDED`: default seguro é download, preview só com componente/serviço suportado.

## 15. P-14 — Definição oficial/expansão de LMP

**Pergunta:** qual é a expansão oficial da sigla para conteúdo user-facing?

**Estado:** `NOT_READY` para glossário final.

Não inventar expansão; manter “LMP” até confirmação.

## 16. P-15 — Indicadores operacionais do Overview

Além dos dois indicadores SI, quais entram na Visão geral P0?

Candidatos: atrasadas, lead, status, NCs.

**Estado:** `NOT_READY`.

Cada indicador exige ficha: pergunta, owner, fórmula, natureza temporal, filtros, null semantics e drill.

## 17. P-16 — Filtros globais da Visão geral

**Pergunta:** além do período, existe filtro de filial/escopo/projeto que afeta coerentemente todos os cards?

**Estado:** `NOT_READY`.

Não copiar filtros de Comercial/Suprimentos por simetria.

## 18. P-17 — Relação NC como rota própria vs seção de LMP

**Pergunta:** manter uma ferramenta/lista global de NCs além da aba por LMP?

**Estado:** `READY_BOUNDED`: legado possui rota/listagem; decisão de IA precisa preservar paridade antes do cutover.

## 19. P-18 — Transformômetro: conteúdo do resumo

**Pergunta:** quais métricas podem ser compostas na Home/Overview sem duplicar a experiência do owner?

**Estado:** `READY_BOUNDED`: indicador estratégico existe; demais blocos exigem contrato real.

## 20. P-19 — Deep links exatos do Controle MP

Confirmar request types, query params e rotas vigentes do `my-requests` no momento da implementação.

**Estado:** `READY_BOUNDED`: ownership está decidido; contrato de navegação deve ser revalidado.

## 21. P-20 — Janela de cutover dos dashboards

Definir após paridade:

- público inicial;
- duração da coexistência;
- critérios de observação;
- data de soft cutover;
- data de redirect;
- janela de rollback.

**Estado:** `NOT_READY`; não bloqueia desenvolvimento do target.

## 22. Resumo de bloqueios

| Decisão | Bloqueia |
|---|---|
| P-01/P-02/P-03/P-04/P-05 | Sala de interação produtiva |
| P-06/P-07 | escopo final Minhas tarefas/actions |
| P-08 | unit scope/RBAC operacional |
| P-10/P-11 | dados sensíveis/desenhos |
| P-12/P-13 | Documentos técnicos |
| P-14 | glossário final |
| P-15/P-16 | composição final do Overview |
| P-17 | paridade/cutover NC |
| P-20 | cutover dos legados |

O plano deve permitir avançar etapas independentes sem transformar essas pendências em decisão implícita.
