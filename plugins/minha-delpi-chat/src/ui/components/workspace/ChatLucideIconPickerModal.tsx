import { ChatNativeTextInput } from "../shared/chatNativeFormFields";
import { useMemo, useState, type ComponentType } from "react";
import { X } from "lucide-react";
import * as LucideIcons from "lucide-react";

import { ChatModal } from "../shared/modal/ChatModal";
import {
  listLucideIconNames,
  resolveLucideIcon,
  toKebabCase,
  toPascalCaseFromKebab,
} from "../../utils/lucideIconResolver";

import "./ChatLucideIconPickerModal.css";

type ChatLucideIconPickerModalProps = {
  open: boolean;
  value?: string | null;
  title?: string;
  onClose: () => void;
  onPick: (iconKebab: string | null) => void;
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

  if (!Icon) {
    return null;
  }

  const kebab = toKebabCase(name);

  return (
    <button
      type="button"
      className={
        active
          ? "mdc-chat-lucide-icon-card mdc-chat-lucide-icon-card--active"
          : "mdc-chat-lucide-icon-card"
      }
      onClick={onSelect}
      title={kebab}
    >
      <span className="mdc-chat-lucide-icon-card__icon" aria-hidden="true">
        <Icon size={22} />
      </span>
      <span className="mdc-chat-lucide-icon-card__label">{kebab}</span>
    </button>
  );
}

export function ChatLucideIconPickerModal({
  open,
  value,
  title = "Selecionar ícone (Lucide)",
  onClose,
  onPick,
}: ChatLucideIconPickerModalProps) {
  const [query, setQuery] = useState("");

  const allIcons = useMemo(() => listLucideIconNames(), []);

  const normalizedSelectedPascal = useMemo(() => {
    const current = String(value ?? "").trim();

    if (!current) {
      return "";
    }

    return current.includes("-") ? toPascalCaseFromKebab(current) : current;
  }, [value]);

  const SelectedIcon = useMemo(() => resolveLucideIcon(value), [value]);

  const filtered = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    if (!normalizedQuery) {
      return allIcons;
    }

    return allIcons.filter((pascal) => {
      const kebab = toKebabCase(pascal);

      return kebab.includes(normalizedQuery) || pascal.toLowerCase().includes(normalizedQuery);
    });
  }, [allIcons, query]);

  return (
    <ChatModal
      open={open}
      onClose={onClose}
      size="lg"
      mobileLayout="centered"
      panelClassName="mdc-chat-lucide-icon-picker"
      ariaLabel={title}
    >
      <header className="mdc-chat-lucide-icon-picker__header">
        <h2>{title}</h2>

        <button
          type="button"
          className="mdc-chat-modal-icon-btn mdc-chat-modal-icon-btn--outlined mdc-chat-modal-icon-btn--sm"
          onClick={onClose}
          aria-label="Fechar"
        >
          <X size={17} aria-hidden="true" />
        </button>
      </header>

      <div className="mdc-chat-lucide-icon-picker__body">
        <ChatNativeTextInput
          className="mdc-chat-lucide-icon-picker__search"
          placeholder="Buscar ícone (ex: book, user, bell...)"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />

        <div className="mdc-chat-lucide-icon-picker__meta">
          <p>
            Clique em um ícone para selecionar. Salvo em <code>kebab-case</code> (ex.:{" "}
            <code>book-headphones</code>).
          </p>

          {value ? (
            <div className="mdc-chat-lucide-icon-picker__selected">
              {SelectedIcon ? <SelectedIcon size={18} aria-hidden="true" /> : null}
              <code>{value}</code>
            </div>
          ) : (
            <span className="mdc-chat-muted">(sem ícone)</span>
          )}
        </div>

        <div className="mdc-chat-lucide-icon-picker__grid">
          {filtered.slice(0, 360).map((pascal) => (
            <IconCard
              key={pascal}
              name={pascal}
              active={pascal === normalizedSelectedPascal}
              onSelect={() => {
                onPick(toKebabCase(pascal));
                onClose();
              }}
            />
          ))}
        </div>

        {filtered.length > 360 ? (
          <p className="mdc-chat-lucide-icon-picker__hint">
            Mostrando 360 resultados. Refine a busca para achar mais rápido.
          </p>
        ) : null}
      </div>

      <footer className="mdc-chat-lucide-icon-picker__footer">
        <button
          type="button"
          className="mdc-chat-ws-outline-btn"
          onClick={() => {
            onPick(null);
            onClose();
          }}
        >
          Remover ícone
        </button>
        <button type="button" className="mdc-chat-ws-primary-btn" onClick={onClose}>
          Fechar
        </button>
      </footer>
    </ChatModal>
  );
}
