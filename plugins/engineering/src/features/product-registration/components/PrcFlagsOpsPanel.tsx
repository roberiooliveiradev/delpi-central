/** Visão operacional transversal de bandeiras (AuthZ no backend). */

import { useCallback, useEffect, useState } from "react";
import { Flag } from "lucide-react";

import { HomeApiError } from "../../../api/httpClient";
import {
  EngineeringActionButton,
  EngineeringFilterInput,
  EngineeringFilterSelect,
  EngineeringFiltersRow,
  EngineeringLoadingActivityCard,
  EngineeringStateBanner,
} from "../../../ui/engineeringUi";
import {
  fetchPrcFlagsCrossCase,
  type PrcAttendanceFlag,
} from "../api/productRegistrationApi";
import { PRC_FIELD_LABELS, PRC_STATUS_LABELS, prcShortId } from "../prcCopy";
import { navigatePrc, PRC_PATHS } from "../prcNavigate";

export function PrcFlagsOpsPanel({ basePath }: { basePath: string }) {
  const [open, setOpen] = useState(false);
  const [status, setStatus] = useState("OPEN");
  const [targetPath, setTargetPath] = useState("");
  const [targetAttribute, setTargetAttribute] = useState("");
  const [productCode, setProductCode] = useState("");
  const [items, setItems] = useState<PrcAttendanceFlag[]>([]);
  const [totals, setTotals] = useState({
    total: 0,
    openCount: 0,
    distinctRequestCount: 0,
    distinctProductCount: 0,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [page, setPage] = useState(1);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await fetchPrcFlagsCrossCase({
        status: status === "all" ? "all" : (status as "OPEN" | "RESOLVED"),
        targetPath: targetPath || undefined,
        targetAttribute: targetAttribute || undefined,
        productCode: productCode.trim() || undefined,
        page,
        pageSize: 25,
      });
      const data = res.data;
      setItems(data.items || []);
      setTotals({
        total: data.total ?? 0,
        openCount: data.openCount ?? 0,
        distinctRequestCount: data.distinctRequestCount ?? 0,
        distinctProductCount: data.distinctProductCount ?? 0,
      });
    } catch (err) {
      setError(
        err instanceof HomeApiError
          ? err.message
          : "Não foi possível carregar bandeiras.",
      );
    } finally {
      setLoading(false);
    }
  }, [status, targetPath, targetAttribute, productCode, page]);

  useEffect(() => {
    if (!open) return;
    void load();
  }, [open, load]);

  return (
    <section className="engineering-prc__flags-ops" aria-label="Bandeiras">
      <EngineeringActionButton
        variant={open ? "secondary" : "ghost"}
        onClick={() => setOpen((v) => !v)}
      >
        <Flag size={14} aria-hidden />{" "}
        {open ? "Ocultar campos sinalizados" : "Campos sinalizados / bandeiras"}
      </EngineeringActionButton>
      {open ? (
        <>
          <EngineeringFiltersRow>
            <div className="engineering-prc__flags-ops-filters">
              <EngineeringFilterSelect
                label="Situação da bandeira"
                value={status}
                onChange={(v) => {
                  setPage(1);
                  setStatus(v);
                }}
                options={[
                  { value: "OPEN", label: "Abertas" },
                  { value: "RESOLVED", label: "Resolvidas" },
                  { value: "all", label: "Todas" },
                ]}
              />
              <EngineeringFilterSelect
                label="Campo"
                value={targetPath}
                onChange={(v) => {
                  setPage(1);
                  setTargetPath(v);
                }}
                options={[
                  { value: "", label: "Todos os campos" },
                  ...Object.entries(PRC_FIELD_LABELS).map(([value, label]) => ({
                    value,
                    label,
                  })),
                ]}
              />
              <EngineeringFilterSelect
                label="Atributo SA5"
                value={targetAttribute}
                onChange={(v) => {
                  setPage(1);
                  setTargetAttribute(v);
                }}
                options={[
                  { value: "", label: "Todos" },
                  { value: "partNumber", label: "Part Number" },
                  { value: "catalogNumber", label: "Catálogo" },
                ]}
              />
              <EngineeringFilterInput
                label="Produto"
                value={productCode}
                onChange={setProductCode}
                placeholder="Código oficial"
              />
              <EngineeringActionButton
                variant="secondary"
                onClick={() => {
                  setPage(1);
                  void load();
                }}
              >
                Filtrar
              </EngineeringActionButton>
            </div>
          </EngineeringFiltersRow>
          <p className="engineering-prc__muted" aria-live="polite">
            {totals.total} bandeira(s) · {totals.distinctRequestCount}{" "}
            solicitação(ões) · {totals.distinctProductCount} produto(s) ·{" "}
            {totals.openCount} aberta(s) — totais do servidor (escopo
            autorizado).
          </p>
          {error ? (
            <EngineeringStateBanner variant="error">{error}</EngineeringStateBanner>
          ) : null}
          {loading ? (
            <EngineeringLoadingActivityCard
              title="Carregando bandeiras"
              description="Consulta transversal autorizada na Engineering API."
            />
          ) : null}
          {!loading && !error ? (
            <ul className="engineering-prc__flags-list">
              {items.map((f) => {
                const field =
                  f.subject === "FIELD"
                    ? PRC_FIELD_LABELS[f.targetPath || ""] || f.targetPath
                    : f.subject === "SUPPLIER_LINK"
                      ? `${f.targetAttribute} · ${f.supplierKey?.supplierCode}/${f.supplierKey?.store}`
                      : "Geral";
                return (
                  <li key={f.id} className="engineering-prc__flag-card">
                    <div className="engineering-prc__flag-main">
                      <div className="engineering-prc__flag-title-row">
                        <strong>{f.title}</strong>
                        <span
                          className={
                            f.status === "OPEN"
                              ? "engineering-prc__flag-badge engineering-prc__flag-badge--open"
                              : "engineering-prc__flag-badge engineering-prc__flag-badge--resolved"
                          }
                        >
                          {f.status === "OPEN" ? "Aberta" : "Resolvida"}
                        </span>
                      </div>
                      <p className="engineering-prc__muted">
                        {f.productCode || "—"} · {prcShortId(f.requestId)} ·{" "}
                        {field} ·{" "}
                        {PRC_STATUS_LABELS[f.requestStatus || ""] ||
                          f.requestStatus ||
                          "—"}
                      </p>
                    </div>
                    <EngineeringActionButton
                      variant="ghost"
                      onClick={() =>
                        navigatePrc(PRC_PATHS.detail(f.requestId), basePath)
                      }
                    >
                      Abrir solicitação
                    </EngineeringActionButton>
                  </li>
                );
              })}
              {!items.length ? (
                <li className="engineering-prc__muted">
                  Nenhuma bandeira no filtro atual.
                </li>
              ) : null}
            </ul>
          ) : null}
          {totals.total > 25 ? (
            <div className="engineering-prc__flags-actions">
              <EngineeringActionButton
                variant="ghost"
                disabled={page <= 1 || loading}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                Anterior
              </EngineeringActionButton>
              <span className="engineering-prc__muted">Página {page}</span>
              <EngineeringActionButton
                variant="ghost"
                disabled={page * 25 >= totals.total || loading}
                onClick={() => setPage((p) => p + 1)}
              >
                Próxima
              </EngineeringActionButton>
            </div>
          ) : null}
        </>
      ) : null}
    </section>
  );
}
