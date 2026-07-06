export type RichTreeNode = {
  id: string;
  label: string;
  subtitle?: string;
  badge?: string;
  metaCaption?: string;
  highlight?: "asis" | "tobe" | "changed" | "removed";
  children?: RichTreeNode[];
};
