import { app } from "../../../scripts/app.js";

// Locks the "preview" widget to read-only and fills it with the loaded
// text (or the "No Text found: ..." reason) after each execution.
app.registerExtension({
	name: "PhoenixLoadText.Preview",
	async beforeRegisterNodeDef(nodeType, nodeData, app) {
		if (nodeData.name !== "PhoenixLoadText") {
			return;
		}

		const onNodeCreated = nodeType.prototype.onNodeCreated;
		nodeType.prototype.onNodeCreated = function () {
			onNodeCreated?.apply(this, arguments);
			const widget = this.widgets?.find((w) => w.name === "preview");
			if (widget?.inputEl) {
				widget.inputEl.readOnly = true;
				widget.inputEl.style.opacity = 0.6;
			}
		};

		const onExecuted = nodeType.prototype.onExecuted;
		nodeType.prototype.onExecuted = function (message) {
			onExecuted?.apply(this, arguments);
			const widget = this.widgets?.find((w) => w.name === "preview");
			if (widget) {
				widget.value = message?.text?.[0] ?? "";
			}
		};
	},
});
