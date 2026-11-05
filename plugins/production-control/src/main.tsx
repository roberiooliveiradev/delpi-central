import { mount } from "./bootstrap";

const root = document.getElementById("root");
if (root) {
  // Preview standalone: espelha um usuário com as duas filiais.
  mount(root, {
    isSuperadmin: true,
    permissions: [
      "production-control.access",
      "production-control.view.filial-01",
      "production-control.view.filial-02",
    ],
  });
}
