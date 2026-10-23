# ROPA — Registro de Operações de Tratamento de Dados Pessoais

**Controlador:** DELPI Energia & Conectividade  
**Encarregado (DPO):** Michael Marotto — ti@delpi.com.br  
**Última atualização:** 26/05/2026

---

## 1. Cadastro de Usuários (core-api)

| Campo | Detalhe |
|-------|---------|
| **Dados tratados** | Nome, email, data de nascimento, último login |
| **Finalidade** | Autenticação, controle de acesso (RBAC), personalização |
| **Base legal** | Execução de contrato (Art. 7º, V) / Legítimo interesse (Art. 7º, IX) |
| **Retenção** | Enquanto a conta estiver ativa; anonimizado após solicitação |
| **Compartilhamento** | Keycloak (autenticação), minha-delpi-ai-api (contexto do chat, com consentimento) |

## 2. Logs de Auditoria (core-api, transformometro-api, strategic-indicators-api)

| Campo | Detalhe |
|-------|---------|
| **Dados tratados** | User ID, endereço IP truncado (core-api), email anonimizado (transformometro/strategic-indicators), payload mascarado |
| **Finalidade** | Segurança, rastreabilidade, conformidade |
| **Base legal** | Legítimo interesse (Art. 7º, IX) / Obrigação legal (Art. 7º, II) |
| **Retenção** | 2 anos; IP e payload anonimizados após o prazo |
| **Compartilhamento** | Interno apenas |
| **Medidas de minimização** | IP truncado no último octeto antes de armazenar; campos pessoais mascarados no transformometro |

## 3. Notificações (core-api)

| Campo | Detalhe |
|-------|---------|
| **Dados tratados** | User ID, conteúdo da mensagem (pode incluir nomes) |
| **Finalidade** | Comunicação com o usuário |
| **Base legal** | Execução de contrato (Art. 7º, V) |
| **Retenção** | 180 dias; soft-deleted purgados após 30 dias |
| **Compartilhamento** | Interno apenas |

## 4. Rastreamento de Uso (core-api)

| Campo | Detalhe |
|-------|---------|
| **Dados tratados** | User ID, app acessado, rota, timestamp, plugin originador (`caller_app_id`, opcional) |
| **Finalidade** | Analytics de uso, melhoria do produto, identificação de apps subutilizados |
| **Base legal** | Consentimento (Art. 7º, I) — requer consentimento `usage_tracking` |
| **Retenção** | 1 ano (job `data_retention_job`); purge imediato ao revogar consentimento ou anonimizar titular |
| **Compartilhamento** | Interno apenas |
| **Canais** | Socket.IO (portal), integração HTTP (api-delpi → `POST /integrations/app-usage/record`) |

## 5. Chat de IA (minha-delpi-ai-api)

| Campo | Detalhe |
|-------|---------|
| **Dados tratados** | User ID, conteúdo de mensagens (texto livre), contexto de perfil |
| **Finalidade** | Assistente de IA conversacional |
| **Base legal** | Consentimento (Art. 7º, I) — requer consentimento `ai_context` para dados de perfil |
| **Retenção** | Mensagens: 12 meses; titular pode excluir sessões a qualquer momento |
| **Compartilhamento** | Modelo LLM (Ollama — on-premise, rede interna Docker) |

## 6. Processos do Transformômetro (transformometro-api)

| Campo | Detalhe |
|-------|---------|
| **Dados tratados** | Nome do gestor responsável, email do aprovador |
| **Finalidade** | Gestão de processos e workflow de aprovação |
| **Base legal** | Execução de contrato (Art. 7º, V) |
| **Retenção** | Enquanto o processo estiver ativo; soft-deleted purgados após 90 dias; dados pessoais mascarados nos audit logs |
| **Compartilhamento** | core-api (notificações de workflow via roleIds/userIds) |

## 7. Indicadores Estratégicos (strategic-indicators-api)

| Campo | Detalhe |
|-------|---------|
| **Dados tratados** | User ID do criador/atualizador de metas e configurações (email não é mais gravado em novos registros — Art. 6 III) |
| **Finalidade** | Rastreabilidade de configurações |
| **Base legal** | Legítimo interesse (Art. 7º, IX) |
| **Retenção** | Enquanto o indicador estiver ativo; settings_audit anonimizado após 2 anos; colunas `*_by_email` históricas anonimizadas pelo job de retenção |
| **Compartilhamento** | Interno apenas |

## 8. Consentimentos (core-api)

| Campo | Detalhe |
|-------|---------|
| **Dados tratados** | User ID, finalidade, IP truncado, user-agent, timestamps |
| **Finalidade** | Registro de consentimento conforme LGPD |
| **Base legal** | Obrigação legal (Art. 7º, II) |
| **Coleta** | Modal obrigatório exibido após login (Art. 8 §1 — consentimento informado): (1) leitura da Política de Privacidade com scroll obrigatório, (2) seleção de consentimentos com `data_processing` obrigatório. O modal não reaparece após aceite. O titular pode alterar preferências a qualquer momento em "Privacidade de Dados". |
| **Retenção** | 5 anos após revogação (evidência legal) |
| **Compartilhamento** | Interno apenas |

---

## 9. Comunicação Inter-serviço (Risco Aceito — Art. 46)

| Campo | Detalhe |
|-------|---------|
| **Dados transferidos** | JWT do usuário (contém sub, email, name, roles) |
| **Fluxo** | api-delpi → transformometro-api; strategic-indicators-api → api-delpi; minha-delpi-ai-api → external actions |
| **Justificativa** | As APIs downstream necessitam do contexto de identidade e permissões (RBAC) do titular para aplicar controle de acesso. Não é viável usar token de serviço sem perder o contexto do usuário. |
| **Mitigações aplicadas** | (1) Todos os serviços operam na mesma rede privada Docker (`delpi-network`), sem exposição externa. (2) JWT possui expiração curta (padrão Keycloak). (3) O JWT não é repassado a serviços fora da infraestrutura. (4) O token interno `API_DELPI_INTERNAL_SERVICE_TOKEN` é usado como fallback quando não há contexto de usuário. |
| **Classificação** | **Risco aceito** — comunicação interna em rede privada com tokens de curta duração. |
| **Ref. auditoria** | Inconformidade 8.1 |

---

## Canal do Encarregado (DPO)

Para exercer seus direitos (acesso, correção, exclusão, portabilidade), entre em contato:
- **DPO:** Michael Marotto
- **Email:** ti@delpi.com.br
- **Endpoint:** `GET /me/data-export` (portabilidade automatizada)
- **Endpoint:** `GET /me/consents` (gestão de consentimentos)
- **Endpoint:** `GET /me/privacy` (informações sobre tratamento)
- **Portal:** Seção "Privacidade e Dados" no menu do usuário
- **Modal de consentimento:** Exibido automaticamente no primeiro login — leitura obrigatória da política + aceite de consentimentos
