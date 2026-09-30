# The Unofficial Guide

Giao Nguyen. Corpus: `advice_threads`.

---

# Unit 1

## What This Does

This is a retrieval-augmented question answerer built on the `advice_threads`
corpus, 23 student advice-forum threads (study spots, textbook editions,
internship timing, pass/fail policy, laptop specs, and similar) split into 46
chunks. Ask it a question the threads actually cover and it retrieves the
relevant reply, answers from it, and names the source file. Ask it something
the corpus doesn't cover, anything from a different world entirely, like
world history or car maintenance, and a relevance gate refuses before the
question ever reaches the model, instead of letting it guess.

## Chunking Strategy

**Chunk size:** Not a fixed character count, at most 2 replies per chunk plus the thread title. In practice that produces chunks ranging from 157 to 423 characters (297 on average) across my 23 documents.

**Overlap:** 0 characters. Splits land on `--- reply N ---` markers, not raw character offsets, so there's no boundary left to protect with overlap.

I didn't start here. My first strategy was `fallback_split`'s fixed-size window, and I picked `chunk_size=1050` / `overlap=124` for it based on what I actually measured in my corpus: my longest document is 794 characters and my longest single sentence is 124 characters. I set the window's step (`chunk_size - overlap`) above 794 so it would never slice a document into a real chunk plus a meaningless leftover tail (the original `chunk_size=800`/`overlap=120` defaults did exactly that to 3 of my documents, producing a 2-character garbage chunk), and set the overlap to 124 to cover my longest sentence in case a split ever did happen.

That fixed the fragment problem, but reading the resulting chunks surfaced a second, separate issue no character count could fix: threads with 4-5 replies (like `thread_bike_commute.txt`) still had every reply crammed into one chunk, mixing unrelated sub-questions, bike storage, winter durability, theft registration, into a single result that matched several different questions a little and none of them well. That's a bundling problem, not a size problem, so I replaced `split_documents` entirely instead of continuing to tune the window. `CHUNK_SIZE`/`CHUNK_OVERLAP` in `config.py` are still set to 1050/124 and `fallback_split` still uses them for comparison, but the final `split_documents` doesn't use raw size or overlap at all, it cuts on the corpus's own structure instead. The result: 23 documents produce 46 chunks, shortest 157 characters and longest 423, with no chunk ever bundling more than 2 replies.

## Sample Chunks

**Chunk 1** — source: `thread_bike_commute.txt#0` — produced by: `chunker.py::split_documents`

```
THREAD: Is a bike worth it for a 20 minute walk commute?

--- reply 1 (14 votes) ---
Yeah. Cuts an 18 minute walk to about 6. The thing nobody mentions is storage — covered bike parking exists at three buildings and is full by 9am at all three.

--- reply 2 (9 votes) ---
Counterpoint, I sold mine. Between November and March the paths are either icy or salted and salt destroys a drivetrain in one season.
```

**Chunk 2** — source: `thread_bike_commute.txt#1` — produced by: `chunker.py::split_documents`

```
THREAD: Is a bike worth it for a 20 minute walk commute?

--- reply 3 (22 votes) ---
Both true. I keep a cheap bike for September to November and walk the rest of the year. Total cost was about $120 for the bike and I don't care what happens to it.

--- reply 4 (5 votes) ---
If you do get one, the campus does free registration and it's the only reason I got mine back after it was taken.
```

**Chunk 3** — source: `thread_clubs.txt#1` — produced by: `chunker.py::split_documents`

```
THREAD: How many clubs is too many?

--- reply 3 (18 votes) ---
If you want a leadership position later, depth in one is worth more than breadth across five.
```

**Chunk 4** — source: `thread_meal_plan_tier.txt#0` — produced by: `chunker.py::split_documents`

