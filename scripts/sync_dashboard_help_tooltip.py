#!/usr/bin/env python3
"""Replica HelpTooltip.tsx do dashboard-commercial para os demais dashboards."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "plugins/dashboard-commercial/src/components/HelpTooltip.tsx"

TARGET_PLUGINS: list[tuple[str, str, str | None, str]] = [
    ("plugins/dashboard-hr", "dh", "dh-field__label", "dh-field__label"),
    ("plugins/dashboard-production", "dp", "dp-field__label", "dp-field__label"),
    ("plugins/dashboard-financial", "ds", "ds-field__label", "ds-field__label"),
    ("plugins/dashboard-supplies", "ds", "ds-field__label", "ds-field__label"),
    ("plugins/dashboard-engineering", "ds", "ds-field__label", "ds-field__label"),
    ("plugins/dashboard-quality", "dq", "dq-field__label", "dq-field__label"),
    ("plugins/dashboard-lmps", "lmps", "lmps-field__label", "lmps-field__label"),
    ("plugins/quality-action-plans", "pac", None, "pac-field__label-row"),
]

TITLE_WITH_HELP = '''
export function TitleWithHelp({
  title,
  hint,
  className,
}: {
  title: string;
  hint?: string;
  className?: string;
}) {
  return (
    <span className={`pac-title-with-help${className ? ` ${className}` : ""}`}>
      <span>{title}</span>
      {hint ? <HelpTooltip content={hint} ariaLabel={`Ajuda: ${title}`} /> : null}
    </span>
  );
}
'''


def transform(content: str, prefix: str, field_label_class: str) -> str:
    content = content.replace("dc-help-tooltip", f"{prefix}-help-tooltip")
    if field_label_class == "pac-field__label-row":
        content = content.replace(
            'export function FieldLabel({ label, hint }: { label: string; hint?: string }) {\n'
            '  return (\n'
            '    <span className="dc-field__label">\n'
            '      {label}\n'
            '      {hint ? <HelpTooltip content={hint} ariaLabel={`Ajuda: ${label}`} /> : null}\n'
            '    </span>\n'
            '  );\n'
            '}',
            'export function FieldLabel({ label, hint }: { label: string; hint?: string }) {\n'
            '  return (\n'
            '    <span className="pac-field__label-row">\n'
            '      <span>{label}</span>\n'
            '      {hint ? <HelpTooltip content={hint} ariaLabel={`Ajuda: ${label}`} /> : null}\n'
            '    </span>\n'
            '  );\n'
            '}',
        )
        content = content.rstrip() + TITLE_WITH_HELP
    else:
        content = content.replace(
            'className="dc-field__label"',
            f'className="{field_label_class}"',
        )
    return content


def main() -> None:
    source_content = SOURCE.read_text(encoding="utf-8")
    for plugin_rel, prefix, _legacy, field_label_class in TARGET_PLUGINS:
        target = ROOT / plugin_rel / "src/components/HelpTooltip.tsx"
        if plugin_rel == "plugins/quality-action-plans":
            target = ROOT / plugin_rel / "src/components/ui/HelpTooltip.tsx"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            transform(source_content, prefix, field_label_class),
            encoding="utf-8",
        )
        print(f"OK {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
