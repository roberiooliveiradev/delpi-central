import {
  createDashboardFileDropzone,
  fileDropzoneBemClasses,
} from "@delpi/plugin-ui";

const classNames = {
  ...fileDropzoneBemClasses("tm"),
  hint: "ds-hint tm-evidence-dropzone__hint",
};

export const EvidenceDropzone = createDashboardFileDropzone({
  classNames,
  labels: {
    title: "Arraste arquivos aqui ou clique para buscar",
    hint: "Fotos, PDFs, planilhas e documentos (até 25 MB por arquivo).",
  },
});
