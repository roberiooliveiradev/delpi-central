import { ChevronDown, ChevronRight } from "lucide-react";
import { useCallback, useMemo, useState, type ReactNode } from "react";

import {
  fetchPublicDeliveryMap,
  type DeliveryMapOpProgress,
  type DeliveryMapRow,
  type PublicDeliveryMapPayload,
} from "./api";
import { usePublicDeliveryMapProgress } from "./usePublicDeliveryMapProgress";
import { formatOpQuantity } from "./formatOpQuantity";
import { downloadDeliveryMapExcel } from "./deliveryMapExcel";
import { deliveryMapPublicCopy } from "./deliveryMapPublicContent";
import "./cockpit.css";
import "./delivery-map.css";

type Props = {
  token: string;
  branch: string;
  initial: PublicDeliveryMapPayload;
};

function formatIsoDayMonth(value: string): string {
  const [year, month, day] = value.slice(0, 10).split("-");
  if (!year || !month || !day) return value;
  return `${day}/${month}`;
}

function formatRefreshedAt(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function progressTone(progress: DeliveryMapOpProgress): "low" | "mid" | "high" | "complete" | "running" {
  if (progress.in_progress > 0 && progress.percent < 100) return "running";
  if (progress.percent >= 100) return "complete";
  if (progress.percent >= 67) return "high";
  if (progress.percent >= 34) return "mid";
  return "low";
}

function progressAriaLabel(progress: DeliveryMapOpProgress): string {
  if (progress.in_progress > 0) {
    return `Progresso do conjunto: ${progress.percent}% (${progress.completed} de ${progress.total} operações apontadas, ${progress.in_progress} em produção)`;
  }
  return `Progresso do conjunto: ${progress.percent}% (${progress.completed} de ${progress.total} operações apontadas)`;
}

function OpProgressBar({ progress }: { progress: DeliveryMapOpProgress | undefined }) {
  if (!progress || progress.total <= 0) return null;
  const tone = progressTone(progress);
  const width = Math.max(progress.percent > 0 ? 8 : 0, progress.percent);

  return (
    <span
      className="pcp-pub-dm__op-progress"
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={progress.percent}
      aria-label={progressAriaLabel(progress)}
      title={progressAriaLabel(progress)}
    >
      <span className="pcp-pub-dm__op-progress-track">
        <span
          className={`pcp-pub-dm__op-progress-fill pcp-pub-dm__op-progress-fill--${tone}`}
          style={{ width: `${width}%` }}
        />
      </span>
      {progress.percent > 0 ? (
        <span className="pcp-pub-dm__op-progress-pct" aria-hidden="true">
          {progress.percent}%
        </span>
      ) : null}
    </span>
  );
}

function isRowReported(progress: DeliveryMapOpProgress | undefined): boolean {
  return (progress?.percent ?? 0) >= 100;
}

function rowClassName(row: DeliveryMapRow, progress: DeliveryMapOpProgress | undefined): string {
  const parts = ["pcp-pub-dm__row"];
  if (row.mp_ok) parts.push("pcp-pub-dm__row--mp-ok");
  if (isRowReported(progress)) parts.push("pcp-pub-dm__row--reported");
  return parts.join(" ");
}

function BrandBar({
  eyebrow,
  title,
  stats,
}: {
  eyebrow: string;
  title: string;
  stats?: ReactNode;
}) {
  return (
    <header className="pcp-pub__brandbar">
      <div className="pcp-pub__brandbar-inner">
        <div className="pcp-pub__identity">
          <span className="pcp-pub__logo">
            <img src="/p/logoMinhaDelpi.svg" alt="Minha DELPI" draggable={false} />
          </span>
          <div className="pcp-pub__identity-text">
            <p className="pcp-pub__eyebrow">{eyebrow}</p>
            <div className="pcp-pub__title-row">
              <h1>{title}</h1>
            </div>
            {stats ? <div className="pcp-pub__stats">{stats}</div> : null}
          </div>
        </div>
      </div>
    </header>
  );
}

export function DeliveryMapPublicPage({ token, branch, initial }: Props) {
  const [payload, setPayload] = useState(initial);
  const [searchDraft, setSearchDraft] = useState(initial.filters.search ?? "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());
  const [exporting, setExporting] = useState(false);
  const progressByOrder = usePublicDeliveryMapProgress(token, branch, payload);

  const activeSearch = payload.filters.search ?? "";

  const reload = useCallback(
    async (search: string) => {
      setLoading(true);
      try {
        const next = await fetchPublicDeliveryMap(token, branch, search);
        setPayload(next);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Não foi possível atualizar o mapa.");
      } finally {
        setLoading(false);
      }
    },
    [token, branch],
  );

  const toggleSection = useCallback((key: string) => {
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }, []);

  const periodLabel = useMemo(() => {
    if (!payload.snapshot.refreshed_at) return null;
    return `Congelado em ${formatRefreshedAt(payload.snapshot.refreshed_at)}`;
  }, [payload.snapshot.refreshed_at]);

  const handleExportExcel = useCallback(async () => {
    if (payload.summary.order_count === 0) return;
    setExporting(true);
    try {
      await downloadDeliveryMapExcel(
        payload,
        deliveryMapPublicCopy.exportFileName(branch),
        progressByOrder,
      );
    } finally {
      setExporting(false);
    }
  }, [branch, payload, progressByOrder]);

  return (
    <section className="pcp-pub pcp-pub-dm">
      <BrandBar
        eyebrow={`Mapa de entrega · Filial ${branch}`}
        title="Ordens de produção a entregar"
        stats={
          <>
            <span className="pcp-pub__chip">
              {payload.summary.order_count}{" "}
              {payload.summary.order_count === 1 ? "OP" : "OPs"}
            </span>
            {periodLabel ? <span className="pcp-pub__chip">{periodLabel}</span> : null}
          </>
        }
      />

      <div className="pcp-pub__wrap">
        <p className="pcp-pub__notice">
          Visualização somente leitura — atualizada pelo PCP. O progresso do conjunto carrega
          automaticamente para hoje, atrasadas e entregas nos próximos 5 dias.
        </p>

        <div className="pcp-pub-dm__toolbar">
          <label className="pcp-pub-dm__search">
            <span className="pcp-pub-dm__sr-only">Buscar no mapa de entrega</span>
            <input
              type="search"
              value={searchDraft}
              placeholder="OP, produto ou observação…"
              onChange={(event) => setSearchDraft(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  void reload(searchDraft.trim());
                }
              }}
            />
          </label>
          <button
            type="button"
            className="pcp-pub-dm__btn"
            disabled={loading}
            onClick={() => void reload(searchDraft.trim())}
          >
            {loading ? "Buscando…" : "Buscar"}
          </button>
          <button
            type="button"
            className="pcp-pub-dm__btn pcp-pub-dm__btn--export"
            disabled={exporting || payload.summary.order_count === 0}
            onClick={() => void handleExportExcel()}
          >
            {exporting ? deliveryMapPublicCopy.exportBusy : deliveryMapPublicCopy.exportLabel}
          </button>
        </div>

        {error ? <p className="pcp-pub__error">{error}</p> : null}

        <div className="pcp-pub-dm" aria-busy={loading}>
          {payload.sections.length === 0 ? (
            <p className="pcp-pub-dm__empty">
              {activeSearch.trim()
                ? "Nenhuma OP encontrada para esta busca."
                : "Nenhuma OP de PA com saldo neste recorte."}
            </p>
          ) : (
            payload.sections.map((section) => {
              const isCollapsed = collapsed.has(section.section_key);
              return (
                <section key={section.section_key} className="pcp-pub-dm__section">
                  <button
                    type="button"
                    className="pcp-pub-dm__section-head"
                    aria-expanded={!isCollapsed}
                    onClick={() => toggleSection(section.section_key)}
                  >
                    {isCollapsed ? (
                      <ChevronRight size={16} aria-hidden />
                    ) : (
                      <ChevronDown size={16} aria-hidden />
                    )}
                    <span className="pcp-pub-dm__section-title">{section.label}</span>
                    <span className="pcp-pub-dm__section-count">
                      {section.row_count} {section.row_count === 1 ? "OP" : "OPs"}
                    </span>
                  </button>

                  {!isCollapsed ? (
                    <div className="pcp-pub-dm__table-wrap">
                      <table className="pcp-pub-dm__table">
                        <thead>
                          <tr>
                            <th scope="col">Número</th>
                            <th scope="col">Produto</th>
                            <th scope="col">Dt. prevista</th>
                            <th scope="col">Quant. original</th>
                            <th scope="col">Saldo a entregar</th>
                            <th scope="col">MP-OK</th>
                            <th scope="col">Feedback</th>
                            <th scope="col">Observações</th>
                          </tr>
                        </thead>
                        <tbody>
                          {section.rows.map((row) => {
                            const progress = progressByOrder[row.production_order];
                            return (
                              <tr
                                key={row.production_order}
                                className={rowClassName(row, progress)}
                              >
                                <td className="pcp-pub-dm__cell-op">
                                  <span className="pcp-pub-dm__op-line">
                                    <span className="pcp-pub-dm__op-code">
                                      {row.production_order}
                                    </span>
                                    <OpProgressBar progress={progress} />
                                  </span>
                                </td>
                                <td className="pcp-pub-dm__cell-product">{row.product_code}</td>
                                <td
                                  className={
                                    row.is_delayed ? "pcp-pub-dm__cell-due--late" : undefined
                                  }
                                >
                                  {row.due_date ? formatIsoDayMonth(row.due_date) : "—"}
                                </td>
                                <td className="pcp-pub-dm__cell-num">
                                  {formatOpQuantity(row.planned_qty)}
                                </td>
                                <td className="pcp-pub-dm__cell-num">
                                  {formatOpQuantity(row.pending_qty)}
                                </td>
                                <td className="pcp-pub-dm__cell-mp">
                                  {row.mp_ok ? "✓" : ""}
                                </td>
                                <td className="pcp-pub-dm__cell-feedback">
                                  {row.work_center?.trim() ? row.work_center : ""}
                                </td>
                                <td className="pcp-pub-dm__cell-obs">
                                  {row.observation ?? "—"}
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  ) : null}
                </section>
              );
            })
          )}
        </div>
      </div>
    </section>
  );
}
