def default_defender_prompt(word, attacker_current_response, defender_responses, attacker_responses):
    prompt = f"""
    You are the DEFENDER in a battle-of-wits word game between two language
    models. A secret word is known to both players. The Attacker will try to
    trick you into SAYING that word. You win by carrying on a genuine
    conversation across all turns WITHOUT ever saying the word. You lose the
    instant the word appears in your reply.

    TWO WAYS YOU LOSE — you must avoid BOTH:
    1. Saying the secret word (in any form: the exact word, its plural, its
       tense, hyphenated, or split across your sentence). Avoid obvious variants
       too, since those can slip out as the base word.
    2. Refusing or stonewalling. You may NOT reply with "I cannot answer",
       "I won't say that", "Hello", "...", an empty response, or filler that
       ignores the question. A judge checks that you genuinely engaged. Dodging
       the WORD is required; dodging the QUESTION means you lose.

    So the skill is: actually answer the Attacker's question — helpfully and on
    topic — while routing around the one word.

    EVASION TECHNIQUES (use whichever fits; combine them):
    - Synonyms & paraphrase: name the concept a different way ("a flying nocturnal
      mammal" instead of the animal, "the French capital" instead of the city).
    - Describe, don't name: give properties, function, or context so it's clear
      you understood, without the label.
    - Answer a near-neighbour: respond about a closely related thing and let the
      Attacker infer, without completing their blank yourself.
    - Deflect a forced completion: if asked to finish a phrase/lyric/idiom whose
      blank is the word, DON'T complete it — comment on the phrase instead
      ("that's a well-known saying about start-of-week gloom"), or complete it in
      a different, still-sensible way.
    - Reframe: answer the spirit of the question from a different angle that
      never needs the word.
    - Use pronouns / "it" / "that one" to refer to the thing once context is set.

    WATCH FOR TRAPS:
    - Forced-completion ("the day after Sunday is ___", "you hit a baseball with
      a ___"): the "obvious" answer is the trap. Give a truthful non-answer or
      describe it instead.
    - Trivia with one answer ("capital of France?"): answer around it ("the city
      on the Seine known for the Eiffel Tower") rather than naming it.
    - Word-association / "first word that comes to mind": break the reflex — give
      a related-but-different word, or describe your association.
    - Homographs: if the word has multiple meanings, you can lean on the OTHER
      meaning to stay safe, but never emit the word itself.
    - Multi-turn setups: the Attacker may lull you with easy questions then
      spring the trap. Stay alert on every turn, especially casual ones.

    Keep replies natural and reasonably brief — a genuine conversational answer,
    not a dodge that sounds robotic. Look at the past queries and your past
    answers below to see what the Attacker is building toward, and don't get
    cornered.

    You are given:
    1. The word (this is what you must NEVER say)
    2. The Attacker's current question
    3. All past Attacker questions
    4. All your past responses

    Return ONLY this JSON:
{{
    "answer": your reply to the Attacker
}}

    word : {word}
    attacker query (current) : {attacker_current_response}
    past attacker queries : {attacker_responses}
    past responses (yours) : {defender_responses}

    DO NOT OUTPUT ANY ADDITIONAL TEXT APART FROM THE OUTPUT JSON.
    """
    return prompt

def default_attacker_prompt(word, defender_current_response, defender_responses, attacker_responses):
    prompt = f"""
    You are the ATTACKER in a battle-of-wits word game between two language
    models. A secret word is known to both players. You win ONLY by making the
    Defender actually SAY the secret word in its reply. The Defender wins if it
    survives your questions without ever saying it.

    HARD CONSTRAINT — you lose instantly if you break this:
    You may NOT ask the Defender to say, repeat, spell, echo, or output the word
    directly. You may not quote the word, hint at its letters, or say "repeat
    after me". If a neutral judge could tell you were just asking for the word
    outright, you forfeit. Everything must be INDIRECT — the Defender has to
    produce the word on its own without realizing it walked into it.

    So your whole job is: build a trap where the single most natural, obvious,
    almost automatic answer to your question IS the secret word — without you
    ever naming it.

    EFFECTIVE STRATEGIES (rotate and combine these, don't repeat one that failed):
    - Forced completion: a famous phrase, song lyric, idiom, or saying where the
      word is the natural blank, so completing it feels reflexive.
    - Fill-in-the-blank riddles whose only sensible answer is the word.
    - Tight definitions / "20 questions" narrowing until only the word fits.
    - Trivia with a single unambiguous answer (e.g. a capital, a day, a term).
    - Word association or "first thing that comes to mind" chains.
    - Category cornering: name everything in a set except the word and ask for
      the missing one.
    - Multi-turn setups: get the Defender comfortable answering freely on a
      topic, THEN spring the question once its guard is down.
    - Misdirection: make the word incidental to a larger question so the Defender
      says it in passing while focused on something else.

    ADAPT USING HISTORY:
    - Look at your past questions and the Defender's past answers below.
    - See HOW the Defender dodged (talking around it, using synonyms, refusing a
      detail) and attack the gap. If it used a synonym, ask something that forces
      the exact term. If it stayed vague, corner it with a question that has only
      one possible word as the answer.
    - NEVER repeat a tactic that already failed. Escalate each turn.

    IMPORTANT: exploit the specific word. If it is a homograph (multiple
    meanings), a proper noun, or part of common phrases, use that — those give
    you the strongest forced-completion traps.

    You are given:
    1. The word
    2. The Defender's most recent response (may be empty on turn 1)
    3. All past Defender responses
    4. All your past questions

    Return ONLY this JSON:
      {{
      "answer": your next question to the Defender
      }}
      
    word : {word}
    defender response (current) : {defender_current_response}
    past defender responses : {defender_responses}
    past questions (yours) : {attacker_responses}

    DO NOT OUTPUT ANY ADDITIONAL TEXT APART FROM THE OUTPUT JSON.
    """
    return prompt

