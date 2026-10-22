/**
 * Shape público alinhado a docs/12-roadmap-e-evolucao/delpi-news/CONTRACTS.md §3.2.
 * Na Etapa 1 a fonte é fixture de demonstração; depois virá GET /public/boards/{token}.
 */
export interface PublicNewsBoardItem {
  id: string;
  title: string;
  summary: string | null;
  canonical_url: string | null;
  image_url: string | null;
  category_name: string | null;
  source_name: string;
  published_at: string | null;
  is_featured: boolean;
}

export interface PublicNewsBoard {
  board_id: string;
  title: string;
  subtitle: string | null;
  /** Quando true, a UI deve marcar inequívocamente o conteúdo como demonstração. */
  is_demo: boolean;
  rotation_interval_sec: number;
  items: PublicNewsBoardItem[];
}
