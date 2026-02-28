// src/ui/admin/modals/base/UIBaseFields.tsx

import { FormField } from "../../../../components/FormField";

type RenderMode = "embedded" | "external" | "federated";

type Props = {
  manifest: any;
  setBase: (patch: any) => void;
};

export const UIBaseFields = ({
  manifest,
  setBase,
}: Props) => {
  const current: RenderMode =
    manifest.ui?.renderMode ?? "embedded";

  const setRenderMode = (mode: RenderMode) => {
    setBase({
      ui: {
        ...(manifest.ui || {}),
        renderMode: mode,
      },
    });
  };

  return (
    <>
      <FormField label="Modo de Renderização">
        <select
          value={current}
          onChange={(e) =>
            setRenderMode(
              e.target.value as RenderMode
            )
          }
        >
          <option value="embedded">
            embedded (iframe interno)
          </option>

          {manifest.type === "iframe" && (
            <option value="external">
              external (abrir em nova aba)
            </option>
          )}

          {manifest.type === "microfrontend" && (
            <option value="federated">
              federated (Module Federation)
            </option>
          )}
        </select>
      </FormField>

      <div className="hint">
        Define como o Portal irá renderizar esta aplicação.
      </div>
    </>
  );
};