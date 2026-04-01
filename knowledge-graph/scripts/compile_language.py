"""
Compile language graph YAML nodes into a JSON cache for the lexer/parser.

YAML is the source of truth (provenance, human-readable).
JSON is what the solver reads at runtime (fast, flat).

Usage:
    python knowledge-graph/scripts/compile_language.py
    # writes knowledge-graph/compiled/language.json
"""

import json
import re
import yaml
from pathlib import Path

NODES_DIR = Path(__file__).parent.parent / "nodes" / "language"
OUTPUT_DIR = Path(__file__).parent.parent / "compiled"


def load_yaml(filename: str) -> dict:
    with open(NODES_DIR / filename) as f:
        return yaml.safe_load(f)


def compile_all():
    compiled = {}

    # L02: Notation rules
    data = load_yaml("L02-notation.yaml")
    compiled["notations"] = []
    for n in data["notations"]:
        # Validate the regex compiles
        try:
            re.compile(n["pattern"])
        except re.error as e:
            print(f"  WARNING: bad pattern in {n['id']}: {e}")
            continue
        compiled["notations"].append({
            "id": n["id"],
            "symbol": n["symbol"],
            "position": n["position"],
            "token_type": n["resolves_to"]["token_type"],
            "unit": n["resolves_to"].get("unit"),
            "scale": n["resolves_to"].get("scale"),
            "operation": n["resolves_to"].get("operation"),
            "pattern": n["pattern"],
        })

    # L03: Number words
    data = load_yaml("L03-number-words.yaml")
    compiled["number_words"] = data["number_words"]

    # L04: Multipliers
    data = load_yaml("L04-multipliers.yaml")
    compiled["scale_multipliers"] = data["scale_multipliers"]
    compiled["unit_multipliers"] = data["unit_multipliers"]

    # L05: References
    data = load_yaml("L05-references.yaml")
    compiled["references"] = []
    for r in data["references"]:
        try:
            re.compile(r["pattern"])
        except re.error as e:
            print(f"  WARNING: bad pattern in {r['id']}: {e}")
            continue
        compiled["references"].append({
            "id": r["id"],
            "resolves_to": r["resolves_to"],
            "pattern": r["pattern"],
            "captures": r.get("captures"),
            "multiplier_words": r.get("multiplier_words", False),
        })

    # L06: Rate indicators
    data = load_yaml("L06-rate-indicators.yaml")
    compiled["rate_indicators"] = [
        {"word": r["word"], "position": r["position"]}
        for r in data["rate_indicators"]
    ]

    # L07: Pair semantics
    data = load_yaml("L07-pair-semantics.yaml")
    compiled["pair_is_one_unit"] = data["pair_is_one_unit"]
    compiled["default_pair_value"] = data["default_pair_value"]

    # L08: Stop words
    data = load_yaml("L08-stop-words.yaml")
    compiled["stop_words"] = data["stop_words"]

    # L09: Verb-operation mappings
    data = load_yaml("L09-verb-operations.yaml")
    compiled["verb_operations"] = {}
    compiled["synset_operations"] = {}
    compiled["verb_index"] = {}
    for op_id, op_data in data["operations"].items():
        compiled["verb_operations"][op_id] = {
            "name": op_data["name"],
            "identity": op_data["identity"],
            "commutative": op_data["commutative"],
            "inverse": op_data["inverse"],
        }
        for synset in op_data.get("synsets", []):
            compiled["synset_operations"][synset] = op_id
        for verb in op_data.get("verbs", []):
            compiled["verb_index"][verb] = op_id

    # L10: Question phrases
    data = load_yaml("L10-question-phrases.yaml")
    compiled["question_triggers"] = [
        {"phrase": q["phrase"],
         "question_type": q["question_type"],
         "default_unit": q.get("default_unit")}
        for q in data["question_triggers"]
    ]

    # L11: Semantic fields
    data = load_yaml("L11-semantic-fields.yaml")
    compiled["semantic_fields"] = {}
    for field_name, field_data in data["fields"].items():
        entry = {"words": field_data["words"]}
        if "values" in field_data:
            entry["values"] = field_data["values"]
        compiled["semantic_fields"][field_name] = entry

    # L12: Aggregation cues
    data = load_yaml("L12-aggregation-cues.yaml")
    compiled["aggregation_cues"] = {}
    for agg_type, agg_data in data["aggregation_types"].items():
        compiled["aggregation_cues"][agg_type] = agg_data["words"]

    # L13: Comparatives
    data = load_yaml("L13-comparatives.yaml")
    compiled["comparatives"] = {}
    for direction, dir_data in data["comparatives"].items():
        compiled["comparatives"][direction] = {
            "words": dir_data["words"],
            "operation": dir_data["operation"],
        }

    # L14: World constants
    data = load_yaml("L14-world-constants.yaml")
    compiled["world_constants"] = []
    for c in data["constants"]:
        for v in c["values"]:
            compiled["world_constants"].append({
                "word": c["word"],
                "value": v["value"],
                "unit": v.get("unit", ""),
            })

    # L15: Unit cooccurrence rules
    data = load_yaml("L15-unit-cooccurrence.yaml")
    compiled["unit_cooccurrence"] = [
        {"unit_a": r["unit_a"], "unit_b": r["unit_b"],
         "value": r["value"], "result_unit": r["result_unit"]}
        for r in data["cooccurrence_rules"]
    ]

    # L16: Recipient nouns
    data = load_yaml("L16-recipient-nouns.yaml")
    compiled["recipient_nouns"] = data["recipient_nouns"]

    # Write
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / "language.json"
    with open(output_path, "w") as f:
        json.dump(compiled, f, indent=2)

    # Stats
    print(f"Compiled language graph to {output_path}")
    print(f"  Notations:     {len(compiled['notations'])}")
    print(f"  Number words:  {len(compiled['number_words'])}")
    print(f"  Scale mult:    {len(compiled['scale_multipliers'])}")
    print(f"  Unit mult:     {len(compiled['unit_multipliers'])}")
    print(f"  References:    {len(compiled['references'])}")
    print(f"  Rate indicators: {len(compiled['rate_indicators'])}")
    print(f"  Pair exceptions: {len(compiled['pair_is_one_unit'])}")
    print(f"  Stop words:    {len(compiled['stop_words'])}")
    print(f"  Synset maps:   {len(compiled['synset_operations'])}")
    print(f"  Verb index:    {len(compiled['verb_index'])}")
    print(f"  Question trig: {len(compiled['question_triggers'])}")
    print(f"  Semantic flds: {len(compiled['semantic_fields'])}")
    print(f"  Aggregation:   {len(compiled['aggregation_cues'])}")
    print(f"  Comparatives:  {len(compiled['comparatives'])}")
    print(f"  World consts:  {len(compiled['world_constants'])}")
    print(f"  Unit cooccur:  {len(compiled['unit_cooccurrence'])}")
    print(f"  Recipient ns:  {len(compiled['recipient_nouns'])}")


if __name__ == "__main__":
    compile_all()
