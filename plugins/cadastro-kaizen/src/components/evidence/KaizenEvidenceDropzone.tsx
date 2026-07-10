import {
  createDashboardFileDropzone,
  fileDropzoneKaizenClasses,
} from "@delpi/plugin-ui/index";

const classNames = {
  ...fileDropzoneKaizenClasses(),
  hint: "kz-empty-hint kz-dropzone__hint",
};

export const KaizenEvidenceDropzone = createDashboardFileDropzone({
  classNames,
  labels: {
    title: "Arraste arquivos aqui ou clique para buscar na pasta",
    hint: "Você pode selecionar mais de um arquivo (fotos, PDFs, planilhas…).",
  },
});
