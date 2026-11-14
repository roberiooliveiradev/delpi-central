/** Revisões publicadas — índice imutável + snapshot read-only sob
 * demanda (GET .../revisions/{n}). Comparação entre versões deriva dos
 * snapshots já contratados — sem endpoint inventado. */

import { useCallback, useEffect, useState } from "react";

import {
  EngineeringActionButton,
  EngineeringDetailCard,
  EngineeringDetailFieldGrid,
  EngineeringEmptyState,
  EngineeringLoadingActivityCard,
  EngineeringSectionCard,
  EngineeringStateBanner,
} from "../../../ui/engineeringUi";
import type { DataTableColumn } from "../../lmps/components/dataTableUi";
import { DataTableSection } from "../../lmps/components/DataTableSection";
import {
  fetchPrcRevision,
  type PrcRevisionDetail,
  type PrcRevisionSummary,
} from "../api/productRegistrationApi";
import { prcDetailTabHref } from "../prcNavigate";
import {
  PRC_COPY,
  prcFieldLabel,
  prcPersonLabel,
  prcShortId,
} from "../prcCopy";

function fmt(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  if (Array.isArray(value)) return `${value.length} item(ns)`;
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

export function PrcRevisionsSection({
  recordId,
  revisions,
  basePath,
}: {
  recordId: string | null | undefined;
  revisions: PrcRevisionSummary[];
  /** Base do MFE — link «Solicitação de origem» (proveniência §56). */
  basePath?: string;
}) {
  const [snapshot, setSnapshot] = useState<PrcRevisionDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const open = useCallback(
    async (revisionNumber: number) => {
      if (!recordId) return;
      setSnapshot(null);
      setError("");
      setLoading(true);
      try {
        const env = await fetchPrcRevision(recordId, revisionNumber);
        setSnapshot(env.data);
      } catch (e) {
        setError(
          (e as { message?: string }).message ||
            "Falha ao carregar a revisão.",
        );
      } finally {
        setLoading(false);
      }
    },
    [recordId],
  );

  useEffect(() => {
    setSnapshot(null);
  }, [recordId]);

  if (!recordId) {
    return <EngineeringEmptyState message={PRC_COPY.noRevisions} />;
  }

  const columns: DataTableColumn<PrcRevisionSummary>[] = [
    {
      key: "revisionNumber",
      header: "Revisão",
      render: (r) => `R${r.revisionNumber}`,
    },
    {
      key: "approvedAt",
      header: "Publicada em",
      render: (r) => new Date(r.approvedAt).toLocaleString("pt-BR"),
    },
    {
      key: "approvedBy",
      header: "Responsável",
      render: (r) => prcPersonLabel(r.approvedBy),
    },
    {
      key: "changedPaths",
      header: "Campos alterados",
      render: (r) =>
        r.changedPaths.length
          ? r.changedPaths.map(prcFieldLabel).join(", ")
          : "—",
    },
    {
      key: "requestId",
      header: "Solicitação de origem",
      render: (r) =>
        basePath && r.requestId ? (
          <EngineeringActionButton
            variant="link"
            href={prcDetailTabHref(basePath, r.requestId, "draft")}
            title={`Abrir a solicitação ${prcShortId(r.requestId)} que gerou esta revisão`}
          >
            {prcShortId(r.requestId)}
          </EngineeringActionButton>
        ) : (
          prcShortId(r.requestId || "")
        ),
    },
    {
      key: "view",
      header: "",
      interactive: true,
      render: (r) => (
        <EngineeringActionButton
          variant="link"
          title={`Visualizar snapshot da revisão R${r.revisionNumber}`}
          onClick={() => open(r.revisionNumber)}
        >
          Visualizar
        </EngineeringActionButton>
      ),
    },
  ];

  const snapshotFields = snapshot
    ? Object.entries(snapshot.technical_snapshot || {})
        .filter(([path]) => path !== "suppliers")
        .map(([path, value]) => ({
          label: prcFieldLabel(path),
          value: fmt(value),
        }))
    : [];

  return (
    <div className="engineering-prc__revisions">
      <DataTableSection
        title="Revisões técnicas publicadas"
        hint={PRC_COPY.immutableRevision}
        columns={columns}
        rows={revisions}
        rowKey={(r) => String(r.revisionNumber)}
        hideSearch
        emptyMessage={PRC_COPY.noRevisions}
      />

      {loading ? (
        <EngineeringLoadingActivityCard
          title="Carregando revisão"
          description="Lendo o snapshot imutável."
        />
      ) : null}

      {error ? (
        <EngineeringStateBanner variant="error">{error}</EngineeringStateBanner>
      ) : null}

      {snapshot ? (
        <>
          <EngineeringDetailCard
            title={`Revisão R${snapshot.revision_number} — snapshot imutável`}
            hint={`Publicada em ${new Date(snapshot.approved_at).toLocaleString("pt-BR")} por ${prcPersonLabel(snapshot.approved_by_subject)}${snapshot.request_id ? ` · Solicitação de origem ${prcShortId(snapshot.request_id)}` : ""}`}
          >
            <EngineeringDetailFieldGrid fields={snapshotFields} />
            {Array.isArray(snapshot.technical_snapshot?.suppliers) &&
            snapshot.technical_snapshot.suppliers.length ? (
              <ul className="engineering-prc__supplier-diff">
                {(
                  snapshot.technical_snapshot.suppliers as Record<
                    string,
                    unknown
                  >[]
                ).map((s, i) => (
                  <li key={i}>
                    <strong>
                      {String(s.supplierCode || "—")} · loja{" "}
                      {String(s.store || "—")}
                    </strong>{" "}
                    {String(s.supplierName || "")}
                    {s.partNumber
                      ? ` · PN ${String(s.partNumber)}`
                      : " · PN não informado"}
                    {s.catalogNumber
                      ? ` · catálogo ${String(s.catalogNumber)}`
                      : ""}
                  </li>
                ))}
              </ul>
            ) : null}
          </EngineeringDetailCard>

          {snapshot.changes?.length ? (
            <EngineeringSectionCard
              title="Alterações desta revisão"
              subtitle="Antes → depois por campo, com justificativa"
            >
              <ul className="engineering-prc__supplier-diff">
                {snapshot.changes.map((c, i) => (
                  <li key={i}>
                    <strong>{prcFieldLabel(c.path)}</strong>: {fmt(c.before)} →{" "}
                    {fmt(c.after)}
                    {c.reason ? ` — ${c.reason}` : ""}
                  </li>
                ))}
              </ul>
            </EngineeringSectionCard>
          ) : null}
        </>
      ) : null}
    </div>
  );
}
