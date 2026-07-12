import { useMemo, useState, type CSSProperties } from "react";
import { Search, X, type LucideIcon } from "lucide-react";
import * as LucideIcons from "lucide-react";

import {
  countGroupedLucideIcons,
  countLucideCatalogSize,
  groupLucideIconsBySection,
  lucideIconPtLabel,
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
  catalogHint?: string;
  noResults?: string;
};

export type LucideIconPickerProps = {
  value?: string | null;
  /** Nome do ícone; formato conforme `nameFormat`. `null` = remover. */
  onChange: (iconName: string | null) => void;
  onClose?: () => void;
  /**
   * Se true, a busca fica limitada ao catálogo curado.
   * Se false (recomendado), a busca cobre o Lucide completo.
   */
  curatedOnly?: boolean;
  /** kebab (padrão CX) ou PascalCase (TV / KPI). */
  nameFormat?: "kebab" | "pascal";
  maxResults?: number;
  title?: string;
  labels?: LucideIconPickerLabels;
  className?: string;
  style?: CSSProperties;
  /** Painel embutido no inspetor (sem cabeçalho de diálogo). */
  embedded?: boolean;
};

type IconCardProps = {
  name: string;
  active?: boolean;
  onSelect: () => void;
};

function IconCard({ name, active, onSelect }: IconCardProps) {
  const Icon = (LucideIcons as unknown as Record<string, LucideIcon | undefined>)[name];
  if (!Icon) return null;
  const label = lucideIconPtLabel(name);

  return (
    <button
      type="button"
      className={
        active
          ? "delpi-ui-lucide-icon-card delpi-ui-lucide-icon-card--active"
          : "delpi-ui-lucide-icon-card"
      }
      onClick={onSelect}
      title={label}
      aria-label={label}
      aria-pressed={active}
    >
      <span className="delpi-ui-lucide-icon-card__icon" aria-hidden="true">
        <Icon size={32} strokeWidth={1.75} />
      </span>
      <span className="delpi-ui-lucide-icon-card__label">{label}</span>
    </button>
  );
}

const DEFAULT_LABELS: Required<LucideIconPickerLabels> = {
  title: "Selecionar ícone",
  searchPlaceholder: "Buscar (ex.: indicador, gauge, meta…)",
  selectedHint: "Selecionado:",
  emptyHint: "Nenhum ícone selecionado",
  clear: "Remover ícone",
  close: "Fechar",
  showingLimit: "Mostrando {limit} resultados. Refine a busca.",
  catalogHint: "Navegue por seção ou busque entre {count} ícones Lucide.",
  noResults: "Nenhum ícone encontrado para essa busca.",
};

/** Painel de seleção Lucide (seções em PT + busca no catálogo completo). */
export function LucideIconPicker({
  value,
  onChange,
  onClose,
  curatedOnly = false,
  nameFormat = "kebab",
  maxResults = 480,
  title,
  labels,
  className,
  style,
  embedded = false,
}: LucideIconPickerProps) {
  const [query, setQuery] = useState("");
  const L = { ...DEFAULT_LABELS, ...labels };

  const catalogSize = useMemo(
    () => (curatedOnly ? 0 : countLucideCatalogSize()),
    [curatedOnly],
  );

  const sections = useMemo(
    () =>
      groupLucideIconsBySection({
        curatedOnly,
        query,
        maxResults,
      }),
    [curatedOnly, query, maxResults],
  );

  const visibleCount = useMemo(() => countGroupedLucideIcons(sections), [sections]);

  const normalizedSelectedPascal = useMemo(() => {
    const current = String(value ?? "").trim();
    if (!current) return "";
    return current.includes("-") ? toPascalCaseFromKebab(current) : current;
  }, [value]);

  const SelectedIcon = useMemo(() => resolveLucideIcon(value), [value]);
  const rootClass = [
    "delpi-ui-lucide-icon-picker",
    embedded ? "delpi-ui-lucide-icon-picker--embedded" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");
  const hasQuery = Boolean(query.trim());
  const truncated = hasQuery && !curatedOnly && catalogSize > 0 && visibleCount >= maxResults;

  const emitName = (pascal: string) =>
    nameFormat === "pascal" ? pascal : toKebabCase(pascal);

  return (
    <div className={rootClass} style={style} role="dialog" aria-label={title ?? L.title}>
      {!embedded ? (
        <header className="delpi-ui-lucide-icon-picker__header">
          <h2>{title ?? L.title}</h2>
          {onClose ? (
            <button
              type="button"
              className="delpi-ui-lucide-icon-picker__close"
              onClick={onClose}
              aria-label={L.close}
            >
              <X size={18} aria-hidden="true" />
            </button>
          ) : null}
        </header>
      ) : null}

      <div className="delpi-ui-lucide-icon-picker__body">
        <div className="delpi-ui-lucide-icon-picker__search-wrap" role="search">
          <Search size={18} className="delpi-ui-lucide-icon-picker__search-icon" aria-hidden="true" />
          <input
            type="search"
            className="delpi-ui-lucide-icon-picker__search"
            placeholder={L.searchPlaceholder}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoComplete="off"
            spellCheck={false}
            aria-label={L.searchPlaceholder}
          />
          {query ? (
            <button
              type="button"
              className="delpi-ui-lucide-icon-picker__search-clear"
              onClick={() => setQuery("")}
              aria-label="Limpar busca"
            >
              <X size={16} aria-hidden="true" />
            </button>
          ) : null}
        </div>

        <div className="delpi-ui-lucide-icon-picker__meta">
          {value ? (
            <div className="delpi-ui-lucide-icon-picker__selected">
              <span>{L.selectedHint}</span>
              {SelectedIcon ? <SelectedIcon size={20} aria-hidden="true" /> : null}
              <code>{lucideIconPtLabel(value)}</code>
            </div>
          ) : (
            <span className="delpi-ui-lucide-icon-picker__empty">{L.emptyHint}</span>
          )}
          {!hasQuery && !curatedOnly && catalogSize > 0 ? (
            <span className="delpi-ui-lucide-icon-picker__catalog-hint">
              {L.catalogHint.replace("{count}", String(catalogSize))}
            </span>
          ) : null}
        </div>

        {sections.length === 0 ? (
          <p className="delpi-ui-lucide-icon-picker__hint">{L.noResults}</p>
        ) : (
          <div className="delpi-ui-lucide-icon-picker__sections">
            {sections.map((section) => (
              <section key={section.id} className="delpi-ui-lucide-icon-picker__section">
                <h3 className="delpi-ui-lucide-icon-picker__section-title">{section.label}</h3>
                <div className="delpi-ui-lucide-icon-picker__grid">
                  {section.icons.map((pascal) => (
                    <IconCard
                      key={`${section.id}-${pascal}`}
                      name={pascal}
                      active={pascal === normalizedSelectedPascal}
                      onSelect={() => {
                        onChange(emitName(pascal));
                        onClose?.();
                      }}
                    />
                  ))}
                </div>
              </section>
            ))}
          </div>
        )}

        {truncated ? (
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
        {onClose && !embedded ? (
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
