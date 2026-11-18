"""Resolve HR manager hierarchy to verified, active Core users.

Never resolves by name/email or Protheus SYS_USR; no hierarchy is cached.
"""

from __future__ import annotations

from app.infrastructure.gateways.portal_rh_organization_gateway import (
    PortalRhOrganizationGateway,
)
from app.infrastructure.persistence.sqlalchemy.user_hr_registration_repository import (
    SqlAlchemyUserHrRegistrationRepository,
)


class OrganizationTeamService:
    def __init__(
        self,
        gateway: PortalRhOrganizationGateway,
        mappings: SqlAlchemyUserHrRegistrationRepository,
    ) -> None:
        self.gateway = gateway
        self.mappings = mappings

    def get_team(
        self,
        registration: str,
        *,
        include_indirect: bool = False,
        include_inactive: bool = False,
    ) -> dict:
        result = self.gateway.get_team(
            registration,
            include_indirect=include_indirect,
            include_inactive=include_inactive,
        )
        manager = result["manager"]
        members = result["members"]
        registrations = {manager["registration"]} | {
            row["registration"] for row in members
        }
        lookup = self.mappings.get_core_user_ids(registrations)

        def serialize_person(person: dict) -> dict:
            reg = person["registration"]
            # A collaborator inactive in RH is not eligible for nominal reporting,
            # even if the linked Core account has not yet been deactivated.
            core_user_id = lookup.get(reg) if person["active"] else None
            return {
                "registration": reg,
                "fullName": person["full_name"],
                "branchCode": person["branch_code"],
                "active": person["active"],
                "coreUserId": core_user_id,
                "identityStatus": "mapped" if core_user_id else "unmapped",
            }

        items = []
        for item in members:
            row = serialize_person(item)
            row["relationship"] = item["relationship"]
            row["managerRegistration"] = item["manager_registration"]
            items.append(row)

        return {
            "source": "portal-rh",
            "manager": serialize_person(manager),
            "members": items,
            "count": len(items),
            "unmappedCount": sum(x["coreUserId"] is None for x in items),
            "includeIndirect": result["includeIndirect"],
            "includeInactive": result["includeInactive"],
        }
