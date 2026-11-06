# Skill: Write for AI

Use when the reader is an AI or a program: prompts, tool and connector descriptions, error messages, instructions between agents, saved session files, and step-by-step procedures.
Also use when the user asks to make text "clear", "unambiguous", or "simple English".
Not for friendly messages to people. For those, use `skills/write-for-humans.md`.

## Modes

- **Strict:** procedures, error messages, tool descriptions, instructions. Apply every rule below.
- **Light:** explanations, READMEs. Apply the sentence rules. Word rules are advice only.

## Sentence rules

1. One instruction per sentence.
2. Procedure sentences: at most 20 words. Explanation sentences: at most 25 words.
3. Use active voice. Name who does the action. ("The script deletes the file." not "The file is deleted.")
4. Use simple tenses: present, simple past, future with "will".
5. Write instructions as commands. ("Run the test." not "You should run the test.")
6. Do not drop small words. Keep "the", "a", "is", "that".
7. Put a condition before the action. ("If the test fails, stop.")
8. Give a warning before the step it applies to, not after.
9. One topic per paragraph. Number the steps of a procedure.

## Word rules

1. One word, one meaning. Pick a term and use it every time. Do not switch between "remove", "delete", and "drop" for the same action.
2. Use the common word: "use" not "utilize", "start" not "initiate", "help" not "facilitate", "about" not "approximately".
3. Avoid phrasal verbs with many meanings ("set up", "carry out", "come up"). Use one verb ("configure", "do", "occur").
4. Do not use a word as a different part of speech ("to action", "a must-have").
5. Avoid vague words: "some", "various", "appropriate", "etc.", "handle", "process" (as a vague verb).
6. Write numbers, units, names, and paths exactly.

## Steps

1. Choose the mode.
2. Split long sentences. Make each one do one job.
3. Replace passive and vague words.
4. Check that each term has one meaning in the whole text.
5. Check that every condition and warning comes before its action.

## Boundaries

- Never add facts. Never remove a fact.
- Keep uncertainty: if the source says "may", keep "may".
- Return only the rewritten text unless the user asks for a list of changes.

## Example

Before: "The tool will attempt to synchronize state across the configured backends and, if a conflict is detected, may resolve it automatically depending on the strategy, or otherwise surface it for review."

After: "The tool synchronizes state across the configured backends. If the tool finds a conflict, it reads the configured strategy. If the strategy allows it, the tool resolves the conflict. If not, the tool shows the conflict for manual review."
