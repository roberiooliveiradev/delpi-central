import { useMemo, useState } from "react";
import type { AppProps } from "../../../App";
import {
  createRecurso,
  createVinculo,
  deleteVinculo,
  type OptionsData,
  type RecursoCompartilhado,
  type VinculoRecurso,
} from "../../../data/api/transformometroApi";
import { optionalDateField, toDateInputValue } from "../../../utils/dateInputs";
import { labelCriterioRateio, labelSimNao } from "../../../utils/catalogLabels";
import { formatCurrency } from "../../../utils/format";
import { CadastroSection } from "./CadastroSection";
import { RecursoPreviewCard } from "./RecursoPreviewCard";

export const emptyRecursoForm = () => ({
  nome_recurso: "",
  categoria_recurso: "",
  fornecedor: "",
  tipo_custo: "assinatura",
  recorrencia: "mensal",
  valor_total_recorrente: 0,
  criterio_rateio: "igualitario",
  status_recurso: "ativo",
  centro_custo: "",
  data_inicio_vigencia: "",
  data_fim_vigencia: "",
  observacoes: "",
});

export const emptyVinculoForm = () => ({
  recurso_compartilhado_id: "",
  data_inicio_uso: "",
  data_fim_uso: "",
  ativo: true,
  peso_rateio: "",
  observacoes: "",
});

type Props = Pick<AppProps, "getAccessToken"> & {
  revisaoId: string;
  options: OptionsData;
  recursos: RecursoCompartilhado[];
  vinculos: VinculoRecurso[];
  onError: (message: string | null) => void;
  onReload: () => Promise<void>;
};

