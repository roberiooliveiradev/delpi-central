import { useState } from "react";
import { FormSelectControl, NativeTextAreaControl, NativeTextControl } from "@delpi/plugin-ui/index";
import type { ComunicadoBlock, ComunicadoInputBlock } from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_ROOT_CLASS } from "../constants/pluginRootClass";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { DataParamFields } from "./DataParamFields";
import { DeckField } from "./deck/DeckField";
import {
  INPUT_VARIABLE_DEFAULT_FIELD,
  INPUT_VARIABLE_TYPE_OPTIONS,
  buildVariableDefaultEditorSchema,
  formatEnumOptionsText,
  parseEnumOptionsText,
  parseVariableDefault,
  valueSchemaForTypeId,
  valueSchemaSupportsEnum,
  valueSchemaTypeId,
  variableKeyIssue,
  type InputVariableTypeId,
} from "../utils/inputVariableEditor";

type Props = {
  block: ComunicadoInputBlock;
  blocks: ComunicadoBlock[] | undefined;
  onPatch: (patch: Partial<ComunicadoInputBlock["input"]>) => void;
};

const KEY_ISSUE_MESSAGE = {
  invalid: "Use letras, números e _ (começando por letra ou _).",
  duplicate: "Já existe uma variável com esta chave neste slide.",
} as const;

/** Variável reutilizável do slide — publica `input.<chave>` para expressões das fontes/modelos. */
export function InputVariableBindingFields({ block, blocks, onPatch }: Props) {
  const key = block.input.binding?.key ?? "";
  const valueSchema = block.input.valueSchema ?? { type: "string" as const };
  const [keyDraft, setKeyDraft] = useState(key);
  const [optionsDraft, setOptionsDraft] = useState(() => formatEnumOptionsText(valueSchema));
  const [optionsError, setOptionsError] = useState<number | null>(null);
  const keyIssue = variableKeyIssue(keyDraft, blocks, block.id);

  const commitKey = () => {
    if (keyIssue || keyDraft === key) return;
    onPatch({ binding: { kind: "variable", key: keyDraft } });
  };

  const commitOptions = () => {
    const parsed = parseEnumOptionsText(optionsDraft, valueSchema.type);
    if (!parsed.ok) {
      setOptionsError(parsed.line);
      return;
    }
    setOptionsError(null);
    const next = {
      type: valueSchema.type,
      ...(valueSchema.format ? { format: valueSchema.format } : {}),
      ...(parsed.enum ? { enum: parsed.enum } : {}),
      ...(parsed.enumLabels ? { enumLabels: parsed.enumLabels } : {}),
    };
    const current = block.input.defaultValue;
    const defaultStillValid =
      current === null || current === undefined || !parsed.enum || parsed.enum.some((item) => item === current);
    onPatch({ valueSchema: next, ...(defaultStillValid ? {} : { defaultValue: null }) });
  };

  const changeType = (typeId: InputVariableTypeId) => {
    setOptionsDraft("");
    setOptionsError(null);
    onPatch({ valueSchema: valueSchemaForTypeId(typeId), defaultValue: null });
  };

  return (
    <>
      <DeckField
        id="td-input-variable-key"
        label="Chave da variável"
        hint={TV_DASHBOARD_HELP_TOOLTIPS.data.inputVariableKey}
      >
        <NativeTextControl
          id="td-input-variable-key"
          value={keyDraft}
          aria-invalid={keyIssue ? true : undefined}
          spellCheck={false}
          onChange={setKeyDraft}
          onBlur={commitKey}
        />
        {keyIssue ? (
          <p className="td-deck-inspector__hint" role="alert">
            {KEY_ISSUE_MESSAGE[keyIssue]}
          </p>
        ) : null}
      </DeckField>

      <DeckField id="td-input-variable-type" label="Tipo">
        <FormSelectControl
          id="td-input-variable-type"
          ariaLabel="Tipo da variável"
          portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
          value={valueSchemaTypeId(valueSchema)}
          onChange={(value) => changeType(value as InputVariableTypeId)}
          options={INPUT_VARIABLE_TYPE_OPTIONS}
        />
      </DeckField>

      {valueSchemaSupportsEnum(valueSchema) ? (
        <DeckField
          id="td-input-variable-options"
          label="Opções (opcional)"
          hint="Uma opção por linha: valor=rótulo. Ex.: 0=Segunda-feira"
        >
          <NativeTextAreaControl
            id="td-input-variable-options"
            rows={4}
            value={optionsDraft}
            aria-invalid={optionsError ? true : undefined}
            onChange={setOptionsDraft}
            onBlur={commitOptions}
          />
          {optionsError ? (
            <p className="td-deck-inspector__hint" role="alert">
              Linha {optionsError} inválida para o tipo escolhido (ou repetida).
            </p>
          ) : null}
        </DeckField>
      ) : null}

      <DataParamFields
        schema={buildVariableDefaultEditorSchema(valueSchema)}
        values={{ [INPUT_VARIABLE_DEFAULT_FIELD]: block.input.defaultValue ?? null }}
        idPrefix="td-input-variable-default"
        onChange={(updates) => {
          const raw = updates[INPUT_VARIABLE_DEFAULT_FIELD];
          if (raw === undefined || typeof raw === "object") return;
          onPatch({ defaultValue: parseVariableDefault(String(raw ?? ""), valueSchema) });
        }}
      />
    </>
  );
}
