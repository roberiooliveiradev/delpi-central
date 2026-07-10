import { useCallback, useEffect, useState } from "react";

import type { AppProps } from "../../App";
import { FieldLabel } from "@delpi/plugin-ui/index";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import {
  fetchInstanciaContexto,
  saveInstanciaContexto,
} from "../../data/api/transformometroDecompositionApi";
import { emptyInstanciaContexto, type InstanciaContextoV1 } from "../../types/decomposition";
import { InstanciaContextoReadView } from "./InstanciaContextoReadView";
import { TmNativeTextAreaField } from "../ui/tmNativeFormFields";

const C = TM_HELP_TOOLTIPS.decomposition;

type Props = Pick<AppProps, "getAccessToken"> & {
  instanciaId: string;
  readOnly?: boolean;
  embeddedInCard?: boolean;
  resyncVersion?: number;
  onError: (message: string | null) => void;
  onSaved?: () => void;
};

export function InstanciaContextoSection({
  instanciaId,
  getAccessToken,
  readOnly = false,
  embeddedInCard = false,
  resyncVersion = 0,
  onError,
  onSaved,
}: Props) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [contexto, setContexto] = useState<InstanciaContextoV1>(emptyInstanciaContexto());

  const load = useCallback(async () => {
    setLoading(true);
    onError(null);
    try {
      const data = await fetchInstanciaContexto(instanciaId, getAccessToken);
      setContexto(data.conteudo ?? emptyInstanciaContexto());
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao carregar contexto operacional.");
    } finally {
      setLoading(false);
    }
  }, [getAccessToken, instanciaId, onError]);

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
      await saveInstanciaContexto(instanciaId, contexto, getAccessToken);
      await load();
      onSaved?.();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao salvar contexto operacional.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <p className="ds-hint">Carregando contexto operacional…</p>;
  }

  if (readOnly) {
    return (
      <div className="tm-instancia-contexto">
        <InstanciaContextoReadView contexto={contexto} />
      </div>
    );
  }

  return (
    <div className="tm-instancia-contexto">
      {!embeddedInCard ? (
        <FieldLabel className="tm-field__label" label="Contexto operacional" hint={C.contextoInstancia} />
      ) : null}

      <div className="tm-inst-form__row">
        <label className="ds-field">
          <FieldLabel className="tm-field__label" label="Responsável local" hint={C.contextoResponsavel} />
          <input
            value={contexto.responsavel_local ?? ""}
            onChange={(event) =>
              setContexto({ ...contexto, responsavel_local: event.target.value || null })
            }
          />
        </label>
        <label className="ds-field">
          <FieldLabel className="tm-field__label" label="Contato" hint={C.contextoContato} />
          <input
            value={contexto.contato ?? ""}
            onChange={(event) => setContexto({ ...contexto, contato: event.target.value || null })}
          />
        </label>
      </div>

      <TmNativeTextAreaField
        id="tm-instancia-contexto-rollout"
        label="Observações de rollout"
        hint={C.contextoObservacoesRollout}
        span
        rows={3}
        value={contexto.observacoes_rollout ?? ""}
        onChange={(value) =>
          setContexto({ ...contexto, observacoes_rollout: value || null })
        }
      />

      <button type="button" className="ds-primary-btn" disabled={saving} onClick={() => void handleSave()}>
        {saving ? "Salvando…" : "Salvar contexto"}
      </button>
    </div>
  );
}
