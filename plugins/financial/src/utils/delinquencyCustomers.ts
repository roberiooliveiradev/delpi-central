import { fetchDelinquencyCustomers } from "../api/financialApi";
import type { DelinquencyCustomer } from "../types";

export type DelinquencyCustomerOption = {
  key: string;
  customerCode: string;
  store: string;
  label: string;
};

const CUSTOMER_KEY_SEPARATOR = "|";

export function encodeDelinquencyCustomerKey(customerCode: string, store: string): string {
  return `${customerCode}${CUSTOMER_KEY_SEPARATOR}${store}`;
}

export function decodeDelinquencyCustomerKey(
  value: string | null | undefined,
): { customerCode: string; store: string } | null {
  const text = value?.trim() ?? "";
  if (!text) return null;
  const separator = text.indexOf(CUSTOMER_KEY_SEPARATOR);
  if (separator <= 0) return null;
  const customerCode = text.slice(0, separator).trim();
  const store = text.slice(separator + 1).trim();
  if (!customerCode || !store) return null;
  return { customerCode, store };
}

export function formatDelinquencyCustomerOptionLabel(customer: DelinquencyCustomer): string {
  const shortName = customer.shortName?.trim() || customer.customerName?.trim() || "—";
  return `${shortName} (${customer.customerCode}/${customer.store})`;
}

export function toDelinquencyCustomerOption(
  customer: DelinquencyCustomer,
): DelinquencyCustomerOption {
  return {
    key: encodeDelinquencyCustomerKey(customer.customerCode, customer.store),
    customerCode: customer.customerCode,
    store: customer.store,
    label: formatDelinquencyCustomerOptionLabel(customer),
  };
}

export async function fetchAllDelinquencyCustomerOptions(params: {
  startDate: string | null;
  endDate: string | null;
  signal?: AbortSignal;
}): Promise<DelinquencyCustomerOption[]> {
  const pageSize = 100;
  let page = 1;
  const options: DelinquencyCustomerOption[] = [];
  const seen = new Set<string>();

  while (true) {
    const response = await fetchDelinquencyCustomers({
      startDate: params.startDate,
      endDate: params.endDate,
      page,
      pageSize,
      sortBy: "customer_name",
      sortDir: "asc",
      onlyWithDelays: false,
      signal: params.signal,
    });

    for (const item of response.items) {
      const option = toDelinquencyCustomerOption(item);
      if (seen.has(option.key)) continue;
      seen.add(option.key);
      options.push(option);
    }

    if (
      options.length >= response.pagination.totalItems ||
      response.items.length < pageSize ||
      !response.pagination.hasNext
    ) {
      break;
    }
    page += 1;
  }

  return options.sort((left, right) => left.label.localeCompare(right.label, "pt-BR"));
}
