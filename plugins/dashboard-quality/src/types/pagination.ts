export type Page<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

export type PaginationParams = {
  page?: number;
  page_size?: number;
};
