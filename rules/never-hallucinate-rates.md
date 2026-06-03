# Rule: Never Hallucinate Rates or Underwriting Rules

## Applies To

All responses involving insurance premiums, coverage limits, deductibles, commission percentages, discount amounts, roof-age thresholds, eligibility criteria, utility provider rates, and any other specific number or rule used in the C1 Insurance or MyUtilities business.

## The Rule

**If a number or rule is not present in the source documents under `data/`, do not state it.**

This applies regardless of whether the question sounds routine. Common rates and rules change frequently. A hallucinated number presented with confidence to an advisor can result in a misquoted policy, a client expectation that cannot be met at binding, a carrier submission that gets declined, or a compliance issue.

## What "Present in the Source Documents" Means

A fact is present if it appears verbatim or can be directly inferred from the text in one of these files:

- `data/carriers/safeco.txt`
- `data/carriers/travelers.txt`
- `data/utilities/dallas-providers.txt`
- `data/workflows/new-homeowner-quote.txt`
- `data/workflows/crosssell-protocol.txt`

Recalling a similar number from general knowledge or training data does not count. The number must be retrievable from the current document set.

## How to Respond When the Answer Is Not in the Documents

Use one of these responses:

- "That specific rate is not in the current carrier guides. Please verify directly with the carrier or in EZLynx."
- "The documents do not cover that scenario. The advisor should call the underwriting desk before quoting."
- "I can see the related rule for [X], but the specific figure you are asking about is not documented here."

Do not hedge with phrases like "it's typically around" or "usually in the range of." Those formulations still constitute hallucination.

## Specific Numbers That Must Never Be Invented

| Category | Example of what not to invent |
| --- | --- |
| Policy premiums | "A $450K home in Plano typically runs about $1,800/year with Safeco" |
| Discount percentages | Any discount not listed by name in the carrier guide |
| Commission rates | Any rate not stated in the carrier's commission section |
| Roof-age thresholds | Any year cutoff not stated in the carrier's roof section |
| Hail zone surcharges | Any percentage not listed in the hail zone table |
| Electricity rates | Any cents-per-kWh figure not in `data/utilities/dallas-providers.txt` |
| Utility commissions | Any amount not in the commission summary table |

## Enforcement in the Pipeline

The `brain.py` knowledge query engine includes this instruction in its system prompt. The `call_intelligence.py` demo fallback uses only hardcoded, verified facts. The UI displays answers sourced from ChromaDB chunks, with source file attribution shown to the advisor.
