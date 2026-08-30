"""Task family for the v4 compounding instrument.

Six fields, every task exercises all six, each scored by exact match.

WHAT CHANGED FROM v3 AND WHY
----------------------------
v3 could not express negative per-entry effects: a pre-registered coverage gate
returned 1/12 against a threshold of 3. The diagnosed cause was that v3's wrong
entries were *implausible* — they contradicted transforms the model performs
confidently, and it simply ignored them (`w_iban` measured +0.00 against a
hint-free baseline of 1.00). Models resist implausible instructions precisely
where they are competent.

v4 abandons the requirement that a wrong entry overpower an unaided default.
Instead a store already holding the CORRECT entry admits a plausible-wrong one,
and accuracy falls where the two disagree. Two flavours, both plausible:
conditional qualifiers that agree with the correct rule except on an identifiable
subset (dob, amount, code, iban), and alternative conventions that are simply a
different defensible output format (zip, state). Neither contradicts confident
behaviour, so neither is dismissed the way v3's were.

That guarantees dynamic range by construction rather than by hoping a default
lands the right way, which is what the three previous instruments each got wrong
in a different place.

Each field therefore carries a SUBSET FLAG in the task record, so an entry's damage
can be attributed to exactly the records its qualifier misdescribes.
"""

import random

FIELDS = ["iban", "zip", "phone", "ref", "amount", "code"]

FIRST = ["Adaeze", "Tomasz", "Yuki", "Priya", "Kwame", "Ingrid", "Rafael", "Mei",
         "Oleksiy", "Fatima", "Bjorn", "Nadia", "Hiroshi", "Amara", "Dmitri", "Leila"]
LAST = ["Okonkwo", "Wisniewski", "Tanaka", "Raghunathan", "Mensah", "Bergstrom",
        "Almeida", "Zhang", "Kovalenko", "Haddad", "Lindqvist", "Petrova",
        "Yamamoto", "Diallo", "Sokolov", "Nasser"]
STATES = ["ca", "ny", "tx", "wa", "il", "ma", "az", "co", "or", "ga"]


def make_tasks(n: int = 60, seed: int = 20260829):
    """Deterministic. Each task carries `subsets`: which wrong-entry qualifiers
    misdescribe this record, so damage can be attributed rather than inferred."""
    rng = random.Random(seed)
    tasks = []
    for i in range(n):
        first, last = rng.choice(FIRST), rng.choice(LAST)

        # Leading group is 4 or 5 chars, so "four-character leading group" names a
        # real subset rather than every record.
        grp = (f"{rng.choice('ABCDEFGH')}{rng.choice('JKLMNPQR')}{rng.randint(10, 99)}"
               if rng.random() < 0.5 else
               f"{rng.choice('ABCDEFGH')}{rng.choice('JKLMNPQR')}{rng.randint(100, 999)}")
        iban_raw = f"{grp} {rng.randint(1000, 9999)} {rng.randint(1000, 9999)}"

        z = f"{rng.randint(10000, 99999)}"
        zip_split = 3 if rng.random() < 0.5 else 2      # real subset for zip qualifiers
        zip_raw = f"{z[:zip_split]} {z[zip_split:]}"

        cc = rng.choice(["44", "33", "49", "31"])
        area = rng.randint(10, 99)
        sub_n = rng.randint(1000000, 9999999)
        phone_raw = f"+{cc} (0){area} {sub_n}"

        r1, r2 = rng.choice("abcdefgh"), rng.choice("jklmnpqr")
        r3 = rng.randint(10, 99)
        ref_raw = f"{r1}{r2}/{r3}/{rng.choice('xyzw')}"
        ref_core = ref_raw.replace("/", "")
        long_area = area >= 50                      # subset for phone qualifiers
        ref_early = r1 in "abcd"                    # subset for ref qualifiers

        # Half the dates are ambiguous (day <= 12); a quarter predate 1970.
        ambiguous = i % 2 == 0
        day = rng.randint(1, 12) if ambiguous else rng.randint(13, 28)
        month = rng.randint(1, 12)
        year = rng.randint(1955, 1969) if i % 4 == 0 else rng.randint(1970, 2005)

        cents = rng.randint(1000, 999999)
        big = cents >= 100000                       # "large amounts" subset

        a, b = rng.choice("abcdefgh"), rng.choice("ijklmnop")
        core = f"{a}{b}{rng.randint(10, 99)}{rng.choice('xyzw')}"
        code_hyph = f"{core[:2]}-{core[2:4]}-{core[4:]}"
        early_letter = a in "abcd"                  # "codes beginning A-D" subset

        record = {
            "iban": iban_raw,
            "zip": zip_raw,
            "phone": phone_raw,
            "ref": ref_raw,
            "amount": str(cents),
            "code": code_hyph,
        }
        expected = {
            "iban": iban_raw.replace(" ", ""),
            "zip": zip_raw.replace(" ", ""),
            "phone": f"+{cc}{area}{sub_n}",              # strip prefix and spacing
            "ref": ref_core.upper(),                     # strip slashes, uppercase
            "amount": f"{cents // 100}.{cents % 100:02d}",
            "code": core.upper(),
        }
        # Which wrong-entry qualifiers misdescribe this record.
        subsets = {
            "phone_long_area": long_area,
            "ref_early_letter": ref_early,
            "amount_large": big,
            "code_early_letter": early_letter,
            "iban_short_group": len(grp) == 4,
            "zip_split_two": zip_split == 2,

            # Always-applicable competing transforms are flagged so the analysis
            # does not mistake them for subset entries.
            "zip_any": True,
            "phone_any": True,
            "ref_any": True,
            "amount_any": True,
            "code_any": True,
            "iban_any": True,
        }
        tasks.append({"id": i, "record": record, "expected": expected,
                      "subsets": subsets})
    return tasks


def render_record(record: dict) -> str:
    return "\n".join(f"  {k}: {v}" for k, v in record.items())


def strip_thinking(text: str) -> str:
    """Drop reasoning preambles so they cannot be mined for key=value lines."""
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
