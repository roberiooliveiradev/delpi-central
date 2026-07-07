export type ProcessoArquivoType = "anexo" | "foto" | "documento" | "link";

export type ProcessoArquivo = {
  arquivo_id: string;
  processo_id: string;
  tipo: ProcessoArquivoType;
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

export type ProcessoArquivoList = {
  total: number;
  items: ProcessoArquivo[];
};
