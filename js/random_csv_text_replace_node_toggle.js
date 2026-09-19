import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

// Resolves _NODE(nodename)_/_NOTNODE(nodename)_ tags in a
// PhoenixRandomCSVTextReplace node's terms before a prompt is queued, and
// sets the mode (active/bypass) of the named nodes accordingly. This has
// to happen here rather than in
// the node's own Python execution: node bypass state is baked into the
// prompt when the graph is converted, before the backend runs anything,
// so a pick made during this node's execution is already too late to
// affect which other nodes ran in that same prompt. The pick itself is
// resolved by hitting a backend endpoint that reuses the exact same
// selection logic PhoenixRandomCSVTextReplace.replace() uses, so the
// toggled nodes always match the term actually substituted for the same
// seed.
//
// Hooked onto app.graphToPrompt(), not app.queuePrompt() (2026-08-29):
// in current ComfyUI frontends, app.queuePrompt() just pushes a request
// descriptor onto a shared `queueItems` stack and, if a previous call is
// still draining that stack (`processingQueue === true`), returns
// immediately without doing anything else. The actual graph
// serialization (app.graphToPrompt(), which is what reads node.mode for
// bypass state) happens later, inside that draining loop, one queued
// item at a time, in LIFO order. Since node.mode lives on the live node
// object (not a per-queue-item snapshot), patching queuePrompt meant a
// second queued render could re-toggle the shared LoRA nodes before the
// first (still-pending) render had reached its own graphToPrompt() call
// - baking the wrong LoRA into that first render even though its own
// text pick was resolved correctly. Patching graphToPrompt() instead
// keeps "set the toggles" and "serialize this exact prompt" atomic per
// call, since the queue-draining loop awaits each graphToPrompt() call
// in turn before moving to the next queued item. This does mean a
// manual "export workflow"/save action (which also calls
// app.graphToPrompt()) will now re-resolve and apply the toggles too -
// harmless (it just syncs the saved node.mode to what the current
// seed/terms would pick), and arguably more correct than leaving it
// stale.
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

// A node's "defines" input, resolved back to the RandomCSV node feeding
// it (through virtual pass-through nodes, so routing defines via KJNodes'
// SetNode/GetNode works the same way a routed seed does). Returns null
// when nothing, or nothing of this type, is wired in.
function definesOrigin(node) {
	const visited = new Set();
	while (node && !visited.has(node)) {
		visited.add(node);
		const slotIndex = node.inputs?.findIndex((i) => i.name === "defines");
		if (slotIndex == null || slotIndex < 0 || node.inputs[slotIndex].link == null) {
			return null;
		}
		const origin = resolveRealOrigin(node, slotIndex);
		if (origin?.node?.type !== NODE_TYPE) return null;
		node = origin.node;
		if (node.mode === MODE_ALWAYS) return node;
		if (node.mode !== MODE_BYPASS) return null;
		// Bypass forwards the defines input unchanged, ignoring this node's
		// terms and pass_through_defines widget. Follow it back to the source.
	}
	return null;
}

// Orders the nodes so that one feeding another's "defines" input comes
// first. Canvas order (app.graph._nodes) says nothing about execution
// order, but _IF(...)_ has to see what an upstream _DEFINE(...)_ set, so
// the pre-queue pass must walk the same chain the executor will.
function orderByDefinesChain(nodes) {
	const ids = new Set(nodes.map((n) => n.id));
	const upstream = new Map();
	for (const node of nodes) {
		const up = definesOrigin(node);
		upstream.set(node.id, up && ids.has(up.id) ? up.id : null);
	}
	const ordered = [];
	const done = new Set();
	let remaining = [...nodes];
	while (remaining.length) {
		const ready = remaining.filter((n) => {
			const up = upstream.get(n.id);
			return up == null || done.has(up);
		});
		if (!ready.length) {
			// Can only happen if the defines links form a cycle, which the
			// graph shouldn't allow. Emit the rest as-is rather than hang.
			console.warn("Phoenix Random CSV Text Replace: cycle in the defines chain, falling back to canvas order.");
			ordered.push(...remaining);
			break;
		}
		for (const node of ready) {
			ordered.push(node);
			done.add(node.id);
		}
		remaining = remaining.filter((n) => !done.has(n.id));
	}
	return { ordered, upstream };
}

function passesThrough(node) {
	return widgetValue(node, "pass_through_defines") !== false;
}

async function resolveToggles(node, definesIn) {
	const terms = widgetValue(node, "terms");
	const tagged =
		typeof terms === "string" &&
		(terms.includes("_NODE(") || terms.includes("_NOTNODE(") || terms.includes("_DEFINE(") || terms.includes("_IF(") || terms.includes("_IFNOT("));
	if (!tagged) {
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
			body: JSON.stringify({ terms, seed, unique, defines: definesIn, pass_through: passesThrough(node) }),
		});
		return await response.json();
	} catch (err) {
		console.warn(`Phoenix Random CSV Text Replace "${node.title}": failed to resolve _NODE(...) tags`, err);
		return null;
	}
}

let callCounter = 0;

async function applyNodeToggles() {
	const callId = ++callCounter;
	const t0 = performance.now();
	const sourceNodes = app.graph._nodes.filter((n) => n.type === NODE_TYPE && n.mode === MODE_ALWAYS);
	console.debug(
		`[Phoenix NodeToggle #${callId}] graphToPrompt intercepted, resolving ${sourceNodes.length} active "${NODE_TYPE}" node(s)...`
	);
	// Later nodes (and later rows within one node, resolved server-side)
	// override earlier ones for the same name.
	const { ordered, upstream } = orderByDefinesChain(sourceNodes);
	const state = {};
	const definesById = new Map();
	for (const node of ordered) {
		const upId = upstream.get(node.id);
		const definesIn = (upId != null ? definesById.get(upId) : null) || [];
		const result = await resolveToggles(node, definesIn);
		if (result) {
			Object.assign(state, result.toggles);
			definesById.set(node.id, result.defines || []);
		} else {
			// Nothing to resolve for this node (no tags, or a seed we couldn't
			// read). It still sits in the chain, so hand its input set on.
			definesById.set(node.id, passesThrough(node) ? definesIn : []);
		}
	}
	console.debug(`[Phoenix NodeToggle #${callId}] resolved state:`, state);

	let changed = false;
	for (const [title, active] of Object.entries(state)) {
		const targets = app.graph._nodes.filter((n) => n.title === title);
		if (!targets.length) {
			console.warn(`Phoenix Random CSV Text Replace: no node titled "${title}" found for a _NODE(...) tag.`);
			continue;
		}
		for (const target of targets) {
			if (target.mode !== (active ? MODE_ALWAYS : MODE_BYPASS)) {
				console.debug(
					`[Phoenix NodeToggle #${callId}] "${title}" (id ${target.id}): mode ${target.mode} -> ${
						active ? MODE_ALWAYS : MODE_BYPASS
					}`
				);
			}
			target.mode = active ? MODE_ALWAYS : MODE_BYPASS;
			changed = true;
		}
	}
	if (changed) {
		app.graph.setDirtyCanvas(true, true);
	}
	console.debug(`[Phoenix NodeToggle #${callId}] done in ${(performance.now() - t0).toFixed(1)}ms`);
}

app.registerExtension({
	name: "PhoenixRandomCSVTextReplace.NodeToggle",
	async setup() {
		const originalGraphToPrompt = app.graphToPrompt.bind(app);
		app.graphToPrompt = async (...args) => {
			await applyNodeToggles();
			return originalGraphToPrompt(...args);
		};
	},
});
