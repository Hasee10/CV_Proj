// Use Vite's bundled esbuild to render the same TSX diagrams as the application.
import { build } from "esbuild";
import { writeFile, unlink } from "node:fs/promises";
import { fileURLToPath } from "node:url";
const runtime = new URL(".study-svg-runtime.mjs", import.meta.url);
const result = await build({
  entryPoints: [
    fileURLToPath(new URL("create-study-svg.tsx", import.meta.url)),
  ],
  bundle: true,
  write: false,
  platform: "node",
  format: "esm",
  packages: "external",
  jsx: "automatic",
});
await writeFile(runtime, result.outputFiles[0].text);
try {
  await import(runtime.href);
} finally {
  await unlink(runtime);
}