```
THREAD: Which meal plan tier is right?

--- reply 1 (24 votes) ---
Depends entirely on whether your building has a kitchen. Fenwick has kitchenettes, so people there go down a tier and cook two or three nights. Everywhere else, get the middle tier.

--- reply 2 (19 votes) ---
The highest tier only makes sense if you eat three meals a day in the halls every single day, which basically nobody does past October.
```

**Chunk 5** — source: `thread_winter_advice.txt#0` — produced by: `chunker.py::split_documents`

```
THREAD: First winter here — what do I need?

--- reply 1 (26 votes) ---
Layers, not a big coat. The buildings are overheated and you'll carry a parka around all day.

--- reply 2 (31 votes) ---
Boots with actual tread. The path past the pond ices over and people go down on it every year.
```

## Sample Answer

<!-- One complete question and answer, pasted as text, with the source line
     visible. Milestone 4. -->

**Question:** Is there a quiet study spot near or on campus?

**Answer:**

```
Yes, there are several quiet study spots mentioned:
* Ridgeway Café before 10am is described as empty and quiet (thread_study_spots.txt).
* The library third floor reliably delivers silence (thread_study_spots.txt).
* The science building has open lounges on floors 2 through 5 that are unlocked and almost always empty (thread_study_spots.txt).
```

Sources retrieved: thread_commuting.txt, thread_office_hours_etiquette.txt, thread_roommate_conflict.txt, thread_study_spots.txt

Retrieval (top-k 5) pulled in three unrelated threads alongside the right one, but the
answer only cites `thread_study_spots.txt` — the grounding instruction filtered the
noise rather than working stray details from the other three into the answer.

**My relevance cutoff:**

I kept `THRESHOLD = 0.6`. The five in-corpus questions all landed between 0.315
and 0.421; the five out-of-scope questions all landed between 0.806 and 0.938.
That leaves a clean gap from 0.421 to 0.806 with nothing in it, and 0.6 sits
almost exactly in the middle of that gap rather than hugging either edge.

| Question | In corpus? | Best distance |
|---|---|---|
| Is there a quiet study spot near or on campus? | yes | 0.347 |
| When should I apply for internships? | yes | 0.315 |
| Do I need to get the latest edition for every textbook? | yes | 0.359 |
| What kind of laptop specs should I look for when buying a laptop for school? | yes | 0.401 |
| What is the policy for pass/fail declaration? | yes | 0.421 |
| What is the recommended dosage of ibuprofen for a headache? | no | 0.806 |
| How do I write a for loop in Rust? | no | 0.827 |
| Who won the 1994 World Cup? | no | 0.893 |
| How do I change the oil in a diesel engine? | no | 0.896 |
| What is the capital of Mongolia? | no | 0.938 |

---

# Unit 2

<!-- These sections get ADDED to what's already above. Don't delete or rewrite
     unit 1 — the point is that someone can see what you said before you knew
     how it went. -->

## Run Log — Before

<!-- Your five criteria, three runs each. `python run_eval.py --label before`
     runs the questions, puts the OUT_OF_SCOPE ones through the gate, and
     writes it all into results/ for you. Targets come from criteria.md; the
     verdict column is your call.

     Criterion 3 is measured in one deterministic pass rather than three, so
     the same number goes in all three run columns. That's correct, not lazy.

     Milestone 1. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 4/5 | 4/5 | 4/5 | MET |
| 2. Every answer names a source | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 4. Chunks are the right size and don't bundle too many replies | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 5. Answers don't state facts the source doesn't back up | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |

<!-- Underneath, paste the REAL output for each criterion from one of your
     runs — the actual text your system produced, not a description of it.
     Name the file and function that produced it. -->

## Verdicts

