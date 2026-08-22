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

function isVirtualNode(node) {
	return !!node?.isVirtualNode;
}

// Widget-to-input conversions can be fed through virtual pass-through
// nodes (e.g. KJNodes' GetNode/SetNode pair, used for wiring a value like
// a shared seed across a graph without a drawn link). Those nodes carry
// no real value themselves; each overrides getInputLink() to hand back
// the link one hop further up the real chain (GetNode resolves to its
// named SetNode's own input link). Walking that chain here mirrors what
// ComfyUI's own prompt serialization does to skip virtual nodes.
function resolveRealOrigin(node, slotIndex) {
	let link = node.graph?.links?.[node.inputs?.[slotIndex]?.link];
	for (let hops = 0; hops < 20 && link; hops++) {
		const originNode = node.graph?.getNodeById?.(link.origin_id);
		if (!originNode) {
			return null;
		}
		if (!isVirtualNode(originNode)) {
			return { node: originNode, slot: link.origin_slot };
		}
		if (typeof originNode.getInputLink !== "function") {
			return null;
		}
		link = originNode.getInputLink(link.origin_slot);
	}
	return null;
}

function widgetValue(node, name) {
	const slotIndex = node.inputs?.findIndex((i) => i.name === name);
	if (slotIndex == null || slotIndex < 0 || node.inputs[slotIndex].link == null) {
		return node.widgets?.find((w) => w.name === name)?.value;
	}
	const origin = resolveRealOrigin(node, slotIndex);
	if (!origin) {
		return undefined;
	}
	const namedWidget = origin.node.widgets?.find((w) => w.name === name);
	if (namedWidget) {
		return namedWidget.value;
	}
	// Common case for primitive/passthrough nodes: a single widget holding
	// the value, just not named the same as the input it's feeding. A
	// primitive's own "control_after_generate"-style combo widget (e.g.
	// PrimitiveInt's "fixed"/"increment"/"decrement"/"randomize" companion)
	// doesn't carry the value itself, so it's excluded before counting.
	const CONTROL_AFTER_GENERATE_VALUES = new Set(["fixed", "increment", "decrement", "randomize"]);
	const candidates = (origin.node.widgets || []).filter(
		(w) => !(w.type === "combo" && CONTROL_AFTER_GENERATE_VALUES.has(w.value))
	);
	if (candidates.length === 1) {
		return candidates[0].value;
	}
	return undefined;
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
			`Phoenix Random CSV Text Replace "${node.title}": couldn't resolve a concrete seed/unique value ahead of queuing (linked from something other than a plain widget or a single-widget passthrough node), can't resolve _NODE(...) tags before queuing.`
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
