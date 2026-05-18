# app/domain/notifications/notification_templates.py

from dataclasses import dataclass


@dataclass(frozen=True)
class NotificationTemplateSpec:
    id: str
    category: str
    default_type: str
    default_title: str
    default_message: str
    required_vars: tuple[str, ...]
    optional_vars: tuple[str, ...] = ()
    recipient_vars: tuple[str, ...] = ()


NOTIFICATION_TEMPLATES: dict[str, NotificationTemplateSpec] = {
    "welcome_v1": NotificationTemplateSpec(
        id="welcome_v1",
        category="welcome",
        default_type="success",
        default_title="Bem-vindo à Minha DELPI",
        default_message="Olá, {userName}! Sua conta está pronta para explorar os aplicativos.",
        required_vars=(),
        recipient_vars=("userName",),
    ),
    "birthday_v1": NotificationTemplateSpec(
        id="birthday_v1",
        category="birthday",
        default_type="success",
        default_title="Feliz aniversário!",
        default_message="A equipe DELPI deseja um excelente dia, {userName}!",
        required_vars=(),
        recipient_vars=("userName",),
    ),
    "company_event_v1": NotificationTemplateSpec(
        id="company_event_v1",
        category="company_event",
        default_type="info",
        default_title="Evento da empresa",
        default_message="Você está convidado(a) para {eventName}.",
        required_vars=("eventName",),
        optional_vars=("eventDate", "location"),
    ),
}

ALLOWED_TEMPLATE_IDS = frozenset(NOTIFICATION_TEMPLATES.keys())
