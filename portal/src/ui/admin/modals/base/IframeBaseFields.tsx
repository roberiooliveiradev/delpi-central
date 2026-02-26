// src/ui/admin/modals/base/IframeBaseFields.tsx

import { FormField } from "../../../../components/FormField";

type Props = {
  manifest: any;
  setBase: (patch: any) => void;
  markTouched: (path: string) => void;
  isTouched: (path: string) => boolean;
  getFieldErrors: (path: string) => string[];
};

export const IframeBaseFields = ({
  manifest,
  setBase,
  markTouched,
  isTouched,
  getFieldErrors,
}: Props) => {
  return (
    <>
      <FormField
        label="Entry (URL do iframe)"
        required
        htmlFor="manifest-entry"
        error={isTouched("entry") ? getFieldErrors("entry") : []}
      >
        <input
          value={manifest.entry ?? ""}
          onBlur={() => markTouched("entry")}
          onChange={(e) => setBase({ entry: e.target.value })}
          placeholder="ex: https://glpi.suaempresa.com"
        />
      </FormField>

      <div className="hint">
        <strong>Dica:</strong> Iframe deve apontar para uma URL externa iniciando com http:// ou https://
      </div>
    </>
  );
};