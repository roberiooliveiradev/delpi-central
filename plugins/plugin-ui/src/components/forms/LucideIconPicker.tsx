import { useMemo, useState, type CSSProperties, type ComponentType } from "react";
import { Search, X } from "lucide-react";
import * as LucideIcons from "lucide-react";

import {
  CURATED_LUCIDE_ICON_NAMES,
  listLucideIconNames,
  resolveLucideIcon,
  toKebabCase,
  toPascalCaseFromKebab,
} from "./lucideIconResolver";

export type LucideIconPickerLabels = {
  title?: string;
  searchPlaceholder?: string;
  selectedHint?: string;
  emptyHint?: string;
  clear?: string;
  close?: string;
  showingLimit?: string;
};

export type LucideIconPickerProps = {
  value?: string | null;
  /** kebab-case Lucide, ex.: "eye". `null` = remover. */
  onChange: (iconKebab: string | null) => void;
  onClose?: () => void;
  /** Se false, só a lista curada. Default true. */
  curatedOnly?: boolean;
  maxResults?: number;
  title?: string;
  labels?: LucideIconPickerLabels;
  className?: string;
  style?: CSSProperties;
};

type IconCardProps = {
  name: string;
  active?: boolean;
  onSelect: () => void;
};

function IconCard({ name, active, onSelect }: IconCardProps) {
  const Icon = (LucideIcons as unknown as Record<string, ComponentType<{ size?: number }> | undefined>)[
    name
  ];
  if (!Icon) return null;
  const kebab = toKebabCase(name);

  return (
    <button
      type="button"
      className={
        active
          ? "delpi-ui-lucide-icon-card delpi-ui-lucide-icon-card--active"
          : "delpi-ui-lucide-icon-card"
      }
      onClick={onSelect}
      title={kebab}
    >
      <span className="delpi-ui-lucide-icon-card__icon" aria-hidden="true">
        <Icon size={22} />
      </span>
      <span className="delpi-ui-lucide-icon-card__label">{kebab}</span>
    </button>
  );
}

const DEFAULT_LABELS: Required<LucideIconPickerLabels> = {
  title: "Selecionar ícone",
  searchPlaceholder: "Buscar ícone (ex: eye, heart, star…)",
  selectedHint: "Selecionado:",
  emptyHint: "(sem ícone)",
  clear: "Remover ícone",
  close: "Fechar",
  showingLimit: "Mostrando {limit} resultados. Refine a busca.",
};

/** Painel de seleção Lucide (lista curada ou completa). */
export function LucideIconPicker({
  value,
  onChange,
  onClose,
  curatedOnly = true,
  maxResults = 360,
  title,
  labels,
  className,
  style,
}: LucideIconPickerProps) {
  const [query, setQuery] = useState("");
  const L = { ...DEFAULT_LABELS, ...labels };

  const allIcons = useMemo(() => {
    if (curatedOnly) {
      return CURATED_LUCIDE_ICON_NAMES.map((kebab) => toPascalCaseFromKebab(kebab)).filter(
        (pascal) => Boolean((LucideIcons as Record<string, unknown>)[pascal]),
      );
    }
    return listLucideIconNames();
  }, [curatedOnly]);

  const normalizedSelectedPascal = useMemo(() => {
    const current = String(value ?? "").trim();
    if (!current) return "";
    return current.includes("-") ? toPascalCaseFromKebab(current) : current;
  }, [value]);

  const SelectedIcon = useMemo(() => resolveLucideIcon(value), [value]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return allIcons;
    return allIcons.filter((pascal) => {
      const kebab = toKebabCase(pascal);
      return kebab.includes(q) || pascal.toLowerCase().includes(q);
    });
  }, [allIcons, query]);

  const visible = filtered.slice(0, maxResults);
  const rootClass = ["delpi-ui-lucide-icon-picker", className].filter(Boolean).join(" ");

  return (
    <div className={rootClass} style={style} role="dialog" aria-label={title ?? L.title}>
      <header className="delpi-ui-lucide-icon-picker__header">
        <h2>{title ?? L.title}</h2>
        {onClose ? (
          <button
            type="button"
            className="delpi-ui-lucide-icon-picker__close"
            onClick={onClose}
            aria-label={L.close}
          >
            <X size={17} aria-hidden="true" />
          </button>
        ) : null}
      </header>

      <div className="delpi-ui-lucide-icon-picker__body">
        <label className="delpi-ui-lucide-icon-picker__search-wrap">
          <Search size={16} aria-hidden="true" />
          <input
            className="delpi-ui-lucide-icon-picker__search"
            placeholder={L.searchPlaceholder}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </label>

        <div className="delpi-ui-lucide-icon-picker__meta">
          {value ? (
            <div className="delpi-ui-lucide-icon-picker__selected">
              <span>{L.selectedHint}</span>
              {SelectedIcon ? <SelectedIcon size={18} aria-hidden="true" /> : null}
              <code>{value.includes("-") ? value : toKebabCase(value)}</code>
            </div>
          ) : (
            <span className="delpi-ui-lucide-icon-picker__empty">{L.emptyHint}</span>
          )}
        </div>

        <div className="delpi-ui-lucide-icon-picker__grid">
          {visible.map((pascal) => (
            <IconCard
              key={pascal}
              name={pascal}
              active={pascal === normalizedSelectedPascal}
              onSelect={() => {
                onChange(toKebabCase(pascal));
                onClose?.();
              }}
            />
          ))}
        </div>

        {filtered.length > maxResults ? (
          <p className="delpi-ui-lucide-icon-picker__hint">
            {L.showingLimit.replace("{limit}", String(maxResults))}
          </p>
        ) : null}
      </div>

      <footer className="delpi-ui-lucide-icon-picker__footer">
        <button
          type="button"
          className="delpi-ui-lucide-icon-picker__btn delpi-ui-lucide-icon-picker__btn--ghost"
          onClick={() => {
            onChange(null);
            onClose?.();
          }}
        >
          {L.clear}
        </button>
        {onClose ? (
          <button
            type="button"
            className="delpi-ui-lucide-icon-picker__btn delpi-ui-lucide-icon-picker__btn--primary"
            onClick={onClose}
          >
            {L.close}
          </button>
        ) : null}
      </footer>
    </div>
  );
}

export type LucideIconByNameProps = {
  name?: string | null;
  size?: number;
  strokeWidth?: number;
  className?: string;
  "aria-hidden"?: boolean | "true" | "false";
};

/** Renderiza um ícone Lucide pelo nome (kebab ou PascalCase). */
export function LucideIconByName({
  name,
  size = 24,
  strokeWidth = 2,
  className,
  "aria-hidden": ariaHidden = true,
}: LucideIconByNameProps) {
  const Icon = resolveLucideIcon(name);
  if (!Icon) return null;
  return (
    <Icon size={size} strokeWidth={strokeWidth} className={className} aria-hidden={ariaHidden} />
  );
}
