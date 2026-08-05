export type SellerCustomer = {
  customer_code: string;
  customer_store: string;
  customer_name: string | null;
};

export type SellerCustomerInput = {
  customer_code: string;
  customer_store: string;
  customer_name?: string | null;
};

export type SellerPortfolio = {
  id: string;
  user_id: string;
  display_name: string;
  active: boolean;
  customer_count: number;
  customers: SellerCustomer[];
};

export type SellerPortfolioMeResponse = {
  portfolio: SellerPortfolio | null;
  is_admin: boolean;
};

export type CustomerEnrichmentItem = {
  customer_code: string;
  customer_store: string;
  city: string | null;
  state: string | null;
  last_purchase_date: string | null;
  billed_12m: number;
  has_avatar: boolean;
  avatar_url: string | null;
};

export type TotvsCustomerHit = {
  code: string;
  store: string;
  name: string;
  blocked?: string | null;
};

export type TransferSellerCustomersResult = {
  source: SellerPortfolio;
  target: SellerPortfolio;
  transferred_count: number;
};

export type DirectoryUser = {
  id: string;
  name: string;
  email: string;
};
