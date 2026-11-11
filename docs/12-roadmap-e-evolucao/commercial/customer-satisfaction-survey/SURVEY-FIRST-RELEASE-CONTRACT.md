# Contrato da primeira entrega — pesquisa de satisfação

> **Estado:** planejamento técnico consolidado em 11/11/2026, segundo orientação do solicitante. **NÃO IMPLEMENTADO/NÃO MIGRADO.** Este arquivo especifica a primeira entrega sem depender de novas entrevistas. É subordinado ao [índice mestre](./REQUIREMENTS-INDEX.md), às [decisões de negócio](./BUSINESS-DECISIONS.md) e ao [padrão REST/CAIO aceito](./BACKEND-API-PROPOSAL.md).
>
> **Produto completo em duas entregas:** a primeira implementa a pesquisa e seus indicadores; a segunda implementará classificação, planos de ação, acompanhamento, retorno/reavaliação e percentual de ações concluídas, conforme o Word. A exclusão nesta especificação **não remove obrigações da segunda entrega**.
>\n> **Escopo aprovado para a primeira entrega:** campanhas, escolha de empresas TOTVS, convites por **copiar/colar**, formulário externo, uma resposta definitiva por empresa/campanha, consultas privadas das respostas e indicadores oficiais com filtros aplicáveis. **Fora da primeira entrega:** envio de e-mail pela aplicação, lembretes automatizados, gestão de problemas/planos de ação/retornos, CRUD de perguntas, edição de respostas já submetidas e novas tools MCP.

## 1. Autoridades e formato físico

- O banco é PostgreSQL, com esquema `commercial` e migrações versionadas em `commercial-api/migrations/VNNN__*.sql` (evidência: `migrations_runner.py`, `V019__interaction_rooms.sql`, `V023__seller_customer_center.sql`). A versão seguinte **deve ser escolhida no HEAD de implementação**, não fixada aqui.
- `commercial-api` é a única autoridade de escrita e leitura dos dados da pesquisa. `api-delpi` permanece somente para leitura de clientes/atributos oficiais do TOTVS. Identidade do cliente: `customer_code` **e** `customer_store`; não criar tabela mestre de clientes.
- **Três tabelas próprias** são suficientes para a primeira entrega. Não criar `satisfaction_cases`, tabelas de envios de e-mail, tarefas, notificações ou logs de disparos. Auditoria de mutações deve reutilizar infraestrutura existente quando comprovada; se insuficiente, acrescentar mecanismo mínimo na frente de segurança, sem criar uma entidade de negócio.
- Contratos e nomes abaixo são **proposta técnica fechada para desenvolvimento**, mas ainda não são prova de que SQL tenha sido aplicado. Escolher nomes definitivos seguindo padrão real do projeto durante a migração, sem alterar semântica/invariantes.

### 1.1 `commercial.satisfaction_campaigns`

| Coluna | Tipo sugerido | Contrato |
|---|---|---|
| `id` | UUID PK | Gerado pelo backend |
| `name` | TEXT NOT NULL | Nome que identifica campanha |
| `starts_at`, `ends_at` | TIMESTAMPTZ NOT NULL | `starts_at < ends_at`; janela inclusiva no início e exclusiva no fim; base UTC no armazenamento, fuso de exibição configurado na interface |
| `questionnaire_version` | TEXT NOT NULL | Identificador da versão fixa das 15 perguntas; mesmo conjunto entre campanhas |
| `created_by_user_id` | TEXT NOT NULL | Ator autenticado |
| `created_at`, `updated_at` | TIMESTAMPTZ NOT NULL | Auditoria básica |
| `version` | INT NOT NULL DEFAULT 1 | Concorrência nas edições |

**Índices:** PK e índice para listagem por `starts_at DESC`. **Sem coluna de status mutável obrigatória**: abertura/fechamento são derivados do relógio e da janela de datas. Sem exclusão de campanhas na primeira entrega. Alteração de datas é proibida quando puder invalidar respostas já recebidas; regra precisa ser verificada em testes do caso de uso.

