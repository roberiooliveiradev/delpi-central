"""GLPI #887: read-only discovery of report-eligible direct-team managers.

The caller supplies a *root* RH manager. A root covers only the subtree
returned by the Portal RH hierarchy API, not every independent company tree.
All user IDs come from explicitly verified Core bindings.
"""

from __future__ import annotations

from collections import Counter
from uuid import UUID

from app.application.services.organization_team_service import OrganizationTeamService


class DirectReportManagerDiscoveryService:
    MAX_ROOT_MEMBERS = 500

    def __init__(self, team_service: OrganizationTeamService, users) -> None:
        self.team_service = team_service
        self.users = users

    def preview(self, root_registration: str) -> dict:
        snapshot = self.team_service.get_team(
            root_registration, include_indirect=True, include_inactive=False
        )
        members = snapshot["members"]
        if len(members) > self.MAX_ROOT_MEMBERS:
            raise ValueError("Hierarquia de origem excede 500 pessoas.")

        people = {snapshot["manager"]["registration"]: snapshot["manager"]}
        for item in members:
            registration = item["registration"]
            if registration in people:
                raise ValueError("Matrícula RH duplicada na hierarquia de origem.")
            if not item["active"]:
                raise ValueError("Colaborador inativo em hierarquia filtrada.")
            people[registration] = item

        counts = Counter()
        for item in members:
            parent = item.get("managerRegistration")
            if not isinstance(parent, str) or parent not in people:
                raise ValueError("Hierarquia RH contém gestor fora da subárvore consultada.")
            if parent == item["registration"]:
                raise ValueError("Colaborador não pode gerenciar a si próprio.")
            counts[parent] += 1

        candidates = []
        for registration, count in sorted(counts.items()):
            manager = people[registration]
            status = "missing_mapping"
            user_id = manager.get("coreUserId")
            email = None
            if manager.get("active") and manager.get("identityStatus") == "mapped" and user_id:
                core_user = self.users.get_by_id(UUID(str(user_id)))
                if (
                    core_user is not None
                    and getattr(core_user, "active", False)
                    and isinstance(getattr(core_user, "email", None), str)
                    and "@" in core_user.email
                    and "***" not in core_user.email
                ):
                    email = core_user.email.strip().lower()
                    status = "ready"
                else:
                    status = "missing_email"

            candidates.append({
                "registration": registration,
                "fullName": manager["fullName"],
                "directCount": int(count),
                "status": status,
                "userId": str(user_id) if status == "ready" else None,
                "email": email,
            })

        return {
            "source": "portal-rh+verified-core",
            "rootRegistration": snapshot["manager"]["registration"],
            "scopedToRoot": True,
            "subtreeMembers": len(members),
            "managerCount": len(candidates),
            "readyCount": sum(item["status"] == "ready" for item in candidates),
            "candidates": candidates,
            "readOnly": True,
            "note": (
                "Cobre apenas a hierarquia desta matrícula raiz. "
                "Outras árvores RH independentes precisam ser informadas separadamente. "
                "Não cria relatórios, vínculos nem e-mails."
            ),
        }
