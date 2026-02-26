# app/application/dto/rbac_admin_dto.py

from dataclasses import dataclass


@dataclass
class UserAdminDTO:
    id: str
    email: str
    name: str
    is_superadmin: bool
    active: bool


@dataclass
class RoleAdminDTO:
    id: str
    name: str
    description: str | None


@dataclass
class GroupAdminDTO:
    id: str
    name: str
    description: str | None


@dataclass
class PermissionAdminDTO:
    id: str
    code: str
    module: str
    description: str | None