import { createDashboardFileDropzone, fileDropzoneBemClasses } from "@delpi/plugin-ui";

export const CxPhotoDropzoneEmpty = createDashboardFileDropzone({
  classNames: fileDropzoneBemClasses("cx", "photo-drop"),
  labels: {
    title: "Arraste uma foto ou clique para selecionar",
    hint: "JPEG, PNG ou WebP",
  },
});
