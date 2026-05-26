# ROPA — Registro de Operações de Tratamento de Dados Pessoais

**Controlador:** [Nome da empresa]
**Encarregado (DPO):** [Nome] — [email@empresa.com]
**Última atualização:** 26/05/2026

---

## 1. Cadastro de Usuários (core-api)

| Campo | Detalhe |
|-------|---------|
| **Dados tratados** | Nome, email, data de nascimento, último login |
| **Finalidade** | Autenticação, controle de acesso (RBAC), personalização |
| **Base legal** | Execução de contrato (Art. 7º, V) / Legítimo interesse (Art. 7º, IX) |
| **Retenção** | Enquanto a conta estiver ativa; anonimizado após solicitação |
| **Compartilhamento** | Keycloak (autenticação), minha-delpi-ai-api (contexto do chat) |

## 2. Logs de Auditoria (core-api, transformometro-api, strategic-indicators-api)

| Campo | Detalhe |
|-------|---------|
| **Dados tratados** | User ID, endereço IP (core-api), email (transformometro), payload de ações |
| **Finalidade** | Segurança, rastreabilidade, conformidade |
| **Base legal** | Legítimo interesse (Art. 7º, IX) / Obrigação legal (Art. 7º, II) |
| **Retenção** | 2 anos; IP e payload anonimizados após o prazo |
| **Compartilhamento** | Interno apenas |

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
| **Dados tratados** | User ID, app acessado, rota, timestamp |
| **Finalidade** | Analytics de uso, melhoria do produto |
| **Base legal** | Legítimo interesse (Art. 7º, IX) — requer consentimento `usage_tracking` |
| **Retenção** | 1 ano |
| **Compartilhamento** | Interno apenas |

## 5. Chat de IA (minha-delpi-ai-api)

| Campo | Detalhe |
|-------|---------|
| **Dados tratados** | User ID, conteúdo de mensagens (texto livre), contexto de perfil |
| **Finalidade** | Assistente de IA conversacional |
| **Base legal** | Consentimento (Art. 7º, I) — requer consentimento `ai_context` |
| **Retenção** | Enquanto a sessão existir; titular pode excluir sessões |
| **Compartilhamento** | Modelo LLM (Ollama/vLLM — on-premise) |

## 6. Processos do Transformômetro (transformometro-api)

| Campo | Detalhe |
|-------|---------|
| **Dados tratados** | Nome do gestor responsável, email do aprovador |
| **Finalidade** | Gestão de processos e workflow de aprovação |
| **Base legal** | Execução de contrato (Art. 7º, V) |
| **Retenção** | Enquanto o processo estiver ativo; dados pessoais mascarados nos audit logs |
| **Compartilhamento** | core-api (notificações de workflow) |

## 7. Indicadores Estratégicos (strategic-indicators-api)

| Campo | Detalhe |
|-------|---------|
| **Dados tratados** | User ID e email do criador/atualizador de metas e configurações |
| **Finalidade** | Rastreabilidade de configurações |
| **Base legal** | Legítimo interesse (Art. 7º, IX) |
| **Retenção** | Enquanto o indicador estiver ativo |
| **Compartilhamento** | Interno apenas |

## 8. Consentimentos (core-api)

| Campo | Detalhe |
|-------|---------|
| **Dados tratados** | User ID, finalidade, IP, user-agent, timestamps |
| **Finalidade** | Registro de consentimento conforme LGPD |
| **Base legal** | Obrigação legal (Art. 7º, II) |
| **Retenção** | 5 anos após revogação (evidência legal) |
| **Compartilhamento** | Interno apenas |

---

## Canal do Encarregado (DPO)

Para exercer seus direitos (acesso, correção, exclusão, portabilidade), entre em contato:
- **Email:** [dpo@empresa.com]
- **Endpoint:** GET /me/data-export (portabilidade automatizada)
- **Endpoint:** GET /me/consents (gestão de consentimentos)
