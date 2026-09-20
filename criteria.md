# Acceptance criteria — The Unofficial Guide

Five criteria that say what "working" means for this system, written in unit 1
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"Retrieval works"* is an opinion. *"For at
least 4 of my 5 test questions, the top results include a chunk containing the
answer"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter or looser one. A reason that says something about your corpus or your
pipeline earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## 1. Retrieved chunks contain the answer

For at least 4 of my 5 test questions, the retrieved chunks include one that
contains the answer.

**Why this target:**

My corpus is 23 short advice threads, each covering one self-contained topic in a handful of replies. There's no long document where an answer could be split across sections or buried in an unrelated tangent, so I expect retrieval to either clearly find the right thread or clearly miss it, not partially succeed. The risk I expect is that several threads share overlapping vocabulary (multiple threads mention deadlines, advisers, and "ask before it's too late"), so it's plausible that one of my five questions pulls in a similar-sounding but wrong thread instead of the right one. 4 of 5 leaves room for exactly that kind of near-miss without treating one vocabulary collision as a full system failure.

---

## 2. Every answer names a source

Every answer the system produces names at least one source document.

**Why this target:**

Every reply in this corpus is written in a confident, matter-of-fact tone, citing vote counts, deadlines, and dollar figures. A fabricated or ungrounded-sounding answer would be just as convincing as a real one unless it's tied to a document I can check. `generate.py`'s prompt already instructs the model to name the source it used, and because retrieval always returns some chunks (there's no path where an answer gets generated with zero context), I don't expect a structural reason for a real answer to ever skip a citation. That's why I'm holding this to "every answer" instead of a percentage.

---

## 3. The relevance gate stops out-of-corpus questions

When I ask a question my documents clearly don't cover, the relevance gate
stops it and the system returns "I don't have enough information about that" —
in at least 4 of 5 tries.

<!-- The five questions are the ones in `OUT_OF_SCOPE` at the bottom of
     `questions.py`, and `run_eval.py` puts them through the gate and writes
     what happened into your run log. Swap them for your own if you'd rather —
     just keep five of them, or the "4 of 5" above has nothing to be 4 of. -->

**Why this target:**

advice_threads only covers campus-life topics: laundry, parking, deadlines, and so on. I expect genuinely unrelated questions (engine maintenance, drug dosage, sports trivia) to sit far away from anything in my corpus in embedding space. `config.py`'s own comment on `THRESHOLD` notes that most corpora land their cutoff somewhere between 0.45 and 0.75, which suggests there should be real separation between in-scope and out-of-scope distances for a domain this narrow. I'm targeting 4 of 5 rather than 5 of 5 because it's possible one out-of-scope question happens to share surface wording with a campus topic (e.g. a non-academic use of "schedule" or "deadline") and lands closer than expected. I don't want a single edge case like that to make an otherwise-working gate look broken.

---

## 4. Chunks are the right size and don't bundle too many replies

At least 4 of my 5 sampled chunks pass both checks: the chunk does not bundle more than 2 replies from the same thread, and the chunk is at least 50 characters long.

**Why this target:**

When I read all 26 chunks from `fallback_split`, 3 were meaningless overlap tails, as short as 2 characters. That was caused by my chunk_size/overlap gap (680) being smaller than my longest document (794 chars). I fixed that by raising the gap to 926, and re-checked: all 23 chunks now come out as one per document, shortest 318 characters, so the floor clause passes under this interim config. But that check only covers `fallback_split`. I'm about to replace `split_documents` with something that splits on reply boundaries instead of raw character count, and my shortest single reply is 35 characters, below the floor. If my rewrite ever turns a lone reply into its own chunk without the thread title attached, the floor clause could fail again for a different reason than the one that broke it originally. So this clause isn't settled, it's just currently passing on a chunker I'm about to discard.

Separately, 5 of 26 chunks bundled 4-5 distinct replies covering different sub-questions into a single chunk. For example, `thread_bike_commute.txt`'s one chunk mixes bike storage, winter durability, and theft registration. Every thread with 4+ replies showed this problem, and every thread with 2-3 replies didn't. I haven't fixed this yet; it's what my `split_documents` rewrite is for. 4 of 5 leaves room for one edge case, a thread that genuinely can't be answered without two adjacent replies, without treating it as total failure.

---

## 5. Answers don't state facts the source doesn't back up

For at least 4 of my 5 test questions, every specific fact in the answer, a number, a date, or a dollar amount, also appears in the chunk the answer cites.

**Why this target:**

Replies in this corpus are full of exact figures stated with total confidence: dollar amounts, vote counts, deadlines, week numbers. A model that names the right file but states a different number from inside it would sound just as convincing as a correct answer, and citing the right filename alone wouldn't catch that. Right now my chunks are still whole threads, and a single thread often contains 4 or 5 different facts, so almost any number the model states will technically appear somewhere in the cited chunk, even if it isn't the fact the question actually asked about. That makes this target weaker to test today than it will be once I finish splitting on reply boundaries in Milestone 3, since a narrower chunk leaves nowhere for a wrong number to hide. I'm targeting 4 of 5 rather than 5 of 5 because a model paraphrasing a number, like rounding "$120" to "about $100," is a plausible, minor slip I don't want to treat as a full failure.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 2 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 1. Retrieved chunks contain the answer

         For at least 4 of my 5 test questions, the retrieved chunks include
         one that contains the answer.

         **Why this target:** ...

         > **Revised in unit 2:** For at least 4 of 5 questions, the top three
         > results contain the answer.
         >
         > **Why revised:** I couldn't judge "the chunks include one that
         > contains the answer" the same way twice — I scored two questions
         > differently on Monday than on Wednesday. The new version is
         > something I can actually check.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said 4 of 5 but got 2 of 5, so 2 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.

     The whole reason the originals stay visible is so someone can see what you
     said before you knew the answer.
     ───────────────────────────────────────────────────────────────────────── -->
