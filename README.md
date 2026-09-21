# The Unofficial Guide

<!-- Replace this line with your name and which corpus you picked. -->

> **This file is your submission.** Fill it in as you go — most sections get
> written during the milestone that produces them, not at the end.
>
> How the starter works, and every command you'll need, is in `RUNNING.md`.
> Leave that file alone.
>
> **Paste everything as text.** No screenshots, no video. A typed table gets
> full credit; a picture of the same table gets none.
>
> Delete these instruction blocks as you replace them. The `<!-- -->` comments
> are notes to you and don't show up when the page renders — you can leave them
> or remove them.

---

# Unit 1

## What This Does

This is a retrieval-augmented question answerer built on the `advice_threads`
corpus — 23 student advice-forum threads (study spots, textbook editions,
internship timing, pass/fail policy, laptop specs, and similar) split into 46
chunks. Ask it a question the threads actually cover and it retrieves the
relevant reply, answers from it, and names the source file. Ask it something
the corpus doesn't cover — anything from a different world entirely, like
world history or car maintenance — and a relevance gate refuses before the
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

## How I Used AI

<!-- Two specific moments. For each: what you asked for, what came back, and
     what you changed about it.

     "I asked Claude to write the chunking function from my notes. It ignored
     the overlap, so I added that myself" is the level of detail we're after.
     "I used AI to help me code" is not.

     Milestone 5. -->

**1.**

**2.**

<!-- ── Stretch features ─────────────────────────────────────────────────────
     Doing one? Say so here BEFORE you start. A feature this README never
     claims earns nothing.
     ───────────────────────────────────────────────────────────────────────── -->

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
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

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
| 1 |  |  |  |
| 2 |  |  |  |
| 3 |  |  |  |
| 4 |  |  |  |
| 5 |  |  |  |

## Diagnoses

<!-- For each miss: which stage caused it, and how. The stage alone isn't
     enough — you need the mechanism.

     Not a diagnosis: "Question 3 didn't work."
     A diagnosis:     "Question 3 asks about laundry costs. The answer is in
                       one sentence that got split across two chunks, so
                       neither chunk on its own contains it."

     The five stages: loading → chunking → embedding → retrieval → generation.

     Look for a pattern. If three misses all ask about numbers, that's one
     problem, not three.

     Missed nothing? Say so, then say honestly whether your targets were set
     low, and which one you'd tighten and to what.

     Milestone 3. -->

## The Improvement

**What I changed:**

**Why I picked it:**

<!-- Connect it to a specific diagnosis above in one sentence. If you can't,
     you picked a fix because it sounded impressive. -->

### Run Log — After

<!-- Same format, same five criteria, three runs each.
     `python run_eval.py --label after` -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

**Did it help?**

<!-- Say plainly whether it did, and how you know. If it made things worse,
     say that — a change that backfired, honestly reported, earns full credit
     and is more interesting than one that worked. What matters is that you can
     tell.

     Milestone 4. -->

## What's Still Broken

<!-- For each criterion still missed after your fix: what you'd do about it,
     and why you stopped where you did.

     "I ran out of time" is fine if it's true. Pretending nothing is left is
     not.

     Milestone 5. -->

## What I'd Do Differently

<!-- Knowing what you know now — which of your five criteria would you write
     differently, and why?

     Milestone 5. -->
