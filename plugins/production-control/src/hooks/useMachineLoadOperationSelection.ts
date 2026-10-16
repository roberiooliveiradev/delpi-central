import { useCallback, useMemo, useState } from "react";

import type { MachineLoadOperation } from "../types";
import {
  addKeysToSelection,
  duplicatedOperationKeys,
  machineLoadOperationKey,
  rangeOperationKeys,
  resolveSelectedOperations,
  selectedVisibleIndices,
  toggleKeyInSelection,
} from "../utils/machineLoadOperationSelection";

export type MachineLoadSelectionModifiers = {
  toggle?: boolean;
  range?: boolean;
};

export type MachineLoadSelectionOutcome =
  | "selected"
  | "toggled"
  | "ranged"
  | "ambiguous"
  | "ignored";

export type MachineLoadRowKeyStatus = "ok" | "invalid" | "duplicate";

/**
 * Seleção múltipla de operações do Carga-Máquina.
 *
 * Estado autoritativo = conjunto de chaves canônicas (filial+CT+OP+operação),
 * nunca índices. A seleção é efêmera: mudança de `scopeKey` (filial, CT,
 * período, filtros, snapshot) a zera durante o render, e operações fora do
 * contexto nunca contam — todo consumo passa pelo recorte `effectiveKeys`.
 */
export function useMachineLoadOperationSelection({
  branch,
  scopeKey,
  rows,
  visibleRows,
}: {
  branch: string;
  /** Contexto da seleção — mudou, limpa (filial/CT/período/filtros/snapshot). */
  scopeKey: string;
  /** Fila completa do CT ativo — validade da seleção. */
  rows: MachineLoadOperation[];
  /** Linhas visíveis na ordem vigente — base do Shift+clique e dos índices. */
  visibleRows: MachineLoadOperation[];
}) {
  const [selectedKeys, setSelectedKeys] = useState<ReadonlySet<string>>(
    () => new Set(),
  );
  const [anchorKey, setAnchorKey] = useState<string | null>(null);

  // Reset por escopo via ajuste de estado no render (padrão React para estado
  // derivado de prop/contexto) — não dispara efeito em cascata.
  const [appliedScope, setAppliedScope] = useState(scopeKey);
  if (appliedScope !== scopeKey) {
    setAppliedScope(scopeKey);
    setSelectedKeys(new Set());
    setAnchorKey(null);
  }

  const duplicates = useMemo(
    () => duplicatedOperationKeys(rows, branch),
    [branch, rows],
  );

  // Chaves que ainda existem no contexto — operação transferida/retirada pode
  // ficar no Set interno, mas nunca conta como selecionada.
  const effectiveKeys = useMemo(() => {
    if (selectedKeys.size === 0) return selectedKeys;
    const valid = new Set<string>();
    for (const row of rows) {
      const key = machineLoadOperationKey(row, branch);
      if (key) valid.add(key);
    }
    return new Set([...selectedKeys].filter((key) => valid.has(key)));
  }, [branch, rows, selectedKeys]);

  const visibleKeys = useMemo(
    () => visibleRows.map((row) => machineLoadOperationKey(row, branch)),
    [branch, visibleRows],
  );

  const selectedRows = useMemo(
    () => resolveSelectedOperations(rows, effectiveKeys, branch),
    [branch, rows, effectiveKeys],
  );

  const visibleIndices = useMemo(
    () => selectedVisibleIndices(visibleRows, effectiveKeys, branch),
    [branch, effectiveKeys, visibleRows],
  );

  const keyStatus = useCallback(
    (row: MachineLoadOperation): MachineLoadRowKeyStatus => {
      const key = machineLoadOperationKey(row, branch);
      if (!key) return "invalid";
      return duplicates.has(key) ? "duplicate" : "ok";
    },
    [branch, duplicates],
  );

  const isSelected = useCallback(
    (row: MachineLoadOperation): boolean => {
      const key = machineLoadOperationKey(row, branch);
      return key != null && effectiveKeys.has(key);
    },
    [branch, effectiveKeys],
  );

  const activate = useCallback(
    (
      row: MachineLoadOperation,
      modifiers: MachineLoadSelectionModifiers = {},
    ): MachineLoadSelectionOutcome => {
      const key = machineLoadOperationKey(row, branch);
      if (!key) return "ignored";
      // Chave duplicada dentro do CT: sem atributo autoritativo para
      // distinguir, não selecionar arbitrariamente a primeira ocorrência.
      if (duplicates.has(key)) return "ambiguous";

      if (modifiers.range && anchorKey) {
        const range = rangeOperationKeys(visibleKeys, anchorKey, key);
        if (range.length > 0) {
          setSelectedKeys((prev) =>
            modifiers.toggle ? addKeysToSelection(prev, range) : new Set(range),
          );
          return "ranged";
        }
        // Âncora fora da visão atual: cai para seleção simples do alvo.
      }

      if (modifiers.toggle) {
        setSelectedKeys((prev) => toggleKeyInSelection(prev, key));
        setAnchorKey(key);
        return "toggled";
      }

      setSelectedKeys(new Set([key]));
      setAnchorKey(key);
      return "selected";
    },
    [anchorKey, branch, duplicates, visibleKeys],
  );

  /** Checkbox ou Ctrl+clique — alterna a operação, virando âncora do intervalo. */
  const toggle = useCallback(
    (row: MachineLoadOperation): MachineLoadSelectionOutcome =>
      activate(row, { toggle: true }),
    [activate],
  );

  const clear = useCallback(() => {
    setSelectedKeys(new Set());
    setAnchorKey(null);
  }, []);

  return {
    /** Operações selecionadas presentes na fila atual, na ordem da fila. */
    selectedRows,
    /** Quantidade efetiva — só chaves que ainda existem no contexto. */
    count: selectedRows.length,
    /** Chaves canônicas efetivas (somente operações do contexto atual). */
    keys: effectiveKeys,
    /** Índices visíveis selecionados — render only (DataTable `selection`). */
    visibleIndices,
    /** Múltipla seleção ativa — suspende DnD individual e ativa menu coletivo. */
    hasMultiple: selectedRows.length >= 2,
    isSelected,
    keyStatus,
    activate,
    toggle,
    clear,
  };
}