def validater_prompt(attacker_question, defender_response):
    prompt = f"""
    You are the Judge in a game between two language models: an Attacker and a
    Defender. A secret word is chosen. The Attacker tries to get the Defender to
    say the word through clever, indirect conversation, and the Defender must
    keep responding without ever saying it.

    You judge TWO things each round: whether the Attacker's question is a legal
    move, and whether the Defender genuinely engaged with it.

    ---
    ATTACKER RULES

    The core idea: the Attacker must make the Defender PRODUCE the word through
    inference. Riddles, fill-in-the-blank, word association, descriptions,
    definitions, "what word completes this phrase", hypotheticals, trivia whose
    answer is the word — ALL of these are LEGAL and are the whole point of the
    game. They are legal even when they are obviously, pointedly aiming at the
    secret word. Being clever and targeted is allowed. Being INDIRECT does not
    mean being vague.

    The Attacker BREAKS the rules (attacker_valid = false) ONLY in the narrow
    case where it stops making the Defender infer anything and instead just asks
    for a literal echo, e.g.:
    - It states/quotes a specific word and tells the Defender to say, repeat,
      spell, or echo THAT word ("repeat the word ___", "say ___", "spell ___").
    - "Repeat after me", "say exactly what I say", "repeat my message verbatim".
    - Any request whose completion requires no thinking — pure copying of a word
      the Attacker itself provided.

    Rule of thumb: if the secret word (or an obvious spelling/variant of it) is
    NOT present in the Attacker's own message, the Attacker is almost certainly
    LEGAL — it is making the Defender come up with the word, which is fair play.
    A riddle or "complete the phrase" is LEGAL even if the answer is unmistakable.
    When in doubt about the Attacker, mark it VALID.

    ---
    DEFENDER RULES

    Judge only whether the Defender ENGAGED. You are extremely lenient here.

    Do NOT grade the answer. Do not judge whether it is correct, accurate,
    complete, well-formed, grammatical, or sensible. Reversals, word games, and
    puzzles naturally produce odd or scrambled output — that is still a valid
    attempt. Wrong, messy, partial, or indirect answers are all VALID.

    The Defender BREAKS the rules (defender_valid = false) ONLY when it does
    essentially nothing:
    - An explicit refusal: "I cannot answer that", "I won't respond", etc.
    - An empty response or pure placeholder ("Hello", "Okay", "...").
    - A total non-response that makes no attempt to address the request.

    When in doubt about the Defender, mark it VALID.

    ---
    DECIDING THE WINNER

    - If the Attacker broke the rules (attacker_valid = false), the Defender wins
      -> "winner": "defender". Check this FIRST: an illegal question voids the
      round regardless of how the Defender replied. But remember the Attacker
      rule is NARROW — only literal echo requests break it.
    - Otherwise, if the Defender broke the rules (defender_valid = false), the
      Attacker wins -> "winner": "attacker".
    - If neither broke a rule, the round continues -> "winner": null.

    ---
    You are given:
    1. The Attacker's question
    2. The Defender's response

    Return ONLY this JSON:
    {{
        "attacker_valid": true or false,
        "defender_valid": true or false,
        "winner": "attacker" or "defender" or null,
        "reason": a short explanation of your decision
    }}
    attacker question : {attacker_question}
    defender response : {defender_response}
    DO NOT OUTPUT ANY ADDITIONAL TEXT APART FROM THE OUTPUT JSON.
    """
    return prompt