export function RevisaoRecursosSection({
  revisaoId,
  options,
  recursos,
  vinculos,
  getAccessToken,
  onError,
  onReload,
}: Props) {
  const [showRecursoForm, setShowRecursoForm] = useState(false);
  const [recursoForm, setRecursoForm] = useState(emptyRecursoForm);
  const [vinculoForm, setVinculoForm] = useState(emptyVinculoForm);

  const recursosDisponiveis = useMemo(
    () =>
      recursos.filter(
        (r) => !vinculos.some((v) => v.recurso_compartilhado_id === r.recurso_compartilhado_id)
      ),
    [recursos, vinculos]
  );

  const recursoSelecionado = useMemo(
    () => recursos.find((r) => r.recurso_compartilhado_id === vinculoForm.recurso_compartilhado_id),
    [recursos, vinculoForm.recurso_compartilhado_id]
  );

  const exigePeso = recursoSelecionado?.criterio_rateio === "por_peso";

  async function handleCreateRecurso(e: React.FormEvent) {
    e.preventDefault();
    onError(null);
    try {
      const created = await createRecurso(
        {
          nome_recurso: recursoForm.nome_recurso.trim(),
          tipo_custo: recursoForm.tipo_custo,
          recorrencia: recursoForm.recorrencia,
          valor_total_recorrente: recursoForm.valor_total_recorrente,
          criterio_rateio: recursoForm.criterio_rateio,
          status_recurso: recursoForm.status_recurso,
          categoria_recurso: recursoForm.categoria_recurso.trim() || undefined,
          fornecedor: recursoForm.fornecedor.trim() || undefined,
          centro_custo: recursoForm.centro_custo.trim() || undefined,
          observacoes: recursoForm.observacoes.trim() || undefined,
          data_inicio_vigencia: optionalDateField(recursoForm.data_inicio_vigencia),
          data_fim_vigencia: optionalDateField(recursoForm.data_fim_vigencia),
        },
        getAccessToken
      );
      setShowRecursoForm(false);
      setRecursoForm(emptyRecursoForm());
      setVinculoForm({ ...emptyVinculoForm(), recurso_compartilhado_id: created.recurso_compartilhado_id });
      await onReload();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao criar recurso");
    }
  }

  async function handleAddVinculo(e: React.FormEvent) {
    e.preventDefault();
    if (!vinculoForm.recurso_compartilhado_id) return;
    onError(null);
    try {
      const peso = vinculoForm.peso_rateio.trim()
        ? Number.parseFloat(vinculoForm.peso_rateio)
        : undefined;
      await createVinculo(
        {
          revisao_id: revisaoId,
          recurso_compartilhado_id: vinculoForm.recurso_compartilhado_id,
          ativo: vinculoForm.ativo,
          data_inicio_uso: optionalDateField(vinculoForm.data_inicio_uso),
          data_fim_uso: optionalDateField(vinculoForm.data_fim_uso),
          peso_rateio: peso,
          observacoes: vinculoForm.observacoes.trim() || undefined,
        },
        getAccessToken
      );
      setVinculoForm(emptyVinculoForm());
      await onReload();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao vincular recurso");
    }
  }

  return (
    <CadastroSection
      embedded
      title="Recursos compartilhados"
      hint="Vincule ferramentas do catálogo (ChatGPT, licenças, etc.). O custo entra no rateio conforme o critério do recurso."
      badge={`${vinculos.length} vínculo(s)`}
    >
      {vinculos.length > 0 ? (
        <div className="ds-table-wrap ds-cadastro-section__table">
          <table className="ds-table ds-table--compact">
            <thead>
              <tr>
                <th>Recurso</th>
                <th>Custo/mês</th>
                <th>Rateio</th>
                <th>Uso na revisão</th>
                <th>Peso</th>
                <th>Ativo</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {vinculos.map((v) => (
                <tr key={v.vinculo_id}>
                  <td>
                    <strong>{v.codigo_recurso}</strong>
                    <br />
                    <span className="ds-table__sub">{v.nome_recurso}</span>
                    {v.fornecedor ? (
                      <span className="ds-table__sub"> · {v.fornecedor}</span>
                    ) : null}
                  </td>
                  <td>{formatCurrency(v.valor_total_recorrente)}</td>
                  <td>{labelCriterioRateio(v.criterio_rateio)}</td>
                  <td>
                    {toDateInputValue(v.data_inicio_uso) || "…"} →{" "}
                    {toDateInputValue(v.data_fim_uso) || "…"}
                  </td>
                  <td>{v.peso_rateio ?? (v.criterio_rateio === "por_peso" ? "1" : "—")}</td>
                  <td>{labelSimNao(v.ativo)}</td>
                  <td>
                    <button
                      type="button"
                      className="ds-ghost-btn"
                      onClick={() =>
                        void deleteVinculo(v.vinculo_id, getAccessToken).then(() => onReload())
                      }
                    >
                      Desvincular
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="ds-state-box">Nenhum recurso vinculado. O rateio só considera recursos com vínculo ativo.</p>
      )}

      <form className="ds-cadastro-subsection" onSubmit={handleAddVinculo}>
        <h4 className="ds-cadastro-subsection__title">Vincular recurso à revisão</h4>
        <div className="ds-filters-row">
          <label className="ds-filter-box ds-filter-box--wide">
            Recurso do catálogo
            <select
              required
              value={vinculoForm.recurso_compartilhado_id}
              onChange={(e) =>
                setVinculoForm({ ...vinculoForm, recurso_compartilhado_id: e.target.value })
              }
            >
              <option value="">Selecione…</option>
              {recursosDisponiveis.map((r) => (
                <option key={r.recurso_compartilhado_id} value={r.recurso_compartilhado_id}>
                  {r.codigo_recurso} — {r.nome_recurso} ({formatCurrency(r.valor_total_recorrente)}/mês)
                </option>
              ))}
            </select>
          </label>
          <label className="ds-filter-box">
            Início do uso
            <input
              type="date"
              value={vinculoForm.data_inicio_uso}
              onChange={(e) =>
                setVinculoForm({ ...vinculoForm, data_inicio_uso: e.target.value })
              }
            />
          </label>
          <label className="ds-filter-box">
            Fim do uso
            <input
              type="date"
              value={vinculoForm.data_fim_uso}
              onChange={(e) => setVinculoForm({ ...vinculoForm, data_fim_uso: e.target.value })}
            />
          </label>
          <label className="ds-filter-box">
            Peso do rateio
            <input
              type="number"
              min={0}
              step="any"
              placeholder={exigePeso ? "Usado no critério por_peso" : "Só se critério = por_peso"}
              value={vinculoForm.peso_rateio}
              onChange={(e) =>
                setVinculoForm({ ...vinculoForm, peso_rateio: e.target.value })
              }
            />
          </label>
          <label className="ds-filter-box ds-filter-box--checkbox">
            <span>Vínculo ativo</span>
            <input
              type="checkbox"
              checked={vinculoForm.ativo}
              onChange={(e) => setVinculoForm({ ...vinculoForm, ativo: e.target.checked })}
            />
          </label>
        </div>
        <label className="ds-filter-box ds-filter-box--wide">
          Observações do vínculo
          <input
            placeholder="Ex.: uso apenas nesta automação"
            value={vinculoForm.observacoes}
            onChange={(e) => setVinculoForm({ ...vinculoForm, observacoes: e.target.value })}
          />
        </label>

        {recursoSelecionado ? <RecursoPreviewCard recurso={recursoSelecionado} /> : null}

        <div className="ds-cadastro-form__actions">
          <button type="submit" className="ds-primary-btn" disabled={!vinculoForm.recurso_compartilhado_id}>
            Vincular à revisão
          </button>
        </div>
      </form>

      <div className="ds-cadastro-subsection ds-cadastro-subsection--divider">
        <button
          type="button"
          className="ds-ghost-btn"
          onClick={() => setShowRecursoForm((v) => !v)}
        >
          {showRecursoForm ? "Cancelar novo recurso" : "+ Cadastrar recurso no catálogo"}
        </button>

        {showRecursoForm ? (
          <form className="ds-cadastro-subsection" onSubmit={handleCreateRecurso}>
            <h4 className="ds-cadastro-subsection__title">Novo recurso no catálogo</h4>
            <div className="ds-filters-row">
              <label className="ds-filter-box ds-filter-box--wide">
                Nome *
                <input
                  required
                  value={recursoForm.nome_recurso}
                  onChange={(e) =>
                    setRecursoForm({ ...recursoForm, nome_recurso: e.target.value })
                  }
                />
              </label>
              <label className="ds-filter-box">
                Categoria
                <select
                  value={recursoForm.categoria_recurso}
                  onChange={(e) =>
                    setRecursoForm({ ...recursoForm, categoria_recurso: e.target.value })
                  }
                >
                  <option value="">—</option>
                  {options.categorias.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </label>
              <label className="ds-filter-box">
                Fornecedor
                <input
                  value={recursoForm.fornecedor}
                  onChange={(e) =>
                    setRecursoForm({ ...recursoForm, fornecedor: e.target.value })
                  }
                />
              </label>
              <label className="ds-filter-box">
                Tipo de custo *
                <select
                  value={recursoForm.tipo_custo}
                  onChange={(e) => setRecursoForm({ ...recursoForm, tipo_custo: e.target.value })}
                >
                  {(options.tipo_custo ?? ["fixo", "variavel", "assinatura", "licenca"]).map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </label>
              <label className="ds-filter-box">
                Recorrência *
                <select
                  value={recursoForm.recorrencia}
                  onChange={(e) => setRecursoForm({ ...recursoForm, recorrencia: e.target.value })}
                >
                  {options.recorrencias.map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </select>
              </label>
              <label className="ds-filter-box">
                Valor mensal (R$) *
                <input
                  type="number"
                  min={0}
                  step="any"
                  required
                  value={recursoForm.valor_total_recorrente}
                  onChange={(e) =>
                    setRecursoForm({
                      ...recursoForm,
                      valor_total_recorrente: Number(e.target.value),
                    })
                  }
                />
              </label>
              <label className="ds-filter-box">
                Critério de rateio *
                <select
                  value={recursoForm.criterio_rateio}
                  onChange={(e) =>
                    setRecursoForm({ ...recursoForm, criterio_rateio: e.target.value })
                  }
                >
                  {options.criterio_rateio.map((c) => (
                    <option key={c} value={c}>
                      {labelCriterioRateio(c)}
                    </option>
                  ))}
                </select>
              </label>
              <label className="ds-filter-box">
                Status *
                <select
                  value={recursoForm.status_recurso}
                  onChange={(e) =>
                    setRecursoForm({ ...recursoForm, status_recurso: e.target.value })
                  }
                >
                  {options.status_recurso.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </label>
              <label className="ds-filter-box">
                Centro de custo
                <input
                  value={recursoForm.centro_custo}
                  onChange={(e) =>
                    setRecursoForm({ ...recursoForm, centro_custo: e.target.value })
                  }
                />
              </label>
              <label className="ds-filter-box">
                Início vigência (catálogo)
                <input
                  type="date"
                  value={recursoForm.data_inicio_vigencia}
                  onChange={(e) =>
                    setRecursoForm({ ...recursoForm, data_inicio_vigencia: e.target.value })
                  }
                />
              </label>
              <label className="ds-filter-box">
                Fim vigência (catálogo)
                <input
                  type="date"
                  value={recursoForm.data_fim_vigencia}
                  onChange={(e) =>
                    setRecursoForm({ ...recursoForm, data_fim_vigencia: e.target.value })
                  }
                />
              </label>
            </div>
            <label className="ds-filter-box ds-filter-box--wide">
              Observações do catálogo
              <input
                value={recursoForm.observacoes}
                onChange={(e) => setRecursoForm({ ...recursoForm, observacoes: e.target.value })}
              />
            </label>
            <button type="submit" className="ds-primary-btn">
              Salvar no catálogo e selecionar
            </button>
          </form>
        ) : null}
      </div>
    </CadastroSection>
  );
}
