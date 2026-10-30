export type RichTreeNode = {
  id: string;
  label: string;
  subtitle?: string;
  badge?: string;
  metaCaption?: string;
  /** Código navegável do nó (ficha do produto) — omitido em nós sintéticos. */
  navCode?: string;
  children?: RichTreeNode[];
};
