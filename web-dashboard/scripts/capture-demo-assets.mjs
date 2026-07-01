/* global console, fetch, process, setTimeout */

import { chromium } from "@playwright/test";
import { existsSync, mkdirSync, readdirSync, rmSync } from "node:fs";
import path from "node:path";
import { spawn, spawnSync } from "node:child_process";

const dashboardRoot = path.resolve(import.meta.dirname, "..");
const repoRoot = path.resolve(dashboardRoot, "..");
const assetsDir = path.join(repoRoot, "docs", "assets");
const videoDir = path.join(assetsDir, ".capture-video");
const previewUrl = "http://127.0.0.1:4173/replay";

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd ?? dashboardRoot,
    stdio: "inherit",
  });
  if (result.status !== 0) {
    throw new Error(`${command} ${args.join(" ")} failed`);
  }
}

async function waitForPreview() {
  const deadline = Date.now() + 30_000;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(previewUrl);
      if (response.ok) return;
    } catch {
      // Preview server is still booting.
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  throw new Error(`Timed out waiting for ${previewUrl}`);
}

function convertVideoToGif(webmPath) {
  const palettePath = path.join(videoDir, "palette.png");
  const gifPath = path.join(assetsDir, "dashboard-replay-demo.gif");
  run("ffmpeg", [
    "-y",
    "-i",
    webmPath,
    "-vf",
    "fps=8,scale=900:-1:flags=lanczos,palettegen",
    "-frames:v",
    "1",
    "-update",
    "1",
    palettePath,
  ]);
  run("ffmpeg", [
    "-y",
    "-i",
    webmPath,
    "-i",
    palettePath,
    "-lavfi",
    "fps=8,scale=900:-1:flags=lanczos[x];[x][1:v]paletteuse",
    gifPath,
  ]);
}

async function main() {
  mkdirSync(assetsDir, { recursive: true });
  rmSync(videoDir, { recursive: true, force: true });
  mkdirSync(videoDir, { recursive: true });

  run("npm", ["run", "build"]);
  const server = spawn(
    "npm",
    ["run", "preview", "--", "--host", "127.0.0.1", "--port", "4173"],
    {
      cwd: dashboardRoot,
      stdio: "inherit",
    },
  );

  try {
    await waitForPreview();
    const browser = await chromium.launch();
    const context = await browser.newContext({
      viewport: { width: 1440, height: 1000 },
      recordVideo: {
        dir: videoDir,
        size: { width: 1440, height: 1000 },
      },
    });
    const page = await context.newPage();
    await page.goto(previewUrl, { waitUntil: "networkidle" });
    await page.screenshot({
      path: path.join(assetsDir, "dashboard-replay-actual.png"),
      fullPage: true,
    });
    await page.waitForTimeout(700);
    await page.mouse.wheel(0, 620);
    await page.waitForTimeout(900);
    await page.mouse.wheel(0, 620);
    await page.waitForTimeout(900);
    await context.close();
    await browser.close();

    const videos = readdirSync(videoDir).filter((file) => file.endsWith(".webm"));
    if (videos.length === 0) {
      throw new Error("Playwright did not produce a WebM recording");
    }
    convertVideoToGif(path.join(videoDir, videos[0]));
    rmSync(videoDir, { recursive: true, force: true });
  } finally {
    server.kill("SIGTERM");
  }

  if (!existsSync(path.join(assetsDir, "dashboard-replay-demo.gif"))) {
    throw new Error("GIF output was not created");
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
