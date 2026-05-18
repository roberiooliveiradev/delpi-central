export type Audit5sSummaryParams = {
  start_date?: string;
  end_date?: string;
  branch?: string;
};

export type Audit5s = {
  id: string;
  date: string | null;
  average_line_score: number | null;
  evaluated_area: string | null;
  auditor: string | null;
  audited: string | null;
  inspection_number: string | null;
  shift: string | null;
  branch: string | null;
};

export type Audit5sSummary = {
  start_date: string | null;
  end_date: string | null;
  average_score: number;
  list_audits: Audit5s[];
};
