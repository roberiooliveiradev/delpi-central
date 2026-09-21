# 15 — Capacidades do GLPI × Meus Chamados de TI

> **Status:** inventário sincronizado com o código. Paridade [`16-plano-paridade.md`](./16-plano-paridade.md) **concluída**. Não altera [`06-plano-execucao.md`](./06-plano-execucao.md).
> **Estados:** IMPLEMENTADO / CONSOLE_GLPI / BLOQUEADO / FORA — alinhados a 12/13/14 e ao ledger.
> **Pedido:** preencher o que 12–14 ainda não listaram; corrigir drift com a tela e o contrato vigentes.
> **Fontes:** [Opening a ticket](https://help.glpi-project.org/documentation/modules/assistance/tickets/ticketopening), [Manage tickets](https://help.glpi-project.org/documentation/modules/assistance/tickets/ticketmanagement), [Ticket life cycle](https://help.glpi-project.org/documentation/modules/assistance/tickets/ticketlifecycle), [Forms](https://help.glpi-project.org/faq/glpi/forms), HLAPI 2.2, código da helpdesk-api/MFE em 21/09/2026.
> **Detalhe já fatiado:** mensagem [`12`](./12-conteudo-da-mensagem.md) · lista [`13`](./13-listagem-de-chamados.md) · página/estados [`14`](./14-pagina-e-estados-do-chamado.md).

Este arquivo é a **matriz completa** do módulo Assistência do GLPI 11 que toca chamado. Cada linha tem um destino. Nenhuma some por ter ficado fora de 12–14.

## 1. Como ler o destino

| Destino | Significa |
|---|---|
| IMPLEMENTADO | na Minha DELPI hoje |
| ALVO | inventário ainda aberto (ex.: G-05 lista requester) |
| CONSOLE_GLPI | só no host GLPI |
| BLOQUEADO | HLAPI / decisão impede |
| FORA | fora do produto do solicitante |
| H10 / H11 / H12 | [`05-roadmap.md`](./05-roadmap.md) — H5 foi fatiado |
| BLOQUEADO | evidência impede (HLAPI JSON-only, etc.) |
| CONSOLE_GLPI | fica em `helpdesk.centraldelpi.com.br` |
| FORA | não entra neste produto (outro itemtype, parque, HD-011) |
| HIPOTESE | falta provar campo/rota na HLAPI desta produção |

O recorte não mudou: colaborador achar, abrir e acompanhar o **próprio** chamado. Bancada, inventário e ITIL de técnico continuam no console.

## 2. Drift corrigido neste passe

| Afirmação antiga | Fato agora | Onde estava |
|---|---|---|
| Lista em cartões | tabela `HelpdeskDataTable` + filtros | [`01`](./01-visao-produto.md) §3, [`11`](./11-lacunas-da-experiencia.md) §7 |
| `updated_at` a tela não mostra | coluna «Atualizado» | [`11`](./11-lacunas-da-experiencia.md) §2 |
| Prévia/mime não usados | `HelpdeskAttachmentPreviewStrip` + modal | [`11`](./11-lacunas-da-experiencia.md) §2 e A-01 |
| Kit de anexo «o helpdesk não importa» | importa em `helpdeskUi.tsx` | [`11`](./11-lacunas-da-experiencia.md) §3.2 |
| `mine` pelo nome | id GLPI ou e-mail | [`11`](./11-lacunas-da-experiencia.md) C-01 |
| L-01…L-11 ainda por medir | paginação e filtros **publicados**; H2 da lista velha está morto | [`11`](./11-lacunas-da-experiencia.md) §6 |
| H5 = «listar e baixar anexo» | baixar **já publicado**; H5 só envio novo + satisfação + bancada | [`05`](./05-roadmap.md) |
| Data de solução = só bancada | coluna útil ao solicitante; alvo no 13 | [`11`](./11-lacunas-da-experiencia.md) §7 |
| Pasta não prova que a API existe | MFE e BFF estão publicados; o ledger prova runtime | [`INDEX.md`](./INDEX.md) |

## 3. Matriz — abrir chamado

Doc: [Opening a ticket](https://help.glpi-project.org/documentation/modules/assistance/tickets/ticketopening).

| ID | Capacidade GLPI | Destino |
|---|---|---|
| X-01 | Formulário autenticado (título, descrição, categoria, urgência) | IMPLEMENTADO |
| X-02 | Descrição rica / HTML / colar imagem | **IMPLEMENTADO** leitura+escrita ([`12`](./12-conteudo-da-mensagem.md)); colar imagem BLOQUEADO (A-08) |
| X-03 | Um ou mais documentos na abertura | BLOQUEADO A-08 / N-01 |
| X-04 | Título vazio → GLPI usa os 70 primeiros caracteres da descrição | FORA — a Minha DELPI exige título |
| X-05 | Abrir em nome de outro (delegação / grupo) | FORA HD-011 |
| X-06 | Chamado anônimo (`helpdesk.html`) | FORA — exige JWT + OAuth |
| X-07 | Abrir por e-mail (coletor: assunto, corpo, Cc→observador, anexo) | CONSOLE_GLPI / servidor; o MFE não é o coletor |
| X-08 | Chamado recorrente | CONSOLE_GLPI |
| X-09 | **Formulários nativos + catálogo de serviços (GLPI 11)** | **FORA** — H-X1; não reimplementar o catálogo no MFE |
| X-10 | Modelo de chamado (campo obrigatório / pré-preenchido / oculto) | CONSOLE_GLPI — o BFF não lê template |
| X-11 | «Informar-me por e-mail» + escolher endereço | CONSOLE_GLPI — notificação é do GLPI; e-mail vem do usuário |
| X-12 | Itens de inventário associados na abertura | CONSOLE_GLPI / inventário |
| X-13 | Observadores na abertura | **PROVEN** — `POST …/TeamMember` observer (H-X2). Não é HD-011 |
| X-14 | Pedido de validação já na abertura | CONSOLE_GLPI / H5 |
| X-15 | Origem (Direct, E-Mail, Helpdesk, Phone…) | CONSOLE_GLPI — o POST não envia; o GLPI grava a origem da API |
| X-16 | Localização / telefone do solicitante | CONSOLE_GLPI — cadastro de usuário |
| X-17 | Tipo Incidente / Requisição | FORA na abertura (só urgência); o GLPI usa o padrão do perfil/template |
| X-18 | Entidade | FORA HD-011 |

## 4. Matriz — campos e ciclo do chamado

Doc: [Manage tickets](https://help.glpi-project.org/documentation/modules/assistance/tickets/ticketmanagement) + [life cycle](https://help.glpi-project.org/documentation/modules/assistance/tickets/ticketlifecycle).

| ID | Capacidade GLPI | Destino |
|---|---|---|
| X-20 | Título, descrição, datas de criação e alteração | **IMPLEMENTADO** (HTML + datas absolutas) |
| X-21 | Os sete status | **IMPLEMENTADO** `status_id` + grupos pending/approval ([`14`](./14-pagina-e-estados-do-chamado.md)) |
| X-22 | Urgência do solicitante | IMPLEMENTADO |
| X-23 | Impacto (técnico) e prioridade (matriz) | CONSOLE_GLPI / FORA na UI do colaborador |
| X-24 | Aprovação do chamado («Not subject to approval» / etapas) | CONSOLE_GLPI / H5 |
| X-25 | Atores: requerente, observador, atribuído (pessoa/grupo/fornecedor) | atribuído/requerente/observador **IMPLEMENTADOS** como rótulo; editar CONSOLE |
| X-26 | Notificação por ator (sim/não, e-mail) | CONSOLE_GLPI |
| X-27 | Itens de inventário | CONSOLE_GLPI |
| X-28 | TTO, TTR, TTO/TTR internos, SLA, OLA, próximo nível | CONSOLE para gerir; **TTR/TTO visíveis IMPLEMENTADOS** (`sla_ttr` / `sla_tto`) |
| X-29 | Chamados ligados: Linked to, Duplicates, Child of, Parent of | CONSOLE para criar **e** para ver — H-X4 **FORA** (sem campo/rota na HLAPI) |
| X-30 | Duplicata fecha em cascata | CONSOLE_GLPI — o GLPI aplica; a Minha DELPI só relê o status |
| X-31 | Último editor | CONSOLE_GLPI — [`13`](./13-listagem-de-chamados.md) |

## 5. Matriz — ações no fio

| ID | Capacidade GLPI | Destino |
|---|---|---|
| X-40 | Acompanhamento público | IMPLEMENTADO; HTML no 12 |
| X-41 | Acompanhamento privado | CONSOLE_GLPI — o BFF já omite |
| X-42 | Origem / modelo / promover a chamado | CONSOLE_GLPI |
| X-43 | Documento no follow-up | baixar IMPLEMENTADO; enviar BLOQUEADO; vínculo por bolha A-07 |
| X-44 | Motivo de pendência + lembretes | CONSOLE_GLPI — status Pendente no 14 |
| X-45 | Tarefa (e tarefa planejada → status 3) | CONSOLE_GLPI |
| X-46 | Solução + aprovação do solicitante | **CONSOLE** E10 — [`evidence/e10-cycle-console.md`](./evidence/e10-cycle-console.md) |
| X-47 | Validação / etapas de aprovação | CONSOLE_GLPI |
| X-48 | Menção a usuário | **leitura IMPLEMENTADA** E14 (M-07); escrita `@` **BLOQUEADA** (M-23) |
| X-49 | Excluir chamado Novo sem ação | CONSOLE_GLPI — [`14`](./14-pagina-e-estados-do-chamado.md) P-10 |
| X-50 | Reabrir fechado | **CONSOLE** E10 — PATCH status 403 no Colaborador |
| X-51 | Pesquisa de satisfação | **CONSOLE** E10 — sem path HLAPI |

## 6. Matriz — abas do formulário central

Foto 1101 + doc Manage tickets.

| ID | Aba / peça | Destino |
|---|---|---|
| X-60 | Processamento (conversa) | IMPLEMENTADO no MFE (sem a moldura) |
| X-61 | Estatísticas (tempo, espera, SLA) | CONSOLE_GLPI |
| X-62 | Aprovações | CONSOLE_GLPI / H5 |
| X-63 | Base de conhecimento (ligar artigo) | CONSOLE_GLPI |
| X-64 | Itens | CONSOLE_GLPI |
| X-65 | Análise de impacto (diagrama) | CONSOLE_GLPI |
| X-66 | Custos | CONSOLE_GLPI |
| X-67 | Projetos / tarefas de projeto | CONSOLE_GLPI |
| X-68 | Mudanças | FORA — outro itemtype |
| X-69 | Problemas | FORA — outro itemtype |
| X-70 | Contratos | CONSOLE_GLPI |
| X-71 | Histórico | CONSOLE_GLPI |
| X-72 | Tudo / All Information | CONSOLE_GLPI |
| X-73 | Exportar PDF | CONSOLE_GLPI |
| X-74 | Paginação 2/15 entre chamados | CONSOLE_GLPI — a lista navega |
| X-75 | Salvar / excluir no rodapé | CONSOLE_GLPI |
| X-76 | Kanban, modelos da lista, contadores do parque | CONSOLE_GLPI — [`13`](./13-listagem-de-chamados.md) |

## 7. Matriz — lista e busca

Motor [Search](https://help.glpi-project.org/documentation/readme-1-1/search) + interface simplificada.

| ID | Capacidade GLPI | Destino |
|---|---|---|
| X-80 | Grade do solicitante (id, título, status, datas, categoria, técnico) | **IMPLEMENTADO**; datas absolutas / resolução / fechamento |
| X-81 | Busca no título e no conteúdo | **IMPLEMENTADO** (`q` OR content) |
| X-82 | Critérios AND/OR, multi-itemtype, lixeira, saved search, export, massa, mapa, multi-sort | **fatiado** — multi-itemtype/lixeira/saved search/export/massa/mapa = CONSOLE; critérios + multi-sort do **solicitante** = H13 ([`13`](./13-listagem-de-chamados.md) §3.5, G-50…G-56) |
| X-83 | Busca rápida global (ativos, usuários…) | CONSOLE_GLPI / outro módulo |
| X-84 | Colunas pessoais vs globais | **IMPLEMENTADO** catálogo MFE + prefs localStorage (não `front/ticket.php`) |

## 8. O que ainda **não** está fechado (BLOQUEADO / CONSOLE / residual)

Estes não abrem etapa sozinhos. Só deixam de ser lacuna invisível.

| ID | Capacidade | Por que importa ao solicitante | Estado |
|---|---|---|---|
| X-09 | Catálogo / Forms GLPI 11 | muita abertura real passa por formulário, não pelo ticket genérico | **FORA** (H-X1) |
| X-13 | Observador na abertura | o GLPI simplificado deixa adicionar watcher | **IMPLEMENTADO** `observer_ids` → TeamMember |
| X-28 | TTR visível | «até quando deve ser resolvido» | **IMPLEMENTADO** `sla_ttr` / `sla_tto` |
| X-29 | Vínculo (duplicata / filho) | o solicitante vê que o 1101 é duplicata do 1090 | **FORA** (H-X4); criar vínculo CONSOLE |
| X-46 | Aprovar solução | já era H5; permanece | **CONSOLE** (E10) |
| G-05 | Requerente na lista | detalhe tem; lista BFF não publica | ALVO_LEITURA residual |
| H12 / M-23 | upload / `@` escrita | HLAPI | BLOQUEADO |

Não promover X-09 a tela de catálogo sem endpoint. Não copiar Formcreator/plugin.

## 9. Hipóteses — vereditos (E6.S1, 21/09/2026)

| ID | Veredito | Evidência |
|---|---|---|
| H-X1 | **FORA** | OpenAPI 2.2 sem path Form/Service catalog; `GET /Form`, `/Assistance/Form`, `/ServiceCatalog` = 404. Perfil Colaborador `form: 0`. |
| H-X2 | **PROVEN** | `POST /Assistance/Ticket/{id}/TeamMember` com `{type: User, role: observer, id}` = **201**, sem requester/entity. Schema `Ticket.team[].role` existe; o POST de criação do Ticket não foi o caminho testado. |
| H-X3 | **PROVEN** | lista e detalhe trazem `date_solve`, `date_close`, `sla_ttr.{id,name}`, `sla_tto.{id,name}`. Não há campo `time_to_resolve`. |
| H-X4 | **FORA** | GET Ticket **não** inclui vínculos. Schema `Ticket_Ticket` existe; `GET /Assistance/Ticket_Ticket` = 404. |

`TicketSatisfaction` existe no schema e **não** tem path (404). Solution e Validation **têm** `GET/POST …/Timeline/Solution` e `…/Validation`, mas **não** substituem o aceitar/recusar solução do solicitante na HLAPI atual — ver [`evidence/e10-cycle-console.md`](./evidence/e10-cycle-console.md).

## 10. O que este arquivo não faz

- não substitui 12, 13, 14 nem o [`16`](./16-plano-paridade.md);
- não transforma CONSOLE em ALVO só porque a doc do GLPI lista a aba.

Ordem de código da paridade: [`16-plano-paridade.md`](./16-plano-paridade.md).
