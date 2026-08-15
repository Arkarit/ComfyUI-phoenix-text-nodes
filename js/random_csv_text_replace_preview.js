import { app } from "../../../scripts/app.js";

// Locks the node's "preview" widget to read-only and fills it with the
// result text after each execution. Also manages the "text" input widget's
// growable height so that resizing the node vertically only grows the
// preview widget, not both multiline widgets equally (ComfyUI's default
// DOM-widget behavior when a node has more than one growable textarea) —
// and collapses "text" to zero height while it's link-driven, since the
// DOM textarea otherwise still reserves its layout space even though it's
// not shown.
const TEXT_WIDGET_MAX_HEIGHT = 120;

function isTextInputLinked(node) {
	const input = node.inputs?.find((i) => i.name === "text");
	return input?.link != null;
}

function updateTextWidgetHeight(node) {
	const textWidget = node.widgets?.find((w) => w.name === "text");
	if (!textWidget?.options) {
		return;
	}
	if (isTextInputLinked(node)) {
		textWidget.options.getMinHeight = () => 0;
		textWidget.options.getMaxHeight = () => 0;
	} else {
		textWidget.options.getMinHeight = undefined;
		textWidget.options.getMaxHeight = () => TEXT_WIDGET_MAX_HEIGHT;
	}
	requestAnimationFrame(() => {
		// Grow to fit the new min size if needed, but never shrink — this
		// must not clobber a saved/user-set node size (e.g. right after a
		// workflow loads and onConfigure already restored it).
		const minSize = node.computeSize();
		if (node.size[0] < minSize[0] || node.size[1] < minSize[1]) {
			node.setSize([Math.max(node.size[0], minSize[0]), Math.max(node.size[1], minSize[1])]);
		}
		node.graph?.setDirtyCanvas(true, true);
	});
}

app.registerExtension({
	name: "PhoenixRandomCSVTextReplace.Preview",
	async beforeRegisterNodeDef(nodeType, nodeData, app) {
		if (nodeData.name !== "PhoenixRandomCSVTextReplace") {
			return;
		}

		const onNodeCreated = nodeType.prototype.onNodeCreated;
		nodeType.prototype.onNodeCreated = function () {
			onNodeCreated?.apply(this, arguments);

			updateTextWidgetHeight(this);

			const widget = this.widgets?.find((w) => w.name === "preview");
			if (widget?.inputEl) {
				widget.inputEl.readOnly = true;
				widget.inputEl.style.opacity = 0.6;
			}
		};

		const onConnectionsChange = nodeType.prototype.onConnectionsChange;
		nodeType.prototype.onConnectionsChange = function () {
			onConnectionsChange?.apply(this, arguments);
			updateTextWidgetHeight(this);
		};

		const onConfigure = nodeType.prototype.onConfigure;
		nodeType.prototype.onConfigure = function () {
			onConfigure?.apply(this, arguments);
			requestAnimationFrame(() => updateTextWidgetHeight(this));
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