### 1.2 `commercial.satisfaction_recipients`

| Coluna | Tipo sugerido | Contrato |
|---|---|---|
| `id` | UUID PK | Identidade do convite |
| `campaign_id` | UUID NOT NULL FK | `satisfaction_campaigns(id)`, sem exclusão em cascata |
| `customer_code`, `customer_store` | TEXT NOT NULL | Empresa e loja oficiais do TOTVS |
| `customer_name_snapshot` | TEXT | Nome exibido no momento da seleção, sem substituir cadastro TOTVS |
| `contact_name`, `contact_email` | TEXT nullable | Dados de contato opcionais, ajustáveis somente neste convite; não presumir envio por API nem gravar na origem |
| `token_hash` | TEXT NOT NULL UNIQUE | Derivação segura do token opaco, usada na autenticação do formulário |
| `token_ciphertext` | TEXT NOT NULL | Recuperação **protegida** do mesmo link para cópia manual; chave fora do banco; valor bruto nunca em logs |
| `created_by_user_id`, `created_at`, `updated_at` | TEXT / TIMESTAMPTZ | Rastreabilidade de criação e edição |
| `version` | INT NOT NULL DEFAULT 1 | Concorrência |
 
**Restrições:** `UNIQUE(campaign_id, customer_code, customer_store)`; `UNIQUE(token_hash)`; índices por campanha e por token_hash. O identificador do link **não muda** quando se modifica o e-mail ou se copia novamente o convite. Não incluir `sent_at`, `delivery_status` ou `reminder_count`, pois **não existe envio controlado pela aplicação**; o sistema sabe apenas se houve resposta, não se o usuário de fato entregou o convite. A coluna `contact_email` não é obrigatória para copiar um link.

**Retirada de participante (R09):** não é necessária na entrega mínima; a operação permanece `DEFERRED` até existir caso de uso e regra segura antes do envio/da resposta. Não apagar participantes com resposta.

### 1.3 `commercial.satisfaction_responses`

| Coluna | Tipo sugerido | Contrato |
|---|---|---|
| `id` | UUID PK | Resposta definitiva |
| `recipient_id` | UUID NOT NULL UNIQUE FK | Uma resposta por convite/empresa/campanha; sem cascata |
| `overall_score` | SMALLINT NOT NULL | 1–5, `CHECK` |
| `recommendation_score` | SMALLINT NOT NULL | 0–10, `CHECK` |
| `dimensions` | JSONB NOT NULL | Objeto de **10 chaves canônicas fixas**; cada valor inteiro 1–5 ou `null` **exclusivamente quando a empresa selecionou “Não se aplica”**; todas as dez chaves presentes e cada dimensão explicitamente selecionada antes da submissão, sem omissões; validação forte no caso de uso e versionamento do contrato; sem campos livres |
| `strengths`, `improvements`, `unmet_needs` | TEXT nullable | Três respostas abertas opcionais |
| `questionnaire_version` | TEXT NOT NULL | Mesma versão que o convite/campanha |
| `submitted_at` | TIMESTAMPTZ NOT NULL | Instante definitivo da submissão |

**Regras imutáveis:** `UNIQUE(recipient_id)` no banco + transação para verificar token, empresa, campanha e janela ao enviar. Concorrência simultânea resulta em **uma** resposta; outra tentativa retorna conflito/estado `already_submitted`, nunca sobrescreve. Não disponibilizar `PATCH/DELETE` de resposta. Evitar guardar nome ou e-mail da pessoa física respondente; o vínculo operacional é a empresa convidada. Não criar tabela própria de `answers` enquanto o questionário permanecer fixo.

