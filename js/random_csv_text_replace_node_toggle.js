import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

// Resolves _NODE(nodename)_ tags in a PhoenixRandomCSVTextReplace node's
// terms before a prompt is queued, and sets the mode (active/bypass) of
// the named nodes accordingly. This has to happen here rather than in
// the node's own Python execution: node bypass state is baked into the
// prompt when the graph is converted, before the backend runs anything,
// so a pick made during this node's execution is already too late to
// affect which other nodes ran in that same prompt. The pick itself is
// resolved by hitting a backend endpoint that reuses the exact same
// selection logic PhoenixRandomCSVTextReplace.replace() uses, so the
// toggled nodes always match the term actually substituted for the same
// seed.
const ENDPOINT = "/phoenix/random_csv_node_toggles";
const NODE_TYPE = "PhoenixRandomCSVTextReplace";
const MODE_ALWAYS = 0;
const MODE_BYPASS = 4;

function widgetValue(node, name) {
	const input = node.inputs?.find((i) => i.name === name);
	if (input?.link != null) {
		return undefined;
	}
	return node.widgets?.find((w) => w.name === name)?.value;
}

async function resolveToggles(node) {
	const terms = widgetValue(node, "terms");
	if (typeof terms !== "string" || !terms.includes("_NODE(")) {
		return null;
	}
	const seed = widgetValue(node, "seed");
	const unique = widgetValue(node, "unique");
	if (seed === undefined || unique === undefined) {
		console.warn(
			`Phoenix Random CSV Text Replace "${node.title}": seed/unique is link-driven, can't resolve _NODE(...) tags before queuing.`
		);
		return null;
	}
	try {
		const response = await api.fetchApi(ENDPOINT, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ terms, seed, unique }),
		});
		return await response.json();
	} catch (err) {
		console.warn(`Phoenix Random CSV Text Replace "${node.title}": failed to resolve _NODE(...) tags`, err);
		return null;
	}
}

async function applyNodeToggles() {
	const sourceNodes = app.graph._nodes.filter((n) => n.type === NODE_TYPE && n.mode === MODE_ALWAYS);
	// Later nodes (and later rows within one node, resolved server-side)
	// override earlier ones for the same name.
	const state = {};
	for (const node of sourceNodes) {
		const result = await resolveToggles(node);
		if (result) {
			Object.assign(state, result);
		}
	}

	let changed = false;
	for (const [title, active] of Object.entries(state)) {
		const targets = app.graph._nodes.filter((n) => n.title === title);
		if (!targets.length) {
			console.warn(`Phoenix Random CSV Text Replace: no node titled "${title}" found for a _NODE(...) tag.`);
			continue;
		}
		for (const target of targets) {
			target.mode = active ? MODE_ALWAYS : MODE_BYPASS;
			changed = true;
		}
	}
	if (changed) {
		app.graph.setDirtyCanvas(true, true);
	}
}

app.registerExtension({
	name: "PhoenixRandomCSVTextReplace.NodeToggle",
	async setup() {
		const originalQueuePrompt = app.queuePrompt.bind(app);
		app.queuePrompt = async (...args) => {
			await applyNodeToggles();
			return originalQueuePrompt(...args);
		};
	},
});
