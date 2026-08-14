import { createElement, type ReactNode } from "react";

function TextField(props: {
  id?: string;
  label?: string;
  value?: string;
  onChange?: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
}) {
  return createElement(
    "label",
    null,
    props.label ?? "",
    createElement("input", {
      id: props.id,
      value: props.value ?? "",
      placeholder: props.placeholder,
      disabled: props.disabled,
      onChange: (event: { target: { value: string } }) =>
        props.onChange?.(event.target.value),
    }),
  );
}

function SelectField(props: {
  label?: string;
  value?: string;
  onChange?: (value: string) => void;
  options?: Array<{ value: string; label: string }>;
}) {
  return createElement(
    "label",
    null,
    props.label ?? "",
    createElement(
      "select",
      {
        value: props.value ?? "",
        onChange: (event: { target: { value: string } }) =>
          props.onChange?.(event.target.value),
      },
      (props.options ?? []).map((option) =>
        createElement("option", { key: option.value, value: option.value }, option.label),
      ),
    ),
  );
}

function SegmentToggle(props: {
  options?: Array<{ value: string; label: string }>;
  onChange?: (value: string) => void;
  value?: string;
}) {
  return createElement(
    "div",
    null,
    (props.options ?? []).map((option) =>
      createElement(
        "button",
        {
          type: "button",
          key: option.value,
          onClick: () => props.onChange?.(option.value),
        },
        option.label,
      ),
    ),
  );
}

export function FieldLabel(props: { label: string; hint?: string; htmlFor?: string }) {
  return createElement("label", { htmlFor: props.htmlFor }, props.label);
}

export function NativeCheckboxControl(props: {
  label?: string;
  checked?: boolean;
  disabled?: boolean;
  onChange?: (checked: boolean) => void;
}) {
  return createElement(
    "label",
    null,
    createElement("input", {
      type: "checkbox",
      checked: Boolean(props.checked),
      disabled: Boolean(props.disabled),
      onChange: (event: { target: { checked: boolean } }) =>
        props.onChange?.(event.target.checked),
    }),
    props.label,
  );
}

export function NativeTextAreaControl(props: {
  id?: string;
  value?: string;
  onChange?: (value: string) => void;
}) {
  return createElement("textarea", {
    id: props.id,
    value: props.value ?? "",
    onChange: (event: { target: { value: string } }) => props.onChange?.(event.target.value),
  });
}

export function createDashboardTextField() {
  return TextField;
}

export function createDashboardSelectField() {
  return SelectField;
}

export function createDashboardSegmentToggle() {
  return SegmentToggle;
}

export function HelpTooltip(props: { children?: ReactNode }) {
  return createElement("span", null, props.children);
}

export function createDashboardDetailFieldGrid() {
  return function DetailFields(props: {
    fields?: Array<{ label: string; value?: ReactNode; hint?: string; wide?: boolean }>;
  }) {
    return createElement(
      "dl",
      { "data-testid": "detail-fields" },
      (props.fields ?? []).map((field) =>
        createElement(
          "div",
          { key: field.label },
          createElement("dt", null, field.label),
          createElement("dd", null, field.value ?? "—"),
        ),
      ),
    );
  };
}

export function detailFieldGridBemClasses(prefix: string) {
  return {
    grid: `${prefix}-detail-grid`,
    item: `${prefix}-detail-grid__item`,
    itemWide: `${prefix}-detail-grid__item ${prefix}-detail-grid__item--wide`,
    label: `${prefix}-detail-grid__label`,
    empty: `${prefix}-detail__empty`,
  };
}

export function createDashboardFileDropzone() {
  return function Dropzone(): ReactNode {
    return createElement("div", null, "dropzone");
  };
}

export function fileDropzoneBemClasses() {
  return {};
}

export function selectFieldPacClasses() {
  return { field: {}, control: {} };
}

export function textFieldPacClasses() {
  return {};
}