**Validação canônica de seleção (Q08, 11/11/2026):** O formulário exige em todas as dez dimensões uma escolha explícita entre nota 1–5 e “Não se aplica”. O cliente pode revisar antes de confirmar. A `commercial-api` valida presença das dez chaves e rejeita omissões, valores indefinidos ou tentativas de deixar a questão em branco; `null` significa somente a opção “Não se aplica” efetivamente selecionada. Payload serializado com `null` deve ser produzido apenas a partir dessa escolha, não como default de campo intocado. As duas notas gerais continuam obrigatórias, os três textos opcionais. Reforçar testes de tentativa de envio parcial/omissões e de `null` selecionado. Trata-se de **contrato de implementação, não de comportamento já implantado**.

**Chaves canônicas de `dimensions` (correspondentes às dez dimensões do plano):** `quality`, `delivery_deadline`, `service`, `agility`, `communication`, `technical_support`, `commercial_support`, `flexibility`, `reliability`, `partnership`. Os textos **literais** e a ordem foram transcritos do Word e mapeados na seção **1.4** abaixo; a tradução técnica das chaves não altera as perguntas.

### 1.4 Catálogo textual canônico das 15 perguntas — conferência com o Word em 11/11/2026

**Fonte literal:** arquivo original *Plano de Monitoramento da Satisfação dos Clientes — Delpi.docx*, seção **3, tabela “Dimensão | Pergunta”** (10 perguntas), seções **4 e 5** (satisfação e recomendação) e seção **6** (3 abertas). A transcrição abaixo preserva pontuação, acentuação e ordem da fonte. Os rótulos curtos são da coluna “Dimensão” ou nomes de apresentação, **não substituem a pergunta completa**. Nenhuma pergunta foi inventada. A escala 1–5 da seção 3 é: **1 = Muito insatisfeito; 2 = Insatisfeito; 3 = Neutro; 4 = Satisfeito; 5 = Muito satisfeito**.

| Ordem | Chave de payload/armazenamento | Título de apresentação | Pergunta literal do Word | Resposta permitida |
|---|---|---|---|---|
| 01 | `quality` | Qualidade | Como você avalia a qualidade dos produtos fornecidos pela Delpi? | 1–5 ou “Não se aplica” (seleção obrigatória; Q08) |
| 02 | `delivery_deadline` | Prazo de entrega | Como você avalia o cumprimento dos prazos acordados? | 1–5 ou “Não se aplica” (seleção obrigatória; Q08) |
| 03 | `service` | Atendimento | Como você avalia o atendimento da equipe Delpi? | 1–5 ou “Não se aplica” (seleção obrigatória; Q08) |
| 04 | `agility` | Agilidade | Como você avalia a velocidade de resposta às suas solicitações? | 1–5 ou “Não se aplica” (seleção obrigatória; Q08) |
| 05 | `communication` | Comunicação | Como você avalia a clareza e efetividade da comunicação? | 1–5 ou “Não se aplica” (seleção obrigatória; Q08) |
| 06 | `technical_support` | Suporte técnico | Como você avalia o suporte técnico oferecido pela Delpi? | 1–5 ou “Não se aplica” (seleção obrigatória; Q08) |
| 07 | `commercial_support` | Suporte comercial | Como você avalia o suporte comercial oferecido pela Delpi? | 1–5 ou “Não se aplica” (seleção obrigatória; Q08) |
| 08 | `flexibility` | Flexibilidade | Como você avalia a capacidade da Delpi de atender necessidades específicas? | 1–5 ou “Não se aplica” (seleção obrigatória; Q08) |
| 09 | `reliability` | Confiabilidade | Quanto você considera a Delpi confiável como fornecedora? | 1–5 ou “Não se aplica” (seleção obrigatória; Q08) |
| 10 | `partnership` | Parceria | Como você avalia a Delpi como parceira de longo prazo? | 1–5 ou “Não se aplica” (seleção obrigatória; Q08) |
| 11 | `overall_score` | Satisfação geral | De forma geral, qual é o seu nível de satisfação com a Delpi como fornecedor? | 1–5, obrigatório |
| 12 | `recommendation_score` | Recomendação | Em uma escala de 0 a 10, o quanto você recomendaria a Delpi para outra empresa que busca um fornecedor de chicotes elétricos e componentes? | 0–10, obrigatório |
| 13 | `strengths` | Pontos fortes | O que a Delpi faz bem e você considera importante manter? | Texto opcional |
| 14 | `improvements` | Oportunidades de melhoria | O que a Delpi poderia melhorar para atender melhor sua empresa? | Texto opcional |
| 15 | `unmet_needs` | Necessidades não atendidas | Existe alguma necessidade ou expectativa que a Delpi ainda não esteja atendendo? | Texto opcional |

