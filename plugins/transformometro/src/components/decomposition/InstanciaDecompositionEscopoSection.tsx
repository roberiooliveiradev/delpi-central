import { useCallback, useEffect, useState } from "react";

import type { AppProps } from "../../App";
import { FieldLabel } from "@delpi/plugin-ui";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import {
  fetchInstanciaDecomposicaoEscopo,
  fetchProcessoDecomposicao,
  saveInstanciaDecomposicaoEscopo,
} from "../../data/api/transformometroDecompositionApi";
import {
  emptyDecompositionEscopo,
  emptyDecompositionTree,
  type DecompositionEscopo,
  type DecompositionTreeV1,
} from "../../types/decomposition";

type Props = Pick<AppProps, "getAccessToken"> & {
  processoId: string;
  instanciaId: string;
  readOnly?: boolean;
  embeddedInCard?: boolean;
  resyncVersion?: number;
  onError: (message: string | null) => void;
};

export function InstanciaDecompositionEscopoSection({
  processoId,
  instanciaId,
  getAccessToken,
  readOnly = false,
  embeddedInCard = false,
  resyncVersion = 0,
  onError,
}: Props) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [tree, setTree] = useState<DecompositionTreeV1>(emptyDecompositionTree());
  const [escopo, setEscopo] = useState<DecompositionEscopo>(emptyDecompositionEscopo());

  const load = useCallback(async () => {
    setLoading(true);
    onError(null);
    try {
      const [treeData, escopoData] = await Promise.all([
        fetchProcessoDecomposicao(processoId, getAccessToken),
        fetchInstanciaDecomposicaoEscopo(instanciaId, getAccessToken),
      ]);
      setTree(treeData.conteudo ?? emptyDecompositionTree());
      setEscopo({
        node_ids: escopoData.node_ids ?? [],
        inherit_all: escopoData.inherit_all ?? true,
        include_descendants: escopoData.include_descendants ?? true,
      });
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao carregar escopo WBS.");
    } finally {
      setLoading(false);
    }
  }, [getAccessToken, instanciaId, onError, processoId]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!resyncVersion) return;
    void load();
  }, [resyncVersion, load]);

  const processosChave = tree.nodes.filter((n) => n.level === "processo_chave" && !n.disabled);
  const selected = new Set(
    escopo.inherit_all ? processosChave.map((n) => n.id) : escopo.node_ids
  );

  function toggleNode(nodeId: string) {
    if (readOnly) return;
    setEscopo((current) => {
      if (current.inherit_all) {
        const allIds = processosChave.map((n) => n.id);
        const nextIds = allIds.filter((id) => id !== nodeId);
        return {
          ...current,
          inherit_all: false,
          node_ids: nextIds,
        };
      }
      const has = current.node_ids.includes(nodeId);
      const nextIds = has
        ? current.node_ids.filter((id) => id !== nodeId)
        : [...current.node_ids, nodeId];
      return {
        ...current,
        inherit_all: nextIds.length === processosChave.length,
        node_ids: nextIds.length === processosChave.length ? [] : nextIds,
      };
    });
  }

  async function handleSave() {
    setSaving(true);
    onError(null);
    try {
      const payload: DecompositionEscopo = escopo.inherit_all
        ? { node_ids: [], inherit_all: true, include_descendants: escopo.include_descendants }
        : escopo;
      await saveInstanciaDecomposicaoEscopo(instanciaId, payload, getAccessToken);
      await load();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao salvar escopo WBS.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <p className="ds-hint">Carregando escopo no mapeamento…</p>;
  }

  if (!processosChave.length) {
    return (
      <p className="ds-hint">
        O processo ainda não possui mapeamento WBS. Cadastre a árvore no detalhe do processo-mestre.
      </p>
    );
  }

  return (
    <div className="tm-decomposition-escopo">
      {!embeddedInCard ? (
        <FieldLabel className="tm-field__label" label="Escopo no mapeamento" hint={TM_HELP_TOOLTIPS.decomposition.escopoInstancia} />
      ) : null}

      <label className="ds-check-label">
        <input
          type="checkbox"
          checked={escopo.inherit_all}
          disabled={readOnly}
          onChange={(event) =>
            setEscopo({
              node_ids: [],
              inherit_all: event.target.checked,
              include_descendants: escopo.include_descendants,
            })
          }
        />
        <span>Usar mapeamento completo nesta instância</span>
      </label>

      {!escopo.inherit_all ? (
        <ul className="tm-decomposition-escopo__list">
          {processosChave.map((node) => (
            <li key={node.id}>
              <label className="ds-check-label">
                <input
                  type="checkbox"
                  checked={selected.has(node.id)}
                  disabled={readOnly}
                  onChange={() => toggleNode(node.id)}
                />
                <span>
                  {node.ordem}. {node.label}
                </span>
              </label>
            </li>
          ))}
        </ul>
      ) : null}

      {!readOnly ? (
        <button type="button" className="ds-primary-btn" disabled={saving} onClick={() => void handleSave()}>
          {saving ? "Salvando…" : "Salvar escopo"}
        </button>
      ) : null}
    </div>
  );
}
