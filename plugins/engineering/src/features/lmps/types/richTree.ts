export type RichTreeNode = {
  id: string;
  label: string;
  subtitle?: string;
  badge?: string;
  metaCaption?: string;
  children?: RichTreeNode[];
};
