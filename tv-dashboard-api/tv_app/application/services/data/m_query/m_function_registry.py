"""Registry declarativo deny-by-default de funções M DELPI."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

REGISTRY_PATH = Path(__file__).resolve().parents[4] / "content" / "m_delpi_v1_functions.json"


@dataclass(frozen=True, slots=True)
class MFunctionSpec:
    name: str
    kind: str
    category: str
    signature: str
    description: str
    parameters: tuple[str, ...]
    examples: tuple[str, ...]
    introduced_in: str
    availability: Mapping[str, bool]
    min_args: int
    max_args: int
    argument_types: tuple[str, ...]
    return_type: str
    parameter_expression: bool
    variadic: bool
    lazy_args: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "category": self.category,
            "signature": self.signature,
            "description": self.description,
            "parameters": list(self.parameters),
            "examples": list(self.examples),
            "introducedIn": self.introduced_in,
            "availability": dict(self.availability),
            "minArgs": self.min_args,
            "maxArgs": self.max_args,
            "argumentTypes": list(self.argument_types),
            "returnType": self.return_type,
            "parameterExpression": self.parameter_expression,
            **({"variadic": True} if self.variadic else {}),
            **({"lazyArgs": self.lazy_args} if self.lazy_args else {}),
        }

    def compact_dict(self) -> dict[str, Any]:
        """Projeção mínima para authoring (VISTA actions / frontend)."""
        return {
            "name": self.name,
            "argumentTypes": list(self.argument_types),
            "returnType": self.return_type,
            "minArgs": self.min_args,
            "maxArgs": self.max_args,
            "category": self.category,
            **({"variadic": True} if self.variadic else {}),
            **({"lazyArgs": self.lazy_args} if self.lazy_args else {}),
        }


@dataclass(frozen=True, slots=True)
class MFunctionRegistry:
    profile: str
    version: str
    functions: Mapping[str, MFunctionSpec]

    def resolve(self, name: str) -> MFunctionSpec | None:
        return self.functions.get(name)

    def catalog(self) -> list[dict[str, Any]]:
        return [self.functions[name].to_dict() for name in sorted(self.functions)]


@lru_cache(maxsize=1)
def get_function_registry() -> MFunctionRegistry:
    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    specs: dict[str, MFunctionSpec] = {}
    for item in payload["functions"]:
        spec = MFunctionSpec(
            name=str(item["name"]),
            kind=str(item["kind"]),
            category=str(item["category"]),
            signature=str(item["signature"]),
            description=str(item["description"]),
            parameters=tuple(str(value) for value in item["parameters"]),
            examples=tuple(str(value) for value in item["examples"]),
            introduced_in=str(item["introducedIn"]),
            availability=MappingProxyType(
                {str(key): bool(value) for key, value in item["availability"].items()}
            ),
            min_args=int(item["minArgs"]),
            max_args=int(item["maxArgs"]),
            argument_types=tuple(
                str(value) for value in item.get("argumentTypes") or ()
            ),
            return_type=str(item.get("returnType") or "any"),
            parameter_expression=bool(item.get("parameterExpression")),
            variadic=bool(item.get("variadic")),
            lazy_args=(
                str(item["lazyArgs"]) if item.get("lazyArgs") is not None else None
            ),
        )
        if spec.name in specs:
            raise ValueError(f"Função duplicada no registry: {spec.name}")
        specs[spec.name] = spec
    return MFunctionRegistry(
        profile=str(payload["profile"]),
        version=str(payload["registryVersion"]),
        functions=MappingProxyType(specs),
    )
