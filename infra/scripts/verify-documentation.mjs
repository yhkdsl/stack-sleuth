#!/usr/bin/env node

import { access, readdir, readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const staleText = [
  "This section becomes available after the PostgreSQL demo-data pull request is merged.",
  "Draft; database section becomes verified after PR #9 merges",
  "Database-backed queries and trace fixtures will be added with the feature that makes them executable.",
  "health 도구의 DB 상태는 설정 여부와 실제 연결 가능성을 구분해야 한다.",
  "Python FastAPI agent service | Not started",
  "Planned until agent service implementation",
];
const sensitivePattern =
  /([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})|(bearer\s+[A-Za-z0-9_.-]+)|(sk-[A-Za-z0-9_-]{16,})|(BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY)/i;
const markdownLinkPattern = /\[[^\]]+\]\(([^)]+)\)/g;

async function collectMarkdownFiles(directory) {
  const files = [];
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const entryPath = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      files.push(...(await collectMarkdownFiles(entryPath)));
    } else if (entry.name.endsWith(".md")) {
      files.push(entryPath);
    }
  }
  return files;
}

async function collectExampleFiles(directory) {
  const files = [];
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const entryPath = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      files.push(...(await collectExampleFiles(entryPath)));
    } else if ([".md", ".py", ".sh", ".json"].includes(path.extname(entry.name))) {
      files.push(entryPath);
    }
  }
  return files;
}

async function exists(file) {
  try {
    await access(file);
    return true;
  } catch {
    return false;
  }
}

const markdownFiles = [
  path.join(repoRoot, "README.md"),
  path.join(repoRoot, "python-agent-service/README.md"),
  ...(await collectMarkdownFiles(path.join(repoRoot, "docs"))),
  ...(await collectMarkdownFiles(path.join(repoRoot, "examples"))),
];
const exampleFiles = await collectExampleFiles(path.join(repoRoot, "examples"));
const nonMarkdownExampleFiles = exampleFiles.filter((file) => !file.endsWith(".md"));
const errors = [];

for (const file of [...markdownFiles, ...nonMarkdownExampleFiles]) {
  const text = await readFile(file, "utf8");
  const relative = path.relative(repoRoot, file);

  if (file.endsWith(".md") && (text.match(/```/g)?.length ?? 0) % 2 !== 0) {
    errors.push(`${relative}: unbalanced fenced code block`);
  }

  const sensitiveMatch = text.match(sensitivePattern);
  if (sensitiveMatch) {
    errors.push(`${relative}: possible sensitive value: ${sensitiveMatch[0]}`);
  }

  if (file.endsWith(".md")) {
    for (const stale of staleText) {
      if (text.includes(stale)) {
        errors.push(`${relative}: stale implementation status: ${stale}`);
      }
    }

    for (const match of text.matchAll(markdownLinkPattern)) {
      const target = match[1].split("#", 1)[0];
      if (!target || /^(https?:\/\/|mailto:)/.test(target)) {
        continue;
      }
      const resolved = path.resolve(path.dirname(file), decodeURIComponent(target));
      if (!(await exists(resolved))) {
        errors.push(`${relative}: missing local link target: ${match[1]}`);
      }
    }
  }
}

if (!(await exists(path.join(repoRoot, "examples/curl/read-only-query.sh")))) {
  errors.push("examples/curl/read-only-query.sh: successful SQL example is required");
}

if (errors.length > 0) {
  for (const error of errors) {
    console.error(`FAIL: ${error}`);
  }
  process.exitCode = 1;
} else {
  console.log(`Documentation validation passed across ${markdownFiles.length} Markdown files.`);
}
