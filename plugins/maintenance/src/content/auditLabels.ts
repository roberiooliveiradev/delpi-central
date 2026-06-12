export const AUDIT_ACTION_LABELS: Record<string, string> = {
  "reposicao.create": "Reposição registrada",
  "reposicao.update": "Reposição alterada",
  "reposicao.delete": "Reposição excluída",
  "revisao_programada.create": "Revisão programada criada",
  "revisao_programada.update": "Revisão programada alterada",
  "revisao_programada.delete": "Revisão programada excluída",
  "revisao_programada.registrar": "Revisão marcada como feita",
  "revisao_realizacao.update": "Marcação de revisão alterada",
  "revisao_realizacao.delete": "Marcação de revisão removida",
};

export function auditActionLabel(acao: string): string {
  return AUDIT_ACTION_LABELS[acao] ?? acao;
}

export function auditPayloadSummary(payload: Record<string, unknown> | null | undefined): string {
  if (!payload) return "—";
  const parts: string[] = [];

  if (payload.codigo_peca) {
    parts.push(`Peça ${String(payload.codigo_peca)}`);
  }
  if (payload.golpes != null && payload.golpes !== "") {
    parts.push(`${payload.golpes} golpes`);
  }
  if (payload.data_reposicao) {
    parts.push(`reposição ${String(payload.data_reposicao).slice(0, 16).replace("T", " ")}`);
  }
  if (payload.intervalo_meses != null && payload.intervalo_meses !== "") {
    parts.push(`intervalo ${payload.intervalo_meses} mês(es)`);
  }
  if (payload.data_ultima_revisao) {
    parts.push(`referência ${String(payload.data_ultima_revisao).slice(0, 10)}`);
  }
  if (payload.data_revisao) {
    parts.push(`revisão ${String(payload.data_revisao).slice(0, 10)}`);
  }
  if (payload.observacao && String(payload.observacao).trim()) {
    parts.push(String(payload.observacao).trim());
  }

  return parts.length > 0 ? parts.join(" · ") : "—";
}
