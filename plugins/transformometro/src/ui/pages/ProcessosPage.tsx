import { useCallback, useEffect, useMemo, useState } from "react";
import { Plus } from "lucide-react";

import type { AppProps } from "../../App";
import type { DataTableColumn } from "../../components/DataTable";
import { PageHeader } from "../../components/PageHeader";
import { StatusAlerts } from "../../components/StatusAlerts";
import { TRANSFORMOMETRO_ROUTES } from "../../constants/routes";
import {
  createProcesso,
  fetchOptions,
  fetchProcessos,
  type OptionsData,
  type Processo,
} from "../../data/api/transformometroApi";

type Props = Pick<AppProps, "getAccessToken"> & {
  pathname?: string;
  onNavigate: (path: string) => void;
  onOpenProcesso: (id: string) => void;
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
  const [filialId, setFilialId] = useState("");
  const [setorId, setSetorId] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [searchQ, setSearchQ] = useState("");
  const [familiaFilter, setFamiliaFilter] = useState("");
  const [form, setForm] = useState({
    nome_processo: "",
    filial_id: "01",
    setor_id: "engenharia",
    status_processo: "ativo",
    familia_processo: "",
    agrupador_ferramenta: "",
  });

  const listParams = useMemo(() => {
    const params: Record<string, string> = {};
    if (filialId) params.filial_id = filialId;
    if (setorId) params.setor_id = setorId;
    if (statusFilter) params.status = statusFilter;
    if (searchQ.trim()) params.q = searchQ.trim();
    if (familiaFilter.trim()) params.familia_processo = familiaFilter.trim();
    return params;
  }, [familiaFilter, filialId, searchQ, setorId, statusFilter]);

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

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const created = await createProcesso(
        {
          ...form,
          familia_processo: form.familia_processo.trim() || undefined,
          agrupador_ferramenta: form.agrupador_ferramenta.trim() || undefined,
        },
        getAccessToken
      );
      setShowForm(false);
      await load();
      onOpenProcesso(created.processo_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao criar");
    }
  }

  const columns = useMemo<DataTableColumn<Processo>[]>(
    () => [
      { key: "codigo", header: "Código", render: (row) => row.codigo_processo },
      {
        key: "nome",
        header: "Processo",
        className: "ds-table__col--wide",
        render: (row) => row.nome_processo,
      },
      { key: "filial", header: "Filial", render: (row) => row.filial_id },
      { key: "setor", header: "Setor", render: (row) => row.setor_id },
      { key: "familia", header: "Família", render: (row) => row.familia_processo ?? "—" },
      { key: "status", header: "Status", render: (row) => row.status_processo },
    ],
    []
  );

  return (
    <div className="dashboard-transformometro dashboard-page">
      <PageHeader
        title="Processos"
        subtitle="Cadastro mestre das melhorias monitoradas no PostgreSQL"
        currentPath={pathname ?? TRANSFORMOMETRO_ROUTES.processos}
        onNavigate={onNavigate}
        onRefresh={() => void load()}
        refreshing={refreshing}
        actions={
          <button
            type="button"
            className="ds-primary-btn"
            onClick={() => setShowForm((v) => !v)}
          >
            <Plus size={16} />
            {showForm ? "Cancelar" : "Novo processo"}
          </button>
        }
      />

      <section className="ds-filters-row ds-filters-row--extended">
        <div className="ds-filter-box ds-filter-box--wide">
          <label htmlFor="tm-proc-q">Buscar</label>
          <input
            id="tm-proc-q"
            type="search"
            placeholder="Nome ou código…"
            value={searchQ}
            onChange={(e) => setSearchQ(e.target.value)}
          />
        </div>
        <div className="ds-filter-box">
          <label htmlFor="tm-proc-filial">Filial</label>
          <select
            id="tm-proc-filial"
            value={filialId}
            onChange={(e) => setFilialId(e.target.value)}
          >
            <option value="">Todas</option>
            {(options?.filiais ?? []).map((f) => (
              <option key={f.id} value={f.id}>
                {f.id} — {f.label}
              </option>
            ))}
          </select>
        </div>
        <div className="ds-filter-box">
          <label htmlFor="tm-proc-setor">Setor</label>
          <select
            id="tm-proc-setor"
            value={setorId}
            onChange={(e) => setSetorId(e.target.value)}
          >
            <option value="">Todos</option>
            {(options?.setores ?? []).map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
        <div className="ds-filter-box">
          <label htmlFor="tm-proc-status">Status</label>
          <select
            id="tm-proc-status"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">Todos</option>
            {(options?.status_processo ?? []).map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
        <div className="ds-filter-box">
          <label htmlFor="tm-proc-familia">Família</label>
          <input
            id="tm-proc-familia"
            type="search"
            placeholder="ex.: ia"
            value={familiaFilter}
            onChange={(e) => setFamiliaFilter(e.target.value)}
          />
        </div>
      </section>

      <StatusAlerts
        error={error}
        loading={loading}
        hasData={items.length > 0}
        onRetry={() => void load()}
      />

      {showForm && options ? (
        <section className="ds-card ds-cadastro-form">
          <h2 className="ds-section-title">Novo processo</h2>
          <form onSubmit={handleCreate}>
            <div className="ds-filters-row">
              <div className="ds-filter-box ds-filter-box--wide">
                <label htmlFor="tm-nome">Nome do processo</label>
                <input
                  id="tm-nome"
                  required
                  value={form.nome_processo}
                  onChange={(e) => setForm({ ...form, nome_processo: e.target.value })}
                />
              </div>
              <div className="ds-filter-box">
                <label htmlFor="tm-form-filial">Filial</label>
                <select
                  id="tm-form-filial"
                  value={form.filial_id}
                  onChange={(e) => setForm({ ...form, filial_id: e.target.value })}
                >
                  {options.filiais.map((f) => (
                    <option key={f.id} value={f.id}>
                      {f.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="ds-filter-box">
                <label htmlFor="tm-form-setor">Setor</label>
                <select
                  id="tm-form-setor"
                  value={form.setor_id}
                  onChange={(e) => setForm({ ...form, setor_id: e.target.value })}
                >
                  {options.setores.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>
              <div className="ds-filter-box">
                <label htmlFor="tm-form-status">Status</label>
                <select
                  id="tm-form-status"
                  value={form.status_processo}
                  onChange={(e) => setForm({ ...form, status_processo: e.target.value })}
                >
                  {options.status_processo.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>
              <div className="ds-filter-box">
                <label htmlFor="tm-form-familia">Família (rateio)</label>
                <input
                  id="tm-form-familia"
                  placeholder="ex.: ia, automação"
                  value={form.familia_processo}
                  onChange={(e) => setForm({ ...form, familia_processo: e.target.value })}
                />
              </div>
              <div className="ds-filter-box">
                <label htmlFor="tm-form-ferramenta">Agrupador ferramenta</label>
                <input
                  id="tm-form-ferramenta"
                  placeholder="ex.: ChatGPT, Power Automate"
                  value={form.agrupador_ferramenta}
                  onChange={(e) => setForm({ ...form, agrupador_ferramenta: e.target.value })}
                />
              </div>
            </div>
            <div className="ds-cadastro-form__actions">
              <button type="submit" className="ds-primary-btn">
                Salvar processo
              </button>
            </div>
          </form>
        </section>
      ) : null}

      <section className="ds-card ds-table-section ds-table-section--interactive">
        <div className="ds-table-section__header">
          <h2 className="ds-section-title">Lista de processos</h2>
          <span className="ds-table-section__meta">{items.length} registro(s)</span>
        </div>
        <p className="ds-hint">Clique em uma linha para abrir revisões, medições e investimentos.</p>
        <div className="ds-table-wrap">
          <table className="ds-table ds-table--clickable">
            <thead>
              <tr>
                {columns.map((col) => (
                  <th key={col.key} className={col.className}>
                    {col.header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading && items.length === 0 ? (
                <tr>
                  <td colSpan={columns.length} className="ds-table__empty">
                    Carregando…
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={columns.length} className="ds-table__empty">
                    Nenhum processo. Use Novo processo para cadastrar.
                  </td>
                </tr>
              ) : (
                items.map((row) => (
                  <tr
                    key={row.processo_id}
                    className="ds-table__row--clickable"
                    onClick={() => onOpenProcesso(row.processo_id)}
                  >
                    {columns.map((col) => (
                      <td key={col.key} className={col.className}>
                        {col.render(row)}
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
