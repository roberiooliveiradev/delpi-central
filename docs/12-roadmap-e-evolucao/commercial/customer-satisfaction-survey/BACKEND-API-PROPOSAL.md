# Pesquisa de satisfação — Padrão aprovado de backend e contratos REST/CAIO

> **Estado: PADRÃO DE ARQUITETURA ACEITO PELO SOLICITANTE em 10/11/2026; IMPLEMENTAÇÃO PENDENTE.** O aceite ratifica domínio, famílias REST, seis tools semânticas do CAIO e controles de acesso; **não** comprova deploy, contrato físico, testes, nem obriga a implementar toda operação opcional. Antes de cada frente, confirmar HEAD/branch/working tree e contratos reais.
>
> **Base de negócio:** [índice mestre](./REQUIREMENTS-INDEX.md), [decisões](./BUSINESS-DECISIONS.md), documento integral «Plano de Monitoramento da Satisfação dos Clientes — Delpi» nas fontes do projeto. **Código consultado:** `commercial_app/main.py`, `application/security/commercial_permissions.py`, `interface/http/routes/customer_routes.py`, `interface/mcp/semantic_bridge.py`, `application/caio/semantic_registry.py`, `interface/mcp/tool_bridge.py`, `migrations/V003__tasks_activities.sql`, `middleware/auth_middleware.py`; referências a conferir no HEAD de execução.

## Decisão registrada — aceite do padrão

**Decisão (10/11/2026, solicitante):** "perfeito, aceito o padrão". Este documento torna-se a **referência arquitetural aceita para implementação incremental**, vinculada ao [índice mestre](./REQUIREMENTS-INDEX.md). O conjunto de 20 rotas descreve operações candidatas, **não 20 obrigações de implementação imediata**. R09 (remoção de destinatário), nomes físicos, filtros sem fonte comprovada e demais detalhes técnicos dependem de inventário delimitado. O CAIO continuará com seis tools. **Aprovação do padrão ≠ execução nem homologação.**

## Produto completo em duas entregas — decisão de 11/11/2026

**Escopo obrigatório do produto:** entrega 1 = campanhas, seleção de empresas, convite por cópia, formulário público, respostas, histórico e indicadores oficiais; entrega 2 = consolidação para tratamento, classificação nas oito categorias, planos de ação (problema/cliente/causa/ação/responsável/prazo/status), acompanhamento, retorno, reavaliação e indicador de ações concluídas. O plano Word (§§1–10) é a referência de cobertura. **R17–R20 e `satisfaction_cases` são candidatos reservados para a entrega 2, não funcionalidades descartadas.** Seus contratos exatos devem ser verificados antes da segunda implementação, respeitando o owner e o Abstraction Gate; não criar nova permissão ou tool MCP por conveniência. O primeiro ciclo não implementa essas rotas.

## Escopo da primeira entrega — decisão de 11/11/2026

**Decisão do solicitante:** Priorizar campanha, destinatários, link para copiar/colar, formulário público, registro de respostas e indicadores históricos. **Não há envio de e-mail pelo Portal**; o próprio usuário copia o convite/link e envia por seu canal. **Não haverá desenvolvimento de planos de ação nem integração com `commercial.tasks` nesta entrega.** A permissão nova `commercial.marketing` será tratada durante o desenvolvimento; não criar outras permissões. A ampliação semântica do CAIO e os testes/homologação serão obrigatórios **a cada etapa**, sem tools MCP adicionais.

**Contrato técnico da primeira entrega:** [SURVEY-FIRST-RELEASE-CONTRACT.md](./SURVEY-FIRST-RELEASE-CONTRACT.md) — três tabelas, fluxo, formulário, indicadores e testes. Este recorte retira definitivamente o envio direto R11, mas **apenas adia** tabela/rotas de plano de ação R17–R20 para a segunda entrega, sem autorizar infraestrutura de tarefas antes do inventário pertinente. O restante do padrão arquitetural segue aceito. **Banco físico e rotas ainda não implementados.**

## 1. Ownership e segurança — contrato funcional

