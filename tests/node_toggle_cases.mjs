// Runs the real extension against a minimal graph/API boundary.
export async function runTests(source) {
	let checks = 0;
	function equal(actual, expected) {
		if (JSON.stringify(actual) !== JSON.stringify(expected)) {
			throw new Error(`Expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
		}
		checks++;
	}
	for (const middleModes of [[0], [4], [4, 4], [2]]) {
		const requests = [];
		let extension;
		const graph = { links: {}, _nodes: [], setDirtyCanvas() {}, getNodeById(id) {
			return this._nodes.find((n) => n.id === id);
		} };
		function node(id, mode, terms) {
			const n = { id, mode, title: String(id), type: "PhoenixRandomCSVTextReplace", graph,
				inputs: [{ name: "defines", link: null }], widgets: [
					{ name: "terms", value: terms }, { name: "seed", value: 0 },
					{ name: "unique", value: false }, { name: "pass_through_defines", value: false },
				] };
			graph._nodes.push(n);
			return n;
		}
		function connect(a, b) {
			graph.links[b.id] = { origin_id: a.id, origin_slot: 2 };
			b.inputs[0].link = b.id;
		}
		let previous = node(1, 0, '_DEFINE(See)_');
		for (const mode of middleModes) {
			const middle = node(previous.id + 1, mode, '_DEFINE(other)_');
			connect(previous, middle);
			previous = middle;
		}
		const last = node(previous.id + 1, 0, '_IF(See)_ _NODE(Lora)_');
		connect(previous, last);
		// Route through a virtual Get/Set-style node as well.
		const upstreamLink = graph.links[last.id];
		graph._nodes.push({ id: 99, isVirtualNode: true, getInputLink: () => upstreamLink });
		graph.links[last.id] = { origin_id: 99, origin_slot: 0 };
		const target = { id: 100, title: "Lora", mode: 4 };
		graph._nodes.push(target);
		graph._nodes.reverse(); // Deliberately opposite to dependency order.
		const app = { graph, registerExtension(e) { extension = e; },
			async graphToPrompt() { return target.mode; } };
		const api = { async fetchApi(url, options) {
			const data = JSON.parse(options.body);
			requests.push(data);
			return { async json() {
				if (data.terms === '_DEFINE(See)_') return { toggles: {}, defines: ['See'] };
				if (data.terms === '_DEFINE(other)_') return { toggles: {}, defines: ['other'] };
				return { toggles: { Lora: data.defines.includes('See') }, defines: [] };
			} };
		} };
		const code = source.replace(/^import .*;\s*$/gm, "");
		new Function("app", "api", "console", "performance", code)(
			app, api, { debug() {}, warn() {} }, { now: () => 0 });
		await extension.setup();
		const result = await app.graphToPrompt();
		const bypass = middleModes.every((mode) => mode === 4);
		equal(result, bypass ? 0 : 4);
		equal(requests.at(-1).defines, bypass ? ["See"] : middleModes[0] === 0 ? ["other"] : []);
		equal(requests.length, middleModes[0] === 0 ? 3 : 2);
	}
	// IFNOT alone must trigger the pre-queue API call too, even without
	// DEFINE/IF/NODE tags that would independently activate the resolver.
	let extension;
	const requests = [];
	const sourceNode = { id: 1, mode: 0, type: "PhoenixRandomCSVTextReplace", inputs: [],
		widgets: [{ name: "terms", value: "_IFNOT(See)_ walk" },
			{ name: "seed", value: 0 }, { name: "unique", value: false }] };
	const app = { graph: { _nodes: [sourceNode] }, registerExtension(e) { extension = e; },
		async graphToPrompt() {} };
	const api = { async fetchApi(url, options) {
		requests.push(JSON.parse(options.body));
		return { async json() { return { toggles: {}, defines: [] }; } };
	} };
	new Function("app", "api", "console", "performance", source.replace(/^import .*;\s*$/gm, ""))(
		app, api, { debug() {}, warn() {} }, { now: () => 0 });
	await extension.setup();
	await app.graphToPrompt();
	equal(requests.length, 1);
	equal(requests[0].terms, "_IFNOT(See)_ walk");
	return checks;
}