<!-- MET or MISSED for each of the five, against the target you wrote last
     unit — not a new one. Plus a sentence on how you decided. That sentence
     matters most where it was close.

     If your target said 4 of 5 and your runs came out 4, 3, 4, that's a MISS.
     The target has to hold, not show up occasionally.

     Milestone 2. -->

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 | Retrieved chunk contains the answer | MET | Target was 4/5; all 3 runs scored 4/5, consistently missing only the textbook edition question. |
| 2 | Every answer names a source | MET | Target was 5/5; all generated answers across all 3 runs cited their source file. |
| 3 | Gate stops out-of-corpus questions | MET | Target was 4/5; the relevance gate blocked all 5/5 out-of-scope questions across all runs. |
| 4 | Chunks are the right size and don't bundle too many replies | MET | Target was 4/5; all 46 chunks pass the 50+ char floor and cap reply bundling at 2 per chunk. |
| 5 | Answers don't state facts the source doesn't back up | MET | Target was 4/5; all dates, stats, and numbers in the answers match the retrieved thread chunks. |

## Diagnoses

### Criteria Results Overview
None of the five criteria missed their overall target in the baseline evaluation run (`results/run_2026-09-29_1806_before.md`), so no criterion received a verdict of MISSED.

### Target Tightening Plan
Because every criterion passed on the first try, the original targets were set too safely. Specifically, Criterion 1 permitted 1 failure out of 5 questions, allowing a 100% recurring failure on Question 3 ("Do I need to get the latest edition for every textbook?") to hide behind a passing aggregate score.

* **Criterion to tighten:** Criterion 1 ("Retrieved chunk contains the answer")
* **Original target:** 4 of 5
* **Tighter target:** 5 of 5

### Recurring Failure Analysis: Question 3
* **Question:** "Do I need to get the latest edition for every textbook?"
* **Pipeline Stage:** Retrieval & Scorer / Evaluation
* **Mechanism:** The retrieval pipeline fetches `thread_textbook_editions.txt` and generates a correct answer explaining edition exceptions. However, string-matching in `scorer.py` evaluates exact phrase occurrences rather than semantic intent, resulting in an automated `fail` across all three baseline runs.

## The Improvement

**What I changed:**

Modified `_split_candidates` in `scorer.py` to recognize `,` alongside `;` and `|` as a delimiter, so it can split multi-phrase expectation candidates like `"math and physics, ask the instructor"` into individual phrases.

**Why I picked it:**

The Criterion 1 diagnosis traced Question 3's recurring failure to the scorer, not the pipeline: retrieval and generation both produced a correct, grounded answer, but `scorer.py`'s exact-phrase matching couldn't recognize it because the expected phrase used a comma the splitter didn't handle.

### Run Log — After

- **When:** 2026-09-29 20:11
- **Target:** 5 of 5 on Criterion 1

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 5 of 5 | MET (5/5) | MET (5/5) | MET (5/5) | MET |
| 2. Every answer names a source | 5 of 5 | MET (5/5) | MET (5/5) | MET (5/5) | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | MET (5/5) | MET (5/5) | MET (5/5) | MET |
| 4. Chunks are the right size and don't bundle too many replies | 5 of 5 | MET (5/5) | MET (5/5) | MET (5/5) | MET |
| 5. Answers don't state facts the source doesn't back up | 5 of 5 | MET (5/5) | MET (5/5) | MET (5/5) | MET |

**Did it help?**

Yes. Question 3 moved from `FAIL` to `pass` across all three evaluation runs, bringing Criterion 1 from 4/5 to 5/5 — the fix targeted the scorer bug identified in the diagnosis, not the retrieval or generation pipeline, and the result confirms that was the actual cause.

## What's Still Broken

<!-- For each criterion still missed after your fix: what you'd do about it,
     and why you stopped where you did.

     "I ran out of time" is fine if it's true. Pretending nothing is left is
     not.

     Milestone 5. -->

Even though all 5 criteria achieve passing scores on the current test suite, three key limitations remain in the pipeline design:

