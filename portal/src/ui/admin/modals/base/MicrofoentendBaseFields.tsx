// src/ui/admin/modals/base/MicrofrontendBaseFields.tsx

import { FormField } from "../../../../components/FormField";

type Props = {
  manifest: any;
  computed: any;
  setBase: (patch: any) => void;
  markTouched: (path: string) => void;
  isTouched: (path: string) => boolean;
  getFieldErrors: (path: string) => string[];
  openAppIconPicker: () => void;
  renderLucideIcon: (kebab?: string | null, size?: number) => any;
};

export const MicrofrontendBaseFields = ({
  manifest,
  computed,
  setBase,
  markTouched,
  isTouched,
  getFieldErrors,
}: Props) => {
  const renderMode = manifest?.ui?.renderMode ?? "embedded";
  const isFederated = renderMode === "federated";

  const placeholderEmbedded = `/apps/${computed.id || "app-id"}/`;
  const placeholderFederated = computed.entry; // /apps/{id}/assets/remoteEntry.js

  const value = isFederated
    ? computed.entry
    : (manifest.entry ?? placeholderEmbedded);

  return (
    <>
      <FormField
        label={isFederated ? "Entry (auto - federated)" : "Entry (embedded)"}
        htmlFor="manifest-entry"
        error={isTouched("entry") ? getFieldErrors("entry") : []}
      >
        <>
          <input
            id="manifest-entry"
            value={value}
            readOnly={isFederated}
            disabled={isFederated}
            onBlur={() => markTouched("entry")}
            onChange={(e) => {
              if (isFederated) return;
              setBase({ entry: e.target.value });
            }}
            placeholder={isFederated ? placeholderFederated : placeholderEmbedded}
          />

          {isFederated ? (
            <small>
              Auto: <code>{computed.entry}</code>
            </small>
          ) : (
            <small>
              Embedded: aponte para a raiz do app (ex:{" "}
              <code>{placeholderEmbedded}</code>) ou uma URL absoluta (
              <code>http(s)://</code>).
            </small>
          )}
        </>
      </FormField>

      <div className="hint">
        <strong>Dica:</strong>{" "}
        {isFederated ? (
          <>
            Para <code>renderMode=federated</code>, o <code>entry</code> é gerado
            automaticamente (<code>remoteEntry.js</code>).
          </>
        ) : (
          <>
            Para <code>renderMode=embedded</code>, o <code>entry</code> é a URL do
            app que será aberto em iframe (recomendado usar{" "}
            <code>/apps/{computed.id || "app-id"}/</code> via proxy no Nginx).
          </>
        )}
      </div>
    </>
  );
};