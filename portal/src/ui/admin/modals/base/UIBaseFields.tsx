// src/ui/admin/modals/base/UIBaseFields.tsx


import { FormField } from "../../../../components/FormField";

type Props = {
  manifest: any;
  setBase: (patch: any) => void;
};

export const UIBaseFields = ({
  manifest,
  setBase,
}: Props) => {
  const current = manifest.ui?.renderMode ?? "embedded";

  const setRenderMode = (mode: string) => {
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
          onChange={(e) => setRenderMode(e.target.value)}
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