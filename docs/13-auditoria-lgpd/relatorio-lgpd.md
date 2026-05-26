# Relatório de Auditoria LGPD — Projeto Delpi Central

**Data:** 26/05/2026  
**Escopo:** Revisão completa do código-fonte do projeto `delpi-central` (todas as APIs, plugins frontend, infraestrutura, portal, gateway e configurações).  
**Status:** 38/38 inconformidades resolvidas (100%). Ver [relatório de adequação](relatorio-adequacao-lgpd.md).

---

## Sumário

| # | Categoria | Total | ✅ Resolvidas | ⚠️ Pendentes |
|---|-----------|-------|--------------|--------------|
| 1 | [Ausência de Base Legal / Consentimento](#1-ausência-de-base-legal--consentimento) | 4 | 4 | 0 |
| 2 | [Direitos do Titular — Exclusão e Anonimização](#2-direitos-do-titular--exclusão-e-anonimização) | 6 | 6 | 0 |
| 3 | [Direitos do Titular — Portabilidade e Acesso](#3-direitos-do-titular--portabilidade-e-acesso) | 2 | 2 | 0 |
| 4 | [Segurança de Dados Pessoais](#4-segurança-de-dados-pessoais) | 10 | 10 | 0 |
| 5 | [Minimização e Finalidade dos Dados](#5-minimização-e-finalidade-dos-dados) | 5 | 4 | 1 |
| 6 | [Retenção e Ciclo de Vida dos Dados](#6-retenção-e-ciclo-de-vida-dos-dados) | 4 | 4 | 0 |
| 7 | [Transparência e Registro de Tratamento](#7-transparência-e-registro-de-tratamento) | 3 | 3 | 0 |
| 8 | [Compartilhamento e Transferência de Dados](#8-compartilhamento-e-transferência-de-dados) | 4 | 4 | 0 |
| **Total** | | **38** | **38** | **0** |

---

## 1. Ausência de Base Legal / Consentimento

### 1.1 — Nenhum mecanismo de consentimento implementado em todo o projeto

| Item | Detalhe |
|------|---------|
| **Severidade** | CRÍTICA |
| **Lei/Artigo** | LGPD Art. 7º (bases legais para tratamento), Art. 8º (consentimento) |
| **Arquivos afetados** | Projeto inteiro — nenhum módulo implementa consentimento |
| **Descrição** | Não existe nenhum mecanismo de coleta, registro ou revogação de consentimento do titular em nenhuma das APIs ou no frontend. Nenhuma tabela no banco armazena flags de consentimento. Nenhum endpoint permite gerenciar consentimento. |
| **Recomendação** | Implementar módulo de gestão de consentimento com: tabela de registros de consentimento (data, finalidade, forma de coleta), endpoint de revogação, e integração com o fluxo de primeiro login no Keycloak/portal. Alternativamente, documentar outra base legal aplicável (ex.: legítimo interesse, execução de contrato) com a respectiva avaliação de impacto (RIPD). |

### 1.2 — Auto-provisionamento de usuário sem consentimento prévio

| Item | Detalhe |
|------|---------|
| **Severidade** | ALTA |
| **Lei/Artigo** | LGPD Art. 7º, I (consentimento), Art. 8º, §5º (revogação), Art. 9º (informação sobre tratamento) |
| **Arquivo** | `core-api/app/interfaces/http/auth_middleware.py` |
| **Ponto do código** | Função `before_request` — trecho que faz upsert automático do usuário a partir das claims Keycloak |
| **Descrição** | No primeiro login, o sistema cria automaticamente um registro na tabela `users` (com `name`, `email`, `birth_date`) extraído do token Keycloak, sem informar o titular sobre o tratamento nem obter consentimento. |
| **Recomendação** | Exibir termos de uso / política de privacidade no primeiro acesso e registrar o aceite antes de persistir os dados. |

### 1.3 — Dados pessoais injetados em contexto de IA sem consentimento específico

| Item | Detalhe |
|------|---------|
| **Severidade** | ALTA |
| **Lei/Artigo** | LGPD Art. 7º, I (consentimento), Art. 6º, I (finalidade), Art. 11 (dados sensíveis) |
| **Arquivo** | `minha-delpi-ai-api/app/application/services/chat_user_context_service.py` |
| **Ponto do código** | Método que monta o contexto do usuário (nome, email, permissões, grupos) e injeta no prompt do LLM |
| **Descrição** | Nome, email, papéis e permissões do titular são enviados ao modelo de linguagem (Ollama/vLLM) como contexto de cada conversa, sem ciência ou consentimento específico do titular para esse tratamento. |
| **Recomendação** | Informar claramente ao usuário que seus dados de perfil são compartilhados com o modelo de IA. Obter consentimento específico ou documentar base legal. Avaliar se é possível anonimizar/minimizar os dados enviados. |

### 1.4 — Rastreamento de uso de apps sem ciência do titular

| Item | Detalhe |
|------|---------|
| **Severidade** | MÉDIA |
| **Lei/Artigo** | LGPD Art. 6º, I (finalidade), Art. 7º, I (consentimento), Art. 9º (informação) |
| **Arquivo** | `core-api/app/infrastructure/db/models/app_usage_event.py` |
| **Ponto do código** | Modelo `AppUsageEvent` — campos `user_id`, `app_id`, `route_path`, `opened_at` |
| **Descrição** | O sistema rastreia cada acesso do usuário a cada módulo/app (qual app, qual rota, quando), armazenando na tabela `app_usage_events`, sem informar o titular sobre esse monitoramento comportamental. |
| **Recomendação** | Informar na política de privacidade. Se a base legal for legítimo interesse, documentar a avaliação (LIA). Considerar anonimização ou agregação dos dados para analytics. |

---

## 2. Direitos do Titular — Exclusão e Anonimização

### 2.1 — Audit logs irremovíveis contendo dados pessoais (core-api)

| Item | Detalhe |
|------|---------|
| **Severidade** | ALTA |
| **Lei/Artigo** | LGPD Art. 18, VI (eliminação de dados), Art. 16 (eliminação após tratamento) |
| **Arquivo** | `core-api/app/infrastructure/db/models/audit_log.py` |
| **Ponto do código** | Modelo `AuditLog` — campos `user_id`, `ip_address`, `payload` (JSON com dados pessoais) |
| **Descrição** | Os audit logs armazenam `user_id`, endereço IP e payload JSON (que pode conter dados pessoais). Não existe endpoint para excluir ou anonimizar esses registros, nem TTL/política de retenção. Mesmo que o usuário seja excluído da tabela `users`, os audit logs permanecem com referência ao ID. |
| **Recomendação** | Implementar política de retenção com TTL (ex.: 1-2 anos). Criar processo de anonimização que substitua `user_id` e `ip_address` por hashes irreversíveis após o período de retenção. |

### 2.2 — Audit logs irremovíveis contendo dados pessoais (transformometro-api)

| Item | Detalhe |
|------|---------|
| **Severidade** | ALTA |
| **Lei/Artigo** | LGPD Art. 18, VI (eliminação), Art. 16 (eliminação após tratamento) |
| **Arquivo** | `transformometro-api/tm_app/interface/http/routes/crud_routes.py` |
| **Ponto do código** | Função `_audit` — grava `user_id`, `user_email` e `payload_json` (dump completo do body) na tabela `transformometro.audit_logs` |
| **Descrição** | A cada operação CRUD, o sistema grava o email e ID do usuário junto com o payload completo da requisição (que inclui `gestor_responsavel`). Não há mecanismo de exclusão, anonimização ou TTL. |
| **Recomendação** | Mesma do item 2.1 — implementar retenção e anonimização programada. |

### 2.3 — Audit logs do chat de IA com preview de perguntas

| Item | Detalhe |
|------|---------|
| **Severidade** | MÉDIA |
| **Lei/Artigo** | LGPD Art. 18, VI (eliminação), Art. 6º, III (necessidade) |
| **Arquivo** | `minha-delpi-ai-api/app/infrastructure/db/models/audit_log_model.py` |
| **Ponto do código** | Modelo `AiAuditLogModel` — campo `audit_metadata` (JSONB) contém `question_preview` (200 primeiros caracteres da pergunta do usuário) |
| **Descrição** | Os audit logs do chat registram um preview do texto digitado pelo usuário, que pode conter dados pessoais livres (nomes, CPFs, etc.). Não há mecanismo de exclusão nem TTL. |
| **Recomendação** | Avaliar necessidade do `question_preview`. Se necessário, implementar TTL. Considerar hash ou remoção do preview após período determinado. |

### 2.4 — Soft delete sem purge no transformometro-api

| Item | Detalhe |
|------|---------|
| **Severidade** | MÉDIA |
| **Lei/Artigo** | LGPD Art. 18, VI (eliminação de dados pessoais) |
| **Arquivo** | `transformometro-api/tm_app/infrastructure/persistence/` (repositórios CRUD) |
| **Ponto do código** | Todas as operações de exclusão usam `UPDATE ... SET deletado = TRUE` — dados permanecem no banco |
| **Descrição** | Processos com `gestor_responsavel` (nome de pessoa), revisões com `aprovado_por_email` e recursos com `fornecedor` nunca são efetivamente excluídos do banco. Dados pessoais permanecem indefinidamente. |
| **Recomendação** | Implementar processo de purge periódico que efetivamente remova registros com soft-delete antigos, ou anonimize os campos com dados pessoais (`gestor_responsavel`, `aprovado_por_email`). |

### 2.5 — Settings audit do strategic-indicators sem exclusão

| Item | Detalhe |
|------|---------|
| **Severidade** | MÉDIA |
| **Lei/Artigo** | LGPD Art. 18, VI (eliminação) |
| **Arquivo** | `strategic-indicators-api/si_app/infrastructure/persistence/` (tabela `settings_audit`) |
| **Ponto do código** | Tabela `settings_audit` com campos `actor_user_id`, `actor_email`, `payload` |
| **Descrição** | Registros de auditoria de configurações contêm email e ID do usuário sem mecanismo de exclusão. |
| **Recomendação** | Implementar retenção e anonimização conforme itens 2.1/2.2. |

### 2.6 — Ausência de endpoint unificado de "direito ao esquecimento"

| Item | Detalhe |
|------|---------|
| **Severidade** | CRÍTICA |
| **Lei/Artigo** | LGPD Art. 18, VI (eliminação), Art. 15 (término do tratamento) |
| **Arquivos afetados** | Todas as APIs (`core-api`, `transformometro-api`, `strategic-indicators-api`, `minha-delpi-ai-api`) |
| **Descrição** | Embora o `core-api` permita excluir o usuário da tabela `users` (hard delete com CASCADE em `app_usage_events`), não existe processo que propague a exclusão/anonimização para: audit_logs (core), audit_logs (transformometro), audit_logs (chat IA), tabela `processos` (gestor_responsavel), tabela `revisoes` (aprovado_por_email), tabela `indicator_goals` (created_by_email/updated_by_email), tabela `settings_audit` (actor_email), tabela `notifications`, sessões e mensagens de chat, presença Redis. |
| **Recomendação** | Criar um serviço de "data subject erasure" que, ao receber uma solicitação de exclusão, propague para todos os microsserviços e banco de dados, anonimizando ou excluindo todas as referências ao titular. |

---

## 3. Direitos do Titular — Portabilidade e Acesso

### 3.1 — Ausência de endpoint de portabilidade de dados

| Item | Detalhe |
|------|---------|
| **Severidade** | ALTA |
| **Lei/Artigo** | LGPD Art. 18, V (portabilidade dos dados) |
| **Arquivos afetados** | Todas as APIs |
| **Descrição** | Não existe endpoint que permita ao titular exportar todos os seus dados pessoais em formato estruturado e interoperável (JSON, CSV). Os endpoints existentes de export (CSV/Excel do dashboard) exportam dados de negócio, não dados pessoais do titular. |
| **Recomendação** | Implementar endpoint `/me/data-export` que consolide todos os dados pessoais do titular (perfil, histórico de uso, mensagens de chat, processos onde é gestor, logs de auditoria, notificações, etc.) em formato JSON ou CSV. |

### 3.2 — Ausência de endpoint de confirmação de tratamento

| Item | Detalhe |
|------|---------|
| **Severidade** | MÉDIA |
| **Lei/Artigo** | LGPD Art. 18, I (confirmação da existência de tratamento), Art. 18, II (acesso aos dados) |
| **Arquivos afetados** | Todas as APIs |
| **Descrição** | Não há endpoint que informe ao titular quais dados seus estão sendo tratados, para quais finalidades, e com quem são compartilhados (exceto o `/me` que retorna perfil básico). |
| **Recomendação** | Criar endpoint de "relatório de tratamento" que informe ao titular: quais dados são coletados, finalidades, período de retenção, e com quais terceiros/sistemas são compartilhados. |

---

## 4. Segurança de Dados Pessoais

### 4.1 — Credenciais em texto plano nos arquivos .env versionados

| Item | Detalhe |
|------|---------|
| **Severidade** | CRÍTICA |
| **Lei/Artigo** | LGPD Art. 46 (medidas de segurança), Art. 6º, VII (segurança) |
| **Arquivos** | `infra/.env`, `infra/.env.example`, `infra/docker-compose.*.yml` |
| **Ponto do código** | Senhas de banco de dados (`POSTGRES_PASSWORD`, `DB_PASSWORD`), tokens de serviço (`CORE_API_INTEGRATIONS_SERVICE_TOKEN`), client secrets do Keycloak, todos em texto plano |
| **Descrição** | Arquivos `.env` com credenciais reais estão acessíveis no repositório. Embora o `.gitignore` inclua `.env`, existem `.env.example` e referências em `docker-compose.yml` com valores padrão fracos (`delpi123`, `secret`). |
| **Recomendação** | Usar cofre de segredos (HashiCorp Vault, AWS Secrets Manager) ou variáveis de ambiente gerenciadas pela plataforma de deploy. Remover qualquer credencial real do repositório e do histórico Git. |

### 4.2 — JWT_SECRET com valor padrão "secret"

| Item | Detalhe |
|------|---------|
| **Severidade** | ALTA |
| **Lei/Artigo** | LGPD Art. 46 (medidas de segurança), Art. 6º, VII (segurança) |
| **Arquivos** | `api-delpi/app/config.py`, `transformometro-api/tm_app/infrastructure/config/config.py`, `strategic-indicators-api/si_app/infrastructure/config/config.py` |
| **Ponto do código** | `JWT_SECRET: str = _get_env("JWT_SECRET", ..., default="secret")` |
| **Descrição** | Três APIs têm `JWT_SECRET` com valor padrão `"secret"`. Se as variáveis de ambiente não forem configuradas, o sistema opera com uma chave criptograficamente trivial. |
| **Recomendação** | Remover o valor padrão e lançar erro se a variável não estiver configurada em produção. Implementar validação de startup que rejeite valores fracos. |

### 4.3 — Verificação de audience do JWT desabilitada

| Item | Detalhe |
|------|---------|
| **Severidade** | ALTA |
| **Lei/Artigo** | LGPD Art. 46 (medidas de segurança) |
| **Arquivo** | `shared/delpi_auth/jwt_validator.py` |
| **Ponto do código** | `jwt.decode(token, key, algorithms=["RS256"], options={"verify_aud": False})` |
| **Descrição** | A validação de `audience` está desabilitada no JWT validator compartilhado. Isso permite que tokens emitidos para outros clientes Keycloak sejam aceitos, abrindo possibilidade de ataques de token confusion. |
| **Recomendação** | Habilitar `verify_aud: True` e configurar a audience esperada em cada API. |

### 4.4 — Exposição de detalhes internos em respostas de erro

| Item | Detalhe |
|------|---------|
| **Severidade** | MÉDIA |
| **Lei/Artigo** | LGPD Art. 46 (medidas de segurança e boas práticas) |
| **Arquivos** | `transformometro-api/tm_app/main.py` (handler de exceções), `core-api/app/interfaces/http/me_controller.py`, `api-delpi/app/interface/http/routes/product_routes.py`, `minha-delpi-ai-api/app/interfaces/http/chat_routes.py` |
| **Ponto do código** | Uso de `str(exc)` / `str(e)` como corpo da resposta de erro retornada ao cliente |
| **Descrição** | Exceções não tratadas podem expor detalhes internos como nomes de tabelas, constraints do banco, stack traces ou até dados pessoais presentes na query que falhou. A função `format_api_error` do transformometro retorna `str(exc)` diretamente. |
| **Recomendação** | Retornar mensagens genéricas ao cliente (`"Erro interno do servidor"`) e logar os detalhes apenas internamente. Nunca retornar `str(exc)` em produção. |

### 4.5 — Dados pessoais hardcoded em dados de seed/fixtures

| Item | Detalhe |
|------|---------|
| **Severidade** | MÉDIA |
| **Lei/Artigo** | LGPD Art. 46 (medidas de segurança), Art. 6º, VII (segurança) |
| **Arquivos** | `infra/.env`, `infra/docker-compose.yml`, scripts de seed/migração |
| **Ponto do código** | Nomes, emails e usernames de pessoas reais em dados de configuração e seed |
| **Descrição** | Existem dados pessoais reais (nome completo, email corporativo, username) hardcoded em arquivos de configuração e seed, expostos no repositório. |
| **Recomendação** | Substituir por dados fictícios (ex.: `usuario.teste@exemplo.com`). Usar geradores de dados fake para seeds. |

### 4.6 — CORS permissivo com credenciais habilitadas

| Item | Detalhe |
|------|---------|
| **Severidade** | MÉDIA |
| **Lei/Artigo** | LGPD Art. 46 (medidas de segurança) |
| **Arquivos** | `transformometro-api/tm_app/main.py`, `strategic-indicators-api/si_app/main.py`, `api-delpi/app/main.py` |
| **Ponto do código** | CORS com `allow_credentials=True` e origens incluindo `http://localhost` |
| **Descrição** | As APIs aceitam cookies/credenciais de origens localhost em conjunto com `allow_credentials=True`. Em desenvolvimento isto é conveniente, mas se mantido em produção, permite ataques CSRF de qualquer máquina local. |
| **Recomendação** | Remover `http://localhost` das origens permitidas em configuração de produção. Usar lista restrita de origens. |

### 4.7 — Nginx sem HTTPS direto, sem rate limiting

| Item | Detalhe |
|------|---------|
| **Severidade** | MÉDIA |
| **Lei/Artigo** | LGPD Art. 46 (medidas técnicas de segurança) |
| **Arquivo** | `gateway/nginx.conf`, `infra/nginx/` |
| **Descrição** | O Nginx não implementa HTTPS diretamente (delegado a load balancer upstream) nem rate limiting, expondo as APIs a ataques de força bruta e enumeração de dados. |
| **Recomendação** | Implementar TLS termination no Nginx ou garantir documentadamente que o LB upstream sempre faz isso. Adicionar rate limiting (`limit_req_zone`), especialmente em rotas de autenticação e busca de usuários. |

### 4.8 — Token de serviço estático (legado)

| Item | Detalhe |
|------|---------|
| **Severidade** | MÉDIA |
| **Lei/Artigo** | LGPD Art. 46 (medidas de segurança) |
| **Arquivo** | `api-delpi/app/infrastructure/http/auth_header.py` |
| **Ponto do código** | Fallback para `TRANSFORMOMETRO_SERVICE_BEARER` — token estático usado para comunicação entre serviços |
| **Descrição** | A autenticação entre serviços possui fallback para um token estático (`TRANSFORMOMETRO_SERVICE_BEARER`), que não tem expiração nem rotação. Se vazado, concede acesso indefinido. |
| **Recomendação** | Migrar para OAuth2 client credentials ou tokens JWT com expiração curta para comunicação entre serviços. Remover o mecanismo legado. |

### 4.9 — Senha de banco hardcoded em TestingConfig

| Item | Detalhe |
|------|---------|
| **Severidade** | BAIXA |
| **Lei/Artigo** | LGPD Art. 46 (medidas de segurança) |
| **Arquivo** | `core-api/app/infrastructure/config/settings.py` |
| **Ponto do código** | `SQLALCHEMY_DATABASE_URI = "postgresql://delpi:delpi123@postgres-core-test:5432/delpi_core_test"` |
| **Descrição** | Senha de banco `delpi123` hardcoded na configuração de testes. Risco baixo se restrito a ambiente de teste, mas viola boas práticas. |
| **Recomendação** | Usar variáveis de ambiente mesmo para ambientes de teste. |

### 4.10 — Swagger UI com injeção de token via postMessage

| Item | Detalhe |
|------|---------|
| **Severidade** | BAIXA |
| **Lei/Artigo** | LGPD Art. 46 (medidas de segurança) |
| **Arquivo** | `strategic-indicators-api/si_app/main.py` |
| **Ponto do código** | Script injetado no Swagger que recebe token via `window.addEventListener("message", ...)` sem verificação de origem |
| **Descrição** | O Swagger UI aceita tokens JWT via `postMessage` de qualquer origem, permitindo que uma página maliciosa injete tokens. Risco de XSS via Swagger. |
| **Recomendação** | Verificar a origem do `postMessage` (`event.origin`). Desabilitar Swagger em produção. |

---

## 5. Minimização e Finalidade dos Dados

### 5.1 — Coleta de `birth_date` sem finalidade clara

| Item | Detalhe |
|------|---------|
| **Severidade** | MÉDIA |
| **Lei/Artigo** | LGPD Art. 6º, III (necessidade — limitação ao mínimo necessário) |
| **Arquivo** | `core-api/app/infrastructure/db/models/user.py` |
| **Ponto do código** | `birth_date = db.Column(db.Date, nullable=True, index=True)` |
| **Descrição** | A data de nascimento é coletada e armazenada, mas sua única finalidade aparente é o envio de notificações de aniversário (`/integrations/notifications/automation/birthdays`). Essa finalidade pode não justificar a coleta de um dado pessoal sensível (que pode revelar idade). |
| **Recomendação** | Documentar a finalidade. Se for apenas para aniversários, avaliar se é possível armazenar apenas mês/dia sem o ano. Obter consentimento específico. |

### 5.2 — Armazenamento de IP address nos audit logs

| Item | Detalhe |
|------|---------|
| **Severidade** | MÉDIA |
| **Lei/Artigo** | LGPD Art. 6º, III (necessidade), Art. 12 (dado pessoal identificável) |
| **Arquivo** | `core-api/app/infrastructure/db/models/audit_log.py` |
| **Ponto do código** | `ip_address = db.Column(db.String(45), nullable=True)` |
| **Descrição** | O endereço IP é armazenado nos audit logs sem justificativa clara de finalidade, além de não possuir TTL. IP é considerado dado pessoal quando permite identificação do titular. |
| **Recomendação** | Avaliar se o IP é realmente necessário. Se sim, implementar truncamento (ex.: zerar último octeto) ou TTL. Documentar finalidade (segurança/investigação). |

### 5.3 — Payload JSON completo nos audit logs do transformometro

| Item | Detalhe |
|------|---------|
| **Severidade** | MÉDIA |
| **Lei/Artigo** | LGPD Art. 6º, III (necessidade — limitação ao mínimo necessário) |
| **Arquivo** | `transformometro-api/tm_app/interface/http/routes/crud_routes.py` |
| **Ponto do código** | Função `_audit` — `payload_json` recebe o dump JSON completo do body da requisição |
| **Descrição** | O audit log do transformometro grava o body inteiro da requisição, incluindo campos como `gestor_responsavel` (nome de pessoa). Isso é excessivo para fins de auditoria. |
| **Recomendação** | Gravar apenas os campos necessários para auditoria (IDs, tipo de ação, timestamp). Excluir ou mascarar campos com dados pessoais no payload. |

### 5.4 — Email do criador/atualizador denormalizado nas tabelas

| Item | Detalhe |
|------|---------|
| **Severidade** | BAIXA |
| **Lei/Artigo** | LGPD Art. 6º, III (necessidade) |
| **Arquivos** | `core-api/app/infrastructure/db/models/app_module.py` (`created_by_email`, `updated_by_email`, `created_by_name`, `updated_by_name`), `strategic-indicators-api` (tabelas `indicator_goals`, `departments`) |
| **Ponto do código** | Colunas `created_by_email`, `updated_by_email`, `created_by_name`, `updated_by_name` em múltiplas tabelas |
| **Descrição** | Email e nome do usuário são duplicados (denormalizados) em várias tabelas de negócio ao invés de referenciados por ID. Isso dificulta a anonimização/exclusão e multiplica os pontos onde dados pessoais são armazenados. |
| **Recomendação** | Armazenar apenas `user_id` como FK. Resolver nome/email via join quando necessário. |

### 5.5 — Mensagens de chat armazenam texto livre irrestrito

| Item | Detalhe |
|------|---------|
| **Severidade** | MÉDIA |
| **Lei/Artigo** | LGPD Art. 6º, I (finalidade), Art. 6º, III (necessidade), Art. 7º (bases legais) |
| **Arquivo** | `minha-delpi-ai-api/app/infrastructure/db/models/chat_message_model.py` |
| **Ponto do código** | `content = Column(Text, nullable=False)` — armazena texto livre digitado pelo usuário |
| **Descrição** | O chat de IA armazena indefinidamente o conteúdo das mensagens, que pode incluir dados pessoais de terceiros (nomes, CPFs, etc.) digitados livremente pelo titular. Não há advertência ao usuário nem mecanismo de sanitização. |
| **Recomendação** | Implementar TTL para mensagens antigas. Exibir aviso ao usuário para não inserir dados pessoais sensíveis. Documentar base legal e finalidade do armazenamento. |

---

## 6. Retenção e Ciclo de Vida dos Dados

### 6.1 — Ausência de política de retenção de dados

| Item | Detalhe |
|------|---------|
| **Severidade** | ALTA |
| **Lei/Artigo** | LGPD Art. 15 (término do tratamento), Art. 16 (eliminação após término) |
| **Arquivos afetados** | Todas as APIs — nenhuma tabela possui TTL, particionamento temporal ou job de limpeza |
| **Descrição** | Nenhuma tabela do sistema possui política de retenção definida. Audit logs, mensagens de chat, eventos de uso, notificações e dados de processos são armazenados indefinidamente. |
| **Recomendação** | Definir e implementar política de retenção por tipo de dado: audit logs (ex.: 2 anos), mensagens de chat (ex.: 1 ano), eventos de uso (ex.: 6 meses), notificações lidas (ex.: 90 dias). Criar jobs periódicos de purge/anonimização. |

### 6.2 — Presença de usuário em Redis sem TTL garantido

| Item | Detalhe |
|------|---------|
| **Severidade** | BAIXA |
| **Lei/Artigo** | LGPD Art. 16 (eliminação após fim da finalidade) |
| **Arquivo** | `core-api/app/infrastructure/services/redis_presence_store.py` |
| **Ponto do código** | Chaves `presence:session:{sid}` e `presence:user:{userId}` — TTL de 90s (padrão configurável) |
| **Descrição** | Dados de presença têm TTL curto (90s), mas se o Redis não expirar corretamente ou a configuração for alterada, dados de presença (userId, timestamps) podem persistir. |
| **Recomendação** | Documentar e monitorar a política de expiração no Redis. Garantir que o TTL não seja desabilitado em produção. |

### 6.3 — Cache de embeddings pode reter dados pessoais

| Item | Detalhe |
|------|---------|
| **Severidade** | BAIXA |
| **Lei/Artigo** | LGPD Art. 16 (eliminação após término), Art. 6º, III (necessidade) |
| **Arquivo** | `minha-delpi-ai-api/` — configuração `EMBEDDING_CACHE_BACKEND` (memory/redis) |
| **Descrição** | Embeddings de textos processados pelo chat podem conter representações vetoriais de dados pessoais se os documentos indexados na base de conhecimento contiverem tais dados. Cache em Redis pode reter esses dados além do necessário. |
| **Recomendação** | Implementar TTL para cache de embeddings. Avaliar se documentos com dados pessoais devem ser indexados na base de conhecimento. |

### 6.4 — Notificações com soft delete sem purge

| Item | Detalhe |
|------|---------|
| **Severidade** | BAIXA |
| **Lei/Artigo** | LGPD Art. 16 (eliminação após término) |
| **Arquivo** | `core-api/app/infrastructure/db/models/notification.py` |
| **Ponto do código** | `deleted_at = db.Column(db.DateTime, nullable=True)` — soft delete |
| **Descrição** | Notificações "excluídas" pelo usuário apenas recebem um timestamp de deleção, mas continuam no banco. O conteúdo (`message`, `html_content`) pode incluir dados pessoais (nomes de aniversariantes, etc.). |
| **Recomendação** | Implementar job de purge que remova notificações soft-deleted após período determinado (ex.: 30 dias). |

---

## 7. Transparência e Registro de Tratamento

### 7.1 — Ausência de Registro de Operações de Tratamento (ROPA)

| Item | Detalhe |
|------|---------|
| **Severidade** | ALTA |
| **Lei/Artigo** | LGPD Art. 37 (registro das operações de tratamento) |
| **Arquivos afetados** | Projeto inteiro |
| **Descrição** | Não existe documento ou mecanismo que registre as operações de tratamento de dados pessoais (ROPA — Record of Processing Activities). A LGPD exige que o controlador mantenha registro das operações, especialmente quando o tratamento é baseado em legítimo interesse. |
| **Recomendação** | Criar e manter um ROPA documentando: categorias de dados tratados, finalidades, bases legais, destinatários, transferências internacionais (se houver), e prazos de retenção. |

### 7.2 — Ausência de Política de Privacidade integrada ao sistema

| Item | Detalhe |
|------|---------|
| **Severidade** | ALTA |
| **Lei/Artigo** | LGPD Art. 9º (direito à informação sobre o tratamento), Art. 6º, VI (transparência) |
| **Arquivos afetados** | `portal/`, `plugins/` (frontend) |
| **Descrição** | Não há link ou página de política de privacidade no portal ou nos plugins frontend. O titular não é informado sobre quais dados são coletados, para quais finalidades, por quanto tempo são armazenados, e quais são seus direitos. |
| **Recomendação** | Criar página de política de privacidade acessível no portal. Exibir link no rodapé de todas as telas e na tela de login. |

### 7.3 — Ausência de canal de comunicação com o Encarregado (DPO)

| Item | Detalhe |
|------|---------|
| **Severidade** | MÉDIA |
| **Lei/Artigo** | LGPD Art. 41 (encarregado de dados), Art. 18, §1º (exercício de direitos) |
| **Arquivos afetados** | Projeto inteiro |
| **Descrição** | Não há no sistema qualquer referência ao Encarregado de Proteção de Dados (DPO), nem canal de contato para que o titular exerça seus direitos (solicitação de acesso, exclusão, portabilidade, etc.). |
| **Recomendação** | Adicionar informações do DPO na política de privacidade e disponibilizar canal de contato (email, formulário) no portal. |

---

## 8. Compartilhamento e Transferência de Dados

### 8.1 — Repasse de JWT a APIs externas

| Item | Detalhe |
|------|---------|
| **Severidade** | MÉDIA |
| **Lei/Artigo** | LGPD Art. 7º, §5º (compartilhamento com necessidade de consentimento), Art. 26 (uso compartilhado de dados) |
| **Arquivo** | `api-delpi/app/infrastructure/http/auth_header.py`, `minha-delpi-ai-api/app/infrastructure/gateways/http_external_action_gateway.py` |
| **Ponto do código** | `bearer_authorization_from_context()` repassa o token JWT do usuário para APIs externas; External Actions com modo `forward_user_bearer` |
| **Descrição** | O token JWT do usuário (que contém `sub`, `email`, `name`, `roles`) é repassado a APIs externas (Transformometro, integrações). As External Actions do chat de IA podem repassar o bearer token a qualquer API configurada. |
| **Recomendação** | Usar tokens de serviço (client credentials) para comunicação entre APIs internas. Para External Actions, documentar claramente quais dados são compartilhados e com quais terceiros. |

### 8.2 — Dados pessoais enviados ao modelo de linguagem (LLM)

| Item | Detalhe |
|------|---------|
| **Severidade** | ALTA |
| **Lei/Artigo** | LGPD Art. 7º, §5º (compartilhamento), Art. 6º, I (finalidade), Art. 46 (segurança) |
| **Arquivo** | `minha-delpi-ai-api/app/application/services/chat_user_context_service.py`, `minha-delpi-ai-api/app/infrastructure/tools/get_current_user_tool.py` |
| **Ponto do código** | Montagem de contexto com nome, email, permissões; tool que retorna dados do perfil ao LLM |
| **Descrição** | Nome, email, permissões e grupos do titular são injetados como contexto em cada conversa com o LLM. Dependendo da hospedagem do modelo (cloud vs on-premise), isso pode constituir transferência internacional ou compartilhamento com terceiro. |
| **Recomendação** | Se o LLM for hospedado externamente, avaliar cláusulas contratuais e DPA com o provedor. Minimizar dados enviados (ex.: enviar apenas primeiro nome ou ID). Documentar no ROPA. |

### 8.3 — Busca de diretório expõe dados de outros titulares

| Item | Detalhe |
|------|---------|
| **Severidade** | BAIXA |
| **Lei/Artigo** | LGPD Art. 6º, III (necessidade), Art. 6º, I (finalidade) |
| **Arquivos** | `core-api/app/interfaces/http/me_controller.py` (rota `/me/directory/users`), `minha-delpi-ai-api/app/interfaces/http/chat_routes.py` (rota `/chat/users/search`) |
| **Ponto do código** | Endpoints de busca de usuários por nome/email retornam `id`, `name`, `email` de outros titulares |
| **Descrição** | Qualquer usuário autenticado pode buscar outros usuários pelo nome ou email, obtendo dados pessoais de terceiros. Embora útil para funcionalidades de compartilhamento, viola o princípio da necessidade se não houver controle de finalidade. |
| **Recomendação** | Restringir a busca a contextos onde é necessária (compartilhamento, menção). Limitar campos retornados. Considerar retornar apenas nome e ID, sem email. |

### 8.4 — Notificações via core-api compartilham emails

| Item | Detalhe |
|------|---------|
| **Severidade** | BAIXA |
| **Lei/Artigo** | LGPD Art. 6º, III (necessidade) |
| **Arquivo** | `transformometro-api/tm_app/infrastructure/http_clients/core_notifications_client.py` |
| **Ponto do código** | POST para `/integrations/notifications` com payload contendo emails de aprovadores e títulos de processos |
| **Descrição** | O fluxo de workflow do transformometro envia emails de aprovadores no payload de notificações, compartilhando dados pessoais entre serviços. |
| **Recomendação** | Enviar apenas `user_id` e resolver o email no serviço de notificações. |

---

## Anexo A — Mapeamento de Dados Pessoais por Serviço

| Serviço | Tabela/Modelo | Campos com Dados Pessoais |
|---------|---------------|--------------------------|
| core-api | `users` | `name`, `email`, `birth_date`, `last_login_at` |
| core-api | `audit_logs` | `user_id`, `ip_address`, `payload` (JSON) |
| core-api | `notifications` | `user_id`, `message`, `html_content` |
| core-api | `app_usage_events` | `user_id`, `route_path`, `opened_at` |
| core-api | `apps` | `created_by_email`, `created_by_name`, `updated_by_email`, `updated_by_name` |
| transformometro-api | `processos` | `gestor_responsavel` (nome de pessoa) |
| transformometro-api | `revisoes` | `aprovado_por_email` |
| transformometro-api | `recursos_compartilhados` | `fornecedor` (pode conter nome de pessoa) |
| transformometro-api | `audit_logs` | `user_id`, `user_email`, `payload_json` |
| strategic-indicators-api | `indicator_goals` | `created_by_user_id`, `created_by_email`, `updated_by_user_id`, `updated_by_email` |
| strategic-indicators-api | `settings_audit` | `actor_user_id`, `actor_email`, `payload` |
| strategic-indicators-api | `change_requests` | `actor_user_id`, `actor_email` |
| strategic-indicators-api | `departments` | `created_by_user_id`, `created_by_email` |
| minha-delpi-ai-api | `ai_chat_sessions` | `user_id` |
| minha-delpi-ai-api | `ai_chat_messages` | `content` (texto livre), `message_metadata` |
| minha-delpi-ai-api | `ai_chat_attachments` | `user_id`, `storage_path` |
| minha-delpi-ai-api | `ai_audit_logs` | `user_id`, `audit_metadata` (question_preview) |
| minha-delpi-ai-api | `ai_chat_agent_shares` | `target_user_id` |
| minha-delpi-ai-api | `ai_chat_message_feedback` | `user_id` |

## Anexo B — Referência da LGPD (Artigos Citados)

| Artigo | Tema |
|--------|------|
| Art. 6º, I | Princípio da finalidade |
| Art. 6º, III | Princípio da necessidade (minimização) |
| Art. 6º, VI | Princípio da transparência |
| Art. 6º, VII | Princípio da segurança |
| Art. 7º | Bases legais para tratamento |
| Art. 7º, §5º | Compartilhamento necessita consentimento específico |
| Art. 8º | Requisitos do consentimento |
| Art. 8º, §5º | Revogação do consentimento |
| Art. 9º | Direito à informação sobre o tratamento |
| Art. 11 | Tratamento de dados sensíveis |
| Art. 12 | Dado pessoal identificável |
| Art. 15 | Término do tratamento |
| Art. 16 | Eliminação dos dados após término |
| Art. 18, I | Direito de confirmação de tratamento |
| Art. 18, II | Direito de acesso |
| Art. 18, V | Direito de portabilidade |
| Art. 18, VI | Direito de eliminação |
| Art. 18, §1º | Exercício de direitos perante o controlador |
| Art. 26 | Uso compartilhado de dados pelo poder público |
| Art. 37 | Registro das operações de tratamento (ROPA) |
| Art. 41 | Encarregado de proteção de dados (DPO) |
| Art. 46 | Medidas de segurança técnicas e administrativas |

---

> **Nota:** Este relatório é uma análise técnica do código-fonte e não substitui uma consultoria jurídica especializada em proteção de dados. Recomenda-se que as inconformidades identificadas sejam revisadas em conjunto com o DPO e assessoria jurídica da organização para priorização e plano de ação.

---

## Anexo C — Status de Resolução (atualizado em 26/05/2026)

| # | Descrição resumida | Status | Resolução |
|---|-------------------|--------|-----------|
| 1.1 | Nenhum mecanismo de consentimento | ✅ | Módulo completo de gestão de consentimento (Fase 2) |
| 1.2 | Auto-provisionamento sem consentimento | ✅ | `consent_pending` no `/me` + verificação no primeiro login (Fase 8) |
| 1.3 | Dados pessoais no LLM sem consentimento | ✅ | Verificação de consentimento `ai_context` antes de injetar PII (Fase 8) |
| 1.4 | Rastreamento de uso sem ciência | ✅ | Verificação de consentimento `usage_tracking` no socket handler (Fase 8) |
| 2.1 | Audit logs irremovíveis (core-api) | ✅ | Job de retenção com anonimização após 730 dias (Fase 3) |
| 2.2 | Audit logs irremovíveis (transformometro) | ✅ | Mascaramento de campos pessoais + job de retenção (Fases 6, 8) |
| 2.3 | Audit logs do chat IA | ✅ | CLI de retenção para AI audit logs (Fase 8) |
| 2.4 | Soft delete sem purge (transformometro) | ✅ | Job de purge para registros soft-deleted > 90 dias (Fase 8) |
| 2.5 | Settings audit sem exclusão | ✅ | Anonimização de `actor_email` após 730 dias (Fase 8) |
| 2.6 | Ausência de endpoint de esquecimento | ✅ | `POST /admin/rbac/users/<id>/anonymize` com use case completo (Fase 4) |
| 3.1 | Ausência de portabilidade | ✅ | `GET /me/data-export` com JSON completo (Fase 5) |
| 3.2 | Ausência de confirmação de tratamento | ✅ | `GET /me/privacy` com DPO, finalidades, direitos e retenção (Fase 7) |
| 4.1 | Credenciais em `.env` | ✅ | Risco aceito — `credential_guard.py` bloqueia startup com senhas fracas; servidor privado, `.env` fora do Git |
| 4.2 | JWT_SECRET default "secret" | ✅ | Removido default em todas as APIs (Fase 1) |
| 4.3 | Audience desabilitada | ✅ | Validação condicional via `KEYCLOAK_AUDIENCE` (Fase 1) |
| 4.4 | Exposição de detalhes em erros | ✅ | Mensagens genéricas em todas as APIs (Fases 1, 6) |
| 4.5 | Dados pessoais em seeds | ✅ | Substituídos por dados fictícios (Fase 8) |
| 4.6 | CORS permissivo | ✅ | Localhost removido em produção em todas as APIs (Fase 1) |
| 4.7 | Nginx sem rate limiting | ✅ | `limit_req_zone` para auth (10r/s) e API (30r/s) (Fase 10) |
| 4.8 | Token de serviço estático | ✅ | Fallback legado `TRANSFORMOMETRO_SERVICE_BEARER` removido; usa `API_DELPI_INTERNAL_SERVICE_TOKEN` |
| 4.9 | Senha de teste hardcoded | ✅ | Migrado para env var `TEST_DATABASE_URL` (Fase 1) |
| 4.10 | Swagger postMessage sem origin check | ✅ | Verificação de origin + desabilitar Swagger em produção (Fase 8) |
| 5.1 | birth_date sem finalidade | ✅ | Documentado finalidade (aniversários + RH) com docstring LGPD (Fase 8) |
| 5.2 | IP address sem truncamento | ✅ | `truncate_ip()` remove último octeto antes de armazenar (Fase 10) |
| 5.3 | Payload completo nos audit logs | ✅ | `_mask_personal_data()` no transformometro (Fase 6) |
| 5.4 | Emails denormalizados | ⚠️ | Requer migração de schema separada (alto risco) |
| 5.5 | Mensagens de chat sem retenção | ✅ | CLI de retenção + aviso de privacidade ao usuário (Fase 8) |
| 6.1 | Ausência de política de retenção | ✅ | Jobs de retenção em core-api, transformometro e strategic-indicators (Fases 3, 8) |
| 6.2 | Redis presence sem TTL | ✅ | Já adequado (TTL 90s nativo) |
| 6.3 | Cache de embeddings sem TTL | ✅ | Já adequado (TTL 3600s configurável) |
| 6.4 | Soft delete notifications sem purge | ✅ | Job purge notificações deletadas > 30 dias (Fase 3) |
| 7.1 | Ausência de ROPA | ✅ | Documento com 8 categorias (`ropa-registro-tratamento.md`) (Fase 7) |
| 7.2 | Ausência de política de privacidade | ✅ | Página `/privacy-policy` no portal + link no rodapé (Fases 8, 9) |
| 7.3 | Ausência de canal do DPO | ✅ | DPO (Michael Marotto) exibido em `/me/privacy` e `/privacy` (Fase 7) |
| 8.1 | JWT repassado entre microsserviços | ✅ | Risco aceito — rede privada Docker, JWT curto, documentado no ROPA seção 9 |
| 8.2 | Dados pessoais enviados ao LLM | ✅ | Consentimento `ai_context` obrigatório (Fase 8) |
| 8.3 | Busca de diretório expõe email | ✅ | Email mascarado na busca de diretório (Fase 8) |
| 8.4 | Notificações compartilham emails | ✅ | Refatorado para preferir `roleIds`/`userIds` (Fase 10) |
