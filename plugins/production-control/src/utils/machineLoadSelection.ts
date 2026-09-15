import type { MachineLoadPayload } from "../types";

function normalizeCenter(value: string | null | undefined): string {
  return (value ?? "").trim();
}

/**
 * Centro de trabalho realmente exibido: o pedido quando existe na fila, senão o
 * primeiro disponível. Espelha a regra da API para que o recorte local e a
 * leitura do servidor nunca divirjam.
 */
export function resolveSelectedWorkCenter(
  workCenters: Array<{ work_center: string }>,
  requested: string | null,
): string | null {
  const available = workCenters.map((center) => normalizeCenter(center.work_center));
  const wanted = normalizeCenter(requested);
  if (wanted && available.includes(wanted)) return wanted;
  return available[0] ?? null;
}

/**
 * Recorta a fila da filial no centro pedido, sem nova leitura.
 *
 * Quando o payload não trouxe a fila completa (`includeAllCenters` ausente), o
 * recorte do servidor é a única fonte disponível e é preservado como está.
 */
export function selectMachineLoadCenter(
  payload: MachineLoadPayload,
  requested: string | null,
): MachineLoadPayload {
  const queue = payload.operations;
  if (!queue) return payload;

  const selected = resolveSelectedWorkCenter(payload.work_centers ?? [], requested);
  const items = selected
    ? queue.filter((operation) => normalizeCenter(operation.work_center) === selected)
    : [];

  return {
    ...payload,
    selected: {
      work_center: selected,
      requested_work_center: normalizeCenter(requested) || null,
      items,
      pagination: {
        page: 1,
        page_size: items.length,
        total: items.length,
        is_complete: true,
      },
    },
  };
}
