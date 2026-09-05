import { app } from "../../../scripts/app.js";

const MAX_INPUTS = 100;
const INPUT_NAME_RE = /^input_(\d+)$/;
const FIXED_INPUT_ORDER = ["text", "count", "search_string"];

// When a node is bypassed, ComfyUI routes whichever input sits at the same
// array index as the (single) output straight through to it, as long as
// that input's declared type is connection-compatible with the requested
// one. Our input_N sockets are typed "*" (wildcard) so they always pass
// that check, regardless of what's actually wired to them (e.g. an INT
// seed) - if one of them ends up at index 0 the bypassed node would
// silently forward that unrelated value as if it were the STRING output
// (this is the bug PhoenixFlexConcat V1 has). Keeping the fixed
// text/count/search_string slots first means index 0 is always a real
// STRING/INT slot, so a bypass either yields the template text itself or
// nothing at all - never a stray wildcard-typed connection.
function reorderFixedInputsFirst(node) {
	const inputs = node.inputs;
	if (!inputs || inputs.length === 0) return;

	const fixedIndices = [];
	for (const name of FIXED_INPUT_ORDER) {
		const idx = inputs.findIndex((inp) => inp.name === name);
		if (idx !== -1) fixedIndices.push(idx);
	}
	if (fixedIndices.length === 0) return;

	const restIndices = inputs.map((_, i) => i).filter((i) => !fixedIndices.includes(i));
	const newOrder = [...fixedIndices, ...restIndices];
	if (newOrder.every((oldIdx, newIdx) => oldIdx === newIdx)) return;

	const newInputs = newOrder.map((oldIdx) => inputs[oldIdx]);
	const graph = node.graph;
	newInputs.forEach((inp, newIdx) => {
		if (inp.link == null || !graph) return;
		const link = graph.links.get ? graph.links.get(inp.link) : graph.links[inp.link];
		if (link) link.target_slot = newIdx;
	});
	node.inputs = newInputs;
}

function syncFlexConcatInputs(node, rawCount) {
	const count = Math.max(1, Math.min(MAX_INPUTS, Math.round(rawCount) || 1));

	// Remove sockets beyond the requested count (iterate backwards so
	// removeInput's index shifting doesn't skip entries).
	for (let i = node.inputs.length - 1; i >= 0; i--) {
		const m = INPUT_NAME_RE.exec(node.inputs[i].name);
		if (m && parseInt(m[1], 10) > count) {
			node.removeInput(i);
		}
	}

	// Add any missing sockets up to the requested count.
	const present = new Set(
		node.inputs.filter((inp) => INPUT_NAME_RE.test(inp.name)).map((inp) => inp.name)
	);
	for (let i = 1; i <= count; i++) {
		const name = `input_${i}`;
		if (!present.has(name)) {
			node.addInput(name, "*");
		}
	}

	reorderFixedInputsFirst(node);

	node.setSize(node.computeSize());
	node.setDirtyCanvas(true, true);
}

app.registerExtension({
	name: "phoenix.flex_concat_v2",

	async beforeRegisterNodeDef(nodeType, nodeData) {
		if (nodeData.name !== "PhoenixFlexConcatV2") return;

		const onNodeCreated = nodeType.prototype.onNodeCreated;
		nodeType.prototype.onNodeCreated = function () {
			onNodeCreated?.apply(this, arguments);

			const countWidget = this.widgets?.find((w) => w.name === "count");
			if (!countWidget) return;

			syncFlexConcatInputs(this, countWidget.value);

			const origCallback = countWidget.callback;
			countWidget.callback = (value, ...rest) => {
				const result = origCallback?.call(countWidget, value, ...rest);
				syncFlexConcatInputs(this, countWidget.value);
				return result;
			};
		};
	},
});
