import { useState } from "react";

import { PUC_PREFIX } from "../../app/bemPrefix";
import {
  DateField,
  dateFieldBemClasses,
  FileDropzone,
  fileDropzoneBemClasses,
  MultiSelectField,
  multiSelectBemClasses,
  ReadOnlyField,
  readOnlyFieldPacBemClasses,
  SelectField,
  selectControlBemClasses,
  selectFieldPacClasses,
} from "../../components/forms";
import type { CatalogEntryDraft } from "../types";

const dateCn = dateFieldBemClasses(PUC_PREFIX);
const selectPac = selectFieldPacClasses(PUC_PREFIX);
const multiCn = multiSelectBemClasses(PUC_PREFIX);
const readOnlyCn = readOnlyFieldPacBemClasses(PUC_PREFIX);
const dropzoneCn = fileDropzoneBemClasses(PUC_PREFIX);

const SELECT_OPTIONS = [
  { value: "sc", label: "Filial SC" },
  { value: "es", label: "Filial ES" },
];

export const formsCatalogEntries: CatalogEntryDraft[] = [
  {
    id: "forms.SelectField",
    family: "forms",
    exportName: "SelectField",
    title: "SelectField",
    description: "Select com label, hint e painel ancorado.",
    docAnchor: "selectfield",
    propsSummary: ["label", "options", "value", "onChange"],
    demos: [
      {
        id: "default",
        label: "Padrão",
        render: () => <SelectFieldDemo />,
      },
    ],
  },
  {
    id: "forms.DateField",
    family: "forms",
    exportName: "DateField",
    title: "DateField",
    description: "Input type=date com FieldLabel.",
    docAnchor: "datefield",
    propsSummary: ["label", "value", "onChange", "hint"],
    demos: [
      {
        id: "default",
        label: "Padrão",
        render: () => <DateFieldDemo />,
      },
    ],
  },
  {
    id: "forms.MultiSelectField",
    family: "forms",
    exportName: "MultiSelectField",
    title: "MultiSelectField",
    description: "Multiseleção com busca opcional.",
    docAnchor: "multiselectfield",
    propsSummary: ["label", "options", "selectedValues", "onChange"],
    demos: [
      {
        id: "default",
        label: "Padrão",
        render: () => <MultiSelectDemo />,
      },
    ],
  },
  {
    id: "forms.ReadOnlyField",
    family: "forms",
    exportName: "ReadOnlyField",
    title: "ReadOnlyField",
    description: "Campo somente leitura (ficha / inline).",
    docAnchor: "readonlyfield",
    propsSummary: ["label", "value", "appearance"],
    demos: [
      {
        id: "default",
        label: "Ficha",
        render: () => (
          <ReadOnlyField
            label="Código"
            hint="Identificador do produto"
            value="90.123.456"
            appearance="ficha"
            labelMode="fieldLabel"
            classNames={readOnlyCn}
            labels={{
              emptyDisplay: "—",
              fieldHelpAriaLabel: (label) => `Ajuda: ${label}`,
            }}
          />
        ),
      },
    ],
  },
  {
    id: "forms.FileDropzone",
    family: "forms",
    exportName: "FileDropzone",
    title: "FileDropzone",
    description: "Área de upload com drag-and-drop (mock).",
    docAnchor: "filedropzone",
    propsSummary: ["onFilesSelected", "labels", "accept"],
    demos: [
      {
        id: "default",
        label: "Mock",
        render: () => <FileDropzoneDemo />,
      },
    ],
  },
];

function SelectFieldDemo() {
  const [value, setValue] = useState("sc");

  return (
    <SelectField
      label="Filial"
      hint="Unidade operacional"
      options={SELECT_OPTIONS}
      value={value}
      onChange={setValue}
      classNames={selectPac.field}
      controlClassNames={selectControlBemClasses(PUC_PREFIX)}
      labels={{
        placeholder: "Selecione…",
        emptyLabel: "—",
        control: {
          searchPlaceholder: "Buscar…",
          emptyOptions: "Nenhuma opção encontrada.",
          searchAriaLabel: (label) => (label ? `Buscar em ${label}` : "Buscar opções"),
        },
      }}
    />
  );
}

function DateFieldDemo() {
  const [value, setValue] = useState("2026-07-13");

  return (
    <DateField
      label="Data de referência"
      hint="Competência"
      value={value}
      onChange={setValue}
      classNames={dateCn}
    />
  );
}

function MultiSelectDemo() {
  const [selected, setSelected] = useState<string[]>(["sc"]);

  return (
    <MultiSelectField
      label="Filiais"
      labelHint="Uma ou mais unidades"
      options={SELECT_OPTIONS}
      selectedValues={selected}
      onChange={setSelected}
      searchable
      classNames={multiCn}
      labels={{
        emptyLabel: "Nenhuma selecionada",
        searchPlaceholder: "Buscar…",
        selectVisible: "Selecionar visíveis",
        clear: "Limpar",
        emptyOptions: "Nenhuma opção",
        multipleSelected: (count) => `${count} selecionadas`,
      }}
    />
  );
}

function FileDropzoneDemo() {
  const [names, setNames] = useState<string[]>([]);

  return (
    <div className="puc-stack">
      <FileDropzone
        accept=".pdf,.png,.jpg"
        multiple
        onFilesSelected={(files) => setNames(files.map((f) => f.name))}
        classNames={dropzoneCn}
        labels={{
          title: "Solte arquivos aqui",
          hint: "PDF ou imagem (demo — não envia ao servidor)",
        }}
      />
      {names.length > 0 ? (
        <p className="puc-muted">Selecionados: {names.join(", ")}</p>
      ) : null}
    </div>
  );
}
