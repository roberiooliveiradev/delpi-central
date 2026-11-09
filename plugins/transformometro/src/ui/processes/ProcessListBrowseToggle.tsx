import { FieldLabel } from "@delpi/plugin-ui/index";

import { SegmentToggle } from "../../components/SegmentToggle";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import {
  PROCESSO_LIST_BROWSE_MODES,
  type ProcessoListBrowseMode,
} from "./processListBrowseMode";

type Props = {
  value: ProcessoListBrowseMode;
  onChange: (mode: ProcessoListBrowseMode) => void;
  /** Compact hero: SegmentToggle only (label via aria). */
  compact?: boolean;
  idPrefix?: string;
};

/** Processos / Departamentos — shared by list browser and page hero. */
export function ProcessListBrowseToggle({
  value,
  onChange,
  compact = false,
  idPrefix = "tm-proc-browse",
}: Props) {
  const P = TM_HELP_TOOLTIPS.processos;
  const toggle = (
    <SegmentToggle
      ariaLabel="Visualizar listagem por processos ou departamentos"
      idPrefix={idPrefix}
      prefix="ds"
      size="md"
      options={PROCESSO_LIST_BROWSE_MODES.map((mode) => ({
        value: mode.id,
        label: mode.label,
      }))}
      value={value}
      onChange={onChange}
    />
  );

  if (compact) {
    return <div className="tm-processo-list-browse-toggle">{toggle}</div>;
  }

  return (
    <div className="tm-processo-browser__browse-row">
      <div className="tm-processo-browser__browse-label">
        <FieldLabel className="tm-field__label" label="Visualizar por" hint={P.visaoOrganizacao} />
        <p className="ds-hint tm-processo-browser__browse-hint">
          {value === "departamento"
            ? "Agrupamento por departamento do escopo (preferência salva neste navegador)."
            : "Listagem plana de macroprocessos (preferência salva neste navegador)."}
        </p>
      </div>
      <div className="tm-processo-browser__browse-toggle">{toggle}</div>
    </div>
  );
}
