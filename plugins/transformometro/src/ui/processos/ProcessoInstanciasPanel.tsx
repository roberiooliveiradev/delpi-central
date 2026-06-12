import { useMemo, useState } from "react";
import { Copy, Plus } from "lucide-react";

import type { DataTableColumn } from "../../components/DataTable";
import { DataTableSection } from "../../components/DataTableSection";
import type { OptionsData, ProcessoInstancia } from "../../data/api/transformometroApi";
import { filterSetoresByFilial, resolveSetorIdForFilial } from "../../utils/setores";

type Props = {
  instancias: ProcessoInstancia[];
  selectedInstanciaId: string | null;
  options: OptionsData;
  busy?: boolean;
  onSelect: (instanciaId: string) => void;
  onCreate: (payload: { filial_id: string; setor_id: string; rotulo_instancia?: string }) => Promise<void>;
  onDuplicate: (payload: {
    origemInstanciaId: string;
    filial_id: string;
    setor_id: string;
    rotulo_instancia?: string;
  }) => Promise<void>;
};

export function ProcessoInstanciasPanel({
  instancias,
  selectedInstanciaId,
  options,
  busy = false,
  onSelect,
  onCreate,
  onDuplicate,
}: Props) {
  const [showForm, setShowForm] = useState(false);
  const [duplicateSourceId, setDuplicateSourceId] = useState<string | null>(null);
  const [filialId, setFilialId] = useState(options.filiais[0]?.id ?? "01");
  const [setorId, setSetorId] = useState(
    resolveSetorIdForFilial(options.setores, options.filiais[0]?.id ?? "01", "")
  );
  const [rotulo, setRotulo] = useState("");
  const [saving, setSaving] = useState(false);

  const setoresDisponiveis = useMemo(
    () => filterSetoresByFilial(options.setores, filialId),
    [filialId, options.setores]
  );

  const columns = useMemo<DataTableColumn<ProcessoInstancia>[]>(
    () => [
      {
        key: "filial",
        header: "Filial",
        render: (row) => `${row.codigo_filial ?? row.filial_id} — ${row.nome_filial ?? ""}`.trim(),
      },
      {
        key: "setor",
        header: "Setor",
        render: (row) => `${row.codigo_setor ?? row.setor_id} — ${row.nome_setor ?? ""}`.trim(),
      },
      {
        key: "rotulo",
        header: "Rótulo",
        render: (row) => row.rotulo_instancia ?? "—",
      },
      {
        key: "acoes",
        header: "",
        render: (row) => (
          <div className="ds-table__actions">
            <button
              type="button"
              className={`ds-ghost-btn${selectedInstanciaId === row.instancia_id ? " ds-ghost-btn--active" : ""}`}
              onClick={() => onSelect(row.instancia_id)}
            >
              {selectedInstanciaId === row.instancia_id ? "Selecionada" : "Selecionar"}
            </button>
            <button
              type="button"
              className="ds-ghost-btn"
              onClick={() => {
                setDuplicateSourceId(row.instancia_id);
                setFilialId(row.codigo_filial ?? row.filial_id ?? "01");
                setSetorId(row.codigo_setor ?? row.setor_id ?? "");
                setRotulo("");
                setShowForm(true);
              }}
            >
              <Copy size={14} />
              Replicar
            </button>
          </div>
        ),
      },
    ],
    [onSelect, selectedInstanciaId]
  );

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      if (duplicateSourceId) {
        await onDuplicate({
          origemInstanciaId: duplicateSourceId,
          filial_id: filialId,
          setor_id: setorId,
          rotulo_instancia: rotulo.trim() || undefined,
        });
      } else {
        await onCreate({
          filial_id: filialId,
          setor_id: setorId,
          rotulo_instancia: rotulo.trim() || undefined,
        });
      }
      setShowForm(false);
      setDuplicateSourceId(null);
      setRotulo("");
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <section className="ds-card">
        <div className="ds-table-section__header">
          <div>
            <h2 className="ds-section-title">Instâncias operacionais</h2>
            <p className="ds-hint">Cada par filial × setor possui timeline própria de revisões.</p>
          </div>
          <button
            type="button"
            className="ds-primary-btn"
            disabled={busy}
            onClick={() => {
              setDuplicateSourceId(null);
              setShowForm(true);
            }}
          >
            <Plus size={16} />
            Nova instância
          </button>
        </div>
        <DataTableSection
          title=""
          columns={columns}
          rows={instancias}
          rowKey={(row) => row.instancia_id}
          hideSearch
          emptyMessage="Nenhuma instância cadastrada."
        />
      </section>

      {showForm ? (
        <section className="ds-card ds-cadastro-form">
          <h2 className="ds-section-title">
            {duplicateSourceId ? "Replicar instância" : "Nova instância operacional"}
          </h2>
          <form onSubmit={handleSubmit}>
            <div className="ds-filters-row">
              <div className="ds-filter-box">
                <label htmlFor="tm-inst-filial">Filial *</label>
                <select
                  id="tm-inst-filial"
                  value={filialId}
                  onChange={(e) => {
                    const next = e.target.value;
                    setFilialId(next);
                    setSetorId(resolveSetorIdForFilial(options.setores, next, setorId));
                  }}
                >
                  {options.filiais.map((filial) => (
                    <option key={filial.id} value={filial.id}>
                      {filial.id} — {filial.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="ds-filter-box">
                <label htmlFor="tm-inst-setor">Setor *</label>
                <select
                  id="tm-inst-setor"
                  value={setorId}
                  onChange={(e) => setSetorId(e.target.value)}
                  disabled={setoresDisponiveis.length === 0}
                >
                  {setoresDisponiveis.map((setor) => (
                    <option key={setor.id} value={setor.id}>
                      {setor.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="ds-filter-box ds-filter-box--wide">
                <label htmlFor="tm-inst-rotulo">Rótulo (opcional)</label>
                <input
                  id="tm-inst-rotulo"
                  value={rotulo}
                  onChange={(e) => setRotulo(e.target.value)}
                  placeholder="Ex.: Matriz — Engenharia"
                />
              </div>
            </div>
            <div className="ds-cadastro-form__actions">
              <button type="submit" className="ds-primary-btn" disabled={saving || !filialId || !setorId}>
                {saving ? "Salvando…" : duplicateSourceId ? "Replicar timeline" : "Criar instância"}
              </button>
              <button
                type="button"
                className="ds-ghost-btn"
                disabled={saving}
                onClick={() => {
                  setShowForm(false);
                  setDuplicateSourceId(null);
                }}
              >
                Cancelar
              </button>
            </div>
          </form>
        </section>
      ) : null}
    </>
  );
}