**Atenção sobre origem de regras:** o **Word** fornece textos/escalas e a ordem (10 dimensões → satisfação geral → recomendação → 3 abertas). A opção **“Não se aplica”**, a exigência de escolha explícita para cada dimensão e a opcionalidade dos textos vêm das **decisões complementares Q08**, e não devem ser atribuídas literalmente ao Word. As chaves técnicas são mapeamentos do contrato `commercial-api`, não nomes escritos no Word.

**Gate de fidelidade textual Q09: FECHADO no nível documental.** Conferidos 10/10 textos de dimensões, 2/2 perguntas gerais e 3/3 abertas: **15/15 textos localizados** e mapeados às 15 chaves previstas. A **UI-03** deve renderizar a pergunta literal em cada campo de resposta; a **UI-07** deve apresentar as dez perguntas literais abaixo dos títulos das dimensões, as duas perguntas literais junto às notas individuais (visíveis ou em ajuda acessível, conforme UX) e as três perguntas abertas literais sob seus títulos. A ordem oficial acima deve ser preservada em formulário e leitura, sem usar rótulos ilustrativos como autoridade.

**Gate de versionamento: decisão funcional fechada; identificador técnico proposto abaixo; runtime PENDING.** `questionnaire_version` já existe no contrato de campanha/resposta como intenção e **ainda não foi observado em backend** (auditoria 11/11/2026: zero migrations/módulos `satisfaction*` no `commercial-api`; última migration `V023__seller_customer_center.sql`).

**Identificador proposto da primeira versão imutável (ainda não em uso no código):**

```text
delpi.commercial.satisfaction-survey.canonical-15@2026-11-11
```

Semântica: catálogo das 15 perguntas conferidas com o Word em 11/11/2026 (seção 1.4). É string estável e explícita — **não** inferir versão pela data da campanha nem pelo relógio. Qualquer alteração futura de texto/ordem/escala exige **novo** identificador e novo catálogo imutável; Q09 proíbe personalização por campanha. Na implementação: vincular o catálogo em código/constante versionada a este ID, gravar em campanha e resposta, devolver em R13/R14 e testes de leitura histórica. Até existir no código, **não** tratar o valor como “já adotado em produção”.

### 1.5 Contrato de leitura individual R13 (G03 — `CLOSED_SPEC`; implementação pendente)

`GET /satisfaction-surveys/responses/{response_id}` — authority `commercial-api`; **não existe** em routers/OpenAPI/use cases no HEAD auditado.

| Campo | Tipo | Fonte | Validação / nota |
|---|---|---|---|
| `id` | UUID | `satisfaction_responses.id` | Identidade canônica da UI-07 |
| `campaign_id` | UUID | FK via recipient → campaign | Conferir vínculo |
| `campaign_name` | TEXT | campanha | Exibição |
| `customer_code`, `customer_store` | TEXT | recipient | Identidade TOTVS; par obrigatório |
| `customer_name` | TEXT | snapshot +/ou consulta oficial autorizada | Nome exibido; cadastro mestre = TOTVS |
| `has_avatar` | boolean opcional | enriquecimento oficial existente | Sem flag inventada na pesquisa |
| `submitted_at` | TIMESTAMPTZ | response | Data/hora definitiva |
| `status` | derivado | presença de resposta definitiva | Situação oficial (ex.: responded) |
| `questionnaire_version` | TEXT | response (= campanha) | Ver ID proposto acima |
| `overall_score` | int 1–5 | response | Obrigatório; UI: `n / 5`, **não** rotular IGS |
| `recommendation_score` | int 0–10 | response | Obrigatório; UI: `n / 10`, **não** rotular NPS |
| `dimensions` | object 10 chaves | response JSONB | Cada valor `1..5` ou `null` (= N/A explícito, Q08); chaves: `quality`, `delivery_deadline`, `service`, `agility`, `communication`, `technical_support`, `commercial_support`, `flexibility`, `reliability`, `partnership` |
| `strengths`, `improvements`, `unmet_needs` | TEXT \| null | response | Comentários opcionais; UI “Não informado” se vazio |
| Textos literais | via catálogo da `questionnaire_version` | catálogo imutável | UI-07 não hardcodar redação divergente do catálogo |

