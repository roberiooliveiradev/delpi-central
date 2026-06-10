# app/domain/portal_tour/portal_tour_quest_catalog.py
"""
Catálogo canônico de desafios do tour do portal.

Ao lançar uma funcionalidade nova:
1. Adicionar entrada aqui (id estável, permissões, optional, introduced_in_version).
2. Registrar interação DOM no portal (`portalTourQuestRegistry.ts`).
3. Bump CURRENT_PORTAL_TOUR_VERSION quando quiser reexibir o tour a quem concluiu.
"""

from dataclasses import dataclass


CURRENT_PORTAL_TOUR_VERSION = "2026-06-portal-v6-explore"

ADMIN_PERMISSION = "rbac.manage"


@dataclass(frozen=True)
class PortalTourQuestDefinition:
    id: str
    title: str
    hint: str
    category: str
    scope: str
    optional: bool = False
    required_permissions: tuple[str, ...] = ()
    introduced_in_version: str = CURRENT_PORTAL_TOUR_VERSION


CATEGORY_LABELS: dict[str, str] = {
    "apps": "Apps e favoritos",
    "home": "Página inicial",
    "notifications": "Notificações",
    "profile": "Perfil e RBAC",
    "privacy": "Privacidade",
    "personalization": "Personalização",
    "admin": "Administração",
}

CATEGORY_ORDER: tuple[str, ...] = (
    "apps",
    "home",
    "notifications",
    "profile",
    "privacy",
    "personalization",
    "admin",
)


def _quest(
    *,
    id: str,
    title: str,
    hint: str,
    category: str,
    scope: str,
    optional: bool = False,
    required_permissions: tuple[str, ...] = (),
    introduced_in_version: str = CURRENT_PORTAL_TOUR_VERSION,
) -> PortalTourQuestDefinition:
    return PortalTourQuestDefinition(
        id=id,
        title=title,
        hint=hint,
        category=category,
        scope=scope,
        optional=optional,
        required_permissions=required_permissions,
        introduced_in_version=introduced_in_version,
    )


def get_portal_tour_quest_catalog() -> list[PortalTourQuestDefinition]:
    """Lista completa de desafios — inclui os restritos por permissão."""
    return [
        _quest(
            id="sidebar-favorites",
            title="Favoritos na barra",
            hint="Acesse ou reorganize apps fixados.",
            category="apps",
            scope="sidebar",
        ),
        _quest(
            id="open-apps",
            title="Catálogo de apps",
            hint="Abra a lista completa de aplicativos.",
            category="apps",
            scope="sidebar",
        ),
        _quest(
            id="pin-app",
            title="Fixar um app",
            hint="Salve um app nos favoritos pelo pin.",
            category="apps",
            scope="launcher",
        ),
        _quest(
            id="launcher-search",
            title="Buscar no catálogo",
            hint="Encontre apps e rotas pela busca.",
            category="apps",
            scope="launcher",
        ),
        _quest(
            id="home-summary-notifications",
            title="Resumo de notificações",
            hint="Veja quantas mensagens não lidas você tem.",
            category="home",
            scope="home",
        ),
        _quest(
            id="home-favorites",
            title="Favoritos na home",
            hint="Gerencie favoritos direto da página inicial.",
            category="home",
            scope="home",
        ),
        _quest(
            id="home-recent",
            title="Apps recentes",
            hint="Retome de onde parou.",
            category="home",
            scope="home",
        ),
        _quest(
            id="home-notifications",
            title="Notificações na home",
            hint="Acompanhe avisos sem sair da home.",
            category="home",
            scope="home",
        ),
        _quest(
            id="sidebar-notifications",
            title="Sino na sidebar",
            hint="Prévia rápida sem sair da tela atual.",
            category="notifications",
            scope="sidebar",
        ),
        _quest(
            id="page-notifications-inbox",
            title="Central de notificações",
            hint="Histórico completo com filtros.",
            category="notifications",
            scope="notifications",
        ),
        _quest(
            id="page-notifications-filter",
            title="Filtrar notificações",
            hint="Refine por status, categoria ou importantes.",
            category="notifications",
            scope="notifications",
        ),
        _quest(
            id="page-notifications-preferences",
            title="Preferências de notificação",
            hint="Escolha o que deseja receber.",
            category="notifications",
            scope="notifications",
        ),
        _quest(
            id="sidebar-profile",
            title="Menu de perfil",
            hint="Atalho para conta e privacidade.",
            category="profile",
            scope="sidebar",
        ),
        _quest(
            id="page-profile-info",
            title="Dados da conta",
            hint="Nome, e-mail e status de superadmin.",
            category="profile",
            scope="profile",
        ),
        _quest(
            id="page-profile-rbac",
            title="Grupos, papéis e permissões",
            hint="Entenda seu acesso na plataforma.",
            category="profile",
            scope="profile",
        ),
        _quest(
            id="page-profile-apps",
            title="Apps no perfil",
            hint="Todos os aplicativos liberados para você.",
            category="profile",
            scope="profile",
        ),
        _quest(
            id="page-profile-tour-restart",
            title="Repetir o tour",
            hint="Revise as funcionalidades quando quiser.",
            category="profile",
            scope="profile",
        ),
        _quest(
            id="page-privacy-consent",
            title="Consentimentos LGPD",
            hint="Gerencie finalidades de uso de dados.",
            category="privacy",
            scope="privacy",
        ),
        _quest(
            id="page-privacy-export",
            title="Exportar meus dados",
            hint="Solicite uma cópia dos seus dados.",
            category="privacy",
            scope="privacy",
        ),
        _quest(
            id="sidebar-theme",
            title="Personalizar tema",
            hint="Claro, escuro ou automático.",
            category="personalization",
            scope="sidebar",
        ),
        _quest(
            id="sidebar-admin",
            title="Entrar no Admin",
            hint="Atalho para gestão da plataforma.",
            category="admin",
            scope="sidebar",
            optional=True,
            required_permissions=(ADMIN_PERMISSION,),
        ),
        _quest(
            id="page-admin-users",
            title="Usuários (RBAC)",
            hint="Vínculos de acesso por pessoa.",
            category="admin",
            scope="admin",
            optional=True,
            required_permissions=(ADMIN_PERMISSION,),
        ),
        _quest(
            id="page-admin-roles",
            title="Papéis",
            hint="Perfis reutilizáveis de permissão.",
            category="admin",
            scope="admin",
            optional=True,
            required_permissions=(ADMIN_PERMISSION,),
        ),
        _quest(
            id="page-admin-permissions",
            title="Permissões",
            hint="Catálogo fino de ações na plataforma.",
            category="admin",
            scope="admin",
            optional=True,
            required_permissions=(ADMIN_PERMISSION,),
        ),
        _quest(
            id="page-admin-apps",
            title="Aplicações (Admin)",
            hint="Cadastro e manifestos de apps.",
            category="admin",
            scope="admin",
            optional=True,
            required_permissions=(ADMIN_PERMISSION,),
        ),
    ]


def get_quest_by_id(quest_id: str) -> PortalTourQuestDefinition | None:
    normalized = (quest_id or "").strip()
    if not normalized:
        return None
    for quest in get_portal_tour_quest_catalog():
        if quest.id == normalized:
            return quest
    return None
