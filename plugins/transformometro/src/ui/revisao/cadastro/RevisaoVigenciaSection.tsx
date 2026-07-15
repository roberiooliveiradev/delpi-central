import type { OptionsData, Revisao } from "../../../data/api/transformometroApi";
import { FieldLabel, HelpTooltip, NativeCheckboxControl, NativeTextControl } from "@delpi/plugin-ui/index";
import { SelectField } from "../../../components/ui/SelectField";
import { cenarioLabel, cenarioSelectLabel } from "../../../content/cenarioLabels";
import { mapSelectOptions, mapSelectOptionsFromItems } from "../../../components/ui/selectTypes";
import { revisaoDisplayLabel } from "../../../utils/revisaoLabels";
import { TM_HELP_TOOLTIPS } from "../../../content/helpTooltips";
import { optionalDateField, toDateInputValue } from "../../../utils/dateInputs";
import { CadastroSection } from "./CadastroSection";
import { TmNativeTextAreaField } from "../../../components/ui/tmNativeFormFields";
import { DS_FILTERS_ROW, DS_FILTER_BOX_PLAIN, DS_FILTER_BOX_WIDE } from "../../../components/filterChrome";

const R = TM_HELP_TOOLTIPS.revisao;

export type RevisaoVigenciaForm = {
  versao_revisao: string;
  cenario_tipo: string;
  revisao_referencia_id: string;
  data_inicio_vigencia: string;
  data_implantacao: string;
  data_fim_vigencia: string;
  revisao_ativa: boolean;
  descricao_revisao: string;
  motivo_revisao: string;
  observacoes: string;
};

type Props = {
  revisaoVigencia: RevisaoVigenciaForm;
  options: OptionsData;
  revisoesReferencia?: Revisao[];
  revisaoId?: string;
  readOnly?: boolean;
  embeddedInCard?: boolean;
  hideSubmit?: boolean;
  onChange: (value: RevisaoVigenciaForm) => void;
  onSubmit: (e: React.FormEvent) => void;
};

function VigenciaReadContent({
  revisaoVigencia,
  revisoesReferencia,
}: {
  revisaoVigencia: RevisaoVigenciaForm;
  revisoesReferencia?: Revisao[];
}) {
  const referencia = revisoesReferencia?.find(
    (item) => item.revisao_id === revisaoVigencia.revisao_referencia_id
  );

  return (
    <>
      <dl className="ds-dl-grid">
        <div><dt>Versão</dt><dd>{revisaoVigencia.versao_revisao}</dd></div>
        <div><dt>Cenário</dt><dd>{cenarioLabel(revisaoVigencia.cenario_tipo)}</dd></div>
        {revisaoVigencia.cenario_tipo !== "baseline" ? (
          <div>
            <dt>Compara com</dt>
            <dd>{referencia ? revisaoDisplayLabel(referencia) : "Linha de base (automático)"}</dd>
          </div>
        ) : null}
        <div><dt>Início</dt><dd>{revisaoVigencia.data_inicio_vigencia || "—"}</dd></div>
        <div><dt>Implantação</dt><dd>{revisaoVigencia.data_implantacao || "—"}</dd></div>
        <div><dt>Fim</dt><dd>{revisaoVigencia.data_fim_vigencia || "—"}</dd></div>
        <div><dt>Ativa</dt><dd>{revisaoVigencia.revisao_ativa ? "sim" : "não"}</dd></div>
        {revisaoVigencia.descricao_revisao ? (
          <div><dt>Descrição</dt><dd>{revisaoVigencia.descricao_revisao}</dd></div>
        ) : null}
        {revisaoVigencia.motivo_revisao ? (
          <div><dt>Motivo</dt><dd>{revisaoVigencia.motivo_revisao}</dd></div>
        ) : null}
      </dl>
      {revisaoVigencia.observacoes ? (
        <p className="ds-hint"><strong>Observações:</strong> {revisaoVigencia.observacoes}</p>
      ) : null}
    </>
  );
}

