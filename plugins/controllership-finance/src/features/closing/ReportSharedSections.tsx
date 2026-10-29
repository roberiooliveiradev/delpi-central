/**
 * Seções compartilhadas das páginas contextuais de relatório (UX-011).
 *
 * ReportPdfSlot é o estado honesto de prévia enquanto não houver
 * produtor/contrato homologado — evidências documentais anexadas não
 * são relatórios oficiais. P3ReconciliationSection renderiza apenas
 * a conciliação provada pelo backend (divergence = reported - expected).
 */
import { type P3Status, type SourceState } from "../../api/p3Api";
import type { StockReconciliationPayload } from "../../api/stockReconciliationApi";
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
  p7OperationalAvailable,
}: {
  p3: P3Status | null;
  loading: boolean;
  /** Consulta operacional P7 respondeu — distingue "consulta
   *  disponível" de "fonte elegível para a conciliação". */
  p7OperationalAvailable?: boolean;
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
          {p3.reconciliations.map((recon) => {
            const neverRegistered = !recon.fetched_at;
            const p7Pending =
              recon.domain === "P7" &&
              recon.source_state !== "AVAILABLE" &&
              p7OperationalAvailable;
            const sourceLabel =
              recon.source_state === "AVAILABLE"
                ? SOURCE_STATE_LABELS[recon.source_state]
                : p7Pending
                  ? "Conciliação pendente"
                  : neverRegistered
                    ? "Não registrada"
                    : SOURCE_STATE_LABELS[recon.source_state];
            return (
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
                    label={sourceLabel}
                    variant={
                      recon.source_state === "AVAILABLE"
                        ? "success"
                        : "warning"
                    }
                  />
                  {p7Pending ? (
                    <span className="cf-attention-item__meta">
                      {" "}
                      consulta disponível
                    </span>
                  ) : null}
                </td>
                <td>
                  {recon.fetched_at
                    ? formatDateTime(recon.fetched_at)
                    : "—"}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      {p3.reconciliations.some(
        (recon) => recon.source_state !== "AVAILABLE",
      ) ? (
        <p className="cf-attention-item__meta">
          Fontes sem validação não entram no cálculo — «não registrada»
          indica domínio sem fonte elegível até o momento e nunca é
          lido como divergência zero.
        </p>
      ) : null}
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

const OPERAND_LABELS: Record<string, string> = {
  entradasSaidas: "Entradas e saídas (R05)",
  p7: "Posição de estoque P7 (R03)",
  h02: "Material em processo (R08)",
};

export const OPERAND_STATUS_LABELS: Record<string, string> = {
  AVAILABLE: "Disponível",
  INCOMPLETE: "Parcialmente disponível",
  SOURCE_MISSING: "Fonte indisponível",
  NO_MATCHING_ITEMS: "Sem dados para o filtro",
  UNAVAILABLE: "Indisponível",
};

const PARITY_LABELS: Record<string, string> = {
  IDENTITY_ONLY: "Composição dos saldos consistente",
  DIVERGENCE: "Divergência na composição dos saldos",
  NOT_COMPUTED: "Conciliação pendente de validação",
};

/**
 * Conciliação analítica `DIVERGENCIA = ENTRADAS_SAIDAS − P7 − H02`
 * (doc 15.1) computada pela BFF sobre os três relatórios operacionais —
 * independente da competência formal e do fluxo documental. É superfície
 * analítica: não persiste registro, não substitui a conciliação governada
 * P3 e nunca trata fonte ausente como zero.
 */
export function AnalyticalReconciliationSection({
  reconciliation,
  loading,
}: {
  reconciliation: StockReconciliationPayload | null;
  loading: boolean;
}) {
  if (loading && !reconciliation) {
    return (
      <p aria-live="polite">Consultando a conciliação analítica…</p>
    );
  }
  if (!reconciliation) {
    return (
      <CfFeedbackMessage
        intent="info"
        title="Conciliação analítica de estoque"
      >
        A conciliação analítica não respondeu — ela não é uma divergência
        zero.
      </CfFeedbackMessage>
    );
  }
  const eligible = reconciliation.eligibility === "ELIGIBLE";
  return (
    <CfSectionCard
      title="Conciliação analítica — Entradas/Saídas − P7 − H02"
      hint={CF_HELP.analytics.reconciliation}
    >
      <table
        className="cf-p3-table"
        aria-label="Operandos da conciliação analítica"
      >
        <thead>
          <tr>
            <th>Operando</th>
            <th>Valor</th>
            <th>Fonte</th>
            <th>Data-base</th>
          </tr>
        </thead>
        <tbody>
          {(
            ["entradasSaidas", "p7", "h02"] as const
          ).map((key) => {
            const operand = reconciliation.operands[key];
            return (
              <tr key={key}>
                <td>{OPERAND_LABELS[key]}</td>
                <td>
                  {operand.value !== null
                    ? formatAmount(operand.value)
                    : "—"}
                </td>
                <td>
                  <CfStatusBadge
                    label={
                      OPERAND_STATUS_LABELS[operand.status ?? ""] ??
                      operand.status ??
                      "—"
                    }
                    variant={operand.available ? "success" : "warning"}
                  />
                </td>
                <td>
                  {operand.dataAsOf
                    ? formatDateTime(operand.dataAsOf)
                    : "—"}
                </td>
              </tr>
            );
          })}
          <tr>
            <td>
              <strong>Divergência analítica</strong>
            </td>
            <td>
              {reconciliation.divergenceCents !== null ? (
                <strong>
                  {formatAmount(reconciliation.divergenceCents)}
                </strong>
              ) : (
                "—"
              )}
            </td>
            <td colSpan={2}>
              <CfStatusBadge
                label={PARITY_LABELS[reconciliation.parity]}
                variant={
                  reconciliation.parity === "DIVERGENCE"
                    ? "danger"
                    : "info"
                }
              />
            </td>
          </tr>
        </tbody>
      </table>
      {!eligible ? (
        <p className="cf-attention-item__meta">
          Operandos indisponíveis ou incompletos:{" "}
          {reconciliation.ineligibleOperands
            .map((key) => OPERAND_LABELS[key] ?? key)
            .join(", ")}
          . A divergência não é calculada — fonte ausente nunca entra
          como zero.
        </p>
      ) : null}
      {reconciliation.parity === "IDENTITY_ONLY" ? (
        <p className="cf-attention-item__meta">
          Os três operandos são partições do mesmo universo de saldo —
          a igualdade é um controle de integridade da composição, não
          comprova a paridade entre os relatórios oficiais
          (MATR320 × MATR460 × MATR989).
        </p>
      ) : null}
      {reconciliation.parity === "DIVERGENCE" ? (
        <p className="cf-attention-item__meta">
          A composição dos saldos não fecha — investigue os operandos
          e as fontes acima antes de considerar qualquer conclusão.
        </p>
      ) : null}
      {reconciliation.reconciliationVerdict === "INCONCLUSIVE" ? (
        <p className="cf-attention-item__meta">
          Conciliação entre relatórios independentes: pendente de
          validação — a paridade oficial permanece sujeita a
          homologação por competência.
        </p>
      ) : null}
      <p className="cf-attention-item__meta">
        Visão analítica calculada pela BFF a partir dos relatórios
        operacionais — não persiste registro nem substitui a conciliação
        governada do checklist P3, que permanece a autoridade do
        fechamento.
      </p>
    </CfSectionCard>
  );
}
