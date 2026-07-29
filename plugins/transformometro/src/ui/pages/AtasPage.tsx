import { useCallback, useEffect, useMemo, useState } from "react";
import { ActionButton, StatusBadge } from "@delpi/plugin-ui/index";
import { ChevronRight, FileText, PenLine, Signature } from "lucide-react";

import type { AppProps } from "../../App";
import { PageHeader } from "../../components/PageHeader";
import { StatusAlerts } from "../../components/StatusAlerts";
import { TransformometroShell } from "../../components/TransformometroShell";
import { SelectField } from "../../components/ui/SelectField";
import { buildAtaPath, TRANSFORMOMETRO_ROUTES } from "../../constants/routes";
import { listAtas, type AtaListItem } from "../../data/api/transformometroAtaApi";
import { ATA_STATUS_LABELS } from "../atas/ataLabels";
import {
  ataSignatureProgress,
  ataStatusLabel,
  ataStatusVariant,
  formatAtaMeetingDate,
  tmAtaStatusBadgeClassNames,
} from "../atas/ataStatusUi";

type Props = Pick<AppProps, "getAccessToken"> & {
  pathname?: string;
  onNavigate: (path: string) => void;
};

const UNIT_OPTIONS = [
  { value: "01", label: "Unidade 01" },
  { value: "02", label: "Unidade 02" },
];

const STATUS_OPTIONS = Object.entries(ATA_STATUS_LABELS).map(([value, label]) => ({
  value,
  label,
}));

function countByStatus(items: AtaListItem[], status: string): number {
  return items.filter((item) => item.status === status).length;
}

