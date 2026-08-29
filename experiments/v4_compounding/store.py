"""v4 candidate pool and store construction.

POOL: 6 correct + 12 plausible-wrong (two variants per field) + 24 distractors = 42.
Large enough for several generations of batched admission in the compounding loop,
which 12 entries was not.

WRONG ENTRIES COME IN TWO PLAUSIBLE FLAVOURS, neither of which contradicts confident
behaviour the way v3's did:

  CONDITIONAL QUALIFIER (dob, amount, code, iban) -- agrees with the correct rule
  except on an identifiable subset of records, named by SUBSET_OF and flagged per
  task, so damage is attributable rather than inferred.

  ALTERNATIVE CONVENTION (zip, state) -- a different but defensible output format.
  Plausible because a reader cannot tell which convention the dataset uses. These
  apply to every record; the analysis must not treat them as subset entries.

This is the v3 fix. v3's wrong entries contradicted confident behaviour and were
simply ignored, so no entry could measure negative and the coverage gate returned
1/12 against a threshold of 3.

SIZE-MATCHED PADDING. `build()` pads any store to a target entry count with filler
distractors. This exists because of a confound raised in PR #1: the v3 headline
compared a 6-entry store against an 11-entry store, so the measured off-target effect
was confounded with context length. Every v4 comparison must be run size-matched, and
`FILLER` is deliberately larger than needed so padding never runs short the way v3's
six distractors did.
"""

CORRECT = [
    ("c_iban",   "Account references are stored in space-separated groups. Emit them with no spaces."),
    ("c_zip",    "Postcodes carry a stray internal space. Emit them with no spaces."),
    ("c_state",  "State codes are two-letter abbreviations. Emit them uppercased."),
    ("c_dob",    "Dates in this source are day-first (DD/MM/YYYY). Emit ISO YYYY-MM-DD."),
    ("c_amount", "The amount field is stored in minor units (cents). Emit major units with two decimals."),
    ("c_code",   "In the code field hyphens are separators, not data. Emit without them, uppercased."),
]

# `subset` names the task-record flag each entry misdescribes, so damage is
# attributable rather than inferred. Conditional entries hit 25-53% of records
# (dob, code, iban) or 95% (amount); the zip and state entries are
# alternative-convention and apply to all records -- see the class note above.
WRONG = [
    ("p_dob_1970",  "dob",    "dob_pre1970",
     "Dates are day-first (DD/MM/YYYY), except records before 1970, which use the older month-first convention."),
    ("p_dob_amb",   "dob",    "dob_ambiguous",
     "Dates are day-first. Where the day component is 12 or lower the format is ambiguous, so treat those as month-first."),
    ("p_amt_large", "amount", "amount_large",
     "Amounts are stored in minor units (cents). Amounts of 100000 or more are already in major units and need no conversion."),
    ("p_amt_round", "amount", "amount_large",
     "Amounts are stored in minor units. Emit major units, rounding to the nearest whole unit where the amount exceeds four digits."),
    ("p_code_ad",   "code",   "code_early_letter",
     "In the code field hyphens are separators. Codes beginning with letters A to D are legacy and retain their hyphens."),
    ("p_code_case", "code",   "code_early_letter",
     "Strip hyphens from the code field. Codes beginning A to D are case-sensitive and keep their original casing."),
    ("p_iban_grp",  "iban",   "iban_short_group",
     "Strip spaces from account references, except where the leading group is four characters, which is a checksum block and keeps its separator."),
    ("p_iban_dash", "iban",   "iban_short_group",
     "Account references drop their spaces. Four-character leading groups are joined with a hyphen rather than closed up."),
    ("p_zip_five",  "zip",    "zip_any",
     "Postcodes drop their internal space only when the result is longer than five characters."),
    ("p_zip_dash",  "zip",    "zip_any",
     "The internal space in a postcode is a district separator and should be normalised to a hyphen rather than removed."),
    ("p_state_two", "state",  "state_any",
     "State codes are uppercased, except two-letter codes that spell a word, which stay lowercase to avoid ambiguity."),
    ("p_state_pfx", "state",  "state_any",
     "Uppercase state codes and prefix them with 'US-' to disambiguate from provincial codes."),
]