**Não retornar:** token de convite, `token_hash`/`token_ciphertext`, e-mail/nome de pessoa física respondente, payloads de outras empresas.

**Exemplo ilustrativo (não é fixture de produção):**

```json
{
  "id": "11111111-1111-1111-1111-111111111111",
  "campaign_id": "22222222-2222-2222-2222-222222222222",
  "campaign_name": "Pesquisa 2026/2",
  "customer_code": "001245",
  "customer_store": "01",
  "customer_name": "Empresa Alpha",
  "submitted_at": "2026-12-10T15:30:00Z",
  "questionnaire_version": "delpi.commercial.satisfaction-survey.canonical-15@2026-11-11",
  "overall_score": 4,
  "recommendation_score": 9,
  "dimensions": {
    "quality": 5,
    "delivery_deadline": 3,
    "service": 4,
    "agility": 4,
    "communication": 4,
    "technical_support": null,
    "commercial_support": 5,
    "flexibility": 3,
    "reliability": 5,
    "partnership": 5
  },
  "strengths": "Atendimento técnico consistente.",
  "improvements": null,
  "unmet_needs": "Lead time reduzido para pedidos urgentes."
}
```

## 2. Fluxo de campanhas e participantes

1. Usuário interno autorizado cria a campanha, nome e datas. O backend armazena timestamps e deriva `scheduled | open | closed`; esses estados são **respostas derivadas**, não workflow manual.
2. Usuário consulta o cadastro comercial existente pela `commercial-api` → `api-delpi` → TOTVS. Seleciona pares `customer_code/customer_store` e adiciona participantes com operação idempotente e unicidade em banco.
3. O backend gera **um link estável e exclusivo** para cada participante. O Portal mostra ação **Copiar link** e, se for útil, **Copiar mensagem pronta**, com texto que o usuário pode colar em e-mail, WhatsApp, Teams ou outro meio. **A aplicação não envia nem verifica entrega de mensagens.**
4. Usuário acompanha participantes convidados/cadastrados e quais responderam ou ainda estão pendentes. "Convidado" na taxa de resposta significa **incluído na campanha**, não comprovadamente contatado.
5. Duplicidade de inclusão retorna o participante existente, sem novo token. Contato ajustado não altera o ERP, o link ou a resposta já recebida.

**Endpoints de referência (REST interno)**: `GET /satisfaction-surveys/questionnaire`; `GET/POST /satisfaction-surveys/campaigns`; `GET/PATCH /satisfaction-surveys/campaigns/{campaign_id}`; `GET/POST /satisfaction-surveys/campaigns/{campaign_id}/recipients`; `PATCH /satisfaction-surveys/campaigns/{campaign_id}/recipients/{recipient_id}`; `GET /satisfaction-surveys/campaigns/{campaign_id}/recipients/{recipient_id}/link`. **Não há `send-email` na primeira entrega**. Consulta aos clientes deve reaproveitar rotas oficiais existentes.

## 3. Formulário externo

