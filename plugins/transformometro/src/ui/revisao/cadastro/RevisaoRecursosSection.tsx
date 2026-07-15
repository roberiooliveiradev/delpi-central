import { useMemo, useState } from "react";
import type { AppProps } from "../../../App";
import {
  createRecurso,
  createVinculo,
  deleteVinculo,
  updateVinculo,
  type OptionsData,
  type RecursoCompartilhado,
  type VinculoRecurso,
} from "../../../data/api/transformometroApi";
import { optionalDateField, toDateInputValue } from "../../../utils/dateInputs";
import { labelCriterioRateio, labelSimNao } from "../../../utils/catalogLabels";
import { formatCurrency } from "../../../utils/format";
import { RecursoCatalogFormFields } from "../../recursos/RecursoCatalogFormFields";
import {
  emptyRecursoForm,
  payloadFromRecursoForm,
} from "../../recursos/recursoCatalogForm";
import { Pagination } from "../../../components/Pagination";
import { FieldLabel, HelpTooltip, NativeCheckboxControl, NativeTextControl } from "@delpi/plugin-ui/index";
import { TableHeader } from "../../../components/TableHeader";
import { SelectField } from "../../../components/ui/SelectField";
import { mapSelectOptionsFromItems } from "../../../components/ui/selectTypes";
import { TM_HELP_TOOLTIPS } from "../../../content/helpTooltips";
import { useClientPagination } from "../../../hooks/useClientPagination";
import { CadastroSection } from "./CadastroSection";
import { RecursoPreviewCard } from "./RecursoPreviewCard";
import { DS_GHOST_BTN } from "../../../components/ghostChrome";
import { DS_FILTERS_ROW, DS_FILTER_BOX_PLAIN, DS_FILTER_BOX_WIDE, DS_FILTER_BOX_WIDE_MOD } from "../../../components/filterChrome";

const CADASTRO_TABLE_PAGE_SIZE = 10;
const C = TM_HELP_TOOLTIPS.columns;
const R = TM_HELP_TOOLTIPS.recursos;

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
  readOnly?: boolean;
  embeddedInCard?: boolean;
  onError: (message: string | null) => void;
  onReload: () => Promise<void>;
};

