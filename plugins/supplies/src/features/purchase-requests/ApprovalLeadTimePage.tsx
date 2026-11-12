import { useEffect, useMemo, useState } from "react";
import { RefreshCw } from "lucide-react";

import { useSuppliesSession } from "../../app/SuppliesSessionContext";
import { navigatePluginPath, navigatePluginView } from "../../app/pluginNavigation";
import { buildPluginPath, buildPurchaseRequestDetailPath } from "../../app/pluginRoutes";
import {
  SuppliesActionButton,
  SuppliesEmptyState,
  SuppliesLoadingCard,
  SuppliesPageHero,
  SuppliesPagePath,
  SuppliesSectionCard,
  SuppliesStateBanner,
} from "../../app/suppliesUi";
import {
  getApprovalLeadTime,
  type ApprovalLeadTimeFilters,
  type ApprovalLeadTimeResponse,
} from "./approvalLeadTimeApi";
import { ApprovalLeadTimeApproverInsights } from "./ApprovalLeadTimeApproverInsights";
import { ApprovalLeadTimePendingRequests } from "./ApprovalLeadTimePendingRequests";
import "./ApprovalLeadTimePage.css";

function localToday(): string {
  const now = new Date();
  const date = new Date(now.getTime() - now.getTimezoneOffset() * 60000);
  return date.toISOString().slice(0, 10);
}

function dateLabel(value: string | null | undefined): string {
  if (!value) return "—";
  const [year, month, day] = value.slice(0, 10).split("-");
  return year && month && day ? `${day}/${month}/${year}` : value;
}

