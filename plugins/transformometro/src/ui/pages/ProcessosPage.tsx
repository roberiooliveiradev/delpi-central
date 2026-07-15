import { useCallback, useEffect, useMemo, useState } from "react";
import { Plus } from "lucide-react";

import type { AppProps } from "../../App";
import type { DataTableColumn } from "../../components/DataTable";
import { PageHeader } from "../../components/PageHeader";
import { StatusAlerts } from "../../components/StatusAlerts";
import { TransformometroShell } from "../../components/TransformometroShell";
import { TRANSFORMOMETRO_ROUTES } from "../../constants/routes";
import {
  createProcesso,
  fetchOptions,
  fetchProcessos,
  type OptionsData,
  type Processo,
} from "../../data/api/transformometroApi";
import { FieldLabel, NativeTextControl } from "@delpi/plugin-ui/index";
import { SelectField } from "../../components/ui/SelectField";
import { mapSelectOptions } from "../../components/ui/selectTypes";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { useScrollToRef } from "../../hooks/useScrollToRef";
import { ProcessoFormProgress } from "../../components/processo/ProcessoFormProgress";
import { computeProcessoListCompletion } from "../../utils/processoCompletion";

const C = TM_HELP_TOOLTIPS.columns;
const P = TM_HELP_TOOLTIPS.processos;
import { ProcessoFormFields } from "../processos/ProcessoFormFields";
import { ProcessoEscopoFields } from "../processos/ProcessoEscopoFields";
import { ProcessoFolderBrowser } from "../processos/ProcessoFolderBrowser";
import {
  defaultProcessoEscopoForCreate,
  hasProcessoEscopo,
} from "../processos/processoEscopo";
import {
  emptyProcessoForm,
  masterPayloadFromProcessoForm,
  type ProcessoFormState,
} from "../processos/processoForm";
import { formatDateTime } from "../../utils/format";
import { renderTableStatus } from "../../utils/tablePresentation";
import { DS_GHOST_BTN } from "../../components/ghostChrome";
import { DS_FILTERS_ROW_EXTENDED, DS_FILTER_BOX_WIDE } from "../../components/filterChrome";

type Props = Pick<AppProps, "getAccessToken"> & {
  pathname?: string;
  onNavigate: (path: string) => void;
  onOpenProcesso: (id: string, options?: { setupInstancia?: boolean }) => void;
};

