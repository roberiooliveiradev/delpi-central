// src/ui/admin/modals/IconPickerModal.tsx
import { useMemo, useState } from "react";
import { Modal } from "../../../components/Modal";
import { Button, SearchInput } from "../../../ui-kit";
import "./IconPickerModal.css"
import * as LucideIcons from "lucide-react";
import {
  iconExportNameToKebab,
  resolveIcon,
  resolveIconExportName,
} from "../../../utils/iconResolver";

type Props = {
  open: boolean;
  value?: string | null; // pode ser "book-headphones" ou "BookHeadphones"
  onClose: () => void;
  onPick: (iconKebab: string | null) => void;
};

function isPascalCaseComponentExport(name: string) {
  // evita exports utilitários do pacote
  return /^[A-Z][A-Za-z0-9]*$/.test(name);
}

const toKebabCase = iconExportNameToKebab;

type IconCardProps = {
  name: string; // PascalCase export name
  active?: boolean;
  onSelect: () => void;
};

function IconCard({ name, active, onSelect }: IconCardProps) {
  const Icon = (LucideIcons as any)[name] as React.ComponentType<any> | undefined;
  if (!Icon) return null;

  const kebab = toKebabCase(name);

  return (
    <button
      type="button"
      className={`icon-card ${active ? "active" : ""}`}
      onClick={onSelect}
      title={kebab}
    >
      <div className="icon-card__icon">
        <Icon size={22} />
      </div>
      <div className="icon-card__label">{kebab}</div>
    </button>
  );
}

export const IconPickerModal = ({ open, value, onClose, onPick }: Props) => {
  const [q, setQ] = useState("");

  const allIcons = useMemo(() => {
    return Object.keys(LucideIcons)
      .filter(isPascalCaseComponentExport)
      .sort();
  }, []);

  const normalizedSelectedPascal = useMemo(
    () => resolveIconExportName(value) ?? "",
    [value],
  );

  const SelectedIcon = useMemo(() => resolveIcon(value ?? null), [value]);

  const filtered = useMemo(() => {
    const s = q.trim().toLowerCase();
    if (!s) return allIcons;

    return allIcons.filter((pascal) => {
      const kebab = toKebabCase(pascal);
      return kebab.includes(s) || pascal.toLowerCase().includes(s);
    });
  }, [q, allIcons]);

  return (
    <Modal
      open={open}
      title="Selecionar ícone (Lucide)"
      onClose={onClose}
      size="lg"
      footer={
        <>
          <Button variant="danger-soft" onClick={() => onPick(null)}>
            Remover ícone
          </Button>
          <Button variant="primary" onClick={onClose}>
            Fechar
          </Button>
        </>
      }
    >
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <SearchInput
          placeholder="Buscar ícone (ex: book, user, bell...)"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onClear={() => setQ("")}
        />

        <div className="row between" style={{ marginTop: 4 }}>
          <div className="hint">
            Clique em um ícone para selecionar. Salvo como <code>kebab-case</code> (ex:{" "}
            <code>book-headphones</code>).
          </div>

          {value ? (
            <div style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
              {SelectedIcon ? <SelectedIcon size={18} /> : null}
              <code>{String(value)}</code>
            </div>
          ) : (
            <span className="dt-muted">(sem ícone)</span>
          )}
        </div>

        <div className="icon-picker-grid">
          {filtered.slice(0, 360).map((pascal) => (
            <IconCard
              key={pascal}
              name={pascal}
              active={pascal === normalizedSelectedPascal}
              onSelect={() => onPick(toKebabCase(pascal))}
            />
          ))}
        </div>

        {filtered.length > 360 && (
          <div className="hint">
            Mostrando 360 resultados. Refine a busca para achar mais rápido.
          </div>
        )}
      </div>
    </Modal>
  );
};