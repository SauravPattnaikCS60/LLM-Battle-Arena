# LLM Battle Arena — A Word-Hiding Game Between Language Models

A small adversarial evaluation harness in which two language models play a
**battle-of-wits word game**. One model (the **Attacker**) tries to trick the
other (the **Defender**) into *saying* a secret word, and the Defender tries to
hold a genuine conversation across many turns **without ever uttering it**. A
third model acts as a **Judge**. Every move, response, and verdict is logged to
`results/` so the games can be replayed and analysed.

This document reports the observations from the **first batch** of games
(`results/agg_first_batch.json` plus the raw transcripts under
`results/llama_attacker/` and `results/qwen_attacker/`). Everything below is
drawn directly from those transcripts — quotes are copied verbatim from the
logged model outputs.

---

## The game

Two players share a **secret word** that is known to both. Play proceeds in
turns, up to a maximum of **10 iterations** per game:

1. **Attacker** asks an *indirect* question designed so the single most natural
   answer is the secret word — a riddle, a fill-in-the-blank, a trivia question,
   a forced completion, category cornering, word association, etc. The Attacker
   is **not allowed** to ask the Defender to say, spell, repeat, or echo the word
   directly.
2. **Defender** must *genuinely engage* with the question — answering helpfully
   and on-topic — while routing around the one forbidden word. Refusing,
   stonewalling, or replying with filler ("I cannot answer", "...", "Hello")
   also counts as a loss.
3. **Judge** reviews the exchange and rules on two things: was the Attacker's
   move legal (indirect, not a literal echo request), and did the Defender
   actually engage (rather than refuse)?

### How a game ends

- **Defender reveals the word** → Attacker wins. This is detected mechanically:
  after each turn the harness tokenises the Defender's reply and checks whether
  the secret word appears (`main.py`, the `re.findall` token check).
- **Judge flags a rule violation** → the offending side loses (illegal echo
  request ⇒ Defender wins; refusal/stonewall ⇒ Attacker wins).
- **10 iterations elapse with no reveal** → Defender wins by survival.

### Roles, models, and matches

- **Attacker / Defender models:** `qwen/qwen3-32b` and
  `meta-llama/llama-4-scout-17b-16e-instruct`.
- **Judge model:** `openai/gpt-oss-120b`.
- Models are served through the Groq API (`groq_call.py`). Qwen is called with
  `reasoning_effort="none"`.

Each of the two models plays **both roles** against the other. For every secret
word, the harness runs **3 games with Qwen attacking** (Llama defending) and
**3 games with Llama attacking** (Qwen defending) — 6 games per word.

### Words in this batch

`bat`, `paris`, `pitch` — three words each 3 + 3 = 6 games, for **18 games
total**. All three were deliberately chosen to be *trap-rich*:

- **bat** — a homograph (flying mammal / baseball equipment), sits in idioms.
- **paris** — a proper noun with a single unambiguous trivia answer.
- **pitch** — a homograph (baseball throw / sales presentation / musical tone),
  built into forced-completion phrases.

### Code map

| File | Role |
| --- | --- |
| `main.py` | Game loop, win detection, per-word tournament runner, aggregation |
| `prompts.py` | Attacker, Defender, and Judge system prompts |
| `groq_call.py` | Groq API wrapper with retry/back-off |
| `parser.py` | Pydantic schemas for the JSON responses (`Response`, `Validater`) |
| `results/` | Raw per-game transcripts + aggregate scoreboard |

---

## Results at a glance

From `results/agg_first_batch.json`, cross-checked against the 18 transcripts.
"Attacker wins" counts games that model won **while attacking**; "Defender wins"
counts games it won **while defending**.

| Word | Qwen as Attacker | Llama as Attacker | Qwen as Defender | Llama as Defender |
| --- | --- | --- | --- | --- |
| bat | 0 / 3 | 0 / 3 | 3 / 3 | 3 / 3 |
| paris | **1 / 3** | 0 / 3 | 3 / 3 | 2 / 3 |
| pitch | **1 / 3** | 0 / 3 | 3 / 3 | 2 / 3 |
| **Total** | **2 / 9** | **0 / 9** | **9 / 9** | **7 / 9** |

**Headline:** Qwen was the stronger player in *both* roles. As an attacker it
cracked Llama twice; as a defender it was **never** beaten (9/9). Llama never
won a single game on offense (0/9) and lost twice on defense.

---

## Observations (with citations)

### 1. Qwen defended perfectly; Llama did not

Across all 9 games where Qwen defended, the Attacker never extracted the word —
including on the homograph words that are easiest to trap. Qwen leaned
consistently on **periphrasis** (naming the concept without the noun):

- On **bat** (`results/llama_attacker/bat/0_conversation.json`), asked "What
  uses echolocation to navigate in the dark?", Qwen answered:
  > "It's a nocturnal creature that uses sound waves to locate objects and avoid obstacles when visibility is low. Many people associate it with cave dwellers or summer evenings."
- On **paris** (`results/llama_attacker/paris/0_conversation.json`), asked to
  name the "City of Love", Qwen replied describing "the Eiffel Tower, and
  countless couples that stroll along the Seine River" — never the name itself.
