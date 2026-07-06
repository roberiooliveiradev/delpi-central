import { useMemo } from "react";

import type { DecompositionFlatRow, DecompositionTreeV1 } from "../../types/decomposition";
import { sortDecompositionNodes } from "../../types/decomposition";

type Props = {
  tree: DecompositionTreeV1;
  macroprocesso?: string;
  departamento?: string;
};

function buildPreviewRows(
  tree: DecompositionTreeV1,
  macroprocesso: string,
  departamento: string
): DecompositionFlatRow[] {
  const nodes = sortDecompositionNodes(tree.nodes);
  const byId = new Map(nodes.map((n) => [n.id, n]));
  const processosChave = nodes.filter((n) => n.level === "processo_chave");

  const rows: DecompositionFlatRow[] = [];
  for (const pk of processosChave) {
    const children = nodes.filter((n) => n.parent_id === pk.id);
    const subTarefas = children.filter((n) => n.level === "sub_tarefa");
    const leaves = subTarefas.length
      ? subTarefas
      : children.filter((n) => n.level === "tarefa");
    if (!leaves.length) {
      rows.push({
        departamento,
        macroprocesso,
        num_processo_chave: String(pk.ordem),
        processo_chave: pk.label,
        num_sub_tarefa: "",
        sub_tarefas: pk.label,
        node_id: pk.id,
        highlight: pk.highlight ?? "",
      });
      continue;
    }
    for (const leaf of leaves) {
      rows.push({
        departamento,
        macroprocesso,
        num_processo_chave: String(pk.ordem),
        processo_chave: pk.label,
        num_sub_tarefa: String(leaf.ordem),
        sub_tarefas: leaf.label,
        node_id: leaf.id,
        highlight: leaf.highlight ?? byId.get(leaf.id)?.highlight ?? "",
      });
    }
  }
  return rows;
}

export function DecompositionFlatPreview({ tree, macroprocesso = "", departamento = "" }: Props) {
  const rows = useMemo(
    () => buildPreviewRows(tree, macroprocesso, departamento),
    [tree, macroprocesso, departamento]
  );

  if (!rows.length) {
    return <p className="ds-hint">Nenhuma linha para exibir — cadastre processos-chave na árvore.</p>;
  }

  return (
    <div className="tm-decomposition-preview">
      <table className="ds-table ds-table--compact">
        <thead>
          <tr>
            <th>Dept.</th>
            <th>Macroprocesso</th>
            <th>nº PK</th>
            <th>Processo-chave</th>
            <th>nº ST</th>
            <th>Sub-tarefas</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.node_id}>
              <td>{row.departamento || "—"}</td>
              <td>{row.macroprocesso || "—"}</td>
              <td>{row.num_processo_chave}</td>
              <td>{row.processo_chave}</td>
              <td>{row.num_sub_tarefa || "—"}</td>
              <td>{row.sub_tarefas}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
