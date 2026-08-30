"""v4 candidate pool and store construction.

POOL: 6 correct + 12 plausible-wrong (two variants per field) + 24 distractors = 42.
Large enough for several generations of batched admission in the compounding loop,
which 12 entries was not.

WRONG ENTRIES COME IN TWO PLAUSIBLE FLAVOURS, neither of which contradicts confident
behaviour the way v3's did:

Every wrong entry offers a COMPETING TRANSFORM: a different way of performing the
same operation the correct entry describes. The premise test established that this
is what determines whether an entry bites at all.

  Entries that COMPETE cost accuracy: p_amt_round -0.77, p_zip_dash -0.18,
  p_iban_dash -0.20 on its subset.
  Entries that add an EXTRA STEP are ignored: p_state_pfx ("prefix with US-")
  measured +0.00 against a base of 1.00.
  Entries that state a CONDITIONAL EXCEPTION to a rule are ignored: p_dob_1970,
  p_dob_amb, p_iban_grp, p_zip_five all measured ~0.

Models resolve a conflict between two ways of doing one job, and sometimes resolve
it wrongly. They do not act on carve-outs or add-ons. Half the original v4 pool was
built on the wrong assumption and is replaced here.

Six entries apply to every record; six are restricted to a subset, so damage stays
attributable to the records the qualifier covers.

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
    ("c_phone",  "Phone numbers carry a national trunk prefix in parentheses. Drop it and all spacing, keeping the leading +."),
    ("c_ref",    "In the ref field the slashes are separators, not data. Emit without them, uppercased."),
    ("c_amount", "The amount field is stored in minor units (cents). Emit major units with two decimals."),
    ("c_code",   "In the code field hyphens are separators, not data. Emit without them, uppercased."),
]

# `subset` names the task-record flag each entry misdescribes, so damage is
# attributable rather than inferred. Conditional entries hit 25-53% of records
# (dob, code, iban) or 95% (amount); the zip and state entries are
# alternative-convention and apply to all records -- see the class note above.
WRONG = [
    # ALWAYS-APPLICABLE competing transforms. Every one specifies a dimension of the
    # output the correct entry leaves open -- case, separator, padding, precision --
    # rather than appending content or stating an exception. That distinction is what
    # the premise tests established determines whether an entry bites at all.
    ("p_iban_lower", "iban",  "iban_any",
     "Account references are closed up with no spaces and emitted lowercased."),
    ("p_zip_pad",    "zip",   "zip_any",
     "Postcodes are closed up and zero-padded to six digits."),
    ("p_phone_dash", "phone", "phone_any",
     "Phone numbers drop the parenthesised trunk prefix, with the remaining groups joined by hyphens rather than closed up."),
    ("p_ref_lower",  "ref",   "ref_any",
     "The ref field drops its slashes and is emitted lowercased."),
    ("p_amt_comma",  "amount","amount_any",
     "Amounts are stored in minor units. Emit major units using a comma as the decimal separator."),
    ("p_code_dash",  "code",  "code_any",
     "Emit the code uppercased, retaining a single hyphen before the final character."),

    # SUBSET-RESTRICTED competing transforms. Only two of six registered last round,
    # so attribution rests on thin evidence and is not leaned on in section 6.
    ("p_amt_round",  "amount","amount_large",
     "Amounts are stored in minor units. Emit major units, rounding to the nearest whole unit where the amount exceeds four digits."),
    ("p_iban_dash",  "iban",  "iban_short_group",
     "Account references drop their spaces. Four-character leading groups are joined with a hyphen rather than closed up."),
    ("p_code_ad",    "code",  "code_early_letter",
     "Emit codes without hyphens, uppercased. Codes beginning with letters A to D keep a hyphen before the final character."),
    ("p_zip_two",    "zip",   "zip_split_two",
     "Postcodes are closed up. Where the leading group is two digits the space is normalised to a hyphen instead."),
    ("p_phone_area", "phone", "phone_long_area",
     "Phone numbers close up entirely. Area codes of 50 or above retain a hyphen after the country code."),
    ("p_ref_early",  "ref",   "ref_early_letter",
     "Emit refs without slashes, uppercased. Refs beginning with letters A to D keep a slash before the final character."),
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
    "Export jobs acquire an advisory lock before writing the staging table.",
    "Row counts are reconciled against the source before the batch is marked done.",
    "The consumer contract is versioned independently of the source schema.",
    "Nulls and empty strings are distinct in the source and stay distinct here.",
    "Batch identifiers are monotonic but not contiguous.",
    "Transform errors are counted per field, not per record.",
    "The pipeline runs in the same region as the source database.",
    "Secrets are injected at runtime and never appear in a manifest.",
    "Column comments in the source are not propagated downstream.",
    "The dry-run mode writes to a shadow table with the same schema.",
    "Watermarks are stored per source, not per destination.",
    "Late-arriving records are appended rather than merged.",
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
