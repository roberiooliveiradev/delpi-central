/** Folha de estilo processada pelo bundler (`?inline`) e injetada como
 * texto no shadow root do elemento — mesma fonte para Vite e esbuild. */
declare module "*.css?inline" {
  const styles: string;
  export default styles;
}
