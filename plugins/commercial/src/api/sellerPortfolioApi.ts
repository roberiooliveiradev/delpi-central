/**
 * Shim: superfície CM `sellerPortfolioApi` → commercial-api.
 */
import type {
  DirectoryUser,
  AddSellerCustomerResult,
  SellerCustomerInput,
  SellerPortfolio,
  SellerPortfolioMeResponse,
  SellerPortfolioMemberRole,
  SellerPortfoliosCoverageAudit,
  SellerPortfoliosLoadSummary,
  TotvsCustomerHit,
  TransferSellerCustomersResult,
  BulkTransferSellerCustomersResult,
} from "../types/portfolio";
import * as commercial from "./commercialPortfolioApi";

export type {
  DirectoryUser,
  SellerCustomerInput,
  SellerPortfolio,
  SellerPortfolioMeResponse,
  SellerPortfoliosCoverageAudit,
  SellerPortfoliosLoadSummary,
  TotvsCustomerHit,
  BulkTransferSellerCustomersResult,
};

export async function searchDirectoryUsers(
  query: string,
  limit = 10,
  signal?: AbortSignal,
): Promise<DirectoryUser[]> {
  return commercial.searchDirectoryUsers(query, limit, signal);
}

export async function getMySellerPortfolio(
  signal?: AbortSignal,
): Promise<SellerPortfolioMeResponse> {
  return commercial.getMySellerPortfolio(signal);
}

export async function listSellerPortfolios(options?: {
  activeOnly?: boolean;
  signal?: AbortSignal;
}): Promise<SellerPortfolio[]> {
  return commercial.listSellerPortfolios(options);
}

export async function getSellerPortfolio(
  portfolioId: string,
  signal?: AbortSignal,
): Promise<SellerPortfolio> {
  return commercial.getSellerPortfolio(portfolioId, signal);
}

export async function createSellerPortfolio(input: {
  user_id?: string;
  user_ids?: string[];
  owner_user_id?: string | null;
  display_name: string;
  customers?: SellerCustomerInput[];
}): Promise<SellerPortfolio> {
  return commercial.createSellerPortfolio(input);
}

export async function updateSellerPortfolio(
  sellerId: string,
  input: { display_name?: string; active?: boolean },
): Promise<SellerPortfolio> {
  return commercial.updateSellerPortfolio(sellerId, input);
}

export async function deactivateSellerPortfolio(sellerId: string): Promise<SellerPortfolio> {
  return commercial.deactivateSellerPortfolio(sellerId);
}

export async function purgeSellerPortfolio(sellerId: string): Promise<SellerPortfolio> {
  return commercial.purgeSellerPortfolio(sellerId);
}

export async function addSellerPortfolioMember(
  portfolioId: string,
  input: { user_id: string; role?: SellerPortfolioMemberRole },
): Promise<SellerPortfolio> {
  return commercial.addSellerPortfolioMember(portfolioId, input);
}

export async function removeSellerPortfolioMember(
  portfolioId: string,
  userId: string,
): Promise<SellerPortfolio> {
  return commercial.removeSellerPortfolioMember(portfolioId, userId);
}

export async function setSellerPortfolioOwner(
  portfolioId: string,
  userId: string,
): Promise<SellerPortfolio> {
  return commercial.setSellerPortfolioOwner(portfolioId, userId);
}

export async function replaceSellerCustomers(
  sellerId: string,
  customers: SellerCustomerInput[],
): Promise<SellerPortfolio> {
  return commercial.replaceSellerCustomers(sellerId, customers);
}

export async function addSellerCustomer(
  sellerId: string,
  customer: SellerCustomerInput,
): Promise<AddSellerCustomerResult> {
  return commercial.addSellerCustomer(sellerId, customer);
}

export async function getSellerPortfoliosCoverageAudit(
  signal?: AbortSignal,
): Promise<SellerPortfoliosCoverageAudit> {
  return commercial.getSellerPortfoliosCoverageAudit(signal);
}

export async function getSellerPortfoliosLoadSummary(options?: {
  activeOnly?: boolean;
  signal?: AbortSignal;
}): Promise<SellerPortfoliosLoadSummary> {
  return commercial.getSellerPortfoliosLoadSummary(options);
}

export async function removeSellerCustomer(
  sellerId: string,
  customerCode: string,
  customerStore: string,
): Promise<SellerPortfolio> {
  return commercial.removeSellerCustomer(sellerId, customerCode, customerStore);
}

export type { TransferSellerCustomersResult };

/** Assinatura CM: (sourceId, { target_seller_id, customers }) → commercial transfer. */
export async function transferSellerCustomers(
  sourceSellerId: string,
  input: {
    target_seller_id: string;
    customers: SellerCustomerInput[];
    reason_note?: string;
  },
): Promise<TransferSellerCustomersResult> {
  return commercial.transferSellerCustomers({
    source_portfolio_id: sourceSellerId,
    target_portfolio_id: input.target_seller_id,
    customers: input.customers,
    reason_note: input.reason_note?.trim() || "Transferência via Portal Comercial",
  });
}

export async function transferSellerCustomersBulk(input: {
  source_portfolio_id: string;
  target_portfolio_id: string;
  customers: SellerCustomerInput[];
  reason_note: string;
}): Promise<BulkTransferSellerCustomersResult> {
  return commercial.transferSellerCustomersBulk(input);
}

export async function searchActiveCustomers(
  query: string,
  limitOrOptions: number | { page?: number; pageSize?: number; signal?: AbortSignal } = 20,
  signal?: AbortSignal,
): Promise<TotvsCustomerHit[]> {
  const options =
    typeof limitOrOptions === "number"
      ? { pageSize: limitOrOptions, signal }
      : { ...limitOrOptions, signal: limitOrOptions.signal ?? signal };
  const result = await commercial.searchActiveCustomers(query, options);
  return result.items;
}

export async function searchActiveTotvsCustomers(
  query: string,
  options?: { page?: number; pageSize?: number; signal?: AbortSignal },
): Promise<{ items: TotvsCustomerHit[]; total: number }> {
  return commercial.searchActiveCustomers(query, {
    page: options?.page,
    pageSize: options?.pageSize,
    signal: options?.signal,
  });
}
