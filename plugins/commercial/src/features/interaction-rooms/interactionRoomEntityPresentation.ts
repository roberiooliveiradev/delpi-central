import {
  OPERATIONAL_UNIT_COLUMN_LABEL,
  formatOperationalUnitCode,
} from "@delpi/plugin-ui/index";

import { CUSTOMER_KEY_SEPARATOR } from "../customers/utils/customerIdentity";
import { INTERACTION_ENTITY_TYPES } from "./interactionRoomEntityKeys";

export type RoomEntityAboutField = {
  label: string;
  value: string;
};

export type RoomEntityPresentation = {
  /** Order / entity number for ABOUT primary line (no "Pedido" prefix when title already has it). */
  primaryNumber: string | null;
  unitCode: string | null;
  /** Santa Catarina / Espírito Santo — never raw `01`/`02` as primary label. */
  unitLabel: string | null;
  /** Informational chip text for RoomHeader (unit state name only). */
  chipLabel: string | null;
  aboutFields: RoomEntityAboutField[];
};

export function parseOrderEntityKey(
  entityKey: string | null | undefined,
): { unitCode: string; orderNumber: string } | null {
  const raw = String(entityKey ?? "").trim();
  if (!raw) return null;
  const sep = raw.indexOf(CUSTOMER_KEY_SEPARATOR);
  if (sep <= 0 || sep === raw.length - 1) return null;
  const unitCode = raw.slice(0, sep).trim();
  const orderNumber = raw.slice(sep + 1).trim();
  if (!unitCode || !orderNumber || orderNumber.includes(CUSTOMER_KEY_SEPARATOR)) {
    return null;
  }
  return { unitCode, orderNumber };
}

/**
 * UI-facing identity for room header chip + ABOUT card.
 * Never returns raw `filial|pedido` for display.
 */
export function formatRoomEntityPresentation(
  entityType: string | null | undefined,
  entityKey: string | null | undefined,
  _title?: string | null,
): RoomEntityPresentation {
  const empty: RoomEntityPresentation = {
    primaryNumber: null,
    unitCode: null,
    unitLabel: null,
    chipLabel: null,
    aboutFields: [],
  };

  const type = String(entityType ?? "").trim();
  if (type !== INTERACTION_ENTITY_TYPES.order) {
    return empty;
  }

  const parsed = parseOrderEntityKey(entityKey);
  if (!parsed) return empty;

  const unitLabel = formatOperationalUnitCode(parsed.unitCode, parsed.unitCode);
  const aboutFields: RoomEntityAboutField[] = [
    { label: "Pedido", value: parsed.orderNumber },
    { label: OPERATIONAL_UNIT_COLUMN_LABEL, value: unitLabel },
  ];

  return {
    primaryNumber: parsed.orderNumber,
    unitCode: parsed.unitCode,
    unitLabel,
    chipLabel: unitLabel,
    aboutFields,
  };
}
