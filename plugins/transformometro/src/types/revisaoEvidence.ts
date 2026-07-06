export type RevisaoEvidenceType = "anexo" | "foto" | "documento" | "link";

export type RevisaoEvidence = {
  evidencia_id: string;
  revisao_id: string;
  tipo: RevisaoEvidenceType;
  nome_arquivo?: string | null;
  nome_armazenado?: string | null;
  tipo_mime?: string | null;
  tamanho_bytes?: number | null;
  descricao?: string | null;
  url_externa?: string | null;
  enviado_por_id?: string | null;
  enviado_por_nome?: string | null;
  created_at?: string | null;
};

export type RevisaoEvidenceList = {
  total: number;
  items: RevisaoEvidence[];
};