export function RevisaoRecursosSection({
  revisaoId,
  options,
  recursos,
  vinculos,
  readOnly = false,
  embeddedInCard = false,
  getAccessToken,
  onError,
  onReload,
}: Props) {
  const [showRecursoForm, setShowRecursoForm] = useState(false);
  const [recursoForm, setRecursoForm] = useState(emptyRecursoForm);
  const [vinculoForm, setVinculoForm] = useState(emptyVinculoForm);
  const [editingVinculoId, setEditingVinculoId] = useState<string | null>(null);
  const [editVinculoForm, setEditVinculoForm] = useState(emptyVinculoForm);

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
  const { slice, page, setPage, total } = useClientPagination(vinculos, CADASTRO_TABLE_PAGE_SIZE);

  async function handleCreateRecurso(e: React.FormEvent) {
    e.preventDefault();
    onError(null);
    try {
      const created = await createRecurso(payloadFromRecursoForm(recursoForm), getAccessToken);
      setShowRecursoForm(false);
      setRecursoForm(emptyRecursoForm());
      setVinculoForm({ ...emptyVinculoForm(), recurso_compartilhado_id: created.recurso_compartilhado_id });
      await onReload();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao criar recurso");
    }
  }

  function startEditVinculo(v: VinculoRecurso) {
    const index = vinculos.findIndex((item) => item.vinculo_id === v.vinculo_id);
    if (index >= 0) {
      setPage(Math.floor(index / CADASTRO_TABLE_PAGE_SIZE) + 1);
    }
    setEditingVinculoId(v.vinculo_id);
    setEditVinculoForm({
      recurso_compartilhado_id: v.recurso_compartilhado_id,
      data_inicio_uso: toDateInputValue(v.data_inicio_uso),
      data_fim_uso: toDateInputValue(v.data_fim_uso),
      ativo: Boolean(v.ativo),
      peso_rateio: v.peso_rateio != null ? String(v.peso_rateio) : "",
      observacoes: v.observacoes ?? "",
    });
  }

  async function handleSaveEditVinculo(e: React.FormEvent) {
    e.preventDefault();
    if (!editingVinculoId) return;
    onError(null);
    try {
      const peso = editVinculoForm.peso_rateio.trim()
        ? Number.parseFloat(editVinculoForm.peso_rateio)
        : undefined;
      await updateVinculo(
        editingVinculoId,
        {
          ativo: editVinculoForm.ativo,
          data_inicio_uso: optionalDateField(editVinculoForm.data_inicio_uso),
          data_fim_uso: optionalDateField(editVinculoForm.data_fim_uso),
          peso_rateio: peso,
          observacoes: editVinculoForm.observacoes.trim() || undefined,
        },
        getAccessToken
      );
      setEditingVinculoId(null);
      setEditVinculoForm(emptyVinculoForm());
      await onReload();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao atualizar vínculo");
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

  const body = (
    <>
      {vinculos.length > 0 ? (
        <>
          <div className="ds-table-wrap ds-cadastro-section__table">
          <table className="ds-table ds-table--compact">
            <thead>
              <tr>
                <th><TableHeader label="Recurso" hint={C.nome} /></th>
                <th><TableHeader label="Custo/mês" hint={C.custoMesVigente} /></th>
                <th><TableHeader label="Rateio" hint={C.rateio} /></th>
                <th><TableHeader label="Uso na revisão" hint={C.usoRevisao} /></th>
                <th><TableHeader label="Peso" hint={C.peso} /></th>
                <th><TableHeader label="Ativo" hint={C.ativoVinculo} /></th>
                {!readOnly ? (
                  <th className="ds-table__actions-col">
                    <TableHeader label="Ações" hint={C.acoes} />
                  </th>
                ) : null}
              </tr>
            </thead>
            <tbody>
              {slice.map((v) =>
                !readOnly && editingVinculoId === v.vinculo_id ? (
                  <tr key={v.vinculo_id} className="ds-table__row--editing">
                    <td colSpan={7}>
                      <form className="ds-cadastro-subsection" onSubmit={handleSaveEditVinculo}>
                        <h4 className="ds-cadastro-subsection__title">
                          Editar vínculo — {v.codigo_recurso}
                        </h4>
                        <div className={DS_FILTERS_ROW}>
                          <label className={DS_FILTER_BOX_PLAIN}>
                            <FieldLabel className="tm-field__label" label="Início do uso" hint={R.vinculoInicio} />
                            <NativeTextControl
                              type="date"
                              value={editVinculoForm.data_inicio_uso}
                              onChange={(data_inicio_uso) =>
                                setEditVinculoForm({
                                  ...editVinculoForm,
                                  data_inicio_uso,
                                })
                              }
                            />
                          </label>
                          <label className={DS_FILTER_BOX_PLAIN}>
                            <FieldLabel className="tm-field__label" label="Fim do uso" hint={R.vinculoFim} />
                            <NativeTextControl
                              type="date"
                              value={editVinculoForm.data_fim_uso}
                              onChange={(data_fim_uso) =>
                                setEditVinculoForm({
                                  ...editVinculoForm,
                                  data_fim_uso,
                                })
                              }
                            />
                          </label>
                          <label className={DS_FILTER_BOX_PLAIN}>
                            <FieldLabel className="tm-field__label" label="Peso" hint={R.peso} />
                            <NativeTextControl
                              type="number"
                              min={0}
                              step="any"
                              value={editVinculoForm.peso_rateio}
                              onChange={(peso_rateio) =>
                                setEditVinculoForm({
                                  ...editVinculoForm,
                                  peso_rateio,
                                })
                              }
                            />
                          </label>
                          <NativeCheckboxControl
                            className="ds-check-label"
                            checked={editVinculoForm.ativo}
                            onChange={(ativo) => setEditVinculoForm({ ...editVinculoForm, ativo })}
                            label={<span className="tm-field__label">
                              Ativo
                              <HelpTooltip content={R.vinculoAtivo} ariaLabel="Ajuda: Ativo" />
                            </span>}
                          />
                        </div>
                        <label className={DS_FILTER_BOX_WIDE}>
                          <FieldLabel className="tm-field__label" label="Observações" hint={R.vinculoObservacoes} />
                          <NativeTextControl
                            value={editVinculoForm.observacoes}
                            onChange={(observacoes) =>
                              setEditVinculoForm({
                                ...editVinculoForm,
                                observacoes,
                              })
                            }
                          />
                        </label>
                        <div className="ds-cadastro-form__actions">
                          <button type="submit" className="ds-primary-btn">
                            Salvar vínculo
                          </button>
                          <button
                            type="button"
                            className={DS_GHOST_BTN}
                            onClick={() => {
                              setEditingVinculoId(null);
                              setEditVinculoForm(emptyVinculoForm());
                            }}
                          >
                            Cancelar
                          </button>
                        </div>
                      </form>
                    </td>
                  </tr>
                ) : (
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
                    {!readOnly ? (
                      <td className="ds-table__actions-col">
                        <button
                          type="button"
                          className={DS_GHOST_BTN}
                          onClick={() => startEditVinculo(v)}
                        >
                          Editar
                        </button>
                        <button
                          type="button"
                          className={DS_GHOST_BTN}
                          onClick={() =>
                            void deleteVinculo(v.vinculo_id, getAccessToken).then(() => onReload())
                          }
                        >
                          Desvincular
                        </button>
                      </td>
                    ) : null}
                  </tr>
                )
              )}
            </tbody>
          </table>
        </div>
        <Pagination
          page={page}
          pageSize={CADASTRO_TABLE_PAGE_SIZE}
          total={total}
          onPageChange={setPage}
          hideWhenSinglePage
        />
        </>
      ) : (
        <p className="ds-state-box">Nenhum recurso vinculado. O rateio só considera recursos com vínculo ativo.</p>
      )}

      {!readOnly ? (
        <>
      <form className="ds-cadastro-subsection" onSubmit={handleAddVinculo}>
        <h4 className="ds-cadastro-subsection__title">Vincular recurso à revisão</h4>
        <div className={DS_FILTERS_ROW}>
          <SelectField
            className={DS_FILTER_BOX_WIDE_MOD}
            label="Recurso do catálogo"
            hint={R.catalogoVinculo}
            required
            searchable
            value={vinculoForm.recurso_compartilhado_id}
            onChange={(recursoId) =>
              setVinculoForm({ ...vinculoForm, recurso_compartilhado_id: recursoId })
            }
            options={mapSelectOptionsFromItems(
              recursosDisponiveis,
              (r) => r.recurso_compartilhado_id,
              (r) =>
                `${r.codigo_recurso} — ${r.nome_recurso} (${formatCurrency(r.valor_total_recorrente)}/mês)`
            )}
          />
          <label className={DS_FILTER_BOX_PLAIN}>
            <FieldLabel className="tm-field__label" label="Início do uso" hint={R.vinculoInicio} />
            <NativeTextControl
              type="date"
              value={vinculoForm.data_inicio_uso}
              onChange={(data_inicio_uso) =>
                setVinculoForm({ ...vinculoForm, data_inicio_uso })
              }
            />
          </label>
          <label className={DS_FILTER_BOX_PLAIN}>
            <FieldLabel className="tm-field__label" label="Fim do uso" hint={R.vinculoFim} />
            <NativeTextControl
              type="date"
              value={vinculoForm.data_fim_uso}
            onChange={(data_fim_uso) => setVinculoForm({ ...vinculoForm, data_fim_uso })}
            />
          </label>
          <label className={DS_FILTER_BOX_PLAIN}>
            <FieldLabel className="tm-field__label" label="Peso do rateio" hint={R.peso} />
            <NativeTextControl
              type="number"
              min={0}
              step="any"
              placeholder={exigePeso ? "Usado no critério por_peso" : "Só se critério = por_peso"}
              value={vinculoForm.peso_rateio}
              onChange={(peso_rateio) =>
                setVinculoForm({ ...vinculoForm, peso_rateio })
              }
            />
          </label>
          <NativeCheckboxControl
            className="ds-check-label"
            checked={vinculoForm.ativo}
            onChange={(ativo) => setVinculoForm({ ...vinculoForm, ativo })}
            label={<span className="tm-field__label">
              Vínculo ativo
              <HelpTooltip content={R.vinculoAtivo} ariaLabel="Ajuda: Vínculo ativo" />
            </span>}
          />
        </div>
        <label className={DS_FILTER_BOX_WIDE}>
          <FieldLabel className="tm-field__label" label="Observações do vínculo" hint={R.vinculoObservacoes} />
          <NativeTextControl
            placeholder="Ex.: uso apenas nesta automação"
            value={vinculoForm.observacoes}
          onChange={(observacoes) => setVinculoForm({ ...vinculoForm, observacoes })}
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
          className={DS_GHOST_BTN}
          onClick={() => setShowRecursoForm((v) => !v)}
        >
          {showRecursoForm ? "Cancelar novo recurso" : "+ Cadastrar recurso no catálogo"}
        </button>

        {showRecursoForm ? (
          <form className="ds-cadastro-subsection" onSubmit={handleCreateRecurso}>
            <h4 className="ds-cadastro-subsection__title">Novo recurso no catálogo</h4>
            <RecursoCatalogFormFields
              form={recursoForm}
              options={options}
              onChange={setRecursoForm}
              submitLabel="Salvar no catálogo e selecionar"
            />
          </form>
        ) : null}
      </div>
        </>
      ) : null}
    </>
  );

  if (embeddedInCard) return body;

  return (
    <CadastroSection
      embedded
      title="Recursos compartilhados"
      hint="Vincule ferramentas do catálogo (ChatGPT, licenças, etc.). O custo entra no rateio conforme o critério do recurso."
      badge={`${vinculos.length} vínculo(s)`}
    >
      {body}
    </CadastroSection>
  );
}