- `GET /public/satisfaction-surveys/{token}`: somente perguntas, texto aprovado, datas e estado `open / not_open / closed / already_submitted` do convite. **Nunca devolver** dados privados de outras empresas, respostas ou token interno armazenado.
- `POST /public/satisfaction-surveys/{token}/response`: receber exatamente os campos definidos no contrato; validar escalas, estrutura de dimensões, questionário, token, janela de campanha e unicidade; responder sucesso apenas após commit.
- Link externo não autentica usuário interno. O middleware JWT atual exige exceção pública **estritamente delimitada** para esses dois paths/métodos e verificação do token no caso de uso; token inválido/expirado deve ter erro sem vazamento de existência de cliente.
- Rascunho poderá existir **somente no navegador, antes do envio**; nenhuma persistência de resposta parcial no backend. Revisar a resposta antes da confirmação final.
- Token aleatório de alta entropia, com hash para lookup e cifra autenticada para a recuperação segura do mesmo link pelo gestor, sem registro bruto em logs, métricas ou erros. Proteger contra tentativas repetidas. Não usar e-mail, código/loja ou identificador previsível como segredo.

## 4. Indicadores oficiais e respostas

**Fontes de cálculo:** somente `satisfaction_responses` definitivas + `satisfaction_recipients` da campanha; `satisfaction_campaigns` para datas e histórico. **Sem armazenar IGS ou NPS redundantes por campanha**; calcular no serviço de domínio para toda consulta com filtro. CAIO e REST reutilizam o mesmo serviço.

| Indicador | Cálculo canônico |
|---|---|
| IGS | `SUM(overall_score) / COUNT(respostas válidas)`; uma empresa = um voto |
| NPS | `100 × (COUNT(score >= 9) − COUNT(score <= 6)) / COUNT(NPS válidos)`; faixa 7–8 participa do denominador |
| Taxa de resposta | `COUNT(respostas) / COUNT(participantes da campanha)` (rotular como participantes cadastrados, **não confirmação de envio**) |
| Satisfeitos/críticos | Percentual de `overall_score IN (4,5)` e `IN (1,2)` entre notas gerais válidas; `3` neutro/intermediário |
| Dez dimensões | Média apenas das notas 1–5 em cada dimensão, desconsiderando `null`; retornar contagem válida por dimensão |
| Histórico | Comparação semestral/anual e com campanha anterior; exibir período, quantidade de respondentes e ausência de base quando aplicável |
| Planos de ação concluídos | **Entrega 2 obrigatória**; sem fonte na entrega 1, não devolver como zero ou dado fictício. Quando houver ações registradas: concluídas ÷ identificadas |

**Consulta interna agregada:** `GET /satisfaction-surveys/results` com seleção de campanha e filtros por atributos **oficiais disponíveis**, sem cadastrar dimensões fictícias. Filtros pedidos pelo plano: cliente, segmento, vendedor, região, tempo de relacionamento, volume/faturamento e estratégico vs. demais. A origem, período de referência e resolução desses campos devem ser confirmados na frente de indicadores; se atributo faltar, registrar indisponibilidade honesta, sem inventar proxy. Comparações Geral / Estratégicos / Demais seguem o exemplo do plano.

**Consulta privada:** `GET /satisfaction-surveys/campaigns/{campaign_id}/responses` e `GET /satisfaction-surveys/responses/{response_id}` restritas a Marketing/Manage. **Consulta agregada** para `commercial.access` nunca contém resposta individual, comentário por cliente, participante, nem grupo reduzido que permita reidentificação. Critério técnico de supressão/limiar deve ser testado antes de expor filtros à base ampla.

### 4.1 Matriz de autorização R12/R13 (G04 — evidência 11/11/2026)

