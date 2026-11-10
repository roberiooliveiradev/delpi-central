/** Formulário multi-pergunta de "Solicitar informações" — PRC-REF-019.
 * FIX-01 + REF-021-REF-01: modal wide, SearchableSelect de campo,
 * fornecedor SUPPLIER_LINK apenas por pesquisa oficial SA2. */

import { useId, useMemo, useState } from "react";

import {
  EngineeringActionButton,
  EngineeringFormActions,
  EngineeringHostDialog,
  EngineeringSearchableSelect,
  EngineeringStateBanner,
  EngineeringTextAreaField,
} from "../../../ui/engineeringUi";
import type {
  PrcFieldSpec,
  PrcInformationQuestionInput,
  PrcInformationSupplierAttribute,
  PrcInformationTargetType,
} from "../api/productRegistrationApi";
import { PRC_INFO_COPY, prcFieldLabel } from "../prcCopy";
import {
  buildQuestionInputs,
  emptyInfoQuestion,
  INFO_MAX_QUESTIONS,
  INFO_MESSAGE_MAX,
  INFO_QUESTION_TEXT_MAX,
  INFO_SUPPLIER_ATTRIBUTE_OPTIONS,
  INFO_TARGET_OPTIONS,
  pendingFieldsFromDrafts,
  questionableFieldSpecs,
  validateInfoQuestions,
  type InfoQuestionDraft,
  type InfoSupplierOption,
} from "../prcInformationExchange";
import { PrcOfficialSupplierSearchField } from "./PrcOfficialSupplierSearchField";

export type PrcRequestInformationSubmit = {
  questions: PrcInformationQuestionInput[];
  message?: string;
  pendingFields: string[];
};

