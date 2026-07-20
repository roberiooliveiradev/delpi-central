import { useCallback, useEffect, useMemo, useState } from "react";

import type { AppProps } from "../../App";
import { FieldLabel, NativeTextControl } from "@delpi/plugin-ui/index";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import {
  fetchRevisaoDecomposicaoMerged,
  fetchRevisaoDecomposicaoOverlay,
  saveRevisaoDecomposicaoOverlay,
} from "../../data/api/transformometroDecompositionApi";
import {
  emptyDecompositionOverlay,
  type DecompositionOverlayV1,
  type MergedRevisaoDecomposition,
} from "../../types/decomposition";
import { buildDecompositionRichTree } from "../../utils/decompositionRichTree";
import { DecompositionFlatPreview } from "./DecompositionFlatPreview";
import { DecompositionRichTree } from "./DecompositionRichTree";
import { TabPanelTransition } from "../TabPanelTransition";
import { DS_GHOST_BTN } from "../ghostChrome";

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
  const [overlay, setOverlay] = useState<DecompositionOverlayV1>(emptyDecompositionOverlay());
  const [tab, setTab] = useState<"arvore" | "planilha">("arvore");

  const load = useCallback(async () => {
    setLoading(true);
    onError(null);
    try {
      const [mergedData, overlayData] = await Promise.all([
        fetchRevisaoDecomposicaoMerged(revisaoId, getAccessToken),
        fetchRevisaoDecomposicaoOverlay(revisaoId, getAccessToken),
      ]);
      setMerged(mergedData);
      setOverlay(overlayData.conteudo ?? emptyDecompositionOverlay());
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

  const mergedTree = merged?.tree ?? null;

  const richRoot = useMemo(
    () =>
      mergedTree
        ? buildDecompositionRichTree(mergedTree, {
            title: processoNome ? `Mapeamento — ${processoNome}` : "Mapeamento da revisão",
            overlay,
          })
        : null,
    [mergedTree, overlay, processoNome]
  );

  const disabledIds = overlay.disabled_node_ids ?? [];

  function updateOverride(nodeId: string, label: string) {
    setOverlay((current) => ({
      ...current,
      node_overrides: {
        ...(current.node_overrides ?? {}),
        [nodeId]: {
          ...(current.node_overrides?.[nodeId] ?? {}),
          label,
          highlight: "tobe",
        },
      },
    }));
  }

  function disableNode(nodeId: string) {
    setOverlay((current) => {
      const overrides = { ...(current.node_overrides ?? {}) };
      delete overrides[nodeId];
      const disabled = new Set(current.disabled_node_ids ?? []);
      disabled.add(nodeId);
      return {
        ...current,
        node_overrides: overrides,
        disabled_node_ids: Array.from(disabled),
      };
    });
  }

  function restoreNode(nodeId: string) {
    setOverlay((current) => ({
      ...current,
      disabled_node_ids: (current.disabled_node_ids ?? []).filter((id) => id !== nodeId),
    }));
  }

  async function handleSave() {
    setSaving(true);
    onError(null);
    try {
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

  if (!mergedTree || !mergedTree.nodes.length) {
    return (
      <p className="ds-hint">
        Nenhum mapeamento no escopo desta instância. Cadastre a árvore no processo-mestre e o escopo na instância.
      </p>
    );
  }

  return (
    <div className="tm-decomposition-revisao">
      {!embeddedInCard ? (
        <FieldLabel className="tm-field__label" label="Mapeamento da revisão" hint={TM_HELP_TOOLTIPS.decomposition.mapeamentoRevisao} />
      ) : null}

      {!readOnly ? (
        <p className="ds-hint tm-decomposition-revisao__edit-hint">
          Em edição você altera o <strong>rótulo</strong> ou <strong>desativa</strong> nós do escopo
          (delta to-be). A árvore (PK/T/ST) não se adiciona nem remove aqui — use o{" "}
          <strong>Mapeamento</strong> do processo para a estrutura e o{" "}
          <strong>Escopo no mapeamento</strong> da melhoria para o recorte.
        </p>
      ) : null}

      {merged?.warnings?.length ? (
        <div className="ds-state ds-state--warn" role="status">
          {merged.warnings.map((warning) => (
            <p key={warning}>{warning}</p>
          ))}
        </div>
      ) : null}

      {merged?.baseline_diff ? (
        <p className="ds-hint" role="status">
          Diff vs baseline: {merged.baseline_diff.changed.length} alterados,{" "}
          {merged.baseline_diff.added.length} novos, {merged.baseline_diff.removed.length} removidos.
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
        {tab === "arvore" && richRoot ? (
          <DecompositionRichTree
            root={richRoot}
            expandDepth={2}
            renderLabel={
              readOnly
                ? undefined
                : (node) =>
                    node.id === "decomposition-root" ? (
                      <span className="tm-rich-tree__label">{node.label}</span>
                    ) : (
                      <span className="tm-decomposition-revisao__node-edit">
                        <NativeTextControl
                          className="tm-rich-tree__input"
                          value={
                            overlay.node_overrides?.[node.id]?.label !== undefined
                              ? overlay.node_overrides[node.id]!.label!
                              : node.label
                          }
                          placeholder={node.badge === "PK" ? "Processo-chave" : node.badge === "T" ? "Tarefa" : "Sub-tarefa"}
                          onChange={(label) => updateOverride(node.id, label)}
                          aria-label={`Rótulo ${node.label}`}
                        />
                        <button
                          type="button"
                          className={DS_GHOST_BTN}
                          onClick={() => disableNode(node.id)}
                          title="Desativar nó nesta revisão"
                        >
                          Desativar
                        </button>
                      </span>
                    )
            }
          />
        ) : null}

        {tab === "planilha" ? (
          <DecompositionFlatPreview tree={mergedTree} macroprocesso={processoNome} />
        ) : null}
      </TabPanelTransition>

      {!readOnly && disabledIds.length ? (
        <div className="tm-decomposition-revisao__disabled" role="status">
          <p className="ds-hint">Nós desativados nesta revisão:</p>
          <ul>
            {disabledIds.map((nodeId) => (
              <li key={nodeId}>
                <code>{nodeId}</code>{" "}
                <button type="button" className={DS_GHOST_BTN} onClick={() => restoreNode(nodeId)}>
                  Restaurar
                </button>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {!readOnly ? (
        <button type="button" className="ds-primary-btn" disabled={saving} onClick={() => void handleSave()}>
          {saving ? "Salvando…" : "Salvar mapeamento da revisão"}
        </button>
      ) : null}
    </div>
  );
}