- **commercial-api**: autoridade das campanhas, convites, respostas, tratamentos e indicadores; dados próprios em schema/tabelas do domínio `commercial`. MFE nunca implementa autorização ou cálculos canônicos.
- **api-delpi/TOTVS**: fonte dos clientes e contatos consultados; reutilizar `GET /customers/search` e, onde aplicável, a composição já existente `GET /customers/{customer_code}/{customer_store}/contacts-bundle` do `commercial-api`. Não duplicar cadastro mestre.
- **Gestão privada**: **OR** entre `commercial.marketing` (novo código solicitado, ainda não implementado) e `commercial.manage` (código real já presente no backend e manifest). O termo `commercial.manager` foi usado na entrevista como referência ao perfil; **o código atual comprovado é `commercial.manage`**. Validar a definição/atribuição da nova permissão no Core + manifest + backend.
- **Resumo agregado**: `commercial.access` e perfis de gestão, mas resposta agregada **sem nomes, notas/comentários por cliente nem destinatários**, incluindo proteção contra reidentificação por filtro/conjunto pequeno.
- **Formulário externo**: apenas token opaco exclusivo por empresa/campanha, vinculado a convite e prazo. Não exige conta interna no Keycloak; **não** concede `commercial.access`, `commercial.marketing` ou `commercial.manage`. Apenas leitura do formulário daquele convite e envio final de uma única resposta. O middleware HTTP atual bloqueia rotas sem JWT por padrão; a exceção pública deve ser explícita e restrita a método, path e validação do token.
- **CAIO**: seis tools já existentes; o gate MCP atual exige **`commercial.access`** ao ingressar nas tools, inclusive antes do despacho por ação. Marketing/Manager deverão ter acesso ao produto ou esse gate deverá ser revisto com testes de não regressão. **Não ampliar a permissão global do CAIO sem revisar todos os consumidores/handlers**; a permissão de cada operação é rechecada no caso de uso oficial.
- **Retenção**: histórico das respostas e campanhas por tempo indeterminado como objetivo de negócio, preservando LGPD, controle de acesso, auditoria e eventual obrigação legal de exclusão/anonimização de dado pessoal.

## 2. Rotas REST de referência (com recorte atualizado no contrato da primeira entrega)

O prefixo abaixo refere-se a paths **internos** da `commercial-api` (`/satisfaction-surveys`), não a novas rotas da `api-delpi` nem ao path externo do gateway. Métodos, payloads e schemas precisam passar pelo inventário bounded antes de implantação.

| ID | Método e rota | Função | Controle |
|---|---|---|---|
| R01 | `GET /satisfaction-surveys/questionnaire` | Leitura do questionário oficial fixo (15 perguntas), sem CRUD do texto | Gestão |
| R02 | `GET /satisfaction-surveys/campaigns` | Listar campanhas e janelas | Gestão |
| R03 | `POST /satisfaction-surveys/campaigns` | Criar campanha com datas configuráveis | Gestão |
| R04 | `GET /satisfaction-surveys/campaigns/{campaign_id}` | Detalhe/configuração | Gestão |
| R05 | `PATCH /satisfaction-surveys/campaigns/{campaign_id}` | Editar datas e metadados permitidos, com auditoria | Gestão |
| R06 | `GET /satisfaction-surveys/campaigns/{campaign_id}/recipients` | Empresas selecionadas; status pendente/respondido | Gestão |
| R07 | `POST /satisfaction-surveys/campaigns/{campaign_id}/recipients` | Incluir empresa(s) do TOTVS na campanha e seu link único | Gestão |
| R08 | `PATCH /satisfaction-surveys/campaigns/{campaign_id}/recipients/{recipient_id}` | Ajustar contato/e-mail do convite, sem gravar no ERP | Gestão |
| R09 | `DELETE /satisfaction-surveys/campaigns/{campaign_id}/recipients/{recipient_id}` | Desvincular **somente antes de envio e resposta**, mediante regra auditada | Gestão; exclusão limitada |
| R10 | `GET /satisfaction-surveys/campaigns/{campaign_id}/recipients/{recipient_id}/link` | Recuperar o **mesmo** link copiável, somente para autorizado | Gestão; retorno sensível |
| R11 | ~~`POST /satisfaction-surveys/campaigns/{campaign_id}/recipients/{recipient_id}/send-email`~~ | **RETIRADA da entrega e do padrão de envio**; usuário copia o convite/link e envia externamente | Não implementar |
| R12 | `GET /satisfaction-surveys/campaigns/{campaign_id}/responses` | Tabela de respostas por empresa e campanha | Gestão |
| R13 | `GET /satisfaction-surveys/responses/{response_id}` | Notas e comentários individuais, somente interna | Gestão |
| R14 | `GET /public/satisfaction-surveys/{token}` | Formulário externo e estado da janela | Token de convite, sem JWT de colaborador |
| R15 | `POST /public/satisfaction-surveys/{token}/response` | Uma única submissão final e atômica; sem edição posterior | Token de convite e validação no servidor |
| R16 | `GET /satisfaction-surveys/results` | IGS, NPS, taxa, dimensões, percentuais e comparação histórica com filtros permitidos | `commercial.access` ou Gestão; somente agregados |
| R17 | `GET /satisfaction-surveys/campaigns/{campaign_id}/cases` | Lista dos problemas e planos de ação da campanha | **ENTREGA 2 PLANEJADA** — não implementar neste ciclo |
| R18 | `POST /satisfaction-surveys/campaigns/{campaign_id}/cases` | Abrir tratamento de resposta/comentário relevante | **ENTREGA 2 PLANEJADA** — não implementar neste ciclo |
| R19 | `GET /satisfaction-surveys/cases/{case_id}` | Detalhe do problema, ação e retorno | **ENTREGA 2 PLANEJADA** — não implementar neste ciclo |
| R20 | `PATCH /satisfaction-surveys/cases/{case_id}` | Categoria, causa, ação, responsável, prazo, status, retorno, reavaliação | **ENTREGA 2 PLANEJADA** — não implementar neste ciclo |

