#!/usr/bin/env node

/**
 * generate-pdf.mjs — HTML → PDF via Playwright
 *
 * Usage (standard):
 *   node career-ops/generate-pdf.mjs <input.html> <output.pdf> [--format=letter|a4]
 *
 * Usage (stdin-json mode — called by job_hunter.py):
 *   node career-ops/generate-pdf.mjs --stdin-json [--format=a4]
 *   Reads JSON from stdin: { type, lang, job, ai_summary, cover_opening }
 *   Writes PDF bytes to stdout.
 *
 * Requires: playwright installed.
 * Uses Chromium headless to render the HTML and produce a clean, ATS-parseable PDF.
 */

import { chromium } from 'playwright';
import { resolve, dirname } from 'path';
import { readFile } from 'fs/promises';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

// ── Stdin-JSON mode ───────────────────────────────────────────────────────────
// Called by job_hunter.py: reads context JSON from stdin, renders the CV HTML
// template with the tailored summary injected, outputs raw PDF bytes to stdout.

async function generatePDFFromStdin(format) {
  const chunks = [];
  for await (const chunk of process.stdin) chunks.push(chunk);
  const payload = JSON.parse(Buffer.concat(chunks).toString('utf-8'));

  const { type = 'cv', lang = 'en', job = {}, ai_summary = '', cover_opening = '' } = payload;

  // Load the shared HTML template
  const templatePath = resolve(__dirname, 'templates', 'cv-template.html');
  let html = await readFile(templatePath, 'utf-8');

  // Inject font paths as absolute file:// URLs
  const fontsDir = resolve(__dirname, 'fonts');
  html = html.replace(/url\(['"]?\.\/fonts\//g, `url('file://${fontsDir}/`);
  html = html.replace(/file:\/\/([^'")]+)\.woff2['"]\)/g, `file://$1.woff2')`);

  // Read Marc's CV markdown and inject job-specific context as data attributes
  // so the template can reference them via CSS/print media.
  // We embed the tailored summary and cover opening directly into the HTML.
  const jobTitle = (job.title || '').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const company  = (job.company || '').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const summary  = (ai_summary || '').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const opening  = (cover_opening || '').replace(/</g, '&lt;').replace(/>/g, '&gt;');

  // Inject a <script> block that exposes context to any template JS
  const contextScript = `
<script>
window.__CAREER_OPS_CONTEXT__ = ${JSON.stringify({ type, lang, jobTitle, company, summary, opening })};
</script>`;
  html = html.replace('</head>', `${contextScript}\n</head>`);

  // If the template has a placeholder comment for dynamic summary, fill it in
  html = html.replace(/<!--\s*TAILORED_SUMMARY\s*-->/g, summary || '');
  html = html.replace(/<!--\s*COVER_OPENING\s*-->/g, opening || '');
  html = html.replace(/<!--\s*TARGET_ROLE\s*-->/g, jobTitle);
  html = html.replace(/<!--\s*TARGET_COMPANY\s*-->/g, company);

  const pdfBuffer = await renderHtmlToPdf(html, resolve(__dirname), format);

  // Write raw bytes to stdout — Python reads them back
  process.stdout.write(pdfBuffer);
}

// ── Standard file-to-file mode ───────────────────────────────────────────────

async function generatePDF() {
  const args = process.argv.slice(2);

  // Check for stdin-json mode first
  let stdinJson = false;
  let format = 'a4';

  for (const arg of args) {
    if (arg === '--stdin-json') { stdinJson = true; }
    if (arg.startsWith('--format=')) { format = arg.split('=')[1].toLowerCase(); }
  }

  if (stdinJson) {
    return generatePDFFromStdin(format);
  }

  // Parse file arguments
  let inputPath, outputPath;
  for (const arg of args) {
    if (arg.startsWith('--')) continue;
    if (!inputPath) { inputPath = arg; }
    else if (!outputPath) { outputPath = arg; }
  }

  if (!inputPath || !outputPath) {
    console.error('Usage: node generate-pdf.mjs <input.html> <output.pdf> [--format=letter|a4]');
    process.exit(1);
  }

  inputPath  = resolve(inputPath);
  outputPath = resolve(outputPath);

  const validFormats = ['a4', 'letter'];
  if (!validFormats.includes(format)) {
    console.error(`Invalid format "${format}". Use: ${validFormats.join(', ')}`);
    process.exit(1);
  }

  console.error(`📄 Input:  ${inputPath}`);
  console.error(`📁 Output: ${outputPath}`);
  console.error(`📏 Format: ${format.toUpperCase()}`);

  // Read HTML and fix font paths
  let html = await readFile(inputPath, 'utf-8');
  const fontsDir = resolve(__dirname, 'fonts');
  html = html.replace(/url\(['"]?\.\/fonts\//g, `url('file://${fontsDir}/`);
  html = html.replace(/file:\/\/([^'")]+)\.woff2['"]\)/g, `file://$1.woff2')`);

  const pdfBuffer = await renderHtmlToPdf(html, dirname(inputPath), format);

  const { writeFile } = await import('fs/promises');
  await writeFile(outputPath, pdfBuffer);

  const pdfString  = pdfBuffer.toString('latin1');
  const pageCount  = (pdfString.match(/\/Type\s*\/Page[^s]/g) || []).length;

  console.error(`✅ PDF generated: ${outputPath}`);
  console.error(`📊 Pages: ${pageCount}`);
  console.error(`📦 Size: ${(pdfBuffer.length / 1024).toFixed(1)} KB`);

  return { outputPath, pageCount, size: pdfBuffer.length };
}

// ── Shared Playwright rendering ───────────────────────────────────────────────

async function renderHtmlToPdf(html, baseDir, format = 'a4') {
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage();
    await page.setContent(html, {
      waitUntil: 'networkidle',
      baseURL: `file://${baseDir}/`,
    });
    await page.evaluate(() => document.fonts.ready);
    const pdfBuffer = await page.pdf({
      format,
      printBackground: true,
      margin: { top: '0.6in', right: '0.6in', bottom: '0.6in', left: '0.6in' },
      preferCSSPageSize: false,
    });
    return pdfBuffer;
  } finally {
    await browser.close();
  }
}

// ── Entry point ───────────────────────────────────────────────────────────────

generatePDF().catch((err) => {
  process.stderr.write(`❌ PDF generation failed: ${err.message}\n`);
  process.exit(1);
});
