# Portal de Engenharia — inventário de ativos

> **Data:** 2026-09-11  
> **Status:** baseline documental; revalidar SHA, manifests, rotas e owners antes da implementação.

Legenda: `INCORPORAR` · `INTEGRAR` · `DEEP_LINK` · `MANTER_OWNER` · `DEPRECIAR_APOS_PARIDADE` · `A_VALIDAR` · `FORA_DO_ESCOPO`.

## 1. Ativos atuais diretamente relacionados

| Ativo | Tipo | Função atual | Evidência/permission | Decisão alvo |
|---|---|---|---|---|
| `plugins/dashboard-engineering` | MFE | indicadores de Engenharia, LMPs no prazo e TRANSFORMA+ | `dashboard-engineering.view` | **DEPRECIAR_APOS_PARIDADE** da Visão geral |
| `plugins/dashboard-lmps` | MFE | dashboard LMP, detalhe, produtos/BOM, histórico, Gantt e NCs | `dashboard-lmps.view`, `dashboard-lmps.nc.write` | **DEPRECIAR_APOS_PARIDADE** de LMPs |
| `api-delpi /engineering/*` | API | leitura/regras TOTVS de Engenharia/LMP | contratos existentes | **INTEGRAR** via `engineering-api` |
| `api-delpi /products/*` | API | produto, estrutura, parents, estoque, fornecedor, preço, desenhos | contratos existentes | **INTEGRAR** via `engineering-api` |
| Strategic Indicators | API/plugin | metas, realizado, IDD e catálogo estratégico | `engineering-projects-on-time`, `engineering-transforma-plus` | **MANTER_OWNER / INTEGRAR** |
| `plugins/my-requests` + `requests-api` | MFE/API | solicitações e workflow alvo de Controle de MP | roadmap `controle-mp` | **DEEP_LINK / INTEGRAR RESUMO** |
| `controle-mp` legado | iframe/app legado | criação/alteração de MP | roadmap próprio de migração | **DEPRECIAR PELO ROADMAP CONTROLE-MP**, não pelo Portal |
| Transformômetro / `transformometro-api` | MFE/API | TRANSFORMA+ | owner atual | **MANTER_OWNER / DEEP_LINK / RESUMO** |
| FILESERVER — desenhos | storage corporativo | desenhos técnicos | backend já expõe leitura controlada | **INTEGRAR**, sem browser→share |
| FILESERVER — demais documentos Engenharia | storage corporativo | documentos/LMPs/projetos | leituras pontuais; contrato genérico não congelado | **A_VALIDAR** antes do MVP documental |
| Portal Comercial — Sala de interação | referência | inbox/thread/realtime/menções/anexos | implementação madura | **REFERÊNCIA**, nunca dependência runtime |
| `@delpi/plugin-ui` | design system | shell, TopBar, forms, feedback, tables, help | shared remote/factories | **INTEGRAR / KIT-FIRST** |

## 2. Ativos que o novo Portal deve criar

| Ativo | Papel | Estado |
|---|---|---|
| `plugins/engineering` | MFE do Portal | **NÃO EXISTE** na baseline |
| `engineering-api` | BFF + estado próprio da Engenharia | **NÃO EXISTE** na baseline |
| schema `engineering` | persistência de Sala/estado próprio | **PLANEJADO**, banco/migration runner a confirmar |
| manifesto `engineering` | registro do módulo no Core | **PLANEJADO** |
| catálogo de Help | conteúdo user-facing | **PLANEJADO** |
| contrato realtime Engenharia | eventos da Sala | **PLANEJADO**, tecnologia Flask-compatible a confirmar |

## 3. Destino funcional por superfície

| Capacidade | Origem atual | Portal alvo | Estratégia |
|---|---|---|---|
| Início | inexistente como hub | `/apps/engineering` | **NOVO** |
| Visão geral | dashboard-engineering | `/overview` | **INCORPORAR COM PARIDADE** |
| Sala | referência Comercial | `/rooms` | **NOVO NO OWNER engineering-api** |
| Minhas tarefas | fontes dispersas | `/my-tasks` | **COMPOSIÇÃO**, sem novo workflow owner |
| LMPs | dashboard-lmps | `/lmps` + detalhe | **INCORPORAR COM PARIDADE** |
| Produtos | consultas api-delpi | `/tools/products` | **NOVO MFE / REUSO DE CONTRATOS** |
| Desenhos | api-delpi + FILESERVER | `/tools/drawings` | **NOVO MFE / REUSO BACKEND** |
| Documentos técnicos | FILESERVER | `/tools/documents` | **NOVO**, allowlist e leitura controlada |
| Controle MP | controle-mp → my-requests | `/tools/raw-material-control` como hub/CTA | **DEEP_LINK** |
| TRANSFORMA+ | Transformômetro | `/tools/transforma-plus` como resumo/CTA | **DEEP_LINK + RESUMO** |
| NCs | dashboard-lmps/api-delpi | seção/rota LMP + ferramenta quando necessário | **INCORPORAR COM PARIDADE** |
| Ajuda | inexistente no novo Portal | `/help` | **NOVO** |

## 4. Contratos estratégicos confirmados

Engenharia possui dois indicadores estratégicos canônicos já usados pelo dashboard atual:

```text
engineering-projects-on-time
engineering-transforma-plus
```

O departamento `engineering` usa agregação **consolidated**. O Portal não deve inferir ausência de filial como nota zero nem recalcular IDD no navegador.

## 5. Permissions legadas relevantes

```text
dashboard-engineering.view
dashboard-lmps.view
dashboard-lmps.nc.write
```

Esses códigos não devem ser copiados como arquitetura final. O novo catálogo deve ser mínimo e orientado a risco/capability. Durante coexistência, mapear personas e equivalência antes de qualquer redirect/depreciação.

## 6. Dados que NÃO devem ser clonados

Não criar tabelas locais para copiar apenas por conveniência:

- cadastro mestre de produto;
- estrutura/BOM do TOTVS;
- LMP/OV como nova verdade;
- scores/metas do SI;
- workflow/estado de Controle MP;
- processos/medições do Transformômetro;
- RBAC do Core;
- arquivos binários do FILESERVER sem estratégia de storage própria comprovada.

Caches/read models são permitidos somente com TTL/freshness/origem e sem virar writer concorrente.

## 7. Inventário obrigatório no E0

Antes de criar código, congelar evidência atual de:

1. manifests e rotas dos dois dashboards legados;
2. chamadas HTTP reais do `dashboard-engineering` e `dashboard-lmps`;
3. endpoints OpenAPI de `/engineering/*` e `/products/*` usados por esses MFEs;
4. testes existentes, inclusive regras de Gantt/NC/indicadores;
5. rotas reais do `my-requests` para Controle MP;
6. contrato atual do Transformômetro;
7. contrato atual do Strategic Indicators para `department_id=engineering`;
8. mounts/variáveis de ambiente do FILESERVER e desenho;
9. componentes reutilizáveis do `plugin-ui`;
10. padrões de Sala/realtime do Comercial;
11. consumidores externos/deep links que apontam para dashboards legados;
12. estado real dos registros no Core em DEV/HML/PROD.

## 8. Gate de inventário

Nenhum item `A_VALIDAR` pode ser usado como base de código P0 sem uma subetapa explícita de investigação. Nenhum legado pode ser removido enquanto houver consumidor/deep link sem destino comprovado.
