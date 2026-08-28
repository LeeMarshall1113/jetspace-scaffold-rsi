"""Task family for Q2: messy-record normalisation, knowledge-gated.

Six fields, every task exercises all six, each scored by exact match -- six
binary outcomes per generation.

DESIGN CONSTRAINT (learned from v1, see README): every field must be gated on
*knowing which convention applies*, never on execution difficulty. v1 used a
pounds->kg conversion and European decimal separators; a 3B model knew the rule
and still failed the arithmetic, flooring three of six fields at zero and
destroying the measurement. An entry whose field the model cannot execute has an
effect size of zero on every backbone, which is a floor artefact, not evidence
of model-stability.

Every field is trivial to execute; what varies is whether the model can know the
convention unaided. See the OBVIOUS / ARBITRARY split below -- that split is what
lets a wrong entry show a NEGATIVE effect, which earlier versions could not
express at all.

  iban    space-separated groups -- strip them (obvious)
  zip     stray internal space -- strip it (obvious)
  state   two-letter code -- uppercase it (obvious)
  dob     day-first vs month-first (arbitrary; half the dates are ambiguous)
  amount  stored in minor units (cents) or major units (arbitrary)
  code    hyphens significant or separators (arbitrary)

Deterministic: fixed seed, greedy decoding downstream, no sampling anywhere.
"""

import random

FIELDS = ["iban", "zip", "state", "dob", "amount", "code"]

# Two field classes, and the split is what gives wrong entries somewhere to fall.
#
# OBVIOUS  (iban, zip, state): the expected output is the canonical transform any
#          model produces unprompted, so hint-free accuracy is high. A correct hint
#          adds little; a WRONG hint has correct behaviour to destroy, which is the
#          only way a negative effect becomes expressible.
# ARBITRARY (dob, amount, code): the convention cannot be guessed, so hint-free
#          accuracy is ~0. A correct hint is worth a lot; a wrong hint costs nothing
#          because there was nothing to lose.
#
# The OBVIOUS transform must be INTERNAL, not boundary whitespace: parse_output
# calls .strip() on every value, so leading/trailing space is invisible to
# scoring. An email lowercase+trim field was tried and failed at 0.00 unaided --
# models preserve case, and the trim half could not be measured at all.
#
# v3a used six arbitrary fields. Every hint-free baseline sat at ~0, so no wrong
# entry could show a negative effect no matter how the store was arranged -- the
# instrument was floored by the TASK design, not the store design.
OBVIOUS = {"iban", "zip", "state"}
ARBITRARY = {"dob", "amount", "code"}

FIRST = ["Adaeze", "Tomasz", "Yuki", "Priya", "Kwame", "Ingrid", "Rafael", "Mei",
         "Oleksiy", "Fatima", "Bjorn", "Nadia", "Hiroshi", "Amara", "Dmitri", "Leila"]
LAST = ["Okonkwo", "Wisniewski", "Tanaka", "Raghunathan", "Mensah", "Bergstrom",
        "Almeida", "Zhang", "Kovalenko", "Haddad", "Lindqvist", "Petrova",
        "Yamamoto", "Diallo", "Sokolov", "Nasser"]


STATES = ["ca", "ny", "tx", "wa", "il", "ma", "az", "co", "or", "ga"]


def make_tasks(n: int = 50, seed: int = 20260827):
    rng = random.Random(seed)
    tasks = []
    for i in range(n):
        first, last = rng.choice(FIRST), rng.choice(LAST)

        # --- OBVIOUS fields: canonical transform, high hint-free accuracy ---
        grp = f"{rng.choice('ABCDEFGH')}{rng.choice('JKLMNPQR')}{rng.randint(10,99)}"
        iban_raw = f"{grp} {rng.randint(1000,9999)} {rng.randint(1000,9999)}"
        iban_out = iban_raw.replace(" ", "")

        zip_raw = f"{rng.randint(10000, 99999)}"
        zip_raw = f"{zip_raw[:3]} {zip_raw[3:]}"          # stray internal space
        zip_out = zip_raw.replace(" ", "")

        st = rng.choice(STATES)
        state_raw, state_out = st, st.upper()

        # --- ARBITRARY fields: convention cannot be guessed, ~0 unaided ---
        ambiguous = i % 2 == 0
        day = rng.randint(1, 12) if ambiguous else rng.randint(13, 28)
        month = rng.randint(1, 12)
        year = rng.randint(1955, 2005)

        cents = rng.randint(1000, 999999)
        a, b = rng.choice("abcdefgh"), rng.choice("ijklmnop")
        core = f"{a}{b}{rng.randint(10, 99)}{rng.choice('xyzw')}"
        code_hyph = f"{core[:2]}-{core[2:4]}-{core[4:]}"

        record = {
            "iban": iban_raw,
            "zip": zip_raw,
            "state": state_raw,
            "dob": f"{day:02d}/{month:02d}/{year}",
            "amount": str(cents),
            "code": code_hyph,
        }
        expected = {
            "iban": iban_out,                                # strip inner spaces
            "zip": zip_out,                                  # strip inner space
            "state": state_out,                              # uppercase code
            "dob": f"{year}-{month:02d}-{day:02d}",          # day-first -> ISO
            "amount": f"{cents // 100}.{cents % 100:02d}",   # minor -> major units
            "code": core.upper(),                            # hyphens are separators
        }
        tasks.append({"id": i, "ambiguous_date": ambiguous,
                      "record": record, "expected": expected})
    return tasks


def render_record(record: dict) -> str:
    return "\n".join(f"  {k}: {v}" for k, v in record.items())


def strip_thinking(text: str) -> str:
    """Drop reasoning preambles so they cannot be mined for key=value lines.

    Handles both the tagged form (<think>...</think>) and the untagged
    'Thinking Process:' prose that Qwen3.5 emits. Where a closing tag exists we
    keep only what follows it; an unterminated block means the model never
    reached an answer, and the empty parse is the correct outcome.
    """
    low = text.lower()
    if "</think>" in low:
        return text[low.rindex("</think>") + len("</think>"):]
    if "<think>" in low:
        return ""
    for marker in ("thinking process:", "thought process:"):
        if low.startswith(marker):
            return ""
    return text


def parse_output(text: str) -> dict:
    """Pull 'key=value' lines out of a completion. Last occurrence wins."""
    text = strip_thinking(text)
    out = {}
    for line in text.splitlines():
        line = line.strip().lstrip("-*`# ").strip()
        if "=" not in line:
            continue
        k, _, v = line.partition("=")
        k = k.strip().lower()
        if k in FIELDS:
            out[k] = v.strip().strip('"\'`,')
    return out


def score(parsed: dict, expected: dict) -> dict:
    return {f: int(parsed.get(f, "") == expected[f]) for f in FIELDS}
