import { mount } from "./bootstrap";

const root = document.getElementById("root");
if (root) {
  const devToken = import.meta.env.VITE_DEV_ACCESS_TOKEN;
  mount(root, {
    getAccessToken: devToken ? () => devToken : undefined,
  });
}
