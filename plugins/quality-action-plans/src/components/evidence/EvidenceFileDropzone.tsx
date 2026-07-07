import {
  createDashboardFileDropzone,
  fileDropzoneBemClasses,
} from "@delpi/plugin-ui";

import { PAC_HELP_TOOLTIPS } from "../../content/helpTooltips";

const classNames = {
  ...fileDropzoneBemClasses("pac"),
  hint: "pac-muted pac-evidence-dropzone__hint",
};

export const EvidenceFileDropzone = createDashboardFileDropzone({
  classNames,
  labels: {
    title: "Arraste arquivos aqui ou clique para buscar na pasta",
    hint: `${PAC_HELP_TOOLTIPS.evidence.upload} Você pode selecionar mais de um arquivo.`,
  },
});
