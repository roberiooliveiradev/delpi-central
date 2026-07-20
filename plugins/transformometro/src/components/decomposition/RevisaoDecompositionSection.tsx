import { useCallback, useEffect, useState } from "react";

import type { AppProps } from "../../App";
import { FieldLabel } from "@delpi/plugin-ui/index";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import {
  fetchRevisaoDecomposicaoMerged,
  saveRevisaoDecomposicaoOverlay,
} from "../../data/api/transformometroDecompositionApi";
import {
  emptyDecompositionTree,
  type DecompositionTreeV1,
  type MergedRevisaoDecomposition,
} from "../../types/decomposition";
import { decompositionTreeToOverlay } from "../../utils/decompositionOverlayDiff";
import { DecompositionFlatPreview } from "./DecompositionFlatPreview";
import { DecompositionTreeEditor } from "./DecompositionTreeEditor";
import { TabPanelTransition } from "../TabPanelTransition";

type Props = Pick<AppProps, "getAccessToken"> & {
  revisaoId: string;
  processoNome?: string;
  readOnly?: boolean;
  embeddedInCard?: boolean;
  resyncVersion?: number;
  onError: (message: string | null) => void;
};

export function RevisaoDecompositionSection({
  revisaoId,
  processoNome,
  getAccessToken,
  readOnly = false,
  embeddedInCard = false,
  resyncVersion = 0,
  onError,
}: Props) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [merged, setMerged] = useState<MergedRevisaoDecomposition | null>(null);
  /** Base absoluta (macro no escopo) — usada no diff de gravação. */
  const [treeProcessBase, setTreeProcessBase] = useState<DecompositionTreeV1>(
    emptyDecompositionTree()
  );
  const [editable, setEditable] = useState<DecompositionTreeV1>(emptyDecompositionTree());
  const [tab, setTab] = useState<"arvore" | "planilha">("arvore");

  const load = useCallback(async () => {
    setLoading(true);
    onError(null);
    try {
      const mergedData = await fetchRevisaoDecomposicaoMerged(revisaoId, getAccessToken);
      setMerged(mergedData);
      const processBase = mergedData.tree_base ?? emptyDecompositionTree();
      setTreeProcessBase(processBase);
      // tree já vem da API: referência quando overlay vazio; senão macro+overlay
      setEditable(mergedData.tree ?? emptyDecompositionTree());
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao carregar mapeamento da revisão.");
    } finally {
      setLoading(false);
    }
  }, [getAccessToken, onError, revisaoId]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!resyncVersion) return;
    void load();
  }, [resyncVersion, load]);

  async function handleSave() {
    setSaving(true);
    onError(null);
    try {
      // Overlay absoluto vs macro do processo → composição «agora» pelas vigentes.
      const overlay = decompositionTreeToOverlay(treeProcessBase, editable);
      await saveRevisaoDecomposicaoOverlay(revisaoId, overlay, getAccessToken);
      await load();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao salvar overlay de mapeamento.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <p className="ds-hint">Carregando mapeamento da revisão…</p>;
  }

  if (!merged || (!editable.nodes.length && !treeProcessBase.nodes.length)) {
    return (
      <p className="ds-hint">
        Nenhum mapeamento no escopo desta instância. Cadastre a árvore no processo-mestre e o escopo na instância.
      </p>
    );
  }

  const refLabel =
    merged.referencia?.versao_revisao ||
    (merged.referencia?.revisao_id ? merged.referencia.revisao_id.slice(0, 8) : null);
  const diff = merged.reference_diff ?? merged.baseline_diff;

  return (
    <div className="tm-decomposition-revisao">
      {!embeddedInCard ? (
        <FieldLabel
          className="tm-field__label"
          label="Mapeamento da revisão"
          hint={TM_HELP_TOOLTIPS.decomposition.mapeamentoRevisao}
        />
      ) : null}

      {!readOnly ? (
        <p className="ds-hint tm-decomposition-revisao__edit-hint">
          {refLabel ? (
            <>
              Parte do mapeamento da revisão de referência <strong>{refLabel}</strong>. Altere só o
              delta desta revisão; o <strong>macro composto</strong> («agora») continua a refletir
              as revisões vigentes.
            </>
          ) : (
            <>
              Edite o WBS no escopo desta melhoria. Sem revisão de referência, a âncora é o macro do
              processo; o macro composto «agora» usa as revisões vigentes.
            </>
          )}
        </p>
      ) : null}

      {merged.seeded_from_reference ? (
        <p className="ds-hint" role="status">
          Overlay ainda vazio — árvore iniciada a partir da referência. Ao salvar, o delta fica
          gravado em relação ao macro do processo.
        </p>
      ) : null}

      {merged.warnings?.length ? (
        <div className="ds-state ds-state--warn" role="status">
          {merged.warnings.map((warning) => (
            <p key={warning}>{warning}</p>
          ))}
        </div>
      ) : null}

      {diff ? (
        <p className="ds-hint" role="status">
          Diff vs {refLabel ? `referência (${refLabel})` : "referência"}: {diff.changed.length}{" "}
          alterados, {diff.added.length} novos, {diff.removed.length} removidos.
        </p>
      ) : null}

      <div className="tm-decomposition-section__tabs">
        <button
          type="button"
          className={tab === "arvore" ? "ds-tab-btn is-active" : "ds-tab-btn"}
          onClick={() => setTab("arvore")}
        >
          Árvore
        </button>
        <button
          type="button"
          className={tab === "planilha" ? "ds-tab-btn is-active" : "ds-tab-btn"}
          onClick={() => setTab("planilha")}
        >
          Planilha
        </button>
      </div>

      <TabPanelTransition tabKey={tab}>
        {tab === "arvore" ? (
          <DecompositionTreeEditor
            tree={editable}
            readOnly={readOnly}
            title={processoNome ? `Mapeamento — ${processoNome}` : "Mapeamento da revisão"}
            allowRootProcessoChave={merged.escopo?.inherit_all !== false}
            onChange={setEditable}
          />
        ) : null}

        {tab === "planilha" ? (
          <DecompositionFlatPreview tree={editable} macroprocesso={processoNome} />
        ) : null}
      </TabPanelTransition>

      {!readOnly ? (
        <button type="button" className="ds-primary-btn" disabled={saving} onClick={() => void handleSave()}>
          {saving ? "Salvando…" : "Salvar mapeamento da revisão"}
        </button>
      ) : null}
    </div>
  );
}
