import { useCallback, useEffect, useState } from "react";

import type { AppProps } from "../../App";
import { FieldLabel, NativeTextControl, useEditableDraft } from "@delpi/plugin-ui/index";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import {
  fetchInstanciaContexto,
  saveInstanciaContexto,
} from "../../data/api/transformometroDecompositionApi";
import { emptyInstanciaContexto, type InstanciaContextoV1 } from "../../types/decomposition";
import { InstanciaContextoReadView } from "./InstanciaContextoReadView";
import { TmNativeTextAreaField } from "../ui/tmNativeFormFields";
import { DirtySaveActions } from "../ui/DirtySaveActions";

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
  const { value: contexto, setValue, dirty, replace } = useEditableDraft<InstanciaContextoV1>(
    emptyInstanciaContexto()
  );

  const load = useCallback(async () => {
    setLoading(true);
    onError(null);
    try {
      const data = await fetchInstanciaContexto(instanciaId, getAccessToken);
      replace(data.conteudo ?? emptyInstanciaContexto());
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao carregar contexto operacional.");
    } finally {
      setLoading(false);
    }
  }, [getAccessToken, instanciaId, onError, replace]);

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
          <NativeTextControl
            value={contexto.responsavel_local ?? ""}
            onChange={(responsavel_local) =>
              setValue({ ...contexto, responsavel_local: responsavel_local || null })
            }
          />
        </label>
        <label className="ds-field">
          <FieldLabel className="tm-field__label" label="Contato" hint={C.contextoContato} />
          <NativeTextControl
            value={contexto.contato ?? ""}
            onChange={(contato) => setValue({ ...contexto, contato: contato || null })}
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
          setValue({ ...contexto, observacoes_rollout: value || null })
        }
      />

      <DirtySaveActions
        dirty={dirty}
        saving={saving}
        label="Salvar contexto"
        onSave={() => void handleSave()}
      />
    </div>
  );
}