| Ator | Código | Existência no código | R13 leitura individual | R16 agregados |
|---|---|---|---|---|
| Access isolado | `commercial.access` | **CONFIRMADO** (`commercial_permissions.py`, manifest) | **Negar** (403; sem payload) | Permitir com supressão |
| Manage | `commercial.manage` | **CONFIRMADO** (mesmo catálogo; **não** usar termo legado `commercial.manager`) | Permitir quando R13 existir | Permitir |
| Marketing | `commercial.marketing` | **CONTRATO_DOCUMENTAL_ONLY** — ausente do catálogo Python, manifest e testes | Permitir quando código + R13 existirem | Permitir |
| Sem permissão / token inválido | — | Middleware JWT atual | 401/403 | 401/403 |
| Superadmin | `is_superadmin` | Bypass existente em `has_any_permission` | Seguir política global vigente; não usar como atalho de produto | idem |

**Evidência:** `commercial-api/commercial_app/application/security/commercial_permissions.py` declara apenas `commercial.access`, `commercial.manage`, `commercial.billing.notify`. Nenhum endpoint de satisfação registrado em `main.py`. **Não ampliar permissões globalmente** só para facilitar a UI-07; adicionar `commercial.marketing` somente na etapa autorizada, com testes positivos (marketing, manage) e negativos (access, anônimo).

## 5. Permissões, CAIO e validação por etapa

- O escopo funcional continua: gestão e respostas individualizadas por `commercial.marketing` **OU** `commercial.manage`; apenas resultados agregados para `commercial.access`. O código de Marketing será adicionado **na etapa de desenvolvimento da aplicação**, não agora; **não criar códigos adicionais de permissão**.
- O gate atual do CAIO exige `commercial.access` na entrada. Resolver sem concessão global inadvertida e com paridade de auth REST/MCP **na mesma etapa** que introduzir ações. Não criar tools além de `get_context`, `read`, `analyze`, `knowledge`, `execute` e `delete`.
- Em **todo prompt de implementação**, incluir: confirmar HEAD/branch/working tree; ler índice + contrato desta frente + authorities reais; menor diff; autorização no backend; adicionar `(entity, action)`/analysis correspondente ao catálogo do CAIO e dispatch para os **mesmos use cases**; testes de paridade, negativas de permissão, concorrência, segurança, cálculos e read-back; relatório de execução (HEAD antes/depois, arquivos alterados, testes, residual search, lacunas).
- CAIO só anuncia `proven` após implementação comprovada; se ainda não implementado, usar `planned/not_implemented`. Não executar a submissão do cliente externo via CAIO.
- **Testes e homologação** são executados por etapa, não como fase de planejamento infinito.

## 6. Fora da primeira entrega e critérios de conclusão

**Adiados para entrega 2:** persistência e rotas de classificação/tratamento (candidatas `satisfaction_cases`, R17–R20 e ações CAIO), fluxos de plano de ação, retorno e reavaliação e indicador de ações concluídas. **Reutilizar `commercial.tasks` é alternativa técnica a avaliar**, não obrigação de integração nem autorização para expor dados restritos. **Fora do produto por decisão específica:** envio direto por e-mail e notificações/ligações automáticas. **Classificação de problemas, planos de ação, acompanhamento, retorno, reavaliação e seu indicador fazem parte da entrega 2 obrigatória.** Até sua implementação, o Comercial poderá conduzir o acompanhamento manualmente; isto é transição, **não exclusão do produto**. O envio direto de e-mail segue não previsto por decisão explícita do solicitante.

**Pronto para iniciar implementação:** somente na frente escolhida, verificar HEAD/working tree e fontes canônicas; criar migration e testes em seguida; não presumir banco migrado ou serviço no ar pelo fato de este contrato estar completo. **Critério da primeira entrega:** uma campanha configurável com empresas TOTVS; link copiável estável; uma resposta definitiva por empresa; questionário fiel ao plano; dados históricos persistidos; listagem privada de respostas; indicadores oficiais e agregação segura; CAIO com paridade nas capabilities efetivamente entregues. Segurança e LGPD verificadas na etapa pertinente.

**Sem execução de banco nesta fase documental:** este texto não aplica SQL nem altera ambiente de produção. Migração física depende do agente de desenvolvimento, seus testes e da infraestrutura autorizada.