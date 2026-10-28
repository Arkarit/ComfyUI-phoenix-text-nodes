"""Pure node logic tests; no running ComfyUI or third-party packages needed."""
import asyncio
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load_module(name):
    spec = importlib.util.spec_from_file_location(f"phoenix_review.{name}", ROOT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Only the server registration/response boundary is stubbed. Parsing, seeded
# selection, node execution and the endpoint handler use the actual source.
package = types.ModuleType("phoenix_review")
package.__path__ = [str(ROOT)]
server = types.SimpleNamespace(PromptServer=types.SimpleNamespace(instance=
    types.SimpleNamespace(routes=types.SimpleNamespace(post=lambda path: lambda fn: fn))))
with patch.dict(sys.modules, {
    "phoenix_review": package,
    "server": server,
    "aiohttp": types.SimpleNamespace(web=types.SimpleNamespace(json_response=lambda data: data)),
}):
    csv = load_module("random_csv_text_replace")
flex = load_module("flex_concat_v2")


class FlexTests(unittest.TestCase):
    def test_complete_indices_and_missing_sockets(self):
        result = flex.PhoenixFlexConcatV2().run(
            100, "$1 / $10 / $100 / $2", "$", input_1="eins", input_10="zehn", input_100=100)
        self.assertEqual(result, ("eins / zehn / 100 / $2",))

    def test_inserted_text_is_literal(self):
        self.assertEqual(flex.PhoenixFlexConcatV2().run(
            2, "$1 $2", "$", input_1="$2", input_2="two"), ("$2 two",))

    def test_custom_prefix_and_empty_template(self):
        node = flex.PhoenixFlexConcatV2()
        self.assertEqual(node.run(2, ".*1 .*2", ".*", input_1="a"), ("a .*2",))
        self.assertEqual(node.run(3, "", "$", input_1="a", input_3=0), ("a\n0",))


class CSVTests(unittest.TestCase):
    def run_node(self, terms, incoming=None, forward=True, seed=0,
                 seed_offset=0, row_seed_step=0):
        return csv.PhoenixRandomCSVTextReplace().replace(
            "$1|$2|$3", "$", 1, terms, seed,
            defines=incoming, pass_through_defines=forward,
            seed_offset=seed_offset, row_seed_step=row_seed_step)["result"]

    def test_redefinition_survives_disabled_forwarding(self):
        result = self.run_node('_IF(See)_ boat _DEFINE(See neu)_', {"See", "alt"}, False)
        self.assertEqual(result[0], "boat|$2|$3")
        self.assertEqual(result[2], frozenset({"See", "neu"}))

    def test_incoming_definitions_only_forwarded_when_enabled(self):
        self.assertEqual(self.run_node("plain", {"See"})[2], frozenset({"See"}))
        self.assertEqual(self.run_node("plain", {"See"}, False)[2], frozenset())

    def test_conditions_and_empty_row_indices(self):
        cases = [
            ('See _DEFINE(See)_\nfallback,_IF(See)_ boat', None, "See|boat|$3"),
            ('fallback,_IF(See)_ boat', None, "fallback|$2|$3"),
            ('_IF(missing)_ hidden\nnext', None, "|next|$3"),
            ('fallback,_IF(a b)_ yes', {"a", "b"}, "yes|$2|$3"),
            ('fallback,_IF(a b)_ yes', {"a"}, "fallback|$2|$3"),
            ('fallback,_IF(a)_ _IF(b)_ yes', {"b"}, "yes|$2|$3"),
            ('rain _DEFINE("nass, kalt")_\nfallback,_IF("nass, kalt")_ yes', None, "rain|yes|$3"),
        ]
        for terms, incoming, expected in cases:
            with self.subTest(terms=terms, incoming=incoming):
                self.assertEqual(self.run_node(terms, incoming)[0], expected)

    def test_only_picked_candidate_defines_names(self):
        self.assertEqual(self.run_node('_0_ no _DEFINE(no)_,yes _DEFINE(yes)_')[2], {"yes"})

    def test_ifnot_conditions(self):
        cases = [
            ('fallback,_IFNOT(See)_ walk', None, 'walk|$2|$3'),
            ('fallback,_IFNOT(See)_ walk', {'See'}, 'fallback|$2|$3'),
            ('_IF(See)_ boat,_IFNOT(See)_ walk', {'See'}, 'boat|$2|$3'),
            ('_IF(See)_ boat,_IFNOT(See)_ walk', None, 'walk|$2|$3'),
            ('_IFNOT(See)_ walk\nnext', {'See'}, '|next|$3'),
            ('fallback,_IFNOT(a b)_ yes', None, 'yes|$2|$3'),
            ('fallback,_IFNOT(a b)_ yes', {'a'}, 'fallback|$2|$3'),
            ('fallback,_IFNOT(a)_ _IFNOT(b)_ yes', {'a'}, 'yes|$2|$3'),
            ('fallback,_IF(a)_ _IFNOT(b)_ yes', {'b'}, 'fallback|$2|$3'),
            ('fallback,_IF(a)_ _IFNOT(b)_ yes', {'a', 'b'}, 'yes|$2|$3'),
            ('fallback,_IF(a)_ _IFNOT(b)_ yes', None, 'yes|$2|$3'),
            ('rain _DEFINE(See)_\n_IFNOT(See)_ walk\nlast', None, 'rain||last'),
            ('_IFNOT("nass, kalt")_ "dry, warm"', None, 'dry, warm|$2|$3'),
            ('_IFNOT("nass, kalt")_ "dry, warm"', {'nass, kalt'}, '|$2|$3'),
        ]
        for terms, incoming, expected in cases:
            with self.subTest(terms=terms, incoming=incoming):
                self.assertEqual(self.run_node(terms, incoming)[0], expected)

    def test_ifnot_endpoint_matches_execution(self):
        terms = '_IFNOT(See)_ walk _DEFINE(Land)_ _NODE(Lora)_,_IF(See)_ boat _NOTNODE(Lora)_'
        for incoming in ([], ['See']):
            for seed in range(20):
                async def json():
                    return dict(terms=terms, seed=seed, defines=incoming, pass_through=False)
                response = asyncio.run(csv._random_csv_node_toggles_route(types.SimpleNamespace(json=json)))
                result = self.run_node(terms, incoming, False, seed)
                self.assertEqual(response['toggles'], {'Lora': not bool(incoming)})
                self.assertEqual(set(response['defines']), result[2])
                self.assertEqual(result[1], 'boat' if incoming else 'walk')

    def test_continuations_comments_and_none(self):
        terms = '_0_ red\n# comment\n\n,blue\n_NONE_\nlast'
        self.assertEqual(self.run_node(terms)[:2], ("blue||last", "blue\n\nlast"))

    def test_unique_rows_and_exhaustion(self):
        for seed in range(20):
            result = self.run_node('_UNIQUE_,a,b\n_UNIQUE_,a,b\n_UNIQUE_,a,b', seed=seed)[1].splitlines()
            self.assertEqual(set(result[:2]), {"a", "b"})
            self.assertIn(result[2], {"a", "b"})

    def test_chance_quotes_and_placeholder_literals(self):
        self.assertEqual(self.run_node('"blue, thick" _CHANCE(1 "with scars")_')[1], "blue, thick with scars")
        self.assertEqual(csv._substitute_placeholders("$1/$10/$11", "$", 1,
            ["$10"] + ["x"] * 8 + ["ten"]), "$10/ten/$11")

    def test_endpoint_and_execution_agree(self):
        terms = 'fallback _NOTNODE(Lora)_,_IF(See)_ boat _DEFINE(See)_ _NODE(Lora)_'
        for forward in (False, True):
            for seed in range(20):
                data = dict(terms=terms, seed=seed, unique=False, defines=["See", "old"], pass_through=forward)
                async def json():
                    return data
                response = asyncio.run(csv._random_csv_node_toggles_route(types.SimpleNamespace(json=json)))
                result = self.run_node(terms, data["defines"], forward, seed)
                self.assertEqual(response["toggles"], {"Lora": True})
                self.assertEqual(set(response["defines"]), result[2])


class SeedOffsetTests(unittest.TestCase):
    """Defaults must be byte-for-byte the legacy single-stream behavior."""

    run_node = CSVTests.run_node

    TERMS = 'goose,wizard,astronaut\nmoped,unicycle,tank\n"a forest, at night",downtown,the moon'

    def test_defaults_match_the_pre_offset_reference_values(self):
        # Anchored against the original implementation before the offsets
        # existed; these are the values an existing workflow produces today.
        self.assertEqual(self.run_node(self.TERMS)[1], "astronaut\ntank\ndowntown")
        self.assertEqual(self.run_node(self.TERMS, seed_offset=0, row_seed_step=0)[1],
                         "astronaut\ntank\ndowntown")

    def test_seed_offset_shifts_the_start_and_is_a_plain_seed_shift(self):
        self.assertEqual(self.run_node(self.TERMS, seed_offset=1)[1], "goose\ntank\nthe moon")
        # seed s with offset 0 == seed 0 with offset s, for every s.
        for s in range(30):
            self.assertEqual(self.run_node(self.TERMS, seed=s)[1],
                             self.run_node(self.TERMS, seed_offset=s)[1])

    def test_row_step_zero_keeps_the_shared_stream(self):
        self.assertEqual(self.run_node("a,b,c\na,b,c\na,b,c", row_seed_step=0)[1],
                         "c\nc\nb")

    def test_row_step_above_zero_gives_each_row_its_own_rng(self):
        self.assertEqual(self.run_node("a,b,c\na,b,c\na,b,c", row_seed_step=1)[1],
                         "c\nc\nc")
        # A row's pick depends only on its slot, not on what earlier rows
        # had to choose from.
        for seed in range(20):
            self.assertEqual(
                self.run_node("a,b,c\na,b,c\nx,y,z", seed=seed, row_seed_step=1)[1].splitlines()[2],
                self.run_node("q\nq,r,s,t,u\nx,y,z", seed=seed, row_seed_step=1)[1].splitlines()[2])

    def test_row_slots_do_not_overlap_across_seeds_or_steps(self):
        # An additive seed + row * step would make row 1 at seed s replay
        # row 0 at seed s + 1, and step 2 replay every other row of step 1.
        terms = "\n".join([",".join(f"t{i}" for i in range(100))] * 3)
        picks = {(seed, step): self.run_node(terms, seed=seed, row_seed_step=step)[1].splitlines()
                 for seed in range(40) for step in (1, 2)}
        replays = sum(picks[seed, 1][1] == picks[seed + 1, 1][0] for seed in range(39))
        replays += sum(picks[seed, 2][1] == picks[seed, 1][2] for seed in range(40))
        self.assertLess(replays, 5)

    def test_row_index_counts_processed_rows_not_draws_consumed(self):
        # Row 1 here is gated to nothing, so it consumes no draw at all.
        # Under the shared stream that shifts row 2's position; with a step
        # it can't, because row 2 owns its own slot.
        drew = self.run_node("a,b,c\nx,y,z", seed=1, row_seed_step=0)[1].splitlines()[1]
        skipped = self.run_node("_IF(missing)_ hidden\nx,y,z", seed=1, row_seed_step=0)[1].splitlines()[1]
        self.assertNotEqual(drew, skipped)
        for terms in ("a,b,c\nx,y,z", "_IF(missing)_ hidden\nx,y,z"):
            self.assertEqual(self.run_node(terms, seed=1, row_seed_step=1)[1].splitlines()[1], "y")

    def test_comment_and_blank_lines_do_not_shift_a_row_index(self):
        for terms in ("x,y,z\nx,y,z", "x,y,z\n# note\nx,y,z", "x,y,z\n\nx,y,z"):
            self.assertEqual(self.run_node(terms, row_seed_step=1)[1], "z\nz")

    def test_chance_blocks_use_the_row_rng_not_the_shared_one(self):
        # Same candidate twice: under the shared stream the second row lands
        # on a different draw than the first; with a step each row resolves
        # its own block from its own rng.
        self.assertEqual(self.run_node("red _CHANCE(.2 a .3 b)_\nred _CHANCE(.2 a .3 b)_",
                                       row_seed_step=0)[1], "red\nred b")
        self.assertEqual(self.run_node("red _CHANCE(.2 a .3 b)_\nred _CHANCE(.2 a .3 b)_",
                                       row_seed_step=1)[1], "red b\nred")

    def test_endpoint_and_execution_agree_with_offsets(self):
        terms = ('a _DEFINE(See)_ _NODE(Lora)_,b _NOTNODE(Lora)_\n'
                 '_IF(See)_ boat _NODE(Lora)_,car')
        # seed 1 is the case where the offsets actually change the outcome,
        # so agreement can't be satisfied by both paths agreeing on nothing.
        cases = [
            ([], 0, 0, {"Lora": True}, {"See"}),
            ([], 5, 1, {"Lora": False}, set()),
            (["See"], 0, 0, {"Lora": True}, {"See"}),
            (["See"], 5, 1, {"Lora": True}, set()),
        ]
        for incoming, offset, step, expected_toggles, expected_defines in cases:
            data = dict(terms=terms, seed=1, unique=False, defines=incoming,
                        pass_through=False, seed_offset=offset, row_seed_step=step)
            async def json():
                return data
            response = asyncio.run(csv._random_csv_node_toggles_route(types.SimpleNamespace(json=json)))
            result = self.run_node(terms, incoming, False, 1, offset, step)
            self.assertEqual(response["toggles"], expected_toggles)
            self.assertEqual(set(response["defines"]), expected_defines)
            self.assertEqual(set(response["defines"]), result[2])

    def test_endpoint_defaults_stay_the_legacy_path(self):
        data = dict(terms="_NODE(Lora)_ a,b", seed=0, unique=False, defines=[])
        async def json():
            return data
        response = asyncio.run(csv._random_csv_node_toggles_route(types.SimpleNamespace(json=json)))
        # Row picks 'b', which carries no tag, so the row default applies:
        # a name mentioned only via _NODE elsewhere in the row is bypassed.
        self.assertEqual(response["toggles"], {"Lora": False})
        self.assertEqual(response["defines"], [])


if __name__ == "__main__":
    unittest.main()
