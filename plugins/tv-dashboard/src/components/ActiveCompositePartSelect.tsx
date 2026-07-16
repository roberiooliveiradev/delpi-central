import { FormSelectControl } from "@delpi/plugin-ui/index";

import {
  activePartOptionValue,
  listChartActivePartOptions,
  listKpiActivePartOptions,
  listTableActivePartOptions,
  type ActivePartOption,
} from "../utils/activeCompositePartOptions";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { DeckField } from "./deck/DeckField";

type Props = {
  id: string;
  compact?: boolean;
};

/**
 * Dropdown estilo Excel «Elemento ativo» — troca a parte sem sair do inspetor.
 */
export function ActiveCompositePartSelect({ id, compact = false }: Props) {
  const {
    selected,
    selectedChartPart,
    selectedKpiPart,
    selectedTablePart,
    selectChartPart,
    selectKpiPart,
    selectTablePart,
  } = useComunicadoEditor();

  if (!selected) return null;

  let options: ActivePartOption[] = [];
  let value = "";
  let onChange: ((next: string) => void) | null = null;

  if (selected.type === "chart_view") {
    options = listChartActivePartOptions(selected);
    value = activePartOptionValue({ chartPart: selectedChartPart });
    onChange = (next) => {
      const match = options.find((item) => item.value === next);
      if (match?.chartPart) selectChartPart(selected.id, match.chartPart);
    };
  } else if (selected.type === "kpi_view") {
    options = listKpiActivePartOptions(selected);
    value = activePartOptionValue({ kpiPart: selectedKpiPart });
    onChange = (next) => {
      const match = options.find((item) => item.value === next);
      if (match?.kpiPart) selectKpiPart(selected.id, match.kpiPart);
    };
  } else if (selected.type === "table_view") {
    options = listTableActivePartOptions(selected);
    value = activePartOptionValue({ tablePart: selectedTablePart });
    onChange = (next) => {
      const match = options.find((item) => item.value === next);
      if (match?.tablePart) selectTablePart(selected.id, match.tablePart);
    };
  }

  if (!options.length || !onChange) return null;

  return (
    <DeckField id={id} label="Elemento ativo">
      <FormSelectControl
        id={id}
        className={compact ? "delpi-ui-select--compact" : undefined}
        ariaLabel="Elemento ativo"
        value={value || options[0]!.value}
        onChange={onChange}
        options={options.map((item) => ({ value: item.value, label: item.label }))}
      />
    </DeckField>
  );
}
