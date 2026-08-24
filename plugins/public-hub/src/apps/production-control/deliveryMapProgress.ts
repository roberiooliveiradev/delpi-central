import type { DeliveryMapSection, PublicDeliveryMapPayload } from "./api";

export const DELIVERY_MAP_OVERDUE_SECTION_KEY = "overdue_and_today";
export const DELIVERY_MAP_PROGRESS_HORIZON_DAYS = 5;
export const DELIVERY_MAP_PROGRESS_BATCH_SIZE = 40;

function parseIsoDateOnly(value: string): Date {
  const [year, month, day] = value.slice(0, 10).split("-").map(Number);
  return new Date(year, month - 1, day);
}

function startOfToday(): Date {
  const now = new Date();
  return new Date(now.getFullYear(), now.getMonth(), now.getDate());
}

function addCalendarDays(base: Date, days: number): Date {
  const next = new Date(base);
  next.setDate(next.getDate() + days);
  return next;
}

export function isDeliveryMapSectionEligibleForProgress(
  section: DeliveryMapSection,
  horizonDays = DELIVERY_MAP_PROGRESS_HORIZON_DAYS,
): boolean {
  if (section.section_key === DELIVERY_MAP_OVERDUE_SECTION_KEY) return true;
  if (!section.due_date) return false;
  const due = parseIsoDateOnly(section.due_date);
  const limit = addCalendarDays(startOfToday(), horizonDays);
  return due <= limit;
}

export function collectDeliveryMapProgressOrderBatches(
  payload: PublicDeliveryMapPayload | null,
  horizonDays = DELIVERY_MAP_PROGRESS_HORIZON_DAYS,
): { priority: string[]; deferred: string[] } {
  if (!payload) return { priority: [], deferred: [] };

  const priority = new Set<string>();
  const deferred = new Set<string>();

  for (const section of payload.sections) {
    if (!isDeliveryMapSectionEligibleForProgress(section, horizonDays)) continue;

    const orders = section.rows
      .map((row) => row.production_order)
      .filter((order): order is string => Boolean(order));

    if (section.section_key === DELIVERY_MAP_OVERDUE_SECTION_KEY) {
      for (const order of orders) priority.add(order);
    } else {
      for (const order of orders) deferred.add(order);
    }
  }

  return {
    priority: Array.from(priority),
    deferred: Array.from(deferred),
  };
}

export function chunkDeliveryMapProgressOrders(
  orders: readonly string[],
  batchSize = DELIVERY_MAP_PROGRESS_BATCH_SIZE,
): string[][] {
  if (orders.length === 0) return [];
  const chunks: string[][] = [];
  for (let index = 0; index < orders.length; index += batchSize) {
    chunks.push(orders.slice(index, index + batchSize));
  }
  return chunks;
}
