# Matriz de reconciliação — Portal Comercial × Transformômetro

> **Status:** preparação documental.  
> **Catálogo real do Transformômetro:** ainda não consultado nesta sessão.  
> **Regra:** nenhuma linha pode ser classificada definitivamente como `NOVA_REVISAO` ou `NOVO_CADASTRO` sem localizar o registro real do Transformômetro ou comprovar sua inexistência por fonte canônica.

## Estados de reconciliação

| Estado | Uso |
|---|---|
| `PENDING_TRANSFORMOMETRO` | ainda não consultamos o cadastro real |
| `MATCH_EXISTING` | item existente localizado e semanticamente equivalente |
| `MATCH_PARTIAL` | item existente cobre apenas parte da capacidade/processo atual |
| `NO_MATCH_CONFIRMED` | fonte canônica do Transformômetro confirma ausência de equivalente |
| `NEW_REVISION_CANDIDATE` | forte candidato a nova revisão de item existente |
| `NEW_REGISTRATION_CANDIDATE` | forte candidato a novo cadastro |
| `NEEDS_PROCESS_EVIDENCE` | decisão depende de entender processo humano/uso real |
| `OUT_OF_SCOPE_TRANSFORMOMETRO` | componente puramente técnico sem transformação operacional própria |

## Matriz inicial

| Capacidade Portal | Origem | Macroprocesso Transformômetro | Processo Transformômetro | Melhoria existente | ID/revisão | Estado | Próxima verificação |
|---|---|---|---|---|---|---|---|
| Meus pedidos / pedidos abertos | `pedidos-venda-abertos` → Portal | PENDING | PENDING | PENDING | PENDING | `PENDING_TRANSFORMOMETRO` | localizar cadastro de acompanhamento/pedidos e comparar revisão anterior |
| Propostas comerciais ADY | `propostas-comerciais` → Portal | PENDING | PENDING | PENDING | PENDING | `PENDING_TRANSFORMOMETRO` | localizar cadastro de propostas e comparar escopo anterior |
| Carteiras comerciais | legado PVA + estado canônico Comercial | PENDING | PENDING | PENDING | PENDING | `PENDING_TRANSFORMOMETRO` | localizar gestão de carteira e verificar se multi-membro/ownership exige revisão |
| Overview / gestão à vista | overlap `dashboard-commercial` | PENDING | PENDING | PENDING | PENDING | `PENDING_TRANSFORMOMETRO` | cruzar KPI por KPI, evitando tratar dashboard como uma única melhoria |
| OTD | overlap dashboard + Portal | PENDING | PENDING | PENDING | PENDING | `PENDING_TRANSFORMOMETRO` | localizar processo/melhoria de OTD/prazo de entrega |
| Oportunidades / OV | overlap dashboard + experiência Portal | PENDING | PENDING | PENDING | PENDING | `PENDING_TRANSFORMOMETRO` | localizar melhoria de oportunidades/funil comercial |
| SI/IDD | cadeia de indicadores existente + consumo Portal | PENDING | PENDING | PENDING | PENDING | `PENDING_TRANSFORMOMETRO` | localizar melhoria de indicadores comerciais/IDD |
| Conta 360 | composição híbrida nativa | PENDING | PENDING | PENDING | PENDING | `NEEDS_PROCESS_EVIDENCE` | verificar se já existe transformação de gestão/visão do cliente |
| Faturamento/NF na Conta | dados existentes + experiência Portal | PENDING | PENDING | PENDING | PENDING | `PENDING_TRANSFORMOMETRO` | localizar melhoria de acompanhamento financeiro/comercial do cliente |
| Produção vinculada | dados existentes + experiência Portal | PENDING | PENDING | PENDING | PENDING | `NEEDS_PROCESS_EVIDENCE` | entender se é parte do acompanhamento de pedido ou processo distinto |
| Minhas Tarefas/worklist | estado nativo Comercial | PENDING | PENDING | PENDING | PENDING | `NEW_REGISTRATION_CANDIDATE` | procurar equivalentes antes; depois comprovar processo real de pendências |
| Atividades comerciais | estado nativo | PENDING | PENDING | PENDING | PENDING | `NEEDS_PROCESS_EVIDENCE` | cruzar com tarefas/relacionamento |
| Contatos da conta | híbrido Postgres + SA1 | PENDING | PENDING | PENDING | PENDING | `NEEDS_PROCESS_EVIDENCE` | localizar gestão de relacionamento/contatos |
| Sala de Interação | estado nativo Comercial | PENDING | PENDING | PENDING | PENDING | `NEW_REGISTRATION_CANDIDATE` | buscar equivalente de colaboração/tratativa e validar uso real |
| Tarefa a partir de mensagem | integração sala→worklist | PENDING | PENDING | PENDING | PENDING | `NEEDS_PROCESS_EVIDENCE` | decidir se pertence à revisão de sala ou tarefas |
| Grupos operacionais | estado nativo Comercial | PENDING | PENDING | PENDING | PENDING | `NEEDS_PROCESS_EVIDENCE` | entender papel operacional no processo real |
| Administração de equipe | híbrido Comercial + Core | PENDING | PENDING | PENDING | PENDING | `NEEDS_PROCESS_EVIDENCE` | verificar se é suporte, e não transformação autônoma |
| Políticas de SLA | CRUD implementado; consumo parcial | PENDING | PENDING | PENDING | PENDING | `NEEDS_PROCESS_EVIDENCE` | não considerar parte futura como entregue; localizar eventual cadastro de SLA |
| Favoritos/Home | estado nativo | PENDING | PENDING | PENDING | PENDING | `NEEDS_PROCESS_EVIDENCE` | só registrar se houver problema operacional/resultado associado |
| Perfis comerciais | híbrido Comercial + Core | PENDING | PENDING | PENDING | PENDING | `NEEDS_PROCESS_EVIDENCE` | provavelmente suporte; verificar cadastro existente |
| Notificações operacionais | nativo + Core | PENDING | PENDING | PENDING | PENDING | `PENDING_TRANSFORMOMETRO` | localizar melhoria anterior de alertas/notificações |
| Auditoria | estado nativo | PENDING | PENDING | PENDING | PENDING | `NEEDS_PROCESS_EVIDENCE` | verificar necessidade de controle/rastreabilidade associada |
| Realtime/WebSocket | técnico | — | — | — | — | `OUT_OF_SCOPE_TRANSFORMOMETRO` | usar apenas como evidência técnica de capacidades como sala/notificações |

