/** Seleção de slides no filmstrip (lista ordenada flat). */

export type FilmstripSlideSelection = {
  /** IDs selecionados, ordem de aparição na lista quando possível. */
  selectedIds: string[];
  /** Slide focado no editor (primário). */
  primaryId: string | null;
  /** Âncora para Shift+clique (range). */
  rangeAnchorId: string | null;
};

export type FilmstripSelectionModifiers = {
  /** Shift: seleciona intervalo entre âncora e alvo. */
  range?: boolean;
  /** Ctrl/Cmd, modo multi ou long-press: alterna o alvo na seleção. */
  toggle?: boolean;
};

function uniquePreserveOrder(ids: string[]): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const id of ids) {
    if (seen.has(id)) continue;
    seen.add(id);
    out.push(id);
  }
  return out;
}

function rangeIds(orderedIds: string[], fromId: string, toId: string): string[] {
  const from = orderedIds.indexOf(fromId);
  const to = orderedIds.indexOf(toId);
  if (from < 0 || to < 0) return orderedIds.includes(toId) ? [toId] : [];
  const start = Math.min(from, to);
  const end = Math.max(from, to);
  return orderedIds.slice(start, end + 1);
}

function normalizePrevious(
  orderedIds: string[],
  previous: FilmstripSlideSelection,
): string[] {
  const filtered = previous.selectedIds.filter((id) => orderedIds.includes(id));
  if (filtered.length > 0) return filtered;
  if (previous.primaryId && orderedIds.includes(previous.primaryId)) {
    return [previous.primaryId];
  }
  return [];
}

/**
 * Resolve a próxima seleção do filmstrip a partir do clique (ou long-press → toggle).
 * Clique simples substitui; Shift faz range; toggle adiciona/remove.
 */
export function resolveFilmstripSlideSelection(input: {
  orderedIds: string[];
  previous: FilmstripSlideSelection;
  targetId: string;
  modifiers?: FilmstripSelectionModifiers;
}): FilmstripSlideSelection {
  const { orderedIds, previous, targetId } = input;
  const modifiers = input.modifiers ?? {};
  if (!orderedIds.includes(targetId)) {
    return {
      selectedIds: normalizePrevious(orderedIds, previous),
      primaryId: previous.primaryId && orderedIds.includes(previous.primaryId)
        ? previous.primaryId
        : null,
      rangeAnchorId:
        previous.rangeAnchorId && orderedIds.includes(previous.rangeAnchorId)
          ? previous.rangeAnchorId
          : null,
    };
  }

  const prevIds = normalizePrevious(orderedIds, previous);

  if (modifiers.range) {
    const anchorCandidate =
      (previous.rangeAnchorId && orderedIds.includes(previous.rangeAnchorId)
        ? previous.rangeAnchorId
        : null) ??
      (previous.primaryId && orderedIds.includes(previous.primaryId)
        ? previous.primaryId
        : null) ??
      prevIds[0] ??
      targetId;
    const selectedIds = rangeIds(orderedIds, anchorCandidate, targetId);
    return {
      selectedIds,
      primaryId: targetId,
      rangeAnchorId: previous.rangeAnchorId ?? anchorCandidate,
    };
  }

  if (modifiers.toggle) {
    const exists = prevIds.includes(targetId);
    let selectedIds = exists
      ? prevIds.filter((id) => id !== targetId)
      : [...prevIds, targetId];
    selectedIds = uniquePreserveOrder(selectedIds);
    if (selectedIds.length === 0) {
      return {
        selectedIds: [targetId],
        primaryId: targetId,
        rangeAnchorId: targetId,
      };
    }
    const primaryId = exists
      ? previous.primaryId === targetId
        ? (selectedIds[selectedIds.length - 1] ?? targetId)
        : previous.primaryId && selectedIds.includes(previous.primaryId)
          ? previous.primaryId
          : (selectedIds[selectedIds.length - 1] ?? targetId)
      : targetId;
    return {
      selectedIds,
      primaryId,
      rangeAnchorId: primaryId,
    };
  }

  return {
    selectedIds: [targetId],
    primaryId: targetId,
    rangeAnchorId: targetId,
  };
}

/** Garante o alvo na seleção sem removê-lo (entrada por long-press). */
export function ensureFilmstripSlideInSelection(input: {
  orderedIds: string[];
  previous: FilmstripSlideSelection;
  targetId: string;
}): FilmstripSlideSelection {
  const prevIds = normalizePrevious(input.orderedIds, input.previous);
  if (prevIds.includes(input.targetId)) {
    return {
      selectedIds: prevIds,
      primaryId: input.targetId,
      rangeAnchorId: input.previous.rangeAnchorId ?? input.targetId,
    };
  }
  return resolveFilmstripSlideSelection({
    orderedIds: input.orderedIds,
    previous: input.previous,
    targetId: input.targetId,
    modifiers: { toggle: true },
  });
}