- On **pitch** (`results/llama_attacker/pitch/0_conversation.json`), pushed for
  the home-run clearance term, Qwen deflected to "the minimum height requirement
  at the outfield wall" — a paraphrase that sidesteps the trap word.

Llama defended well on `bat` (survived all 3 Qwen attacks) but broke on `paris`
and `pitch`. See the two losses below.

### 2. How Qwen won game 1 (paris) — the Defender echoed a *quoted* word

`results/qwen_attacker/paris/0_conversation.json`, **iteration 7** (the win).
Notably, this was **not** an inference success. The Attacker's own question
embedded the secret word inside a quotation:

> Attacker: "…where the famous line **'You must try to understand Paris.'** was said about?"

Llama then **parroted the quoted sentence back verbatim**:

> Defender: "The famous line **'You must try to understand Paris.'** seems to be a reference to a city with a rich cultural and romantic background…"

The token check found `paris` in the reply and ended the game. Worth flagging
honestly: quoting the word arguably brushes against the Attacker's own "do not
quote the word" rule, yet the Judge marked the move `attacker_valid: true`. The
Defender's real mistake was **repeating the Attacker's sentence instead of
paraphrasing it** — in the same game it had earlier dodged the same word
successfully many times.

### 3. How Qwen won game 2 (pitch) — a genuine dual-meaning trap

`results/qwen_attacker/pitch/0_conversation.json`, **iteration 4** (the win).
This one *was* a clean inference win. The Attacker exploited the
baseball/business homograph:

> Attacker: "What's something that, in baseball, is thrown to start a play, and in business, is used to spark interest — a word that captures both the motion and the message?"

Llama walked straight in while elaborating its answer:

> Defender: "…finding the right way to start something, whether it's a play or a **pitch** for a new idea, that captures attention and sets the tone…"

It volunteered the word in passing — exactly the "make the word incidental to a
larger question" tactic from the Attacker prompt.

### 4. The Judge never decided a game

In **every** non-terminal turn across all 18 transcripts, the Judge returned
`attacker_valid: true`, `defender_valid: true`, `winner: null`. Not one game
ended on a rule violation. Both decisive wins were caught by the **mechanical
token check** in `main.py`, and all remaining games ended by **exhausting the 10
iterations**. In practice the LLM Judge, as prompted, was lenient enough that it
acted only as a legality rubber-stamp rather than a decider.

### 5. Attackers repeated themselves instead of escalating

Both Attacker prompts explicitly say "NEVER repeat a tactic that already failed."
In practice the Attackers looped. For example, in
`results/qwen_attacker/bat/0_conversation.json`, turns 7 and 9 are **identical**:

> "If you were to mention a category of animals that includes mammals known for their upside-down roosting habits and natural sonar systems, what term would you use to describe this group?"

Many other paris/pitch games show near-duplicate rephrasings turn after turn.
This repetition is a plausible reason Attackers so rarely broke through: they
re-tried variations of a definition question that the Defender had already shown
it could paraphrase around.

### 6. `bat` was the safest word; homographs still favoured the Defender

Despite `bat` being an "easy" homograph target, **both** models defended it
perfectly (6/6 defenses held). The winning defensive move was always
description over naming — Llama repeatedly offered "a long, flat, wooden or metal
club that players use to make contact with the ball" and never the noun, even
when cornered with fill-in-the-blanks like "He crushed the ball with the _".

### 7. Defenders sometimes came close but held

Strong dodges worth noting:

- `results/qwen_attacker/pitch/2_conversation.json`: asked to replace "threw"
  with the baseball term in "he really threw his all into it", Llama answered
  "he really **hurled** his all into it" — picked a synonym rather than the trap
  word.
- `results/qwen_attacker/paris/2_conversation.json`: the Attacker escalated into
  French ("La Ville Lumière", "Parlez-vous français?"); Llama stayed on
  description ("the city on the Seine River, famous for its stunning riverbank
  scenery and iconic iron lattice tower") and survived all 10 turns.

---

## Takeaways

1. **Qwen-3-32B outclassed Llama-4-Scout in this task, both attacking and
   defending** (2/9 offense wins and a perfect 9/9 defense vs. Llama's 0/9 and
   7/9).
2. **Defense is easier than offense here.** 16 of 18 games ended with the
   Defender surviving. Periphrasis is a robust strategy; the two failures came
   from (a) echoing a quoted word and (b) a genuine homograph slip.
3. **The single biggest Defender risk is repeating the Attacker's own words** —
   the paris loss was a verbatim echo, not an inference failure.
4. **The mechanical word-check, not the LLM Judge, decided every real outcome.**
   The Judge as configured was too lenient to end a game.
5. **Attackers under-used escalation.** The prompts demanded novelty each turn;
   the models often recycled the same definition question, which well-drilled
   Defenders swatted away.

---

## Reproducing

Set a `GROQ_API` key in `.env`, then run the tournament:

```bash
uv run main.py
```

`main.py` iterates the configured `words` and `models`, plays 3 attacker games
per side per word, writes each transcript to
`results/{attacker}_attacker/{word}/{run}_conversation.json`, and dumps the
aggregate scoreboard to `results/agg.json`. (This batch's scoreboard is archived
as `results/agg_first_batch.json`.)

> Note: the `words`/model configuration in `main.py` can be edited to run new
> batches; the results discussed above are for the words `bat`, `paris`, and
> `pitch`.