export function AtasPage({ getAccessToken, pathname, onNavigate }: Props) {
  const [items, setItems] = useState<AtaListItem[]>([]);
  const [unitCode, setUnitCode] = useState("");
  const [status, setStatus] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const response = await listAtas(getAccessToken, {
        unit_code: unitCode || undefined,
        status: status || undefined,
      });
      setItems(Array.isArray(response.items) ? response.items : []);
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Não foi possível carregar as atas.");
    } finally {
      setLoading(false);
    }
  }, [getAccessToken, status, unitCode]);

  useEffect(() => {
    void load();
  }, [load]);

  const summary = useMemo(
    () => ({
      total: items.length,
      draft: countByStatus(items, "draft"),
      awaiting: countByStatus(items, "awaiting_signatures") + countByStatus(items, "partially_signed"),
      done: countByStatus(items, "signed") + countByStatus(items, "finalized"),
    }),
    [items],
  );

  return (
    <TransformometroShell>
      <PageHeader
        title="Atas Transforma+"
        subtitle="Documente reuniões, acompanhe assinaturas e finalize o registro oficial."
        currentPath={pathname}
        onNavigate={onNavigate}
        onRefresh={() => void load()}
        refreshing={loading}
        actions={
          <>
            <ActionButton onClick={() => onNavigate(TRANSFORMOMETRO_ROUTES.atasPending)}>
              Pendências
            </ActionButton>
            <ActionButton onClick={() => onNavigate(TRANSFORMOMETRO_ROUTES.minhaAssinatura)}>
              Minha assinatura
            </ActionButton>
            <ActionButton
              variant="primary"
              onClick={() => onNavigate(`${TRANSFORMOMETRO_ROUTES.atas}/new`)}
            >
              Nova ata
            </ActionButton>
          </>
        }
      />

      <section className="tm-atas-summary" aria-label="Resumo das atas">
        <div className="tm-atas-summary__card">
          <span className="tm-atas-summary__value">{summary.total}</span>
          <span className="tm-atas-summary__label">Total na lista</span>
        </div>
        <div className="tm-atas-summary__card">
          <span className="tm-atas-summary__value">{summary.draft}</span>
          <span className="tm-atas-summary__label">Rascunhos</span>
        </div>
        <div className="tm-atas-summary__card">
          <span className="tm-atas-summary__value">{summary.awaiting}</span>
          <span className="tm-atas-summary__label">Em assinatura</span>
        </div>
        <div className="tm-atas-summary__card">
          <span className="tm-atas-summary__value">{summary.done}</span>
          <span className="tm-atas-summary__label">Concluídas</span>
        </div>
      </section>

      <section className="tm-atas-toolbar ds-card" aria-label="Filtros">
        <div className="tm-atas-toolbar__filters">
          <SelectField
            id="tm-atas-unit"
            label="Unidade"
            value={unitCode}
            onChange={setUnitCode}
            allowEmpty
            emptyLabel="Todas as unidades"
            options={UNIT_OPTIONS}
          />
          <SelectField
            id="tm-atas-status"
            label="Status"
            value={status}
            onChange={setStatus}
            allowEmpty
            emptyLabel="Todos os status"
            options={STATUS_OPTIONS}
          />
        </div>
        <p className="tm-atas-toolbar__hint ds-muted">
          Clique em uma ata para abrir. Rascunhos podem ser editados na tela seguinte.
        </p>
      </section>

      <StatusAlerts
        error={error}
        loading={loading}
        hasData={items.length > 0}
        loadingTitle="Carregando atas"
        loadingDescription="Buscando atas Transforma+ da(s) unidade(s) permitidas."
        onRetry={() => void load()}
        onDismissError={() => setError(null)}
      />

      {!loading && !error ? (
        <section className="tm-atas-list ds-card" aria-label="Lista de atas">
          <header className="tm-atas-list__header">
            <div>
              <h2 className="tm-atas-list__title">Atas</h2>
              <p className="tm-atas-list__count ds-muted">
                {items.length === 1 ? "1 registro" : `${items.length} registros`}
              </p>
            </div>
          </header>

          {items.length === 0 ? (
            <div className="tm-atas-empty">
              <FileText size={36} strokeWidth={1.5} aria-hidden />
              <h3>Nenhuma ata neste filtro</h3>
              <p className="ds-muted">
                Crie uma nova ata ou ajuste unidade e status para ver outros registros.
              </p>
              <ActionButton
                variant="primary"
                onClick={() => onNavigate(`${TRANSFORMOMETRO_ROUTES.atas}/new`)}
              >
                Nova ata
              </ActionButton>
            </div>
          ) : (
            <ul className="tm-atas-list__rows">
              {items.map((item) => {
                const progress = ataSignatureProgress(item);
                const href = buildAtaPath(item.id);
                return (
                  <li key={item.id}>
                    <button
                      type="button"
                      className={`tm-atas-row tm-atas-row--${item.status || "draft"}`}
                      onClick={() => onNavigate(href)}
                    >
                      <span className="tm-atas-row__accent" aria-hidden />
                      <span className="tm-atas-row__main">
                        <span className="tm-atas-row__title">{item.title || "Sem título"}</span>
                        <span className="tm-atas-row__meta">
                          <span>{formatAtaMeetingDate(item.meeting_date)}</span>
                          <span aria-hidden>·</span>
                          <span>Unidade {item.unit_code}</span>
                          {item.minute_number ? (
                            <>
                              <span aria-hidden>·</span>
                              <span>Nº {item.minute_number}</span>
                            </>
                          ) : null}
                        </span>
                      </span>
                      <span className="tm-atas-row__side">
                        <StatusBadge
                          label={ataStatusLabel(item.status)}
                          variant={ataStatusVariant(item.status)}
                          classNames={tmAtaStatusBadgeClassNames}
                        />
                        <span className="tm-atas-row__signs" title={progress.label}>
                          <Signature size={14} aria-hidden />
                          <span>
                            {progress.done}/{progress.total || "—"}
                          </span>
                        </span>
                        <ChevronRight className="tm-atas-row__chevron" size={18} aria-hidden />
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </section>
      ) : null}

      <section className="tm-atas-shortcuts" aria-label="Atalhos">
        <button
          type="button"
          className="tm-atas-shortcut"
          onClick={() => onNavigate(`${TRANSFORMOMETRO_ROUTES.atas}/new`)}
        >
          <PenLine size={18} aria-hidden />
          <span>
            <strong>Escrever nova ata</strong>
            <small>Rascunho com pauta, decisões e signatários</small>
          </span>
        </button>
        <button
          type="button"
          className="tm-atas-shortcut"
          onClick={() => onNavigate(TRANSFORMOMETRO_ROUTES.atasPending)}
        >
          <Signature size={18} aria-hidden />
          <span>
            <strong>Assinaturas pendentes</strong>
            <small>Atas que aguardam a sua assinatura</small>
          </span>
        </button>
      </section>
    </TransformometroShell>
  );
}