**Não criar por padrão:** `POST/PUT/PATCH/DELETE` de perguntas (questionário fixo), `PATCH/DELETE` de respostas definitivas (imutabilidade e histórico), `DELETE` irrestrito de campanhas/conclusões, endpoint para cada indicador, disparo automático em WhatsApp/Teams, fluxo separado de cadastro TOTVS ou rotas públicas de resultados individuais. Campanhas abrem/fecham **pela comparação das datas no backend**, sem exigir scheduler para mudar flag; a janela de corte e fuso serão definidos no contrato técnico. O R09 é **proposta condicionada** à necessidade de corrigir público antes de qualquer convite, não autorização para apagar evidência histórica.

**R16:** um endpoint agregado com parâmetros tipados `campaign_id`, `segment`, `seller`, `region`, `relationship_period`, `billing_band`, `strategic` e `compare=previous` **somente se houver origem oficial para cada filtro**. O backend recalcula denominadores corretos e recusa filtros que exponham um cliente individual aos usuários com apenas `commercial.access`. Internamente, Marketing/Manager usam R12–R13 para respostas detalhadas; não transformar R16 em endpoint que retorne rows brutas.

## 3. Persistência mínima proposta

**Base da primeira entrega: três tabelas próprias**, conforme [contrato fechado](./SURVEY-FIRST-RELEASE-CONTRACT.md); a quarta entidade está **reservada para a entrega 2**, sem implementação na primeira. A lista histórica anterior avaliava quatro agregados/tabelas no schema comercial (nomes sujeitos ao padrão de migrations): `satisfaction_campaigns`, `satisfaction_recipients`, `satisfaction_responses` e `satisfaction_cases`.

| Tabela candidata | Responsabilidade | Invariantes principais |
|---|---|---|
| `campaigns` | Identidade, nome, início/fim, questionário oficial/versionamento de referência, autor e auditoria | Configuração por campanha; abertura/fecho pela data |
| `recipients` | Par **cliente TOTVS (código+loja)**, campanha, e-mail ajustável, status de envio, link/token protegido | `UNIQUE(campaign_id, customer_code, customer_store)`; link estável por empresa/campanha |
| `responses` | Uma submissão definitiva por recipient, notas IGS/NPS e 10 dimensões, três respostas abertas, timestamp, versão do formulário | `UNIQUE(recipient_id)` + verificação transacional de campanha e token; sem update/delete operacional |
| `cases` | **Entrega 2 obrigatória** — classificação de problemas, ações, retornos e reavaliação previstos no Word | Não criar na entrega 1; planejar e implementar na entrega 2, após verificar isolamento/contratos |

**Alternativas sujeitas ao Abstraction Gate:** respostas dimensionais podem usar campos tipados ou tabela de itens, conforme consulta e migração comprovadas; não assumir JSONB sem medir o contrato de indicadores. Ações podem integrar a `commercial.tasks` existente **somente** se os acessos comuns a tarefas não expuserem problemas, notas e comentários restritos. A migração V003 já prevê assignee, due, status e vínculo com cliente/entidade, mas suas rotas atuais são acessíveis por `commercial.access`. Caso o isolamento seja mais simples com `cases`, não criar um segundo gerenciador genérico de tarefas.

