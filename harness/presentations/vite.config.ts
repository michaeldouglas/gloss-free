import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";

const twoslashClientShim = fileURLToPath(new URL("./twoslash-client-shim.ts", import.meta.url));

export default defineConfig({
  resolve: {
    alias: [
      {
        find: "@shikijs/vitepress-twoslash/client",
        replacement: twoslashClientShim,
      },
    ],
  },
});
