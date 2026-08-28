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

So each field here is ambiguous without the hint and trivial to execute with it:

  name    'Last, First' vs already-display-order
  dob     day-first vs month-first (half the dates are ambiguous by construction)
  phone   national trunk prefix '(0)' kept or dropped
  amount  stored in minor units (cents) or major units
  weight  column is kilograms or pounds -- a label, not a conversion
  code    hyphens are significant or separators

Deterministic: fixed seed, greedy decoding downstream, no sampling anywhere.
"""

import random

FIELDS = ["name", "dob", "phone", "amount", "weight", "code"]

FIRST = ["Adaeze", "Tomasz", "Yuki", "Priya", "Kwame", "Ingrid", "Rafael", "Mei",
         "Oleksiy", "Fatima", "Bjorn", "Nadia", "Hiroshi", "Amara", "Dmitri", "Leila"]
LAST = ["Okonkwo", "Wisniewski", "Tanaka", "Raghunathan", "Mensah", "Bergstrom",
        "Almeida", "Zhang", "Kovalenko", "Haddad", "Lindqvist", "Petrova",
        "Yamamoto", "Diallo", "Sokolov", "Nasser"]


def make_tasks(n: int = 50, seed: int = 20260827):
    rng = random.Random(seed)
    tasks = []
    for i in range(n):
        first, last = rng.choice(FIRST), rng.choice(LAST)

        # Half the dates are ambiguous (day <= 12) so a month-first belief gives
        # a different answer; the rest are unambiguous controls.
        ambiguous = i % 2 == 0
        day = rng.randint(1, 12) if ambiguous else rng.randint(13, 28)
        month = rng.randint(1, 12)
        year = rng.randint(1955, 2005)

        cc = rng.choice(["44", "33", "49", "31"])
        area = rng.randint(10, 99)
        rest = rng.randint(1000000, 9999999)

        cents = rng.randint(1000, 999999)          # stored in minor units
        kilos = rng.randint(45, 130)               # column is kg, unlabelled
        a, b = rng.choice("abcdefgh"), rng.choice("ijklmnop")
        code_core = f"{a}{b}{rng.randint(10, 99)}{rng.choice('xyzw')}"
        code_hyph = f"{a}{b}-{rng.randint(10, 99)}-{rng.choice('xyzw')}"
        code_hyph = f"{code_core[:2]}-{code_core[2:4]}-{code_core[4:]}"

        record = {
            "name": f"{last}, {first}",
            "dob": f"{day:02d}/{month:02d}/{year}",
            "phone": f"+{cc} (0){area} {rest}",
            "amount": str(cents),
            "weight": str(kilos),
            "code": code_hyph,
        }
        expected = {
            "name": f"{first} {last}",                       # reverse the comma
            "dob": f"{year}-{month:02d}-{day:02d}",          # day-first -> ISO
            "phone": f"+{cc}{area}{rest}",                   # drop '(0)', despace
            "amount": f"{cents // 100}.{cents % 100:02d}",   # minor -> major units
            "weight": f"{kilos} kg",                         # label, no conversion
            "code": code_core.upper(),                       # hyphens are separators
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
