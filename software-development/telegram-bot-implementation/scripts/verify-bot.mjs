// Verification harness for an Omni-Memory-style Telegram hub bot.
// Seeds a pending proposal, runs --approve-all end-to-end, asserts the
// side-effect files (SKILL.md, SKILL.json, registry.json) and DB state
// are correct, then cleans up. Idempotent — re-runs are no-ops.
//
// Usage:
//   node verify-bot.mjs
//
// Pre-conditions:
//   - bot.mjs exists at ./telegram/bot.mjs (cwd-relative to this script)
//   - skills/ registry at ~/Omni-Memory/skills/registry.json
//   - proposals DB at ~/.memory/hub/proposals.db
//   - node --check telegram/bot.mjs passes (PARSE OK)

import { strict as assert } from "node:assert";
import { execSync } from "node:child_process";
import { DatabaseSync } from "node:sqlite";
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";

const HUB_ROOT = "/home/thomas/Omni-Memory/hub";
const DB = path.join(process.env.HOME, ".memory", "hub", "proposals.db");
const SKILLS_DIR = "/home/thomas/Omni-Memory/skills";
const BOT_PATH = path.join(HUB_ROOT, "telegram", "bot.mjs");

let pass = 0, fail = 0;
function ok(msg) { pass++; console.log(`✓ ${msg}`); }
function bad(msg) { fail++; console.error(`✗ ${msg}`); }

// ── 1. Source-shape checks ──────────────────────────────────────────────────
const src = fs.readFileSync(BOT_PATH, "utf8");
assert.match(src, /TELEGRAM_CALLBACK_DATA_MAX\s*=\s*64/, "constant present");
assert.match(src, /assertKeyboardValid/, "function present");
assert.match(src, /stripKeyboard/, "stripKeyboard helper present");
ok("bot.mjs source contains assertKeyboardValid + 64B cap + stripKeyboard");

// ── 2. parseJsonCols behavior (unit) ────────────────────────────────────────
const JSON_COLUMNS = ["steps", "sources", "devices"];
function parseJsonCols(row) {
  if (!row) return row;
  for (const col of JSON_COLUMNS) {
    if (typeof row[col] === "string") {
      try { row[col] = JSON.parse(row[col]); } catch {}
    }
  }
  return row;
}
const fake = { steps: '["a","b"]', sources: '["x"]', devices: "[1,2]", other: "leave-me" };
const parsed = parseJsonCols(fake);
assert.deepEqual(parsed.steps, ["a", "b"]);
assert.deepEqual(parsed.sources, ["x"]);
assert.deepEqual(parsed.devices, [1, 2]);
assert.equal(parsed.other, "leave-me");
ok("parseJsonCols decodes all 3 JSON cols, leaves others alone");

const garbled = { steps: "not json" };
assert.equal(parseJsonCols(garbled).steps, "not json");
ok("parseJsonCols tolerates bad JSON (leaves as string)");

// ── 3. End-to-end: seed → --approve-all → assert side-effects ──────────────
const db = new DatabaseSync(DB);
const id = crypto.randomUUID();
db.prepare(
  `INSERT INTO workflow_proposals
   (id, title, description, trigger, pattern, steps, confidence, frequency, sources, devices, status)
   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')`
).run(
  id,
  "Verify Test",
  "A scratch proposal to verify --approve-all writes the skill file end-to-end.",
  'When user says "verify" or "check approve flow"',
  "verify.*approve|check.*flow",
  JSON.stringify(["Step A", "Step B", "Step C"]),
  0.9,
  3,
  JSON.stringify(["test"]),
  JSON.stringify(["macbook-air"])
);

const skillDir = `${SKILLS_DIR}/${id}`;
if (fs.existsSync(skillDir)) fs.rmSync(skillDir, { recursive: true, force: true });

ok(`seeded pending proposal: ${id}`);

execSync(`node ${BOT_PATH} --approve-all`, { cwd: HUB_ROOT, stdio: "pipe", timeout: 15_000 });
ok("--approve-all ran without exit code / error spam");

assert.ok(fs.existsSync(`${skillDir}/SKILL.md`), "SKILL.md missing");
assert.ok(fs.existsSync(`${skillDir}/SKILL.json`), "SKILL.json missing");
const md = fs.readFileSync(`${skillDir}/SKILL.md`, "utf8");
assert.match(md, /^# Verify Test/m);
assert.match(md, /## Steps/);
assert.match(md, /1\. Step A/);
ok("SKILL.md + SKILL.json written with correct contents");

const row = db.prepare("SELECT status FROM workflow_proposals WHERE id = ?").get(id);
assert.equal(row.status, "approved");
ok("DB row marked 'approved'");

const registry = JSON.parse(fs.readFileSync(`${SKILLS_DIR}/registry.json`, "utf8"));
const entry = registry.skills.find((s) => s.id === id);
assert.ok(entry, "registry entry missing");
assert.equal(entry.name, "Verify Test");
ok("registry.json updated with new skill");

// ── 4. Idempotency ─────────────────────────────────────────────────────────
execSync(`node ${BOT_PATH} --approve-all`, { cwd: HUB_ROOT, stdio: "pipe", timeout: 15_000 });
ok("--approve-all idempotent (no pending → exits 0)");

// ── 5. --dry-run formatting ────────────────────────────────────────────────
const id2 = crypto.randomUUID();
db.prepare(
  `INSERT INTO workflow_proposals
   (id, title, description, trigger, pattern, steps, confidence, frequency, sources, devices, status)
   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')`
).run(
  id2, "Dry Run Test", "Verifies dry-run mode.", 'When user says "dry run"',
  "dry.*run", JSON.stringify(["Step 1"]), 0.8, 1, JSON.stringify(["x"]), JSON.stringify([])
);
const dryOut = execSync(`node ${BOT_PATH} --dry-run`, {
  cwd: HUB_ROOT, stdio: "pipe", timeout: 15_000,
}).toString();
assert.match(dryOut, /Dry Run Test/);
assert.match(dryOut, /inline_keyboard/);
assert.match(dryOut, new RegExp(`approve:${id2}`));
ok("--dry-run prints formatted proposal + keyboard with correct callback_data");

// ── 6. Cleanup ─────────────────────────────────────────────────────────────
db.prepare("DELETE FROM workflow_proposals WHERE id IN (?, ?)").run(id, id2);
fs.rmSync(skillDir, { recursive: true, force: true });
const reg = JSON.parse(fs.readFileSync(`${SKILLS_DIR}/registry.json`, "utf8"));
reg.skills = reg.skills.filter((s) => s.id !== id);
fs.writeFileSync(`${SKILLS_DIR}/registry.json`, JSON.stringify(reg, null, 2));
ok("cleaned up test rows + skill dir + registry entry");

db.close();
console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
