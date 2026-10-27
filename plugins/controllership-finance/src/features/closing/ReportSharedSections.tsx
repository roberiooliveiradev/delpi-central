/**
 * Seções compartilhadas das páginas contextuais de relatório (UX-011).
 *
 * ReportPdfSlot é o estado honesto de prévia enquanto não houver
 * produtor/contrato homologado — evidências documentais anexadas não
 * são relatórios oficiais. P3ReconciliationSection renderiza apenas
 * a conciliação provada pelo backend (divergence = reported - expected).
 */
import { type P3Status, type SourceState } from "../../api/p3Api";
import {
  CfSectionCard,
  CfStatusBadge,
} from "../../app/controllershipFinanceUi";
import { CfFeedbackMessage } from "../../app/cfFeedbackUi";
import { CF_HELP } from "../../content/helpTooltips";
import { formatAmount, formatDateTime } from "../../utils/formatters";

const SOURCE_STATE_LABELS: Record<SourceState, string> = {
  AVAILABLE: "Disponível",
  STALE: "Desatualizada",
  UNAVAILABLE: "Indisponível",
  PARTIAL: "Parcial",
  ERROR: "Erro na fonte",
};

const DOMAIN_LABELS: Record<string, string> = {
  ENTRADAS_SAIDAS: "Entradas e saídas (R05)",
  P7: "Posição de estoque P7 (R03)",
  H02: "Posição H02 (R08)",
};

/**
 * Slot de prévia de PDF — estado honesto enquanto não houver produtor
 * homologado (D7/§26.1). Evidências documentais anexadas NÃO são
 * relatórios oficiais e nunca são exibidas aqui.
 */
export function ReportPdfSlot({ reportName }: { reportName: string }) {
  return (
    <CfSectionCard
      title="Prévia do PDF"
      hint={CF_HELP.monthlyClosing.pdfPreview}
    >
      <div
        className="cf-pdf-preview-slot"
        aria-label={`Prévia do PDF indisponível para ${reportName}`}
      >
        <p>
          A prévia do PDF ainda não está disponível para este relatório.
        </p>
      </div>
    </CfSectionCard>
  );
}

/**
 * Conciliação canônica `DIVERGENCIA = ENTRADAS_SAIDAS - P7 - H02` —
 * renderiza somente o que o backend provou (divergence = reported −
 * expected; igualdade só comprovada com diferença exatamente 0,00).
 */
export function P3ReconciliationSection({
  p3,
  loading,
}: {
  p3: P3Status | null;
  loading: boolean;
}) {
  if (loading && !p3) {
    return <p aria-live="polite">Consultando a conciliação P3…</p>;
  }
  if (!p3) {
    return (
      <CfFeedbackMessage intent="info" title="Conciliação P3">
        A conciliação de estoque ainda não foi executada ou a fonte não
        respondeu — ela não é uma divergência zero.
      </CfFeedbackMessage>
    );
  }
  return (
    <CfSectionCard
      title="Conciliação Entradas/Saídas − P7 − H02"
      hint={CF_HELP.p3.panel}
    >
      <table className="cf-p3-table" aria-label="Conciliação de estoque">
        <thead>
          <tr>
            <th>Domínio</th>
            <th>Esperado</th>
            <th>Reportado</th>
            <th>Diferença</th>
            <th>Fonte</th>
            <th>Consulta</th>
          </tr>
        </thead>
        <tbody>
          {p3.reconciliations.map((recon) => (
            <tr key={recon.domain}>
              <td>{DOMAIN_LABELS[recon.domain] ?? recon.domain}</td>
              <td>
                {recon.expected_amount
                  ? formatAmount(recon.expected_amount)
                  : "—"}
              </td>
              <td>
                {recon.reported_amount
                  ? formatAmount(recon.reported_amount)
                  : "—"}
              </td>
              <td>
                {recon.divergence !== null
                  ? formatAmount(recon.divergence)
                  : "—"}
              </td>
              <td>
                <CfStatusBadge
                  label={SOURCE_STATE_LABELS[recon.source_state]}
                  variant={
                    recon.source_state === "AVAILABLE"
                      ? "success"
                      : "warning"
                  }
                />
              </td>
              <td>
                {recon.fetched_at ? formatDateTime(recon.fetched_at) : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {p3.blockers.length ? (
        <p className="cf-attention-item__meta">
          Bloqueios registrados: {p3.blockers.length} — a conciliação só é
          concluída quando todas as fontes estão disponíveis e a diferença
          é exatamente R$ 0,00.
        </p>
      ) : null}
    </CfSectionCard>
  );
}
