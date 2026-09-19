import { readFile } from "node:fs/promises";
import { runTests } from "./node_toggle_cases.mjs";

const source = await readFile(new URL("../js/random_csv_text_replace_node_toggle.js", import.meta.url), "utf8");
console.log(`${await runTests(source)} node-toggle checks passed`);
