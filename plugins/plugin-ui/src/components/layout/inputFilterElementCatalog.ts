/**
 * Catálogo de elementos do filtro (ligar/desligar famílias de partes).
 */

import type { InputPartRef, InputPartsMap } from "./inputFilterParts";
import {
  getInputPartState,
  mergeInputParts,
  upsertInputPartState,
} from "./inputFilterParts";

export type InputElementId =
  | "inputFrame"
  | "inputIcon"
  | "inputLabel"
  | "inputBadge"
  | "inputControl";

export type InputElementDefinition = {
  id: InputElementId;
  label: string;
  description?: string;
};

export const INPUT_ELEMENT_CATALOG: InputElementDefinition[] = [
  { id: "inputFrame", label: "Moldura", description: "Fundo e contorno do filtro" },
  { id: "inputIcon", label: "Ícone", description: "Ícone Lucide à esquerda" },
  { id: "inputLabel", label: "Rótulo", description: "Texto do parâmetro" },
  { id: "inputBadge", label: "Badge de escopo", description: "Filtro do slide / N fontes" },
  { id: "inputControl", label: "Controle", description: "Select ou input do paramSchema" },
];

export function inputElementPrimaryPartRef(elementId: InputElementId): InputPartRef {
  switch (elementId) {
    case "inputFrame":
      return { kind: "frame" };
    case "inputIcon":
      return { kind: "icon" };
    case "inputLabel":
      return { kind: "label" };
    case "inputBadge":
      return { kind: "badge" };
    case "inputControl":
      return { kind: "control" };
    default: {
      const _exhaustive: never = elementId;
      return _exhaustive;
    }
  }
}

export function inputElementIdForPartRef(ref: InputPartRef): InputElementId {
  switch (ref.kind) {
    case "frame":
      return "inputFrame";
    case "icon":
      return "inputIcon";
    case "label":
      return "inputLabel";
    case "badge":
      return "inputBadge";
    case "control":
      return "inputControl";
    default: {
      const _exhaustive: never = ref;
      return _exhaustive;
    }
  }
}

export function isInputElementEnabled(
  elementId: InputElementId,
  parts?: InputPartsMap | null,
  options?: { hasIconName?: boolean },
): boolean {
  const merged = mergeInputParts(parts);
  const ref = inputElementPrimaryPartRef(elementId);
  const state = getInputPartState(merged, ref);
  if (state?.visible === false) return false;
  if (elementId === "inputIcon" && options?.hasIconName === false) return false;
  return true;
}

export function setInputElementEnabled(
  elementId: InputElementId,
  enabled: boolean,
  parts?: InputPartsMap | null,
): InputPartsMap {
  const ref = inputElementPrimaryPartRef(elementId);
  if (elementId === "inputFrame" || elementId === "inputControl") {
    // Moldura e controle permanecem no modelo; ocultar só por visible.
  }
  return upsertInputPartState(parts, ref, { visible: enabled });
}
