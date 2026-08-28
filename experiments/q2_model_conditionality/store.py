"""The learned-context stores under test.

TWO stores, not one. v1 put the correct and the wrong hint for the same field in
one store; the correct hint dominated, so removing the wrong one changed nothing
and fourteen of eighteen entries measured exactly zero. That is masking, not
model-stability, and it destroys the resolution the question needs.

  Store A = 6 correct hints + 6 distractors
  Store B = 6 wrong hints   + 6 distractors

Each field therefore has exactly one hint in play at a time. Correct entries
should show positive leave-one-out effects in A, wrong entries negative effects
in B, distractors ~0 in both. Those designed signs are the instrument; Q2 does
not ask whether the models recover them, it asks whether the *measured* effect
per entry is the same across backbones. An entry that helps one backbone and
hurts another is the sign flip C3 is predicated on.

Entries are written in the flat imperative register agent memory systems actually
emit (ACE playbook bullets, ReasoningBank strategies), not as documentation.
"""

CORRECT = [
    ("c_name", "The name field is stored 'Last, First'. Emit it as 'First Last'."),
    ("c_dob", "Dates in this source are day-first: DD/MM/YYYY. Emit ISO YYYY-MM-DD."),
    ("c_phone", "Phone numbers include a national trunk prefix '(0)' after the country code. Drop it and all spacing; keep the leading '+'."),
    ("c_amount", "The amount field is stored in minor units (cents). Emit major units with two decimal places."),
    ("c_weight", "The weight column is kilograms. Emit the number followed by ' kg'."),
    ("c_code", "In the code field the hyphens are separators, not data. Emit the code without them, uppercased."),
]

WRONG = [
    ("w_name", "The name field is already in display order. Emit it unchanged."),
    ("w_dob", "Dates in this source are US format: MM/DD/YYYY. Emit ISO YYYY-MM-DD."),
    ("w_phone", "The '(0)' in a phone number is part of the subscriber number. Keep it, and keep the spacing."),
    ("w_amount", "The amount field is stored in whole major units already. Emit it unchanged."),
    ("w_weight", "The weight column is pounds. Emit the number followed by ' lb'."),
    ("w_code", "In the code field the hyphens are significant. Keep them, and keep the original lowercase."),
]

DISTRACTOR = [
    ("d_enc", "Source files are UTF-8 with a byte-order mark; strip the BOM before parsing."),
    ("d_tz", "Timestamps elsewhere in this system are UTC. Do not apply a local offset."),
    ("d_null", "Missing values appear as the literal string 'NULL' rather than an empty field."),
    ("d_order", "Downstream consumers do not depend on field order in the output."),
    ("d_dupe", "Duplicate records are deduplicated upstream, so assume each record is unique."),
    ("d_log", "Parsing failures should be logged at WARN, not ERROR."),
]

STORES = {
    "A": CORRECT + DISTRACTOR,
    "B": WRONG + DISTRACTOR,
}

CLASS_OF = ({k: "correct" for k, _ in CORRECT}
            | {k: "wrong" for k, _ in WRONG}
            | {k: "distractor" for k, _ in DISTRACTOR})

# Field each entry targets. Distractors target nothing.
TARGET_FIELD = {
    "c_name": "name", "c_dob": "dob", "c_phone": "phone",
    "c_amount": "amount", "c_weight": "weight", "c_code": "code",
    "w_name": "name", "w_dob": "dob", "w_phone": "phone",
    "w_amount": "amount", "w_weight": "weight", "w_code": "code",
}


def render(store_key: str, entry_ids) -> str:
    """Render a store as a numbered list, in its fixed canonical order."""
    kept = [(k, t) for k, t in STORES[store_key] if k in entry_ids]
    return "\n".join(f"{i}. {t}" for i, (_, t) in enumerate(kept, 1))


def ids(store_key: str):
    return [k for k, _ in STORES[store_key]]