export function ProcessosPage({
  getAccessToken,
  pathname,
  onNavigate,
  onOpenProcesso,
}: Props) {
  const [items, setItems] = useState<Processo[]>([]);
  const [options, setOptions] = useState<OptionsData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<ProcessoFormState>(emptyProcessoForm);
  const { ref: formSectionRef, scrollToRef: scrollToForm } = useScrollToRef<HTMLElement>();
  const [statusFilter, setStatusFilter] = useState("");
  const [searchQ, setSearchQ] = useState("");

  const listParams = useMemo(() => {
    const params: Record<string, string> = {};
    if (statusFilter) params.status = statusFilter;
    if (searchQ.trim()) params.q = searchQ.trim();
    return params;
  }, [searchQ, statusFilter]);

  const load = useCallback(async () => {
    setRefreshing(true);
    setError(null);
    try {
      const [list, opts] = await Promise.all([
        fetchProcessos(getAccessToken, listParams),
        fetchOptions(getAccessToken),
      ]);
      setItems(list.items);
      setOptions(opts);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [getAccessToken, listParams]);

  useEffect(() => {
    void load();
  }, [load]);

  function startCreate() {
    setForm({
      ...emptyProcessoForm(),
      escopo: options ? defaultProcessoEscopoForCreate(options) : emptyProcessoForm().escopo,
    });
    setShowForm(true);
    scrollToForm();
  }

  function cancelForm() {
    setShowForm(false);
    setForm(emptyProcessoForm());
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!hasProcessoEscopo(form.escopo)) {
      setError("Selecione ao menos uma unidade e um departamento no escopo do processo.");
      return;
    }
    const payload = masterPayloadFromProcessoForm(form);
    try {
      const created = await createProcesso(payload, getAccessToken);
      cancelForm();
      await load();
      onOpenProcesso(created.processo_id, { setupInstancia: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar processo");
    }
  }

  const detailColumns = useMemo<DataTableColumn<Processo>[]>(
    () => [
      { key: "codigo", header: "Código", headerHint: P.codigo, render: (row) => row.codigo_processo, sortable: true },
      {
        key: "nome",
        header: "Processo",
        headerHint: P.nome,
        sortable: true,
        className: "ds-table__col--wide",
        render: (row) => row.nome_processo,
      },
      { key: "status", header: "Status", headerHint: C.status, className: "ds-table__col--status", render: (row) => renderTableStatus(row.status_processo), sortable: true },
      {
        key: "preenchimento",
        header: "Preenchimento",
        headerHint: P.preenchimentoLista,
        className: "ds-table__col--progress",
        sortable: true,
        render: (row) => (
          <ProcessoFormProgress
            compact
            completion={computeProcessoListCompletion(row)}
            title={`Preenchimento do cadastro — ${row.codigo_processo}`}
          />
        ),
      },
      {
        key: "atualizado",
        header: "Atualizado em",
        headerHint: P.atualizadoEm,
        sortable: true,
        render: (row) => formatDateTime(row.updated_at),
      },
    ],
    []
  );

  return (
    <TransformometroShell>
      <PageHeader
        title="Processos"
        subtitle="Cadastro mestre das melhorias monitoradas no PostgreSQL"
        currentPath={pathname ?? TRANSFORMOMETRO_ROUTES.processos}
        onNavigate={onNavigate}
        onRefresh={() => void load()}
        refreshing={refreshing}
        actions={
          <button type="button" className="ds-primary-btn" onClick={startCreate}>
            <Plus size={16} />
            Novo processo
          </button>
        }
      />

      <StatusAlerts
        error={error}
        loading={loading}
        hasData={items.length > 0}
        onRetry={() => void load()}
      />

      {showForm && options ? (
        <section ref={formSectionRef} className="ds-card ds-cadastro-form">
          <h2 className="ds-section-title">Novo processo</h2>
          <p className="ds-hint">
            Cadastre o mestre com unidades e departamentos de escopo. Melhorias e revisões são
            cadastradas na tela do processo, na seção Melhorias.
          </p>
          <form onSubmit={handleSubmit}>
            <ProcessoFormFields
              form={form}
              options={options}
              showInstanciaFields={false}
              onChange={setForm}
            />
            <div className="tm-inst-form tm-inst-form--spaced">
              <h3 className="ds-subsection-title">Unidades e departamentos do processo</h3>
              <p className="ds-hint">
                Escopo operacional do processo-mestre. Ao criar melhorias, você pode replicar esta
                amarração ou definir outra.
              </p>
              <ProcessoEscopoFields
                value={form.escopo}
                options={options}
                onChange={(escopo) => setForm({ ...form, escopo })}
                activeFilialCount={options.filiais.length}
              />
            </div>
            <div className="ds-cadastro-form__actions">
              <button type="submit" className="ds-primary-btn">
                Criar processo
              </button>
              <button type="button" className={DS_GHOST_BTN} onClick={cancelForm}>
                Cancelar
              </button>
            </div>
          </form>
        </section>
      ) : null}

      <ProcessoFolderBrowser
        title="Processos"
        hint="Filtros acima aplicam na API · clique na pasta para abrir o processo"
        items={items}
        loading={loading}
        refreshing={refreshing}
        emptyMessage="Nenhum processo. Use Novo processo para cadastrar."
        detailColumns={detailColumns}
        onOpen={(row) => onOpenProcesso(row.processo_id)}
        onNavigate={onNavigate}
        filters={
          <section className={DS_FILTERS_ROW_EXTENDED}>
            <div className={DS_FILTER_BOX_WIDE}>
              <FieldLabel className="tm-field__label" label="Buscar" hint={P.busca} />
              <NativeTextControl
                id="tm-proc-q"
                type="search"
                placeholder="Nome ou código…"
                value={searchQ}
                onChange={setSearchQ}
              />
            </div>
            <SelectField
              id="tm-proc-list-status"
              label="Status"
              hint={P.filtroStatus}
              value={statusFilter}
              onChange={setStatusFilter}
              allowEmpty
              emptyLabel="Todos"
              options={mapSelectOptions(options?.status_processo ?? [])}
            />
          </section>
        }
        footer={
          <p className="ds-hint">
            Clique na pasta para abrir revisões, medições e investimentos.
          </p>
        }
      />
    </TransformometroShell>
  );
}
