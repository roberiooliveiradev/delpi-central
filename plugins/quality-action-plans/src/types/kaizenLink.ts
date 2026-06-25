export type KaizenLinkSummary = {
  id: string;
  branch_code: string;
  title: string;
  status: string;
  sector?: string | null;
};

export type KaizenLinkListResponse = {
  items: KaizenLinkSummary[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
};
