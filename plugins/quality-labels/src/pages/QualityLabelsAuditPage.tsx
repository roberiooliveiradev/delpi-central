import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Eye,
  FileCheck,
  FileText,
  PlusCircle,
  Power,
  PowerOff,
  RefreshCw,
  Trash2,
} from "lucide-react";
import { NativeTextControl } from "@delpi/plugin-ui/index";

import { listAuditEvents } from "../api/qualityLabelsApi";
import { DataTableSection, type DataTableColumn } from "../components/data";
import { formatOperationalUnit } from "../utils/operationalUnits";
import type { AuditEvent } from "../types/qualityLabels";

type EventMeta = {
  label: string;
  badge: string;
  icon: typeof Eye;
};

const EVENT_META: Record<string, EventMeta> = {
  label_created: { label: "Etiqueta criada", badge: "ql-badge--on", icon: PlusCircle },
  label_activated: { label: "Reativada", badge: "ql-badge--on", icon: Power },
  label_deactivated: { label: "Desativada", badge: "ql-badge--off", icon: PowerOff },
  label_deleted: { label: "Excluída", badge: "ql-badge--danger", icon: Trash2 },
  label_viewed: { label: "Acesso público", badge: "ql-badge--info", icon: Eye },
  certificate_saved: { label: "Certificado salvo", badge: "ql-badge--info", icon: FileText },
  certificate_issued: { label: "Certificado emitido", badge: "ql-badge--on", icon: FileCheck },
};

const RESULT_LABELS: Record<string, string> = {
  approved: "Aprovado",
  rejected: "Reprovado",
  conditional: "Condicional",
};

const FILTER_OPTIONS: { value: string; label: string }[] = [
  { value: "label_created", label: "Criações" },
  { value: "label_activated", label: "Reativações" },
  { value: "label_deactivated", label: "Desativações" },
  { value: "label_deleted", label: "Exclusões" },
  { value: "label_viewed", label: "Acessos públicos" },
  { value: "certificate_saved", label: "Certificados salvos" },
  { value: "certificate_issued", label: "Certificados emitidos" },
];

function eventMeta(eventType: string): EventMeta {
  return (
    EVENT_META[eventType] ?? {
      label: eventType,
      badge: "ql-badge--info",
      icon: Eye,
    }
  );
}

function formatDateTime(value: string | null): string {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "-";
  return date.toLocaleString("pt-BR");
}

export function QualityLabelsAuditPage() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [summary, setSummary] = useState<Record<string, number>>({});
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [typeFilters, setTypeFilters] = useState<string[]>([]);

  const refresh = useCallback(
    async (searchTerm: string, types: string[], signal?: AbortSignal) => {
      setLoading(true);
      setError(null);
      try {
        const page = await listAuditEvents(
          {
            search: searchTerm || undefined,
            eventTypes: types.length > 0 ? types : undefined,
            limit: 200,
          },
          signal,
        );
        setEvents(page.items);
        setSummary(page.summary ?? {});
        setTotal(page.pagination?.total ?? page.items.length);
      } catch (err) {
        if (!(err instanceof DOMException && err.name === "AbortError")) {
          setError(err instanceof Error ? err.message : "Erro ao carregar a auditoria.");
        }
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  useEffect(() => {
    const controller = new AbortController();
    void refresh(search, typeFilters, controller.signal);
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [typeFilters, refresh]);

  function toggleType(value: string) {
    setTypeFilters((prev) =>
      prev.includes(value) ? prev.filter((v) => v !== value) : [...prev, value],
    );
  }

  const columns = useMemo<DataTableColumn<AuditEvent>[]>(
    () => [
      {
        key: "createdAt",
        header: "Data / hora",
        sortable: true,
        sortValue: (row) => row.createdAt ?? "",
        render: (row) => (
          <span className="ql-cell-nowrap">{formatDateTime(row.createdAt)}</span>
        ),
      },
      {
        key: "event",
        header: "Evento",
        sortable: true,
        sortValue: (row) => String(row.eventType),
        render: (row) => {
          const meta = eventMeta(String(row.eventType));
          const Icon = meta.icon;
          return (
            <span className={`ql-badge ${meta.badge}`}>
              <Icon className="ql-badge__icon" />
              {meta.label}
            </span>
          );
        },
      },
      {
        key: "op",
        header: "OP",
        sortable: true,
        sortValue: (row) => row.productionOrder ?? "",
        render: (row) => row.productionOrder ?? "-",
      },
      {
        key: "product",
        header: "Produto",
        sortable: true,
        sortValue: (row) => row.productCode ?? "",
        render: (row) => row.productCode ?? "-",
      },
      {
        key: "unit",
        header: "Unidade",
        sortable: true,
        sortValue: (row) => row.branchName ?? row.branch ?? "",
        render: (row) => row.branchName ?? formatOperationalUnit(row.branch, "-"),
      },
      {
        key: "result",
        header: "Resultado",
        sortable: true,
        sortValue: (row) => (row.result ? String(row.result) : ""),
        render: (row) =>
          row.result ? RESULT_LABELS[String(row.result)] ?? row.result : "-",
      },
      {
        key: "actor",
        header: "Responsável",
        sortable: true,
        sortValue: (row) => row.actorName ?? "",
        render: (row) => row.actorName ?? "-",
      },
    ],
    [],
  );

  return (
    <div className="ql-page-stack">
      {error && <div className="ql-state ql-state--error"><p>{error}</p></div>}

      <section className="ql-audit-summary">
        {FILTER_OPTIONS.map((opt) => {
          const meta = eventMeta(opt.value);
          const Icon = meta.icon;
          const count = summary[opt.value] ?? 0;
          const active = typeFilters.includes(opt.value);
          return (
            <button
              type="button"
              key={opt.value}
              className={`ql-audit-stat ${active ? "ql-audit-stat--active" : ""}`}
              onClick={() => toggleType(opt.value)}
              title={`Filtrar: ${opt.label}`}
            >
              <span className="ql-audit-stat__icon">
                <Icon className="ql-icon" />
              </span>
              <span className="ql-audit-stat__value">{count}</span>
              <span className="ql-audit-stat__label">{opt.label}</span>
            </button>
          );
        })}
      </section>

      <DataTableSection
        title="Trilha de auditoria"
        hint={`${total} evento(s)`}
        columns={columns}
        rows={events}
        rowKey={(row) => row.id}
        loading={loading}
        hideSearch
        hidePageSizeSelect
        clearClientSortOnThirdClick
        defaultSortKey="createdAt"
        defaultSortDirection="desc"
        emptyMessage="Nenhum evento de auditoria registrado."
        toolbarExtra={
          <div className="ql-list__filters">
            <div className="ql-op-row">
              <NativeTextControl
                className="ql-input"
                value={search}
                onChange={setSearch}
                placeholder="Buscar por OP, produto ou usuário"
                onKeyDown={(e) => {
                  if (e.key === "Enter") void refresh(search, typeFilters);
                }}
              />
              <button
                type="button"
                className="ql-btn ql-btn--ghost"
                onClick={() => void refresh(search, typeFilters)}
              >
                <RefreshCw className="ql-icon" /> Atualizar
              </button>
            </div>
          </div>
        }
      />
    </div>
  );
}