**Link e envio:** token de alta entropia com verificador seguro no servidor; se o mesmo URL tiver de ser mostrado novamente, usar armazenamento recuperável protegido ou outra solução determinística que preserve o mesmo link, não apenas um hash irrecuperável. Nunca registrar token bruto em logs. Envio manual idempotente e com histórico de tentativas; reutilizar outbox/serviço de e-mail oficial **se confirmado pelo inventário**, sem afirmar entregabilidade só porque API aceitou pedido.

## 4. Ampliação do CAIO sem tools novas

A ampliação é **semântica**, não de superfície MCP: `get_context` anuncia novas entidades/ações, `read` consulta fatos, `analyze` compõe cálculos retornados pelos **mesmos use cases** de R16, `execute` realiza writes autorizados, `delete` só quando uma exclusão legítima for necessária (proposta selada prepare→commit), `knowledge` pode ganhar orientação versionada sem inventar fato operacional.

| Tool existente | Novas entidades / ações sugeridas | Origem |
|---|---|---|
| `read` | `satisfaction_campaign.list/get/questionnaire`, `satisfaction_recipient.list/link`, `satisfaction_response.list/get`, `satisfaction_case.list/get` | Casos de uso oficiais R01–R13/R17/R19 |
| `analyze` | `analysis_type=satisfaction.summary` ou `satisfaction.trend` (se distinção justificar), com filtros tipados e dados `OBSERVED/CALCULATED` | Mesmo serviço de indicadores de R16; CAIO **não recalcula** |
| `execute` | `satisfaction_campaign.create/update`, `satisfaction_recipient.add/update/send_email`, `satisfaction_case.create/update` | Mesmos casos de uso das rotas REST; permissão Gestão e auditoria |
| `delete` | `satisfaction_recipient.delete` apenas se R09 for homologado, antes do envio | Mesmo owner, proposta selada `prepare → commit` |
| `get_context` / `knowledge` | Descobrir novos contratos, filtros, campos, status de implementação e orientação aprovada | Catálogo semântico existente; sem tool nova |

**Não expor R14/R15 via CAIO:** o cliente externo responde com token, não por uma ação executada por agente autenticado em seu nome. Não retornar links secretos, respostas detalhadas ou nomes de clientes a um principal apenas `commercial.access`. O catálogo é descritivo e **não é uma autorização**.

Arquivos prováveis da futura ampliação (a confirmar no HEAD da execução): `application/caio/semantic_registry.py`, `interface/mcp/semantic_bridge.py`, dispatch/paridade, `tests/test_caio_parity.py`, `tests/test_caio_mcp.py`. Manter **seis** tools; registrar capabilities como `planned`/não implementadas até handlers autorizados, testes e runtime comprovados.

## 5. Entrega limitada e critérios de verificação

**Sequência aprovada para a primeira entrega:** (A) banco, campanhas, questionário fixo e destinatários; (B) link copiável e formulário público com submissão definitiva; (C) agregações, filtros e histórico; **CAIO e testes em cada etapa**. (D) classificação, planos de ação, retorno/reavaliação e indicador de conclusão **integram obrigatoriamente a entrega 2**, não o primeiro ciclo. Detalhes no [contrato da primeira entrega](./SURVEY-FIRST-RELEASE-CONTRACT.md).

Para cada frente: reancorar HEAD, branch, working tree; consultar owners/contratos e consumidores; diferenciar dados públicos/agregados/restritos; definir teste de acesso positivo/negativo, teste de invariantes e leitura posterior do resultado; menor diff, sem refactor lateral.

**Testes indispensáveis:** acesso `marketing`/ `manage` e negação a `access` para dados individuais; CAIO com ator humano e sem elevação; token inexistente/expirado/compartilhado; POST simultâneo duplicado (apenas uma resposta); datas antes/durante/depois; recópia do mesmo link; recópia e compartilhamento apenas manual; IGS/NPS/“não se aplica”; conjunto pequeno com filtro; ausência de detalhes privados em endpoints agregados e logs; auditoria; operação de e-mail sem falsa confirmação de entrega; paridade REST/MCP e status honesto no catálogo.

**Gaps a fechar no inventário bounded:** disponibilidade e autorização para cadastro/filtros TOTVS; estrutura de migration posterior à vigente; status simples das ações; fuso e corte de datas; retenção de dados pessoais/LGPD; proteção dos tokens; compatibilidade de `commercial.marketing` com a entrada no CAIO. Tais detalhes **não reabrem** as decisões principais nem justificam a criação de novas abstrações sem evidência.
