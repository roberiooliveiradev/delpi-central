export type ProcessDocumentSummary = {
  id: string;
  processo_id: string;
  title: string;
  created_by_user_id: string;
  updated_by_user_id: string;
  created_at: string | null;
  updated_at: string | null;
};

export type ProcessDocument = ProcessDocumentSummary & {
  content_md: string;
};

export type ProcessDocumentList = {
  total: number;
  items: ProcessDocumentSummary[];
};
