// src/ui/admin/modals/base/UIBaseFields.tsx

import { FormField, Select } from "../../../../ui-kit";

type RenderMode = "embedded" | "external" | "federated";

type Props = {
  manifest: any;
  setBase: (patch: any) => void;
};

export const UIBaseFields = ({ manifest, setBase }: Props) => {
  const current: RenderMode = manifest.ui?.renderMode ?? "embedded";

  const setRenderMode = (mode: RenderMode) => {
    setBase({
      ui: {
        ...(manifest.ui || {}),
        renderMode: mode,
      },
    });
  };

  const options = [
    { value: "embedded", label: "embedded (iframe interno)" },
    ...(manifest.type === "iframe"
      ? [{ value: "external", label: "external (abrir em nova aba)" }]
      : []),
    ...(manifest.type === "microfrontend"
      ? [{ value: "federated", label: "federated (Module Federation)" }]
      : []),
  ];

  return (
    <FormField
      label="Modo de Renderização"
      htmlFor="manifest-render-mode"
      hint="Define como o Portal irá renderizar esta aplicação."
    >
      <Select
        value={current}
        options={options}
        onChange={(next) => setRenderMode(next as RenderMode)}
      />
    </FormField>
  );
};
