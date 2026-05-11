from dataclasses import dataclass, field


@dataclass(frozen=True)
class AuthenticatedUser:
    sub: str
    email: str
    name: str | None = None
    roles: list[str] = field(default_factory=list)
    groups: list[str] = field(default_factory=list)
