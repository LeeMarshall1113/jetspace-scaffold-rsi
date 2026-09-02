"""Extended candidate pool for the pre-registered degradation test.

12 correct + 30 wrong, as PREREG-degrading-candidates.md requires for 10 generations
of 3 candidates drawn without replacement.

store.py is deliberately NOT modified. Sections 4 and 6 ran against its 6/12 pool
and must stay exactly reproducible; changing an experiment's inputs under its old
name is a mistake this project already made once with the v2 A/B stores.

CORRECT holds two phrasings per field. That is not padding: real stores accumulate
near-duplicate entries, and whether a selection procedure admits both is part of what
is being measured.

WRONG holds five competing transforms per field, in the style the premise tests
validated -- each specifies a dimension of the output the correct entry leaves open
(case, separator, padding, precision) rather than appending content or stating a
carve-out, since those two forms were measured to be ignored.
"""

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import store as S  # noqa: E402

FIELDS = ["iban", "zip", "phone", "ref", "amount", "code"]

CORRECT_EXT = [
    ("c_iban",    "iban",   "Account references are stored in space-separated groups. Emit them with no spaces."),
    ("c_iban_b",  "iban",   "Remove the group spacing from account references; the groups carry no meaning."),
    ("c_zip",     "zip",    "Postcodes carry a stray internal space. Emit them with no spaces."),
    ("c_zip_b",   "zip",    "The space inside a postcode is a formatting artefact. Close it up."),
    ("c_phone",   "phone",  "Phone numbers carry a national trunk prefix in parentheses. Drop it and all spacing, keeping the leading +."),
    ("c_phone_b", "phone",  "Emit phone numbers as the country code followed by the subscriber digits, with no punctuation except the leading +."),
    ("c_ref",     "ref",    "In the ref field the slashes are separators, not data. Emit without them, uppercased."),
    ("c_ref_b",   "ref",    "Strip the slashes from ref and emit the remainder in upper case."),
    ("c_amount",  "amount", "The amount field is stored in minor units (cents). Emit major units with two decimals."),
    ("c_amount_b","amount", "Divide the amount by one hundred and emit it with exactly two decimal places."),
    ("c_code",    "code",   "In the code field hyphens are separators, not data. Emit without them, uppercased."),
    ("c_code_b",  "code",   "Remove the hyphens from code and upper-case what remains."),
]

_W = {
    "iban": [
        ("lower", "Account references are closed up with no spaces and emitted lowercased."),
        ("dash",  "Account references drop their spaces, with the groups joined by hyphens."),
        ("dot",   "Account references drop their spaces, with the groups joined by periods."),
        ("pad",   "Account references are closed up and left-padded with zeros to sixteen characters."),
        ("half",  "Account references close up, except that the leading group keeps a single space after it."),
    ],
    "zip": [
        ("pad",   "Postcodes are closed up and zero-padded to six digits."),
        ("dash",  "The internal space in a postcode is normalised to a hyphen rather than removed."),
        ("dot",   "The internal space in a postcode is normalised to a period rather than removed."),
        ("lead",  "Postcodes are closed up and any leading zeros are dropped."),
        ("suffix","Postcodes are closed up and given a four-zero extension suffix after a hyphen."),
    ],
    "phone": [
        ("dash",  "Phone numbers drop the parenthesised trunk prefix, with the remaining groups joined by hyphens rather than closed up."),
        ("zero",  "The digit inside the parentheses in a phone number is part of the subscriber number; keep it and drop only the brackets."),
        ("paren", "Phone numbers close up, but the country code is retained in parentheses."),
        ("space", "Phone numbers close up, except for a single space separating the country code."),
        ("dot",   "Phone numbers drop the trunk prefix and join the remaining groups with periods."),
    ],
    "ref": [
        ("lower", "The ref field drops its slashes and is emitted lowercased."),
        ("dash",  "In the ref field the slashes are normalised to hyphens rather than removed."),
        ("dot",   "In the ref field the slashes are normalised to periods rather than removed."),
        ("pad",   "The ref field drops its slashes, uppercased, with the numeric section padded to three digits."),
        ("space", "The ref field drops its slashes, uppercased, with the sections separated by single spaces."),
    ],
    "amount": [
        ("comma", "Amounts are stored in minor units. Emit major units using a comma as the decimal separator."),
        ("round", "Amounts are stored in minor units. Emit major units, rounding to the nearest whole unit where the amount exceeds four digits."),
        ("three", "Amounts are stored in minor units. Emit major units with three decimal places."),
        ("space", "Amounts are stored in minor units. Emit major units with a space separating thousands."),
        ("trail", "Amounts are stored in minor units. Emit major units with trailing zeros in the decimal part removed."),
    ],
    "code": [
        ("dash",  "Emit the code uppercased, retaining a single hyphen before the final character."),
        ("lower", "Emit the code with its hyphens removed, in lower case."),
        ("dot",   "In the code field the hyphens are normalised to periods rather than removed."),
        ("space", "In the code field the hyphens are normalised to single spaces rather than removed."),
        ("keep2", "Emit the code uppercased, retaining the first hyphen and removing the second."),
    ],
}
WRONG_EXT = [(f"p_{fld}_{tag}", fld, f"{fld}_any", txt)
             for fld, vs in _W.items() for tag, txt in vs]

TEXT = dict([(k, t) for k, _, t in CORRECT_EXT]
            + [(k, t) for k, _, _, t in WRONG_EXT]
            + list(S.DISTRACTOR) + list(S.FILLER))
CLASS_OF = ({k: "correct" for k, _, _ in CORRECT_EXT}
            | {k: "wrong" for k, _, _, _ in WRONG_EXT}
            | {k: "distractor" for k, _ in S.DISTRACTOR}
            | {k: "filler" for k, _ in S.FILLER})
TARGET_FIELD = ({k: f for k, f, _ in CORRECT_EXT}
                | {k: f for k, f, _, _ in WRONG_EXT})

CORRECT_IDS = [k for k, _, _ in CORRECT_EXT]
WRONG_IDS = [k for k, _, _, _ in WRONG_EXT]
POOL = CORRECT_IDS + WRONG_IDS
BACKGROUND = [k for k, _ in S.DISTRACTOR[:6]]


def build(entry_ids, pad_to=None):
    """Render a store, padded with filler so every comparison is size-matched."""
    ids = list(entry_ids)
    if pad_to is not None:
        if len(ids) > pad_to:
            raise ValueError(f"store of {len(ids)} exceeds pad_to={pad_to}")
        need = pad_to - len(ids)
        fill = [k for k, _ in S.FILLER] + [k for k, _ in S.DISTRACTOR[6:]]
        if need > len(fill):
            raise ValueError(f"need {need} filler, have {len(fill)}")
        ids += fill[:need]
    return "\n".join(f"{i}. {TEXT[k]}" for i, k in enumerate(ids, 1))
