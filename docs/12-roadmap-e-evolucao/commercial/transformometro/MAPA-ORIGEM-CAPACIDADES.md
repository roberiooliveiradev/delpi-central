# Mapa de origem das capacidades — Portal Comercial

> **Finalidade:** distinguir o que foi migrado/evoluído de aplicações anteriores do que é estado/experiência nativa do Portal.  
> **Não substitui:** consulta ao Transformômetro nem evidência de processo humano real.  
> **Baseline:** Fase 1/1R do `INVENTARIO-ESTADO-ATUAL.md`.

## Como ler

A coluna **Origem comprovada** descreve o que o repositório sustenta. A coluna **Tratamento no Transformômetro** é somente a regra de reconciliação esperada; enquanto o catálogo real não for consultado, permanece `PENDING_TRANSFORMOMETRO`.

| Capacidade atual | Estado atual no Portal | Origem comprovada | Classe | Tratamento no Transformômetro | Evidência principal |
|---|---|---|---|---|---|
| Meus pedidos / pedidos abertos | `/open-orders`, detalhe linha, detalhe OP; BFF `commercial-api` → `api-delpi` | MFE `pedidos-venda-abertos` removido no F2c; deep links redirecionados para o Portal | `MIGRATED_LEGACY_MFE` | localizar melhoria/processo anterior e avaliar **nova revisão** | `F2C-CUTOVER-RUNBOOK.md`; inventário §§4, 9, 10 |
| Propostas comerciais ADY | `/proposals`, detalhe/PDF; `proposal-documents` → `api-delpi` | MFE `propostas-comerciais` removido no F2c; rota canônica passou ao Portal | `MIGRATED_LEGACY_MFE` | localizar cadastro anterior e avaliar **nova revisão** | `F2C-CUTOVER-RUNBOOK.md`; inventário §§4, 9 |
| Carteiras comerciais | Minha Carteira + Administração de carteiras; estado em schema `commercial` | havia origem legada no domínio PVA; modelo atual canônico migrou para `commercial.seller_*` | `EVOLVED_LEGACY_CAPABILITY` | localizar cadastro anterior; revisão deve explicitar mudança de ownership/modelo e multi-membro | inventário §§6, 9; F2c multi-membro |
| Membership multi-carteira | `seller_portfolio_members`, N:N usuário↔carteira | schema legado PVA não é mais fonte de verdade; capacidade atual é do domínio Comercial | `PORTAL_NATIVE_STATE` sobre capacidade evoluída | verificar se revisão da gestão de carteiras é suficiente; não criar melhoria isolada sem processo real | migrations V005; inventário §§6, 9 |
| Transferência/atribuição de clientes | CRUD/bulk/owner em `/seller-portfolios*` | evolução do gerenciamento de carteira; persistência/auditoria própria | `PORTAL_NATIVE_STATE` | provável componente de revisão de carteira, não novo macroprocesso por tela | inventário §§5.2, 9, 10 |
| Overview / Gestão à vista | KPIs ROL, carteira, hit rate, OTD, IDD, oportunidades | overlap com `dashboard-commercial`, que continua registrado e consome `api-delpi` direto | `OVERLAP_LEGACY_SIBLING` + `HYBRID` | cruzar KPI/capacidade individual com registros anteriores antes de decidir revisão/novo | inventário §19.2, §19.5 |
| OTD | lista, painel, séries, detalhe de linha no Portal | capacidade também presente no `dashboard-commercial` legado | `OVERLAP_LEGACY_SIBLING` | localizar cadastro anterior; provável revisão se mesma necessidade/processo | inventário §§4, 5.5, 19.2 |
| Oportunidades / OV | lista/detalhe via analytics/proposals da `api-delpi` | overlap com visão OV no `dashboard-commercial`; dados upstream já existiam | `OVERLAP_LEGACY_SIBLING` + `PORTAL_NATIVE_EXPERIENCE_ON_EXISTING_DATA` | cruzar semanticamente com melhoria/processo anterior | inventário §§4, 9, 19.2 |
| Indicadores SI/IDD | badge/indicadores na Overview via `commercial-api` → `api-delpi` → `strategic-indicators-api` | cadeia pré-existente de indicadores; Portal adiciona composição/consumo | `PORTAL_NATIVE_EXPERIENCE_ON_EXISTING_DATA` | revisar cadastro existente se já houver melhoria de indicadores; não criar novo só pelo novo consumidor | inventário §19.5 |
| Conta 360 | tela composta de conta, pedidos, billing, contatos, auditoria, oportunidades | composição nova no Portal sobre dados TOTVS/api-delpi + estado próprio | `HYBRID` | verificar se já existe transformação de gestão de cliente/conta; provável novo somente se não houver equivalente | inventário §§4, 5.3, 9, 10 |
| Faturamento / notas fiscais na Conta | billing series + outbound invoices | dados/contratos TOTVS existentes; experiência consolidada na Conta | `PORTAL_NATIVE_EXPERIENCE_ON_EXISTING_DATA` | normalmente revisão/componente do processo de acompanhamento do cliente, salvo cadastro específico existente | inventário §§5.3, 9 |
| Produção vinculada a pedido/oportunidade | detalhe OP, factory-status/structure | dados e contratos de produção já existentes na `api-delpi` | `PORTAL_NATIVE_EXPERIENCE_ON_EXISTING_DATA` | tratar como evolução do acompanhamento comercial enquanto processo real não provar algo distinto | inventário §§4, 5.6, 9, 10 |
| Minhas Tarefas / worklist | tarefas, responsáveis, concluídas, vínculos com cliente/grupo | estado próprio no schema `commercial`; migrations/tasks repos | `PORTAL_NATIVE_STATE` | verificar duplicidade no Transformômetro; forte candidato a novo registro se não houver gestão de pendências equivalente | inventário §§6, 9, 10 |
| Atividades comerciais | atividades vinculadas a conta/tarefa | persistência própria `activities` | `PORTAL_NATIVE_STATE` | cruzar com gestão de tarefas/relacionamento; não assumir processo novo | inventário §§6, 9 |
| Anexos de tarefas/interações | attachments + volume | persistência própria do Comercial | `PORTAL_NATIVE_STATE` | componente de processo; não melhoria isolada por padrão | inventário §§6, 9 |
| Contatos da conta | CUD em `account_contacts`, combinado com leitura SA1 | estado próprio + fonte upstream | `HYBRID` | verificar cadastro de gestão de relacionamento/contatos | inventário §§5.3, 6, 9 |
| Sala de Interação | inbox, thread, mensagens, menções, anexos, pins, reações, realtime | estado próprio em migrations V019/V021; roadmap da sala entregue E1–E7 | `PORTAL_NATIVE_STATE` | forte candidato a novo registro se não existir transformação equivalente de colaboração/tratativa | inventário §§6, 9, 10; `ROADMAP-INTERACTION-ROOM.md` |
| Tarefa criada a partir de mensagem | vínculo sala→task | estado próprio de sala + worklist | `PORTAL_NATIVE_STATE` | provavelmente melhoria dentro de colaboração/gestão de pendências, não macroprocesso isolado | inventário de tasks/interaction |
| Grupos operacionais | administração de grupos/membros | `commercial_groups` e members no schema Comercial | `PORTAL_NATIVE_STATE` | verificar se representa estrutura operacional já documentada em outro processo | inventário §§6, 8, 9 |
| Administração de equipe | roster, grupos e carteiras | composição Comercial + diretório/Core | `HYBRID` | normalmente suporte à operação, não macroprocesso por si só; cruzar com gestão comercial | inventário §§4, 7, 10 |
| Políticas de SLA | CRUD de `sla_policies`; consumo operacional ainda parcial/backlog | estado próprio implementado, mas uso operacional completo não está provado | `PORTAL_NATIVE_STATE` com limite | não registrar resultado futuro como melhoria entregue; separar CRUD existente de consumo futuro | inventário §§6, 9; backlog separado |
| Favoritos/Home personalizada | `home_favorites` + Home | estado próprio no Comercial | `PORTAL_NATIVE_STATE` | experiência de ferramenta; só vira melhoria relevante se associada a necessidade/processo e resultado | inventário §§6, 9 |
| Perfis comerciais | `commercial_user_profiles` + espelho Core | estado próprio + integração Core | `HYBRID` | suporte operacional; não assumir melhoria comercial isolada | inventário §§6, 7, 9 |
| Notificações operacionais | scheduler/outbox/Core notifications/realtime | implementação própria do Comercial integrada ao Core | `PORTAL_NATIVE_STATE` + integração | localizar eventual melhoria anterior de notificação; revisar ou criar conforme processo associado | inventário §§6, 7, 9, 10 |
| Auditoria | `audit_log`, telas/rotas de conta e carteira | estado próprio | `PORTAL_NATIVE_STATE` | componente de controle/rastreabilidade; não macroprocesso isolado sem necessidade comprovada | inventário §§6, 9 |
| Realtime | WebSocket/hub do Comercial | implementação própria | `PORTAL_NATIVE_STATE` técnico | infraestrutura habilitadora; não cadastrar como melhoria de processo isolada | inventário §§3, 7, 9 |

## O que NÃO deve ser tratado como nova melhoria automaticamente

Os itens abaixo são importantes tecnicamente, mas não equivalem sozinhos a uma transformação de processo:

- nova rota/API;
- novo BFF;
- migration/tabela;
- permission code;
- WebSocket/realtime;
- troca de ownership técnico;
- redirect/cutover de MFE;
- reorganização de menu;
- integração com `api-delpi` ou `core-api` sem mudança operacional comprovada.

Eles podem ser evidência de uma revisão, mas a unidade do Transformômetro deve continuar sendo o processo/melhoria operacional.

## Lacunas que impedem classificação final

Para cada linha ainda é necessário, quando aplicável:

1. localizar ID do macroprocesso/processo/melhoria no Transformômetro;
2. ler descrição/revisão anterior;
3. comparar problema operacional anterior com a capacidade atual;
4. confirmar atores e filiais afetados;
5. confirmar o que mudou no trabalho antes/depois;
6. confirmar resultado/métrica usada ou esperada.

Até isso acontecer, a coluna de tratamento é orientação de reconciliação, não status aprovado.