function numberLabel(value: number | null | undefined, decimals = 0): string {
  return value == null ? "—" : value.toLocaleString("pt-BR", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

function defaultFilters(units: string[]): ApprovalLeadTimeFilters {
  const today = localToday();
  return {
    branches: units.filter((code) => code === "01" || code === "02"),
    dateFrom: `${today.slice(0, 4)}-01-01`,
    dateTo: today,
    requestNumber: "",
    page: 1,
  };
}

export function ApprovalLeadTimePage({ basePath }: { basePath: string }) {
  const session = useSuppliesSession();
  const allowed = useMemo(
    () => session.allowedUnits.filter((code) => code === "01" || code === "02"),
    [session.allowedUnits],
  );
  const [branch, setBranch] = useState("all");
  const [dateFrom, setDateFrom] = useState(() => defaultFilters([]).dateFrom);
  const [dateTo, setDateTo] = useState(localToday);
  const [requestNumber, setRequestNumber] = useState("");
  const [applied, setApplied] = useState<ApprovalLeadTimeFilters | null>(null);
  const [data, setData] = useState<ApprovalLeadTimeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const allowedKey = allowed.join(",");
  useEffect(() => {
    if (!allowedKey) return;
    setApplied((previous) => previous ?? defaultFilters(allowedKey.split(",")));
  }, [allowedKey]);

  useEffect(() => {
    if (!applied?.branches.length) return;
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    getApprovalLeadTime(applied, controller.signal)
      .then((payload) => {
        if (payload.source !== "SCR010" || payload.scope !== "confirmed_history_only") {
          throw new Error("A consulta não confirmou a fonte oficial da aprovação.");
        }
        setData(payload);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setData(null);
        setError(err instanceof Error ? err.message : "Falha ao consultar indicador.");
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [applied, reloadKey]);

  const apply = () => {
    if (!allowed.length) return;
    if (dateFrom > dateTo || !dateFrom || !dateTo) {
      setError("Confira as datas do período.");
      return;
    }
    if (requestNumber.trim() && !/^\d{1,16}$/.test(requestNumber.trim())) {
      setError("Informe somente os dígitos da SC.");
      return;
    }
    setError(null);
    setApplied({
      branches: branch === "all" ? allowed : allowed.filter((code) => code === branch),
      dateFrom,
      dateTo,
      requestNumber,
      page: 1,
    });
  };

  const changePage = (page: number) => {
    if (!applied || loading || !data || page < 1 || page > data.total_pages) return;
    setApplied({ ...applied, page });
  };

  const summary = data?.summary;
  const listHref = buildPluginPath("purchase_requests", basePath);

  return (
    <div className="sp-page-stack sp-approval-lead-time">
      <SuppliesPagePath
        back={{
          label: "Solicitações",
          href: listHref,
          onNavigate: (event) => {
            event.preventDefault();
            navigatePluginView("purchase_requests", { basePath });
          },
        }}
        items={[]}
        current="Tempo de aprovação"
      />
      <SuppliesPageHero
        eyebrow="Portal Suprimentos / Alçadas"
        title="Tempo de aprovação de solicitações"
        description="Da inclusão da SC à última aprovação registrada na alçada. Apenas histórico comprovado na SCR do Protheus."
      />
      <SuppliesSectionCard title="Filtros do indicador" hint="Período pela data de criação da SC. Dias corridos.">
        <form
          className="sp-approval-lead-time__filters"
          onSubmit={(event) => { event.preventDefault(); apply(); }}
        >
          <label>
            Unidade
            <select aria-label="Unidade" value={branch} onChange={(e) => setBranch(e.target.value)}>
              <option value="all">Todas as unidades</option>
              {allowed.map((code) => (
                <option key={code} value={code}>{code === "01" ? "01 · Matriz SC" : "02 · Filial ES"}</option>
              ))}
            </select>
          </label>
          <label>
            Data inicial
            <input aria-label="Data inicial" type="date" required value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
          </label>
          <label>
            Data final
            <input aria-label="Data final" type="date" required value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
          </label>
          <label>
            SC (opcional)
            <input aria-label="Número da SC" inputMode="numeric" placeholder="Ex.: 171945" value={requestNumber} onChange={(e) => setRequestNumber(e.target.value)} />
          </label>
          <SuppliesActionButton type="submit" variant="primary" disabled={loading || !allowed.length}>
            Aplicar filtros
          </SuppliesActionButton>
          <SuppliesActionButton type="button" variant="ghost" disabled={loading || !allowed.length} onClick={() => setReloadKey((key) => key + 1)}>
            <RefreshCw size={16} aria-hidden="true" /> Atualizar
          </SuppliesActionButton>
        </form>
      </SuppliesSectionCard>

      {error ? <SuppliesStateBanner variant="error">{error}</SuppliesStateBanner> : null}
      {!allowed.length ? (
        <SuppliesEmptyState title="Sem unidades disponíveis" message="É necessário ter acesso ao Portal Suprimentos." />
      ) : null}
      {loading ? <SuppliesLoadingCard title="Consultando aprovações comprovadas no Protheus" variant="panel" /> : null}

      {!loading && data ? (
        <>
          <section className="sp-approval-lead-time__metrics" aria-label="Resumo de alçadas">
            {[
              { title: "SCs com histórico comprovado", value: numberLabel(summary?.total_requests) },
              { title: "Tempo médio de aprovação", value: summary?.avg_lead_days == null ? "—" : `${numberLabel(summary.avg_lead_days, 2)} dias` },
              { title: "Aprovadas no mesmo dia", value: numberLabel(summary?.same_day) },
              { title: "Com mais de um nível", value: numberLabel(summary?.multi_level) },
              { title: "SCs com alçada pendente na SCR", value: numberLabel(summary?.pending_requests) },
            ].map((metric) => (
              <div className="sp-approval-lead-time__metric" key={metric.title}>
                <span>{metric.title}</span>
                <strong>{metric.value}</strong>
              </div>
            ))}
          </section>

          <ApprovalLeadTimePendingRequests
            items={data.pending_items}
            total={data.pending_total}
            truncated={data.pending_truncated}
            basePath={basePath}
          />

          <ApprovalLeadTimeApproverInsights
            summary={data.summary}
            approvers={data.approver_stats}
          />

          <SuppliesSectionCard title="Solicitações com histórico comprovado" hint="Clique na SC para abrir a ficha. Expanda a linha para consultar cada nível registrado.">
            {data.items.length === 0 ? (
              <SuppliesEmptyState title="Nenhuma SC encontrada" message="Não há SC liberada com histórico SCR comprovado neste recorte." />
            ) : (
              <div className="sp-approval-lead-time__table-scroll">
                <table className="sp-approval-lead-time__table">
                  <thead><tr>
                    <th>SC</th><th>Unidade</th><th>Solicitante</th>
                    <th>Criação</th><th>Última aprovação</th><th>Último aprovador</th><th>Níveis</th><th>Prazo</th><th>Etapas</th>
                  </tr></thead>
                  <tbody>
                    {data.items.map((item) => (
                      <tr key={`${item.branch}:${item.request_number}`}>
                        <td>
                          <button type="button" className="sp-approval-lead-time__link" onClick={() =>
                            navigatePluginPath(buildPurchaseRequestDetailPath(item.branch, item.request_number, basePath))
                          }>{item.request_number}</button>
                        </td>
                        <td>{item.branch}</td>
                        <td>{item.requester_name || "Não identificado"}</td>
                        <td>{dateLabel(item.issue_date)}</td>
                        <td>{dateLabel(item.final_approval_date)}</td>
                        <td className="sp-approval-lead-time__name-cell">
                          {Array.from(new Set(
                            item.events
                              .filter((event) => event.approved_at === item.final_approval_date)
                              .map((event) => event.approver_name || event.approver_code),
                          )).join(" · ") || "—"}
                        </td>
                        <td>{item.approval_levels}</td>
                        <td><strong>{item.lead_days} d</strong></td>
                        <td>
                          <details>
                            <summary aria-label={`Consultar níveis da SC ${item.request_number}`}>Ver níveis</summary>
                            {item.events.length ? (
                              <ol className="sp-approval-lead-time__events">
                                {item.events.map((event, index) => (
                                  <li key={`${event.level}:${event.approved_at}:${event.approver_code}:${index}`}>
                                    <strong>Nível {event.level}</strong> · {dateLabel(event.approved_at)}
                                    <span>
                                      {event.approver_name || `Aprovador ${event.approver_code}`}
                                      {" · "}código {event.approver_code}
                                      {" · "}usuário Protheus {event.approver_user_code || event.action_user_code}
                                    </span>
                                  </li>
                                ))}
                              </ol>
                            ) : <span>Etapas indisponíveis.</span>}
                          </details>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <div className="sp-approval-lead-time__footer">
              <span>{numberLabel(data.total)} SCs comprovadas · página {data.page} de {Math.max(data.total_pages, 1)}</span>
              <div>
                <SuppliesActionButton type="button" variant="ghost" disabled={data.page <= 1} onClick={() => changePage(data.page - 1)}>Anterior</SuppliesActionButton>
                <SuppliesActionButton type="button" variant="ghost" disabled={data.page >= data.total_pages} onClick={() => changePage(data.page + 1)}>Próxima</SuppliesActionButton>
              </div>
            </div>
          </SuppliesSectionCard>

          <p className="sp-approval-lead-time__note">
            Fonte: SCR010 para aprovações e pendências (status 03 e 02); SAK010 apenas para
            nomes de aprovadores; SC1010 para emissão e estado atual. Pendências, aprovações
            automáticas presumidas e solicitações sem SCR não entram no tempo médio das SCs
            concluídas. Os prazos medem dias corridos, não horas úteis. Reaprovações podem
            influenciar os históricos e devem ser homologadas com Suprimentos.
          </p>
        </>
      ) : null}
    </div>
  );
}
