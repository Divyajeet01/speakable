/* Run the browser engine out of docs/index.html over a list of cases.
 *
 * The page is the product - one file, no build step - so the engine is not
 * importable. This lifts the <script> block out of the page and evaluates it,
 * which is the only way to test the code that actually ships.
 *
 * Usage: node tests/parity.js cases.json  ->  JSON array of outputs on stdout
 */
"use strict";
const fs = require("fs");
const path = require("path");

const page = fs.readFileSync(
  path.join(__dirname, "..", "docs", "index.html"), "utf8");

const open = page.indexOf("<script>");
const end = page.indexOf("/* ---- page ---- */");
if (open < 0 || end < 0) {
  console.error("parity.js: could not find the engine block in index.html");
  process.exit(2);
}
const source = page.slice(page.indexOf("\n", open) + 1, end);

// The block declares everything with const/function at top level, so wrapping
// it in a function body and handing back `normalize` is enough.
const normalize = new Function(source + "\nreturn normalize;")();

const cases = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const out = cases.map(c => normalize(c.text, c.spell_acronyms, c.strip_emoji));
process.stdout.write(JSON.stringify(out));
