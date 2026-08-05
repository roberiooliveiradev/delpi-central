// src/ui/admin/modals/base/MicrofrontendBaseFields.tsx

import { FormField, Input } from "../../../../ui-kit";

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

  const hint = isFederated ? (
    <>
      Gerado automaticamente para <code>renderMode=federated</code>:{" "}
      <code>{computed.entry}</code>
    </>
  ) : (
    <>
      Aponte para a raiz do app (ex.: <code>{placeholderEmbedded}</code>) ou uma
      URL absoluta (<code>http(s)://</code>) — recomendado via proxy no Nginx.
    </>
  );

  return (
    <FormField
      label={isFederated ? "Entry (auto - federated)" : "Entry (embedded)"}
      htmlFor="manifest-entry"
      error={isTouched("entry") ? getFieldErrors("entry") : []}
      hint={hint}
    >
      <Input
        value={value}
        mono
        readOnly={isFederated}
        disabled={isFederated}
        onBlur={() => markTouched("entry")}
        onChange={(e) => {
          if (isFederated) return;
          setBase({ entry: e.target.value });
        }}
        placeholder={isFederated ? placeholderFederated : placeholderEmbedded}
      />
    </FormField>
  );
};