export function RevisaoVigenciaSection({
  revisaoVigencia,
  options,
  revisoesReferencia = [],
  revisaoId,
  readOnly = false,
  embeddedInCard = false,
  hideSubmit = false,
  onChange,
  onSubmit,
}: Props) {
  const isBaseline = revisaoVigencia.cenario_tipo === "baseline";

  if (readOnly) {
    const content = (
      <VigenciaReadContent
        revisaoVigencia={revisaoVigencia}
        revisoesReferencia={revisoesReferencia}
      />
    );
    if (embeddedInCard) return content;
    return (
      <CadastroSection embedded title="Vigência e identificação">
        {content}
      </CadastroSection>
    );
  }

  const referenciaOptions = mapSelectOptionsFromItems(
    revisoesReferencia.filter((item) => item.revisao_id !== revisaoId),
    (item) => item.revisao_id,
    (item) => revisaoDisplayLabel(item)
  );

  const form = (
      <form onSubmit={onSubmit}>
        <div className={DS_FILTERS_ROW}>
          <label className={DS_FILTER_BOX_PLAIN}>
            <FieldLabel className="tm-field__label" label="Versão *" hint={R.versao} />
            <NativeTextControl
              required
              value={revisaoVigencia.versao_revisao}
              onChange={(versao_revisao) => onChange({ ...revisaoVigencia, versao_revisao })}
            />
          </label>
          <SelectField
            label="Cenário *"
            hint={R.cenario}
            required
            value={revisaoVigencia.cenario_tipo}
            onChange={(cenario) => {
              onChange({
                ...revisaoVigencia,
                cenario_tipo: cenario,
                revisao_referencia_id:
                  cenario === "baseline"
                    ? ""
                    : revisaoVigencia.revisao_referencia_id ||
                      referenciaOptions[0]?.value ||
                      "",
                revisao_ativa: cenario === "baseline" ? false : revisaoVigencia.revisao_ativa,
              });
            }}
            options={mapSelectOptions(options.cenario_tipo, cenarioSelectLabel)}
          />
          {!isBaseline ? (
            <SelectField
              label="Compara com *"
              hint={R.referenciaComparacao}
              required
              value={revisaoVigencia.revisao_referencia_id}
              onChange={(revisaoReferenciaId) =>
                onChange({ ...revisaoVigencia, revisao_referencia_id: revisaoReferenciaId })
              }
              options={referenciaOptions}
            />
          ) : null}
          <label className={DS_FILTER_BOX_PLAIN}>
            <FieldLabel className="tm-field__label" label="Início vigência *" hint={R.inicioVigencia} />
            <NativeTextControl
              type="date"
              required
              value={revisaoVigencia.data_inicio_vigencia}
              onChange={(data_inicio_vigencia) =>
                onChange({ ...revisaoVigencia, data_inicio_vigencia })
              }
            />
          </label>
          <label className={DS_FILTER_BOX_PLAIN}>
            <FieldLabel className="tm-field__label" label="Implantação" hint={R.implantacao} />
            <NativeTextControl
              type="date"
              value={revisaoVigencia.data_implantacao}
              onChange={(data_implantacao) =>
                onChange({ ...revisaoVigencia, data_implantacao })
              }
            />
          </label>
          <label className={DS_FILTER_BOX_PLAIN}>
            <FieldLabel className="tm-field__label" label="Fim vigência" hint={R.fimVigencia} />
            <NativeTextControl
              type="date"
              value={revisaoVigencia.data_fim_vigencia}
              onChange={(data_fim_vigencia) =>
                onChange({
                  ...revisaoVigencia,
                  data_fim_vigencia,
                  revisao_ativa: data_fim_vigencia || isBaseline ? false : revisaoVigencia.revisao_ativa,
                })
              }
            />
          </label>
          <NativeCheckboxControl
            className="ds-check-label"
            checked={revisaoVigencia.revisao_ativa}
            disabled={isBaseline || Boolean(revisaoVigencia.data_fim_vigencia)}
            onChange={(revisao_ativa) => onChange({ ...revisaoVigencia, revisao_ativa })}
            label={<span className="tm-field__label">
              Marcar como revisão ativa
              <HelpTooltip content={R.revisaoAtiva} ariaLabel="Ajuda: Marcar como revisão ativa" />
            </span>}
          />
        </div>
        <label className={DS_FILTER_BOX_WIDE}>
          <FieldLabel className="tm-field__label" label="Descrição da revisão" hint={R.descricao} />
          <NativeTextControl
            value={revisaoVigencia.descricao_revisao}
            onChange={(descricao_revisao) =>
              onChange({ ...revisaoVigencia, descricao_revisao })
            }
            placeholder="Ex.: Automação do fechamento mensal"
          />
        </label>
        <label className={DS_FILTER_BOX_WIDE}>
          <FieldLabel className="tm-field__label" label="Motivo da revisão" hint={R.motivo} />
          <NativeTextControl
            value={revisaoVigencia.motivo_revisao}
            onChange={(motivo_revisao) =>
              onChange({ ...revisaoVigencia, motivo_revisao })
            }
            placeholder="Ex.: Nova ferramenta / mudança de escopo"
          />
        </label>
        <TmNativeTextAreaField
          id="revisao-vigencia-observacoes"
          label="Observações"
          hint={R.observacoes}
          span
          rows={2}
          value={revisaoVigencia.observacoes}
          placeholder="Contexto adicional da revisão"
          onChange={(value) => onChange({ ...revisaoVigencia, observacoes: value })}
        />
        {hideSubmit ? null : (
          <button type="submit" className="ds-primary-btn">
            Salvar vigência e identificação
          </button>
        )}
      </form>
  );

  if (embeddedInCard) return form;

  return (
    <CadastroSection
      embedded
      title="Vigência e identificação"
      hint="Versão, cenário e período usados no dashboard. Para reativar uma revisão, remova o fim da vigência e marque como ativa."
    >
      {form}
    </CadastroSection>
  );
}

