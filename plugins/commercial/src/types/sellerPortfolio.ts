export type {
  SellerCustomer,
  SellerCustomerInput,
  SellerPortfolio,
  SellerPortfolioMeResponse,
} from "./portfolio";

export type PortfolioMeta = {
  empty: boolean;
  message: string | null;
  seller_id: string | null;
};
