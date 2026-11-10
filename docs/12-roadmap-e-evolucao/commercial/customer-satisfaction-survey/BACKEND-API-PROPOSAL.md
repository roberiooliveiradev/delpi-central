# Pesquisa de satisfação — Proposta de backend e contratos REST/CAIO

> **Estado: PROPOSTO / NÃO APROVADO PARA IMPLEMENTAÇÃO.** Análise de 10/11/2026; branch consultada: \`main\`, HEAD observado ao iniciar: \`71ae3e9605496f6e6a986e9daa1d3e7c265f624f\`. Antes de implementar, reancorar em HEAD/branch/working tree reais e contratos atuais. Nenhuma rota deste documento está comprovadamente implementada.
>
> **Base de negócio:** [índice mestre](./REQUIREMENTS-INDEX.md), [decisões](./BUSINESS-DECISIONS.md), documento integral «Plano de Monitoramento da Satisfação dos Clientes — Delpi» nas fontes do projeto. **Código consultado:** \`commercial_app/main.py\`, \`application/security/commercial_permissions.py\`, \`interface/http/routes/customer_routes.py\`, \`interface/mcp/semantic_bridge.py\`, \`application/caio/semantic_registry.py\`, \`interface/mcp/tool_bridge.py\`, \`migrations/V003__tasks_activities.sql\`, \`middleware/auth_middleware.py\`; referências a conferir no HEAD de execução.

## 1. Ownership e segurança — contrato funcional

- **commercial-api**: autoridade das campanhas, convites, respostas, tratamentos e indicadores; dados próprios em schema/tabelas do domínio \`commercial\`. MFE nunca implementa autorização ou cálculos canônicos.
- **api-delpi/TOTVS**: fonte dos clientes e contatos consultados; reutilizar \`GET /customers/search\` e, onde aplicável, a composição já existente \`GET /customers/{customer_code}/{customer_store}/contacts-bundle\` do \`commercial-api\`. Não duplicar cadastro mestre.
- **Gestão privada**: **OR** entre \`commercial.marketing\` (novo código solicitado, ainda não implementado) e \`commercial.manage\` (código real já presente no backend e manifest). O termo \`commercial.manager\` foi usado na entrevista como referência ao perfil; **o código atual comprovado é \`commercial.manage\`**. Validar a definição/atribuição da nova permissão no Core + manifest + backend.
- **Resumo agregado**: \`commercial.access\` e perfis de gestão, mas resposta agregada **sem nomes, notas/comentários por cliente nem destinatários**, incluindo proteção contra reidentificação por filtro/conjunto pequeno.
- **Formulário externo**: apenas token opaco exclusivo por empresa/campanha, vinculado a convite e prazo. Não exige conta interna no Keycloak; **não** concede \`commercial.access\`, \`commercial.marketing\` ou \`commercial.manage\`. Apenas leitura do formulário daquele convite e envio final de uma única resposta. O middleware HTTP atual bloqueia rotas sem JWT por padrão; a exceção pública deve ser explícita e restrita a método, path e validação do token.
- **CAIO**: seis tools já existentes; o gate MCP atual exige **\`commercial.access\`** ao ingressar nas tools, inclusive antes do despacho por ação. Marketing/Manager deverão ter acesso ao produto ou esse gate deverá ser revisto com testes de não regressão. **Não ampliar a permissão global do CAIO sem revisar todos os consumidores/handlers**; a permissão de cada operação é rechecada no caso de uso oficial.
- **Retenção**: histórico das respostas e campanhas por tempo indeterminado como objetivo de negócio, preservando LGPD, controle de acesso, auditoria e eventual obrigação legal de exclusão/anonimização de dado pessoal.

## 2. Rotas REST propostas

O prefixo abaixo refere-se a paths **internos** da \`commercial-api\` (\`/satisfaction-surveys\`), não a novas rotas da \`api-delpi\` nem ao path externo do gateway. Métodos, payloads e schemas precisam passar pelo inventário bounded antes de implantação.

| ID | Método e rota | Função | Controle |
|---|---|---|---|
| R01 | \`GET /satisfaction-surveys/questionnaire\` | Leitura do questionário oficial fixo (15 perguntas), sem CRUD do texto | Gestão |
| R02 | \`GET /satisfaction-surveys/campaigns\` | Listar campanhas e janelas | Gestão |
| R03 | \`POST /satisfaction-surveys/campaigns\` | Criar campanha com datas configuráveis | Gestão |
| R04 | \`GET /satisfaction-surveys/campaigns/{campaign_id}\` | Detalhe/configuração | Gestão |
| R05 | \`PATCH /satisfaction-surveys/campaigns/{campaign_id}\` | Editar datas e metadados permitidos, com auditoria | Gestão |
| R06 | \`GET /satisfaction-surveys/campaigns/{campaign_id}/recipients\` | Empresas selecionadas; status pendente/respondido | Gestão |
| R07 | \`POST /satisfaction-surveys/campaigns/{campaign_id}/recipients\` | Incluir empresa(s) do TOTVS na campanha e seu link único | Gestão |
| R08 | \`PATCH /satisfaction-surveys/campaigns/{campaign_id}/recipients/{recipient_id}\` | Ajustar contato/e-mail do convite, sem gravar no ERP | Gestão |
| R09 | \`DELETE /satisfaction-surveys/campaigns/{campaign_id}/recipients/{recipient_id}\` | Desvincular **somente antes de envio e resposta**, mediante regra auditada | Gestão; exclusão limitada |
| R10 | \`GET /satisfaction-surveys/campaigns/{campaign_id}/recipients/{recipient_id}/link\` | Recuperar o **mesmo** link copiável, somente para autorizado | Gestão; retorno sensível |
| R11 | \`POST /satisfaction-surveys/campaigns/{campaign_id}/recipients/{recipient_id}/send-email\` | Envio/reenvio manual do mesmo convite, sem job de lembretes | Gestão; idempotência/auditoria |
| R12 | \`GET /satisfaction-surveys/campaigns/{campaign_id}/responses\` | Tabela de respostas por empresa e campanha | Gestão |
| R13 | \`GET /satisfaction-surveys/responses/{response_id}\` | Notas e comentários individuais, somente interna | Gestão |
| R14 | \`GET /public/satisfaction-surveys/{token}\` | Formulário externo e estado da janela | Token de convite, sem JWT de colaborador |
| R15 | \`POST /public/satisfaction-surveys/{token}/response\` | Uma única submissão final e atômica; sem edição posterior | Token de convite e validação no servidor |
| R16 | \`GET /satisfaction-surveys/results\` | IGS, NPS, taxa, dimensões, percentuais e comparação histórica com filtros permitidos | \`commercial.access\` ou Gestão; somente agregados |
| R17 | \`GET /satisfaction-surveys/campaigns/{campaign_id}/cases\` | Lista dos problemas e planos de ação da campanha | Gestão |
| R18 | \`POST /satisfaction-surveys/campaigns/{campaign_id}/cases\` | Abrir tratamento de resposta/comentário relevante | Gestão |
| R19 | \`GET /satisfaction-surveys/cases/{case_id}\` | Detalhe do problema, ação e retorno | Gestão |
| R20 | \`PATCH /satisfaction-surveys/cases/{case_id}\` | Categoria, causa, ação, responsável, prazo, status, retorno, reavaliação | Gestão |

**Não criar por padrão:** \`POST/PUT/PATCH/DELETE\` de perguntas (questionário fixo), \`PATCH/DELETE\` de respostas definitivas (imutabilidade e histórico), \`DELETE\` irrestrito de campanhas/conclusões, endpoint para cada indicador, disparo automático em WhatsApp/Teams, fluxo separado de cadastro TOTVS ou rotas públicas de resultados individuais. Campanhas abrem/fecham **pela comparação das datas no backend**, sem exigir scheduler para mudar flag; a janela de corte e fuso serão definidos no contrato técnico. O R09 é **proposta condicionada** à necessidade de corrigir público antes de qualquer convite, não autorização para apagar evidência histórica.

**R16:** um endpoint agregado com parâmetros tipados \`campaign_id\`, \`segment\`, \`seller\`, \`region\`, \`relationship_period\`, \`billing_band\`, \`strategic\` e \`compare=previous\` **somente se houver origem oficial para cada filtro**. O backend recalcula denominadores corretos e recusa filtros que exponham um cliente individual aos usuários com apenas \`commercial.access\`. Internamente, Marketing/Manager usam R12–R13 para respostas detalhadas; não transformar R16 em endpoint que retorne rows brutas.

## 3. Persistência mínima proposta

Começar avaliando **quatro agregados/tabelas** no schema comercial (nomes sujeitos ao padrão de migrations): \`satisfaction_campaigns\`, \`satisfaction_recipients\`, \`satisfaction_responses\` e \`satisfaction_cases\`.

| Tabela candidata | Responsabilidade | Invariantes principais |
|---|---|---|
| \`campaigns\` | Identidade, nome, início/fim, questionário oficial/versionamento de referência, autor e auditoria | Configuração por campanha; abertura/fecho pela data |
| \`recipients\` | Par **cliente TOTVS (código+loja)**, campanha, e-mail ajustável, status de envio, link/token protegido | \`UNIQUE(campaign_id, customer_code, customer_store)\`; link estável por empresa/campanha |
| \`responses\` | Uma submissão definitiva por recipient, notas IGS/NPS e 10 dimensões, três respostas abertas, timestamp, versão do formulário | \`UNIQUE(recipient_id)\` + verificação transacional de campanha e token; sem update/delete operacional |
| \`cases\` | Classificação (8 categorias), problema, cliente/resposta vinculada, causa, ação, responsável, prazo, status, retorno/reavaliação | Histórico auditável; somente perfis gestores; evitar CRUD de workflows genéricos |

**Alternativas sujeitas ao Abstraction Gate:** respostas dimensionais podem usar campos tipados ou tabela de itens, conforme consulta e migração comprovadas; não assumir JSONB sem medir o contrato de indicadores. Ações podem integrar a \`commercial.tasks\` existente **somente** se os acessos comuns a tarefas não expuserem problemas, notas e comentários restritos. A migração V003 já prevê assignee, due, status e vínculo com cliente/entidade, mas suas rotas atuais são acessíveis por \`commercial.access\`. Caso o isolamento seja mais simples com \`cases\`, não criar um segundo gerenciador genérico de tarefas.

**Link e envio:** token de alta entropia com verificador seguro no servidor; se o mesmo URL tiver de ser mostrado novamente, usar armazenamento recuperável protegido ou outra solução determinística que preserve o mesmo link, não apenas um hash irrecuperável. Nunca registrar token bruto em logs. Envio manual idempotente e com histórico de tentativas; reutilizar outbox/serviço de e-mail oficial **se confirmado pelo inventário**, sem afirmar entregabilidade só porque API aceitou pedido.

## 4. Ampliação do CAIO sem tools novas

A ampliação é **semântica**, não de superfície MCP: \`get_context\` anuncia novas entidades/ações, \`read\` consulta fatos, \`analyze\` compõe cálculos retornados pelos **mesmos use cases** de R16, \`execute\` realiza writes autorizados, \`delete\` só quando uma exclusão legítima for necessária (proposta selada prepare→commit), \`knowledge\` pode ganhar orientação versionada sem inventar fato operacional.

| Tool existente | Novas entidades / ações sugeridas | Origem |
|---|---|---|
| \`read\` | \`satisfaction_campaign.list/get/questionnaire\`, \`satisfaction_recipient.list/link\`, \`satisfaction_response.list/get\`, \`satisfaction_case.list/get\` | Casos de uso oficiais R01–R13/R17/R19 |
| \`analyze\` | \`analysis_type=satisfaction.summary\` ou \`satisfaction.trend\` (se distinção justificar), com filtros tipados e dados \`OBSERVED/CALCULATED\` | Mesmo serviço de indicadores de R16; CAIO **não recalcula** |
| \`execute\` | \`satisfaction_campaign.create/update\`, \`satisfaction_recipient.add/update/send_email\`, \`satisfaction_case.create/update\` | Mesmos casos de uso das rotas REST; permissão Gestão e auditoria |
| \`delete\` | \`satisfaction_recipient.delete\` apenas se R09 for homologado, antes do envio | Mesmo owner, proposta selada \`prepare → commit\` |
| \`get_context\` / \`knowledge\` | Descobrir novos contratos, filtros, campos, status de implementação e orientação aprovada | Catálogo semântico existente; sem tool nova |

**Não expor R14/R15 via CAIO:** o cliente externo responde com token, não por uma ação executada por agente autenticado em seu nome. Não retornar links secretos, respostas detalhadas ou nomes de clientes a um principal apenas \`commercial.access\`. O catálogo é descritivo e **não é uma autorização**.

Arquivos prováveis da futura ampliação (a confirmar no HEAD da execução): \`application/caio/semantic_registry.py\`, \`interface/mcp/semantic_bridge.py\`, dispatch/paridade, \`tests/test_caio_parity.py\`, \`tests/test_caio_mcp.py\`. Manter **seis** tools; registrar capabilities como \`planned\`/não implementadas até handlers autorizados, testes e runtime comprovados.

## 5. Entrega limitada e critérios de verificação

**Sequência proposta, sem novos documentos obrigatórios:** (A) base de campanhas, questionário fixo e destinatários; (B) link público + submissão definitiva; (C) agregações e filtros; (D) tratamento/retorno; (E) paridade CAIO em cada frente, e não só no final.

Para cada frente: reancorar HEAD, branch, working tree; consultar owners/contratos e consumidores; diferenciar dados públicos/agregados/restritos; definir teste de acesso positivo/negativo, teste de invariantes e leitura posterior do resultado; menor diff, sem refactor lateral.

**Testes indispensáveis:** acesso \`marketing\`/ \`manage\` e negação a \`access\` para dados individuais; CAIO com ator humano e sem elevação; token inexistente/expirado/compartilhado; POST simultâneo duplicado (apenas uma resposta); datas antes/durante/depois; recópia do mesmo link; reenvio apenas manual; IGS/NPS/“não se aplica”; conjunto pequeno com filtro; ausência de detalhes privados em endpoints agregados e logs; auditoria; operação de e-mail sem falsa confirmação de entrega; paridade REST/MCP e status honesto no catálogo.

**Gaps a fechar no inventário bounded:** disponibilidade e autorização para cadastro/filtros TOTVS; serviço de e-mail e outbox; estrutura de migration posterior à vigente; status simples das ações; fuso e corte de datas; retenção de dados pessoais/LGPD; proteção dos tokens; compatibilidade de \`commercial.marketing\` com a entrada no CAIO. Tais detalhes **não reabrem** as decisões principais nem justificam a criação de novas abstrações sem evidência.