export function buildRevisaoVigenciaFromRevisao(revisao: Revisao): RevisaoVigenciaForm {
  return {
    versao_revisao: revisao.versao_revisao ?? "",
    cenario_tipo: revisao.cenario_tipo ?? "baseline",
    revisao_referencia_id: revisao.revisao_referencia_id ?? "",
    data_inicio_vigencia: toDateInputValue(revisao.data_inicio_vigencia),
    data_implantacao: toDateInputValue(revisao.data_implantacao),
    data_fim_vigencia: toDateInputValue(revisao.data_fim_vigencia),
    revisao_ativa: Boolean(revisao.revisao_ativa),
    descricao_revisao: revisao.descricao_revisao ?? "",
    motivo_revisao: revisao.motivo_revisao ?? "",
    observacoes: revisao.observacoes ?? "",
  };
}

export function revisaoPayloadFromVigenciaForm(form: RevisaoVigenciaForm) {
  return {
    versao_revisao: form.versao_revisao.trim(),
    cenario_tipo: form.cenario_tipo,
    revisao_referencia_id:
      form.cenario_tipo === "baseline" ? undefined : form.revisao_referencia_id || undefined,
    data_inicio_vigencia: form.data_inicio_vigencia,
    data_implantacao: optionalDateField(form.data_implantacao),
    data_fim_vigencia: optionalDateField(form.data_fim_vigencia),
    revisao_ativa: form.cenario_tipo === "baseline" ? false : form.revisao_ativa,
    descricao_revisao: form.descricao_revisao.trim() || undefined,
    motivo_revisao: form.motivo_revisao.trim() || undefined,
    observacoes: form.observacoes.trim() || undefined,
  };
}
