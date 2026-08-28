import { app } from "../../../scripts/app.js";

const MAX_INPUTS = 100;
const INPUT_NAME_RE = /^input_(\d+)$/;

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

	node.setSize(node.computeSize());
	node.setDirtyCanvas(true, true);
}

app.registerExtension({
	name: "phoenix.flex_concat",

	async beforeRegisterNodeDef(nodeType, nodeData) {
		if (nodeData.name !== "PhoenixFlexConcat") return;

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
