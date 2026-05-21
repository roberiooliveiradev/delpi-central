import { useCallback, useEffect, useState } from "react";
import type { AppProps } from "../../App";
import { LoadingActivityCard } from "../../components/LoadingActivityCard";
import {
  activateRevisao,
  createInvestimento,
  createRecurso,
  createVinculo,
  deleteInvestimento,
  deleteVinculo,
  fetchInvestimentos,
  fetchMedicao,
  fetchRecursos,
  fetchVinculos,
  updateRevisao,
  upsertMedicao,
  type Investimento,
  type Medicao,
  type OptionsData,
  type RecursoCompartilhado,
  type Revisao,
  type VinculoRecurso,
} from "../../data/api/transformometroApi";
import {
  optionalDateField,
  todayDateInput,
  toDateInputValue,
  toMonthInputValue,
} from "../../utils/dateInputs";

const TIPOS_CUSTO = ["fixo", "variavel", "assinatura", "licenca"] as const;

const emptyMedicao = (revisaoId: string): Medicao => ({
  revisao_id: revisaoId,
  volume_mensal: 0,
  tempo_medio_execucao_min: 0,
  tempo_retrabalho_min: 0,
  percentual_retrabalho: 0,
  percentual_erro: 0,
  quantidade_erros_mes: 0,
  custo_hora_mao_obra: 0,
  custo_unitario_erro: 0,
  custo_unitario_retrabalho: 0,
  custo_outros_desperdicios: 0,
});

type Props = Pick<AppProps, "getAccessToken"> & {
  revisao: Revisao;
  options: OptionsData;
  onError: (message: string | null) => void;
  onRevisaoUpdated: () => void;
};

