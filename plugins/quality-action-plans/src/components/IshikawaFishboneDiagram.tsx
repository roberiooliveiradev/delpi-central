import type { CSSProperties } from "react";
import { Cog, FlaskConical, Leaf, Plus, Ruler, Trash2, Users, Wrench } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { FormActions } from "./ui/FormActions";
import { TextAreaField } from "./ui/TextAreaField";
import type { IshikawaCategoryKey, IshikawaCausesForm } from "../utils/ishikawaCauses";

type BranchConfig = {
  key: IshikawaCategoryKey;
  label: string;
  color: string;
  icon: LucideIcon;
};

const FISHBONE_COLUMNS: { top: BranchConfig; bottom: BranchConfig }[] = [
  {
    top: { key: "method_process", label: "Método", color: "#e8b923", icon: Wrench },
    bottom: { key: "material", label: "Material", color: "#7b5ea7", icon: FlaskConical },
  },
  {
    top: { key: "machine", label: "Máquina", color: "#e255a1", icon: Cog },
    bottom: { key: "measurement", label: "Medição", color: "#5bc0eb", icon: Ruler },
  },
  {
    top: { key: "manpower", label: "Mão de obra", color: "#8b2942", icon: Users },
    bottom: { key: "environment", label: "Meio ambiente", color: "#3daa7e", icon: Leaf },
  },
];

type Props = {
  problem: string;
  causes: IshikawaCausesForm;
  notes: string;
  onChange: (next: IshikawaCausesForm) => void;
  onNotesChange: (notes: string) => void;
  saving?: boolean;
  onSave: () => void;
};

function updateCause(
  form: IshikawaCausesForm,
  key: IshikawaCategoryKey,
  index: number,
  value: string,
): IshikawaCausesForm {
  const nextItems = [...form[key]];
  nextItems[index] = value;
  return { ...form, [key]: nextItems };
}

function addCause(form: IshikawaCausesForm, key: IshikawaCategoryKey): IshikawaCausesForm {
  return { ...form, [key]: [...form[key], ""] };
}

function removeCause(
  form: IshikawaCausesForm,
  key: IshikawaCategoryKey,
  index: number,
): IshikawaCausesForm {
  const nextItems = form[key].filter((_, itemIndex) => itemIndex !== index);
  return { ...form, [key]: nextItems.length ? nextItems : [""] };
}

function BranchPanel({
  branch,
  causes,
  onCauseChange,
  onAddCause,
  onRemoveCause,
}: {
  branch: BranchConfig;
  causes: string[];
  onCauseChange: (index: number, value: string) => void;
  onAddCause: () => void;
  onRemoveCause: (index: number) => void;
}) {
  const Icon = branch.icon;

  return (
    <div
      className="pac-fishbone-branch__panel"
      style={{ "--branch-color": branch.color } as CSSProperties}
    >
      <div className="pac-fishbone-branch__head">
        <span className="pac-fishbone-branch__badge" aria-hidden="true">
          <Icon size={14} />
        </span>
        <span className="pac-fishbone-branch__label">{branch.label}</span>
      </div>
      <ul className="pac-fishbone-branch__causes">
        {causes.map((cause, index) => (
          <li key={`${branch.key}-${index}`} className="pac-fishbone-branch__cause">
            <input
              className="pac-field__control pac-fishbone-branch__input"
              value={cause}
              onChange={(event) => onCauseChange(index, event.target.value)}
              placeholder={`Causa ${index + 1}`}
              aria-label={`${branch.label} — causa ${index + 1}`}
            />
            <button
              type="button"
              className="pac-fishbone-branch__remove"
              onClick={() => onRemoveCause(index)}
              disabled={causes.length === 1 && !cause.trim()}
              aria-label={`Remover causa ${index + 1} de ${branch.label}`}
            >
              <Trash2 size={14} />
            </button>
          </li>
        ))}
      </ul>
      <button type="button" className="pac-fishbone-branch__add" onClick={onAddCause}>
        <Plus size={14} />
        Adicionar causa
      </button>
    </div>
  );
}

export function IshikawaFishboneDiagram({
  problem,
  causes,
  notes,
  onChange,
  onNotesChange,
  saving = false,
  onSave,
}: Props) {
  return (
    <div className="pac-fishbone">
      <div className="pac-fishbone__diagram">
        <div className="pac-fishbone__spine" aria-hidden="true">
          <span className="pac-fishbone__tail" />
          <span className="pac-fishbone__spine-track" />
          <span className="pac-fishbone__spine-arrow" />
        </div>

        {FISHBONE_COLUMNS.map((column) => (
          <div key={`${column.top.key}-${column.bottom.key}`} className="pac-fishbone__column">
            <div className="pac-fishbone__branch-slot pac-fishbone__branch-slot--top">
              <BranchPanel
                branch={column.top}
                causes={causes[column.top.key]}
                onCauseChange={(index, value) =>
                  onChange(updateCause(causes, column.top.key, index, value))
                }
                onAddCause={() => onChange(addCause(causes, column.top.key))}
                onRemoveCause={(index) => onChange(removeCause(causes, column.top.key, index))}
              />
              <span
                className="pac-fishbone__rib pac-fishbone__rib--down"
                style={{ "--branch-color": column.top.color } as CSSProperties}
                aria-hidden="true"
              />
            </div>

            <div className="pac-fishbone__joint" aria-hidden="true" />

            <div className="pac-fishbone__branch-slot pac-fishbone__branch-slot--bottom">
              <span
                className="pac-fishbone__rib pac-fishbone__rib--up"
                style={{ "--branch-color": column.bottom.color } as CSSProperties}
                aria-hidden="true"
              />
              <BranchPanel
                branch={column.bottom}
                causes={causes[column.bottom.key]}
                onCauseChange={(index, value) =>
                  onChange(updateCause(causes, column.bottom.key, index, value))
                }
                onAddCause={() => onChange(addCause(causes, column.bottom.key))}
                onRemoveCause={(index) => onChange(removeCause(causes, column.bottom.key, index))}
              />
            </div>
          </div>
        ))}

        <aside className="pac-fishbone__head" role="group" aria-label="Problema analisado">
          <span className="pac-fishbone__head-kicker">Problema</span>
          <p className="pac-fishbone__head-text">
            {problem.trim() || "Descreva o problema na identificação do plano."}
          </p>
        </aside>
      </div>

      <TextAreaField
        id="pac-ishikawa-notes"
        label="Observações gerais (opcional)"
        value={notes}
        onChange={onNotesChange}
        rows={2}
        fullWidth
      />

      <FormActions>
        <button type="button" className="pac-primary-btn" disabled={saving} onClick={onSave}>
          {saving ? "Salvando…" : "Salvar Ishikawa"}
        </button>
      </FormActions>
    </div>
  );
}
