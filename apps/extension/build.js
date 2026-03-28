const esbuild = require("esbuild");
const fs = require("fs");

const entries = [
  { in: "src/background.ts", out: "background" },
  { in: "src/content.ts", out: "content" },
  { in: "src/popup.ts", out: "popup" },
];

async function build() {
  for (const entry of entries) {
    await esbuild.build({
      entryPoints: [entry.in],
      bundle: true,
      outfile: `${entry.out}.js`,
      platform: "browser",
      target: "chrome120",
      format: "iife",
    });
  }
  console.log("Extension built.");
}

build().catch(console.error);