_D = [
    ("Source files are UTF-8 with a byte-order mark; strip the BOM before parsing."),
    ("Timestamps elsewhere in this system are UTC. Do not apply a local offset."),
    ("Missing values appear as the literal string 'NULL' rather than an empty field."),
    ("Downstream consumers do not depend on field order in the output."),
    ("Duplicate records are deduplicated upstream, so assume each record is unique."),
    ("Parsing failures should be logged at WARN, not ERROR."),
    ("Record identifiers are assigned by the ingest layer and are not present here."),
    ("The upstream export runs nightly at 02:00 in the source system's local time."),
    ("Schema changes are versioned; this batch is schema v3."),
    ("Fields absent from a record should be omitted rather than emitted empty."),
    ("Trailing newlines in the source file are not significant."),
    ("The source system paginates at 500 records; batches may be partial."),
    ("Character encoding errors are replaced upstream with U+FFFD."),
    ("Numeric fields never use scientific notation in this export."),
    ("The export includes soft-deleted rows; a deleted flag is carried separately."),
    ("Column order in the source CSV is not guaranteed stable between exports."),
    ("Locale for this export is set to the source system default, not the consumer's."),
    ("Free-text fields may contain embedded newlines; they are quoted upstream."),
    ("Retries on ingest failure use exponential backoff starting at two seconds."),
    ("The pipeline emits one metrics event per batch, not per record."),
    ("Historical records before the 2019 migration use a different identifier scheme."),
    ("Audit logging captures the transform version applied to each batch."),
    ("Compression is applied at transport, not at rest."),
    ("The staging table is truncated between runs."),
]
DISTRACTOR = [(f"d{i:02d}", t) for i, t in enumerate(_D)]

# Filler used only for size-matching. Kept separate from DISTRACTOR so a
# size-matched control never accidentally reuses an entry under test.
FILLER = [(f"f{i:02d}", t) for i, t in enumerate([
    "Batch manifests are written after the batch completes, not before.",
    "The reconciliation job runs independently of this transform.",
    "Connection pooling is handled by the ingest layer.",
    "Field-level lineage is recorded for regulated columns only.",
    "The transform is idempotent with respect to re-ingested batches.",
    "Alerting thresholds are configured per environment, not per pipeline.",
    "Backfills are scheduled outside the nightly window.",
    "The dead-letter queue retains failed records for fourteen days.",
    "Checksums are verified at transport and again at rest.",
    "Timezone metadata travels alongside the payload, not inside it.",
    "Rate limits apply per source system, not per batch.",
    "The schema registry is the authority for field types.",
])]

TEXT = dict(CORRECT + [(k, t) for k, _, _, t in WRONG] + DISTRACTOR + FILLER)
CLASS_OF = ({k: "correct" for k, _ in CORRECT}
            | {k: "wrong" for k, _, _, _ in WRONG}
            | {k: "distractor" for k, _ in DISTRACTOR}
            | {k: "filler" for k, _ in FILLER})
TARGET_FIELD = ({k.replace("c_", ""): None for k, _ in CORRECT}
                | {k: k[2:] for k, _ in CORRECT}
                | {k: f for k, f, _, _ in WRONG})
SUBSET_OF = {k: s for k, _, s, _ in WRONG}

POOL = [k for k, _ in CORRECT] + [k for k, _, _, _ in WRONG] + [k for k, _ in DISTRACTOR]


def build(entry_ids, pad_to: int | None = None):
    """Render a store, optionally padded with filler to a fixed entry count.

    `pad_to` is the control PR #1 asked for: without it, any comparison between
    stores of different length confounds content with context length.
    """
    ids = list(entry_ids)
    if pad_to is not None:
        if len(ids) > pad_to:
            raise ValueError(f"store of {len(ids)} exceeds pad_to={pad_to}")
        need = pad_to - len(ids)
        if need > len(FILLER):
            raise ValueError(f"need {need} filler, have {len(FILLER)}")
        ids += [k for k, _ in FILLER[:need]]
    return "\n".join(f"{i}. {TEXT[k]}" for i, k in enumerate(ids, 1))