## Regra de decisão para nova revisão

Classificar como `NEW_REVISION_CANDIDATE` somente quando:

1. houver item existente no Transformômetro;
2. o problema/processo central permanecer semanticamente o mesmo;
3. o Portal tenha alterado solução, abrangência, atores, dados, integração ou resultado;
4. seja possível descrever claramente **o que mudou desde a revisão anterior**.

Exemplos fortes a verificar primeiro: **Pedidos**, **Propostas**, **Carteiras**, **OTD**, **Indicadores/Gestão à vista**.

## Regra de decisão para novo cadastro

Classificar como `NEW_REGISTRATION_CANDIDATE` somente quando:

1. nenhum item semanticamente equivalente for localizado;
2. a capacidade corresponder a uma necessidade/processo operacional identificável, não apenas uma tela;
3. houver atores, gatilho, entrada, atividade, resultado e owner minimamente conhecidos;
4. a granularidade correta estiver definida: melhoria dentro de processo existente vs novo processo vs novo macroprocesso.

**Novo macroprocesso deve ser exceção.** A existência de uma funcionalidade nova no Portal não implica macroprocesso novo.

## Dados que devem ser preenchidos a partir do Transformômetro

Para cada possível match:

- `macroprocess_id` e nome;
- `process_id` e nome;
- `improvement_id` e título;
- revisão/versionamento atual;
- status;
- unidade/filial quando aplicável;
- problema original;
- situação anterior registrada;
- situação posterior registrada;
- métricas/ganhos existentes;
- owner/responsável;
- evidências/anexos associados.

## Dados adicionais do processo real

Quando a equivalência não puder ser decidida apenas pelo cadastro anterior, levantar:

- quem utiliza;
- em quais filiais/unidades;
- gatilho;
- dado de entrada e autoridade;
- atividades antes/depois;
- handoffs;
- espera;
- retrabalho;
- sistemas paralelos (TOTVS, e-mail, Teams, WhatsApp, planilhas);
- resultado entregue;
- como resultado é medido.

Esses dados devem ser registrados antes de pedir ao TÉO para redesenhar ou sugerir métricas futuras.