1. **Scorer Bag-of-Words Fallback:** In `scorer.py`, if exact substring matching fails, the judge falls back to verifying that every individual word in an expectation candidate exists somewhere in the answer. If a generated answer includes all target words scattered across different sentences or in an incorrect context, `scorer.py` will log a false-positive `pass`.
2. **Relevance Gate Keyword Overlap:** The fixed distance threshold (`0.6`) effectively stops completely off-topic questions (e.g., diesel engines or world geography), but out-of-scope questions that share common campus terminology (such as asking about textbook or internship policies at a different university) could drop below `0.6` and bypass the gate.
3. **Multi-Reply Structural Splitting:** `split_documents` caps chunk sizes at 2 replies per chunk to prevent over-bundling. However, if a thread contains a continuous advice chain spanning 3 or 4 replies, the context gets split across multiple chunks, meaning the retriever may only fetch partial advice.

## What I'd Do Differently

<!-- Knowing what you know now — which of your five criteria would you write
     differently, and why?

     Milestone 5. -->

Knowing what I know now after running the baseline and post-fix evaluations, I would rewrite two of my five criteria to be more robust:

1. **Criterion 1 (Answer Matching Expectation):** I would rewrite how expectations are defined in Criterion 1 to avoid relying on rigid exact-string matches. Question 3 failed initially not because the model gave a bad answer, but because the candidate splitter in the scorer couldn't parse comma-separated target phrases. I would write this criterion to evaluate semantic intent (or explicitly support flexible delimiters) rather than strict word matching.
2. **Criterion 3 (Out-of-Scope Relevance Gate):** I would rewrite Criterion 3's test suite to include "near-miss" out-of-scope questions that share common academic terminology (e.g., asking about textbook or internship policies at a different university). The original criterion only used completely unrelated topics (like car maintenance or world history), which made the gate look 100% effective without testing its limits against domain-adjacent vocabulary overlap.

---

# How I Used AI

**1. The `split_documents` rewrite.** I asked Claude to rewrite `split_documents()` to fix the bundling problem diagnosed in `criteria.md`: split on `--- reply N ---` boundaries instead of raw character count, and glue the thread title onto each chunk so it stays self-contained (needed because my shortest lone reply is only 35 characters). It came back with a regex split (`REPLY_HEADER = re.compile(r"^--- reply \d+.*?---$", re.MULTILINE)`) that groups replies into chunks of at most 2 (`MAX_REPLIES_PER_CHUNK = 2`), prepends the title to every group, and falls back to treating the whole document as one chunk if no reply markers are found at all — that fallback wasn't something I asked for, Claude added it defensively for documents that don't match the thread format. I kept it since it costs nothing and doesn't affect my corpus (every document in `advice_threads` has reply markers), but I didn't just trust the summary: I ran `python app.py chunks -n 46` myself and checked the shortest chunk by hand (157 characters, `thread_clubs.txt#1`) to confirm the floor actually holds on the real trailing-lone-reply case, not just in theory.

**2. Catching a milestone-ordering mistake in my criteria.** While drafting the "why this target" reasoning for criteria 1 and 3 in `criteria.md`, I asked Claude whether both needed rewriting given the chunking work I'd already done. It answered by conflating all five criteria under the same "write it blind, before you have results" rule. I caught the inconsistency by pasting the actual Milestone 2 instructions back at it, which forced a correction distinguishing criteria that can legitimately be reasoned from corpus structure alone (like #1) from ones that specifically need a real measured result before the "why" can be honest (like #3). I rewrote the criterion 3 reasoning myself once I understood the distinction, instead of letting the blanket answer stand.

**3. Scorer Bug Diagnosis & Regex Fix (Unit 2).** Used AI to trace the execution of `scorer.py` when diagnosing Question 3's recurring failure. Identified that `_split_candidates()` failed on comma-separated expectations and generated the updated delimiter regex `r"[;,|]"`.

**4. Documentation & Retrospective.** Used AI to format evaluation tables, structure run logs, and refine reflection sections across Milestones 1–5.
