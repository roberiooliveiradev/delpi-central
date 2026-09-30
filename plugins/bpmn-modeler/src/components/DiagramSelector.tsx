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
    <label className="bpmnm-diagram-selector">
      Diagrama
      <select
        value={activeId ?? diagrams[0]?.id ?? ""}
        onChange={(e) => onSelect(e.target.value)}
      >
        {diagrams.map((d) => (
          <option key={d.id} value={d.id}>
            {d.name ?? d.id}
          </option>
        ))}
      </select>
      <span className="bpmnm-hint">{diagrams.length} diagramas neste arquivo</span>
    </label>
  );
}
