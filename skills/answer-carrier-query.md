# Skill: Answer Carrier Query

## When to Use This Skill

Use this skill when an advisor asks a question about one of the four C1 carriers (Safeco, Travelers, Progressive, Kemper) — including coverage tiers, eligibility rules, discounts, commission rates, roof-age thresholds, DFW underwriting notes, or carrier comparisons.

## Step-by-Step Template

### Step 1 — Identify the carrier and topic

Determine which carrier the question is about. If the question is a comparison ("Safeco vs. Travelers for a $600K home"), handle both.

Identify the topic category:
- Coverage tier (Essential / Standard / Premier)
- Eligibility or sweet spot
- Roof age or hail rules
- Discount (name and percentage)
- Commission rate
- What to avoid / decline triggers
- Competitive positioning

### Step 2 — Retrieve from the carrier guide

Look up the answer in the relevant section of `data/carriers/safeco.txt` or `data/carriers/travelers.txt`. Use the ChromaDB knowledge base (`query_brain`) or read the file directly.

If the answer is not present, stop and say: "That detail is not in the current carrier guide for [carrier]. Please verify with the carrier or underwriting."

### Step 3 — Format the answer

Use this structure:

```
[CARRIER] — [TOPIC]

[Direct answer in plain English, 1-3 sentences.]

[Specific number or rule from the document, quoted or paraphrased accurately.]

Source: data/carriers/[filename].txt — [section name]
```

For comparisons, use this structure:

```
SAFECO vs. TRAVELERS — [TOPIC]

Safeco: [relevant fact]
Travelers: [relevant fact]

For this client profile, [carrier] is the better fit because [specific reason from the document].

Sources: data/carriers/safeco.txt, data/carriers/travelers.txt
```

### Step 4 — Add a next step if relevant

If the answer involves a threshold the client is near (e.g., roof is 14 years old and the limit is 15), add one sentence flagging the risk: "Note: the roof age is close to the threshold. Confirm the exact year with the home inspection report before binding."

If the answer involves a discount, add one sentence about what documentation is required to apply it.

## Example: Discount Query

**Question:** Does Safeco give a discount for Class 4 impact-resistant shingles?

**Answer:**

```
SAFECO — Class 4 Impact-Resistant Roof Discount

Yes. Safeco offers a 12% discount for Class 4 impact-resistant shingles.

To apply it, the advisor must submit the manufacturer certification at binding.
Qualifying products include Malarkey Vista, GAF Armorshield II, CertainTeed
Landmark IR, and Owens Corning Duration Storm.

Note: Travelers offers a smaller 8% discount for the same shingle class.
Safeco's 12% is the stronger incentive if the client qualifies.

Source: data/carriers/safeco.txt — DISCOUNTS
```

## Example: Eligibility Query

**Question:** Can we write a 19-year-old roof on Travelers Standard?

**Answer:**

```
TRAVELERS — Roof Age Eligibility

No. Travelers Standard requires RCV (replacement cost value) coverage on roofs
up to 16 years old. A 19-year-old roof falls into the ACV-only range (17-22 years).

The policy can still be written, but the client will receive ACV settlement on
roof claims rather than replacement cost. The client must sign a written
acknowledgment of this.

Exception: if the roof has Class 4 impact-resistant shingles, Travelers may
treat it as 3 years younger, which would put a 19-year-old Class 4 roof at
the 16-year threshold. Confirm with underwriting.

Source: data/carriers/travelers.txt — DALLAS HAIL AND ROOF-AGE UNDERWRITING NOTES
```

## What Not to Do

- Do not state a discount percentage that is not in the document.
- Do not say a risk is eligible without checking the decline triggers section.
- Do not recommend a carrier without noting any relevant caveats (roof age, claims history, dog breed, construction type).
- Do not answer questions about Progressive or Kemper from general knowledge. C1's current documents only cover Safeco and Travelers in detail. For Progressive or Kemper, direct the advisor to call underwriting.
