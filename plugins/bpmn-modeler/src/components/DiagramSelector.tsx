import { NativeSelectControl } from "@delpi/plugin-ui/index";

import type { DiagramRef } from "../editor/BpmnEditorAdapter";

type Props = {
  diagrams: DiagramRef[];
  activeId: string | null;
  onSelect: (diagramId: string) => void;
};

/** Seletor de diagramas quando o artefato contém múltiplos BPMNDiagram (P4 §44). */
export function DiagramSelector({ diagrams, activeId, onSelect }: Props) {
  if (diagrams.length <= 1) return null;
  return (
    <span className="bpmnm-diagram-selector">
      <span>Diagrama</span>
      <NativeSelectControl
        value={activeId ?? diagrams[0]?.id ?? ""}
        onChange={onSelect}
        options={diagrams.map((d) => ({ value: d.id, label: d.name ?? d.id }))}
        aria-label="Selecionar diagrama"
      />
      <span className="bpmnm-hint">{diagrams.length} diagramas neste arquivo</span>
    </span>
  );
}
