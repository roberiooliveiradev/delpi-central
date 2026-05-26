"""
Constantes de privacidade e LGPD.
Centraliza informações do DPO e política de privacidade.
"""

DPO_EMAIL = "dpo@empresa.com"
DPO_NAME = "Encarregado de Proteção de Dados"

PRIVACY_POLICY_URL = "/privacy-policy"

CONSENT_PURPOSES = {
    "data_processing": "Tratamento geral de dados pessoais para funcionamento do sistema",
    "analytics": "Coleta de métricas de uso para melhoria do produto",
    "ai_context": "Envio de dados do perfil como contexto para o assistente de IA",
    "birthday_notifications": "Uso da data de nascimento para notificações de aniversário",
    "usage_tracking": "Rastreamento de uso de aplicativos e rotas acessadas",
}

DATA_RETENTION_DAYS = {
    "audit_logs": 730,
    "notifications": 180,
    "deleted_notifications": 30,
    "usage_events": 365,
    "consent_records": 1825,
}
