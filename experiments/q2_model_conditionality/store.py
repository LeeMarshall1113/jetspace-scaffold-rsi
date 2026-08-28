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

# OBVIOUS-field hints (email, zip, state): the correct hint restates what the
# model does anyway, so it should measure near zero. The wrong hint contradicts a
# default the model gets right, which is what makes a negative effect expressible.
# ARBITRARY-field hints (dob, amount, code): the reverse -- correct hints carry
# most of the value, wrong hints have little to destroy.
CORRECT = [
    ("c_iban", "Account references are stored in space-separated groups. Emit them with no spaces."),
    ("c_zip", "Postcodes are stored with a stray internal space. Emit them with no spaces."),
    ("c_state", "State codes are two-letter abbreviations. Emit them uppercased."),
    ("c_dob", "Dates in this source are day-first: DD/MM/YYYY. Emit ISO YYYY-MM-DD."),
    ("c_amount", "The amount field is stored in minor units (cents). Emit major units with two decimal places."),
    ("c_code", "In the code field the hyphens are separators, not data. Emit the code without them, uppercased."),
]

WRONG = [
    ("w_iban", "The group spacing in an account reference is significant and must be preserved exactly."),
    ("w_zip", "The space inside a postcode is a significant district separator. Keep it."),
    ("w_state", "State codes are stored lowercase by convention. Emit them lowercased."),
    ("w_dob", "Dates in this source are US format: MM/DD/YYYY. Emit ISO YYYY-MM-DD."),
    ("w_amount", "The amount field is stored in whole major units already. Emit it unchanged."),
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

# ---------------------------------------------------------------- store sets
#
# v2 (A/B): all-correct vs all-wrong. Measured cleanly in one direction and
# floored in the other -- see RESULTS.md. The cause was NOT a floor in the naive
# sense. Six same-direction wrong hints make the model adopt a coherent
# "preserve the raw formatting" stance, and that stance survives removing any
# single hint: with w_phone dropped, Qwen2.5-Coder-3B still emitted
# '+31%20(0)%2015%207814226' rather than reverting to its 0.96-accurate default.
# So a wrong entry's leave-one-out effect measured ~0 because its neighbours
# were doing its job. Cross-entry interference, not absence of headroom.
#
# v3 (M1/M2): each field gets exactly one hint, and the correct/wrong assignment
# alternates by field, so no coherent global stance can form. Removing a wrong
# hint now leaves a majority-correct context, and the model falls back to its own
# default for that field -- which is what makes a negative effect expressible.
# The two stores are complementary, so every field is measured in both directions
# across the pair.

_BY_ID = dict(CORRECT + WRONG + DISTRACTOR)


def _mixed(correct_fields):
    """One hint per field: correct for the named fields, wrong for the rest."""
    out = []
    for f in ("iban", "zip", "state", "dob", "amount", "code"):
        eid = f"{'c' if f in correct_fields else 'w'}_{f}"
        out.append((eid, _BY_ID[eid]))
    return out + DISTRACTOR


M1 = _mixed({"iban", "state", "amount"})    # wrong on zip, dob, code
M2 = _mixed({"zip", "dob", "code"})         # wrong on iban, state, amount

# The v2 A/B stores are deliberately NOT defined here. Their entry ids referred to
# fields (name, phone, weight) that no longer exist, so keeping the names alive
# would silently run a DIFFERENT experiment under an old label -- the same class of
# bug that has already cost one full run today. v2 is reproducible at commit
# dc15ee7, and its raw data and findings are committed under results/ and
# RESULTS.md.
STORES = {"M1": M1, "M2": M2}
STORE_SETS = {"mixed": ("M1", "M2")}

CLASS_OF = ({k: "correct" for k, _ in CORRECT}
            | {k: "wrong" for k, _ in WRONG}
            | {k: "distractor" for k, _ in DISTRACTOR})

# Field each entry targets. Distractors target nothing.
TARGET_FIELD = {
    "c_iban": "iban", "c_zip": "zip", "c_state": "state",
    "c_dob": "dob", "c_amount": "amount", "c_code": "code",
    "w_iban": "iban", "w_zip": "zip", "w_state": "state",
    "w_dob": "dob", "w_amount": "amount", "w_code": "code",
}


def render(store_key: str, entry_ids) -> str:
    """Render a store as a numbered list, in its fixed canonical order."""
    kept = [(k, t) for k, t in STORES[store_key] if k in entry_ids]
    return "\n".join(f"{i}. {t}" for i, (_, t) in enumerate(kept, 1))


def ids(store_key: str):
    return [k for k, _ in STORES[store_key]]
