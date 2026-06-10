#!/usr/bin/env node
/**
 * notebooklm-bb-auth.js
 * Use BrowserBase as the browser for NotebookLM authentication.
 * Creates a BrowserBase session, connects via Playwright CDP,
 * navigates to NotebookLM so Thomas can complete Google login,
 * then saves the auth state to ~/.notebooklm/storage-state.json.
 *
 * Usage:
 *   BROWSERBASE_API_KEY="bb_live_..." node notebooklm-bb-auth.js
 */
const { chromium } = require('/home/thomas/.local/lib/nodejs/node-v22.22.2-linux-x64/lib/node_modules/notebooklm/node_modules/playwright');
const { execSync } = require('child_process');

const BB_API_KEY = process.env.BROWSERBASE_API_KEY;

function bbCommand(args) {
  const out = execSync(`BROWSERBASE_API_KEY=${BB_API_KEY} bb ${args} 2>/dev/null`, { encoding: 'utf8' });
  const lines = out.split('\n');
  let jsonStart = -1;
  for (let i = 0; i < lines.length; i++) {
    const stripped = lines[i].trim();
    if (stripped.startsWith('[') || stripped.startsWith('{')) {
      jsonStart = i;
      break;
    }
  }
  if (jsonStart === -1) return null;
  return JSON.parse(lines.slice(jsonStart).join(''));
}

async function main() {
  if (!BB_API_KEY) {
    console.error('Error: BROWSERBASE_API_KEY not set');
    process.exit(1);
  }

  console.log('Creating BrowserBase session...');
  const session = bbCommand('sessions create --record-session');
  if (!session || !session.connectUrl) {
    console.error('Failed to create session. Check API key and session limit (max 3 concurrent).');
    process.exit(1);
  }

  console.log('Session ID:', session.id);
  console.log('Connecting via Playwright CDP...');

  let browser;
  try {
    browser = await chromium.connectOverCDP(session.connectUrl, { timeout: 20000 });
  } catch (err) {
    console.error('CDP connection failed:', err.message);
    console.error('Session may have expired (times out after ~5 min idle).');
    process.exit(1);
  }

  console.log('Connected!');

  let page;
  const ctx = browser.contexts()[0];
  if (ctx && ctx.pages().length > 0) {
    page = ctx.pages()[0];
  } else {
    const newCtx = await browser.newContext({
      userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    });
    page = await newCtx.newPage();
  }

  await page.goto('https://notebooklm.google.com', { waitUntil: 'networkidle', timeout: 30000 });
  console.log('URL:', page.url());
  console.log('');
  console.log('========================================');
  console.log('BROWSERBASE BROWSER READY');
  console.log('========================================');
  console.log('Open browserbase.com → project → Sessions');
  console.log('Find session', session.id, 'and click to view.');
  console.log('Complete Google login, then press Enter.');
  console.log('========================================');

  await new Promise(resolve => {
    process.stdin.once('data', () => resolve());
  });

  const finalUrl = page.url();
  if (finalUrl.includes('accounts.google.com')) {
    console.error('Login not completed.');
    await browser.close();
    process.exit(1);
  }

  console.log('Saving auth state...');
  const fs = require('fs');
  const output = `${process.env.HOME}/.notebooklm/storage-state.json`;
  fs.mkdirSync(require('path').dirname(output), { recursive: true });
  await page.context().storageState({ path: output });
  console.log('✅ Auth saved to:', output);
  await browser.close();
}

main().catch(err => {
  console.error('Error:', err.message);
  process.exit(1);
});