export function RevisaoCadastroPanel({
  revisao,
  options,
  getAccessToken,
  onError,
  onRevisaoUpdated,
}: Props) {
  const [medicao, setMedicao] = useState<Medicao>(() => emptyMedicao(revisao.revisao_id));
  const [investimentos, setInvestimentos] = useState<Investimento[]>([]);
  const [vinculos, setVinculos] = useState<VinculoRecurso[]>([]);
  const [recursos, setRecursos] = useState<RecursoCompartilhado[]>([]);
  const [loading, setLoading] = useState(true);

  const [invForm, setInvForm] = useState({
    tipo_investimento: "unico",
    descricao_item: "",
    quantidade: 1,
    valor_unitario: 0,
    recorrencia: "unico",
    categoria_investimento: "",
    data_investimento: todayDateInput(),
    meses_vigencia: "",
  });

  const [recursoForm, setRecursoForm] = useState({
    nome_recurso: "",
    tipo_custo: "assinatura",
    recorrencia: "mensal",
    valor_total_recorrente: 0,
    criterio_rateio: "igualitario",
    status_recurso: "ativo",
    data_inicio_vigencia: "",
    data_fim_vigencia: "",
  });
  const [showRecursoForm, setShowRecursoForm] = useState(false);
  const [vinculoRecursoId, setVinculoRecursoId] = useState("");
  const [vinculoDatas, setVinculoDatas] = useState({
    data_inicio_uso: "",
    data_fim_uso: "",
  });

  const [revisaoDatas, setRevisaoDatas] = useState({
    data_inicio_vigencia: toDateInputValue(revisao.data_inicio_vigencia),
    data_implantacao: toDateInputValue(revisao.data_implantacao),
    data_fim_vigencia: toDateInputValue(revisao.data_fim_vigencia),
  });

  useEffect(() => {
    setRevisaoDatas({
      data_inicio_vigencia: toDateInputValue(revisao.data_inicio_vigencia),
      data_implantacao: toDateInputValue(revisao.data_implantacao),
      data_fim_vigencia: toDateInputValue(revisao.data_fim_vigencia),
    });
  }, [revisao.revisao_id, revisao.data_inicio_vigencia, revisao.data_implantacao, revisao.data_fim_vigencia]);

  const load = useCallback(async () => {
    setLoading(true);
    onError(null);
    try {
      const [med, inv, vin, rec] = await Promise.all([
        fetchMedicao(revisao.revisao_id, getAccessToken),
        fetchInvestimentos(revisao.revisao_id, getAccessToken),
        fetchVinculos(revisao.revisao_id, getAccessToken),
        fetchRecursos(getAccessToken),
      ]);
      setMedicao(med ? { ...med, revisao_id: revisao.revisao_id } : emptyMedicao(revisao.revisao_id));
      setInvestimentos(inv.items);
      setVinculos(vin.items);
      setRecursos(rec.items);
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao carregar cadastro da revisão");
    } finally {
      setLoading(false);
    }
  }, [getAccessToken, onError, revisao.revisao_id]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleSaveRevisaoDatas(e: React.FormEvent) {
    e.preventDefault();
    onError(null);
    try {
      await updateRevisao(
        revisao.revisao_id,
        {
          processo_id: revisao.processo_id,
          versao_revisao: revisao.versao_revisao,
          cenario_tipo: revisao.cenario_tipo,
          revisao_ativa: revisao.revisao_ativa,
          data_inicio_vigencia: revisaoDatas.data_inicio_vigencia,
          data_implantacao: optionalDateField(revisaoDatas.data_implantacao),
          data_fim_vigencia: optionalDateField(revisaoDatas.data_fim_vigencia),
        },
        getAccessToken
      );
      onRevisaoUpdated();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao salvar vigência da revisão");
    }
  }

  async function handleSaveMedicao(e: React.FormEvent) {
    e.preventDefault();
    onError(null);
    try {
      await upsertMedicao(medicao, getAccessToken);
      await load();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao salvar medição");
    }
  }

  async function handleAddInvestimento(e: React.FormEvent) {
    e.preventDefault();
    onError(null);
    try {
      await createInvestimento(
        {
          revisao_id: revisao.revisao_id,
          tipo_investimento: invForm.tipo_investimento,
          descricao_item: invForm.descricao_item,
          quantidade: invForm.quantidade,
          valor_unitario: invForm.valor_unitario,
          recorrencia: invForm.recorrencia,
          categoria_investimento: invForm.categoria_investimento || undefined,
          data_investimento: optionalDateField(invForm.data_investimento),
          meses_vigencia: invForm.meses_vigencia
            ? Number.parseInt(invForm.meses_vigencia, 10)
            : undefined,
        },
        getAccessToken
      );
      setInvForm({
        tipo_investimento: "unico",
        descricao_item: "",
        quantidade: 1,
        valor_unitario: 0,
        recorrencia: "unico",
        categoria_investimento: "",
        data_investimento: todayDateInput(),
        meses_vigencia: "",
      });
      await load();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao criar investimento");
    }
  }

  async function handleCreateRecurso(e: React.FormEvent) {
    e.preventDefault();
    onError(null);
    try {
      const created = await createRecurso(
        {
          ...recursoForm,
          data_inicio_vigencia: optionalDateField(recursoForm.data_inicio_vigencia),
          data_fim_vigencia: optionalDateField(recursoForm.data_fim_vigencia),
        },
        getAccessToken
      );
      setShowRecursoForm(false);
      setVinculoRecursoId(created.recurso_compartilhado_id);
      await load();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao criar recurso");
    }
  }

  async function handleAddVinculo(e: React.FormEvent) {
    e.preventDefault();
    if (!vinculoRecursoId) return;
    onError(null);
    try {
      await createVinculo(
        {
          revisao_id: revisao.revisao_id,
          recurso_compartilhado_id: vinculoRecursoId,
          data_inicio_uso: optionalDateField(vinculoDatas.data_inicio_uso),
          data_fim_uso: optionalDateField(vinculoDatas.data_fim_uso),
        },
        getAccessToken
      );
      setVinculoRecursoId("");
      setVinculoDatas({ data_inicio_uso: "", data_fim_uso: "" });
      await load();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao vincular recurso");
    }
  }

  async function handleActivate() {
    onError(null);
    try {
      await activateRevisao(revisao.revisao_id, getAccessToken);
      onRevisaoUpdated();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao ativar revisão");
    }
  }

  if (loading) {
    return (
      <LoadingActivityCard
        title="Carregando cadastro da revisão"
        description="Medição, investimentos e recursos compartilhados."
        variant="compact"
      />
    );
  }

  const recursosDisponiveis = recursos.filter(
    (r) => !vinculos.some((v) => v.recurso_compartilhado_id === r.recurso_compartilhado_id)
  );

  return (
    <div className="ds-cadastro-panel">
      <div className="ds-cadastro-panel__toolbar">
        <span>
          {revisao.versao_revisao} · {revisao.cenario_tipo}
        </span>
        {!revisao.revisao_ativa ? (
          <button type="button" className="ds-ghost-btn" onClick={() => void handleActivate()}>
            Definir como ativa
          </button>
        ) : null}
      </div>

      <form className="ds-cadastro-panel__block" onSubmit={handleSaveRevisaoDatas}>
        <h3 className="ds-section-title">Vigência da revisão</h3>
        <p className="ds-hint">
          Define o período em que a revisão entra no cálculo do dashboard. Deixe fim vazio para
          vigência aberta.
        </p>
        <div className="ds-filters-row">
          <label>
            Início vigência
            <input
              type="date"
              required
              value={revisaoDatas.data_inicio_vigencia}
              onChange={(e) =>
                setRevisaoDatas({ ...revisaoDatas, data_inicio_vigencia: e.target.value })
              }
            />
          </label>
          <label>
            Implantação
            <input
              type="date"
              value={revisaoDatas.data_implantacao}
              onChange={(e) =>
                setRevisaoDatas({ ...revisaoDatas, data_implantacao: e.target.value })
              }
            />
          </label>
          <label>
            Fim vigência
            <input
              type="date"
              value={revisaoDatas.data_fim_vigencia}
              onChange={(e) =>
                setRevisaoDatas({ ...revisaoDatas, data_fim_vigencia: e.target.value })
              }
            />
          </label>
        </div>
        <button type="submit" className="ds-primary-btn">
          Salvar vigência
        </button>
      </form>

      <form className="ds-cadastro-panel__block" onSubmit={handleSaveMedicao}>
        <h3 className="ds-section-title">Medição operacional</h3>
        <div className="ds-filters-row">
          <label>
            Volume mensal
            <input
              type="number"
              min={0}
              step="any"
              value={medicao.volume_mensal}
              onChange={(e) =>
                setMedicao({ ...medicao, volume_mensal: Number(e.target.value) })
              }
            />
          </label>
          <label>
            Tempo médio (min)
            <input
              type="number"
              min={0}
              step="any"
              value={medicao.tempo_medio_execucao_min}
              onChange={(e) =>
                setMedicao({ ...medicao, tempo_medio_execucao_min: Number(e.target.value) })
              }
            />
          </label>
          <label>
            Custo hora MO (R$)
            <input
              type="number"
              min={0}
              step="any"
              value={medicao.custo_hora_mao_obra}
              onChange={(e) =>
                setMedicao({ ...medicao, custo_hora_mao_obra: Number(e.target.value) })
              }
            />
          </label>
          <label>
            % retrabalho
            <input
              type="number"
              min={0}
              step="any"
              value={medicao.percentual_retrabalho}
              onChange={(e) =>
                setMedicao({ ...medicao, percentual_retrabalho: Number(e.target.value) })
              }
            />
          </label>
          <label>
            % erro
            <input
              type="number"
              min={0}
              step="any"
              value={medicao.percentual_erro}
              onChange={(e) =>
                setMedicao({ ...medicao, percentual_erro: Number(e.target.value) })
              }
            />
          </label>
          <label>
            Outros desperdícios (R$/mês)
            <input
              type="number"
              min={0}
              step="any"
              value={medicao.custo_outros_desperdicios}
              onChange={(e) =>
                setMedicao({ ...medicao, custo_outros_desperdicios: Number(e.target.value) })
              }
            />
          </label>
          <label>
            Mês de referência (metadado)
            <input
              type="month"
              value={toMonthInputValue(medicao.base_referencia_mes)}
              onChange={(e) =>
                setMedicao({
                  ...medicao,
                  base_referencia_mes: e.target.value || undefined,
                })
              }
            />
          </label>
        </div>
        <button type="submit" className="ds-primary-btn">
          Salvar medição
        </button>
      </form>

      <section className="ds-cadastro-panel__block">
        <h3 className="ds-section-title">Investimentos ({investimentos.length})</h3>
        {investimentos.length > 0 ? (
          <div className="ds-table-wrap">
          <table className="ds-table">
            <thead>
              <tr>
                <th>Tipo</th>
                <th>Descrição</th>
                <th>Qtd</th>
                <th>Unit.</th>
                <th>Total</th>
                <th>Data</th>
                <th>Meses vig.</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {investimentos.map((inv) => (
                <tr key={inv.investimento_id}>
                  <td>{inv.tipo_investimento}</td>
                  <td>{inv.descricao_item}</td>
                  <td>{inv.quantidade}</td>
                  <td>{inv.valor_unitario.toLocaleString("pt-BR")}</td>
                  <td>{inv.valor_total.toLocaleString("pt-BR")}</td>
                  <td>{toDateInputValue(inv.data_investimento) || "—"}</td>
                  <td>{inv.meses_vigencia ?? "—"}</td>
                  <td>
                    <button
                      type="button"
                      className="ds-ghost-btn"
                      onClick={() =>
                        void deleteInvestimento(inv.investimento_id, getAccessToken).then(load)
                      }
                    >
                      Remover
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        ) : (
          <p className="ds-hint">Nenhum investimento nesta revisão.</p>
        )}

        <form className="ds-cadastro-panel__block" onSubmit={handleAddInvestimento}>
          <div className="ds-filters-row">
            <label>
              Tipo
              <select
                value={invForm.tipo_investimento}
                onChange={(e) => setInvForm({ ...invForm, tipo_investimento: e.target.value })}
              >
                {options.tipo_investimento.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Descrição
              <input
                required
                value={invForm.descricao_item}
                onChange={(e) => setInvForm({ ...invForm, descricao_item: e.target.value })}
              />
            </label>
            <label>
              Qtd
              <input
                type="number"
                min={0}
                step="any"
                value={invForm.quantidade}
                onChange={(e) => setInvForm({ ...invForm, quantidade: Number(e.target.value) })}
              />
            </label>
            <label>
              Valor unit. (R$)
              <input
                type="number"
                min={0}
                step="any"
                value={invForm.valor_unitario}
                onChange={(e) =>
                  setInvForm({ ...invForm, valor_unitario: Number(e.target.value) })
                }
              />
            </label>
            <label>
              Recorrência
              <select
                value={invForm.recorrencia}
                onChange={(e) => setInvForm({ ...invForm, recorrencia: e.target.value })}
              >
                {options.recorrencias.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Data do investimento
              <input
                type="date"
                value={invForm.data_investimento}
                onChange={(e) =>
                  setInvForm({ ...invForm, data_investimento: e.target.value })
                }
              />
            </label>
            <label>
              Meses de vigência
              <input
                type="number"
                min={1}
                step={1}
                placeholder="Opcional"
                value={invForm.meses_vigencia}
                onChange={(e) => setInvForm({ ...invForm, meses_vigencia: e.target.value })}
              />
            </label>
          </div>
          <button type="submit" className="ds-primary-btn">
            Adicionar investimento
          </button>
        </form>
      </section>

      <section className="ds-cadastro-panel__block">
        <h3 className="ds-section-title">Recursos compartilhados vinculados ({vinculos.length})</h3>
        {vinculos.length > 0 ? (
          <ul className="ds-cadastro-list">
            {vinculos.map((v) => (
              <li key={v.vinculo_id}>
                <span>
                  {v.codigo_recurso} — {v.nome_recurso}
                  {v.data_inicio_uso || v.data_fim_uso
                    ? ` (${toDateInputValue(v.data_inicio_uso) || "…"} → ${toDateInputValue(v.data_fim_uso) || "…"})`
                    : ""}
                </span>
                <button
                  type="button"
                  className="ds-ghost-btn"
                  onClick={() => void deleteVinculo(v.vinculo_id, getAccessToken).then(load)}
                >
                  Desvincular
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p className="ds-hint">Nenhum recurso vinculado. Rateio igualitário só conta após o vínculo.</p>
        )}

        <form className="ds-filters-row" onSubmit={handleAddVinculo}>
          <label>
            Vincular recurso existente
            <select
              value={vinculoRecursoId}
              onChange={(e) => setVinculoRecursoId(e.target.value)}
            >
              <option value="">Selecione…</option>
              {recursosDisponiveis.map((r) => (
                <option key={r.recurso_compartilhado_id} value={r.recurso_compartilhado_id}>
                  {r.codigo_recurso} — {r.nome_recurso} (R$ {r.valor_total_recorrente}/mês)
                </option>
              ))}
            </select>
          </label>
          <label>
            Início uso
            <input
              type="date"
              value={vinculoDatas.data_inicio_uso}
              onChange={(e) =>
                setVinculoDatas({ ...vinculoDatas, data_inicio_uso: e.target.value })
              }
            />
          </label>
          <label>
            Fim uso
            <input
              type="date"
              value={vinculoDatas.data_fim_uso}
              onChange={(e) =>
                setVinculoDatas({ ...vinculoDatas, data_fim_uso: e.target.value })
              }
            />
          </label>
          <button type="submit" className="ds-primary-btn" disabled={!vinculoRecursoId}>
            Vincular
          </button>
        </form>

        <button
          type="button"
          className="ds-ghost-btn"
          onClick={() => setShowRecursoForm((v) => !v)}
        >
          {showRecursoForm ? "Cancelar novo recurso" : "+ Novo recurso no catálogo"}
        </button>

        {showRecursoForm ? (
          <form className="ds-cadastro-panel__block" onSubmit={handleCreateRecurso}>
            <div className="ds-filters-row">
              <label>
                Nome
                <input
                  required
                  value={recursoForm.nome_recurso}
                  onChange={(e) =>
                    setRecursoForm({ ...recursoForm, nome_recurso: e.target.value })
                  }
                />
              </label>
              <label>
                Tipo custo
                <select
                  value={recursoForm.tipo_custo}
                  onChange={(e) => setRecursoForm({ ...recursoForm, tipo_custo: e.target.value })}
                >
                  {TIPOS_CUSTO.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Valor mensal (R$)
                <input
                  type="number"
                  min={0}
                  step="any"
                  value={recursoForm.valor_total_recorrente}
                  onChange={(e) =>
                    setRecursoForm({
                      ...recursoForm,
                      valor_total_recorrente: Number(e.target.value),
                    })
                  }
                />
              </label>
              <label>
                Rateio
                <select
                  value={recursoForm.criterio_rateio}
                  onChange={(e) =>
                    setRecursoForm({ ...recursoForm, criterio_rateio: e.target.value })
                  }
                >
                  {options.criterio_rateio.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Início vigência (catálogo)
                <input
                  type="date"
                  value={recursoForm.data_inicio_vigencia}
                  onChange={(e) =>
                    setRecursoForm({ ...recursoForm, data_inicio_vigencia: e.target.value })
                  }
                />
              </label>
              <label>
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
            <button type="submit" className="ds-primary-btn">
              Criar recurso
            </button>
          </form>
        ) : null}
      </section>
    </div>
  );
}
