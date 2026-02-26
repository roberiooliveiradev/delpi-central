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
  openAppIconPicker,
  renderLucideIcon,
}: Props) => {
  return (
    <>
      <FormField
        label="Entry (auto)"
        htmlFor="manifest-entry"
        error={getFieldErrors("entry")}
      >
        <>
          <input
            value={computed.entry}
            disabled
          />
          <small>Auto: {computed.entry}</small>
        </>
      </FormField>

      <div className="hint">
        <strong>Dica:</strong> microfrontend gera <code>entry</code> automaticamente baseado no ID.
      </div>
    </>
  );
};