export function PrcRequestInformationModal({
  open,
  busy,
  requesterLabel,
  fieldSpecs,
  suppliers,
  onSubmit,
  onCancel,
}: {
  open: boolean;
  busy: boolean;
  requesterLabel?: string;
  fieldSpecs?: PrcFieldSpec[] | null;
  suppliers?: InfoSupplierOption[];
  onSubmit: (payload: PrcRequestInformationSubmit) => void;
  onCancel: () => void;
}) {
  const formId = useId();
  const [drafts, setDrafts] = useState<InfoQuestionDraft[]>(() => [
    emptyInfoQuestion(),
  ]);
  const [message, setMessage] = useState("");
  const [rowErrors, setRowErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState("");

  const fieldOptions = useMemo(
    () =>
      questionableFieldSpecs(fieldSpecs).map((spec) => ({
        value: spec.path,
        label: prcFieldLabel(spec.path),
      })),
    [fieldSpecs],
  );

  /* `suppliers` da ficha permanece disponível como contexto opcional
   * no ActionBar, mas a identidade SUPPLIER_LINK vem só da pesquisa
   * oficial SA2 (REF-021-REF-01) — sem fallback manual. */
  void suppliers;

  const patch = (rowId: string, change: Partial<InfoQuestionDraft>) => {
    setDrafts((list) =>
      list.map((d) => (d.rowId === rowId ? { ...d, ...change } : d)),
    );
    setRowErrors((errors) => {
      if (!errors[rowId]) return errors;
      const next = { ...errors };
      delete next[rowId];
      return next;
    });
    setFormError("");
  };

  const addQuestion = () => {
    if (drafts.length >= INFO_MAX_QUESTIONS) return;
    setDrafts((list) => [...list, emptyInfoQuestion()]);
  };

  const removeQuestion = (rowId: string) => {
    setDrafts((list) => list.filter((d) => d.rowId !== rowId));
    setRowErrors((errors) => {
      const next = { ...errors };
      delete next[rowId];
      return next;
    });
  };

  const confirm = () => {
    const result = validateInfoQuestions(drafts);
    if (!result.valid) {
      setRowErrors(result.rowErrors);
      setFormError(result.formError);
      return;
    }
    const trimmed = message.trim();
    onSubmit({
      questions: buildQuestionInputs(drafts),
      message: trimmed || undefined,
      pendingFields: pendingFieldsFromDrafts(drafts),
    });
  };

  if (!open) return null;

  return (
    <EngineeringHostDialog
      open={open}
      onClose={busy ? () => undefined : onCancel}
      title={PRC_INFO_COPY.requestTitle}
      className="engineering-prc-info-modal engineering-modal--wide delpi-ui-modal--wide"
      footer={
        <EngineeringFormActions>
          <EngineeringActionButton
            variant="ghost"
            disabled={busy}
            onClick={onCancel}
          >
            {PRC_INFO_COPY.cancel}
          </EngineeringActionButton>
          <EngineeringActionButton
            variant="primary"
            softDisabled={busy}
            onClick={confirm}
          >
            {PRC_INFO_COPY.submitRequest}
          </EngineeringActionButton>
        </EngineeringFormActions>
      }
    >
      <div className="engineering-prc__info-form" id={formId}>
        <p className="engineering-prc__muted">{PRC_INFO_COPY.requestIntro}</p>

        <dl className="engineering-prc__info-recipient">
          <dt>{PRC_INFO_COPY.recipient}</dt>
          <dd>
            <strong>
              {requesterLabel || PRC_INFO_COPY.recipientUnknown}
            </strong>
            <span className="engineering-prc__muted">
              {PRC_INFO_COPY.recipientHint}
            </span>
          </dd>
        </dl>

        <h3 className="engineering-prc__info-heading">
          {PRC_INFO_COPY.questionsTitle}
        </h3>

        <ol className="engineering-prc__info-questions">
          {drafts.map((draft, index) => {
            const base = `${formId}-q${draft.rowId}`;
            const error = rowErrors[draft.rowId];
            const selectedSupplier =
              draft.supplierCode && draft.store
                ? {
                    supplierCode: draft.supplierCode,
                    store: draft.store,
                  }
                : null;
            return (
              <li
                key={draft.rowId}
                className="engineering-prc__info-question"
                aria-label={`Pergunta ${index + 1}`}
              >
                <div className="engineering-prc__info-question-head">
                  <strong>{`Pergunta ${index + 1}`}</strong>
                  {drafts.length > 1 ? (
                    <EngineeringActionButton
                      variant="ghost"
                      disabled={busy}
                      onClick={() => removeQuestion(draft.rowId)}
                    >
                      {PRC_INFO_COPY.removeQuestion}
                    </EngineeringActionButton>
                  ) : null}
                </div>

                <div className="engineering-prc__info-question-target">
                  <EngineeringSearchableSelect
                    id={`${base}-type`}
                    label={PRC_INFO_COPY.targetType}
                    value={draft.targetType}
                    onChange={(value) =>
                      patch(draft.rowId, {
                        targetType: value as PrcInformationTargetType,
                        targetPath: "",
                        supplierCode: "",
                        store: "",
                        targetAttribute: "partNumber",
                      })
                    }
                    options={INFO_TARGET_OPTIONS.map((o) => ({
                      value: o.value,
                      label: o.label,
                    }))}
                    disabled={busy}
                  />

                  {draft.targetType === "FIELD" ? (
                    <EngineeringSearchableSelect
                      id={`${base}-field`}
                      label={PRC_INFO_COPY.targetField}
                      searchable
                      value={draft.targetPath}
                      onChange={(value) =>
                        patch(draft.rowId, { targetPath: value })
                      }
                      options={fieldOptions}
                      placeholder={PRC_INFO_COPY.targetFieldPlaceholder}
                      required
                      disabled={busy}
                    />
                  ) : null}

                  {draft.targetType === "SUPPLIER_LINK" ? (
                    <>
                      <PrcOfficialSupplierSearchField
                        id={`${base}-supplier-search`}
                        selected={selectedSupplier}
                        disabled={busy}
                        onSelect={(hit) =>
                          patch(draft.rowId, {
                            supplierCode: hit.supplierCode,
                            store: hit.store,
                          })
                        }
                        onClear={() =>
                          patch(draft.rowId, {
                            supplierCode: "",
                            store: "",
                          })
                        }
                      />
                      <EngineeringSearchableSelect
                        id={`${base}-supplier-attr`}
                        label={PRC_INFO_COPY.supplierAttribute}
                        value={draft.targetAttribute}
                        onChange={(value) =>
                          patch(draft.rowId, {
                            targetAttribute:
                              value as PrcInformationSupplierAttribute,
                          })
                        }
                        options={INFO_SUPPLIER_ATTRIBUTE_OPTIONS.map((o) => ({
                          value: o.value,
                          label: o.label,
                        }))}
                        disabled={busy}
                      />
                    </>
                  ) : null}
                </div>

                <EngineeringTextAreaField
                  id={`${base}-text`}
                  label={PRC_INFO_COPY.questionText}
                  hint={PRC_INFO_COPY.questionTextHint}
                  value={draft.questionText}
                  onChange={(value) =>
                    patch(draft.rowId, { questionText: value })
                  }
                  maxLength={INFO_QUESTION_TEXT_MAX}
                  rows={3}
                  required
                  disabled={busy}
                />
                {error ? (
                  <p className="engineering-prc__field-error" role="alert">
                    {error}
                  </p>
                ) : null}
              </li>
            );
          })}
        </ol>

        <div>
          <EngineeringActionButton
            variant="ghost"
            disabled={busy || drafts.length >= INFO_MAX_QUESTIONS}
            onClick={addQuestion}
          >
            {PRC_INFO_COPY.addQuestion}
          </EngineeringActionButton>
        </div>

        <EngineeringTextAreaField
          id={`${formId}-message`}
          label={PRC_INFO_COPY.message}
          hint={PRC_INFO_COPY.messageHint}
          value={message}
          onChange={setMessage}
          maxLength={INFO_MESSAGE_MAX}
          rows={3}
          disabled={busy}
        />

        {formError ? (
          <EngineeringStateBanner variant="error">
            {formError}
          </EngineeringStateBanner>
        ) : null}
      </div>
    </EngineeringHostDialog>
  );
}
