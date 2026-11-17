# AI Interactions Log

## Agentic Workflow Enhancement

TuneJudge 2.0 runs a multi-step decision chain for every request, implemented in `src/pipeline.py` (`TuneJudge.run`):

1. **Check** the request (input guardrail): block empty, oversized, off-topic, or prompt-injection input.
2. **Plan** what to look for: parse the request into a taste profile (genre, mood, energy, acoustic).
3. **Act / retrieve:** rank the catalog with the 1.0 scorer, keep the top 5, and look up genre notes for them.
4. **Act / generate:** Gemini chooses 3 of the 5 songs and explains each, replying in JSON.
5. **Check its own work:** the output guardrail verifies every pick. If anything fails, the system writes specific feedback ("'X' is not one of the retrieved catalog songs. Only use these exact titles: …") and sends Gemini a corrected prompt. This happens at most once.
6. **Decide:** use the verified AI picks, or fall back to the rule-based top 3 if the AI still fails or the API errors.
7. **Score and report:** compute a confidence score, attach warnings, and log every step.

Each step is recorded in the result's trace. Print it with `python -m src.main --trace "<request>"`, or save it with `--save-trace`.

### Saved intermediate reasoning traces

- [`eval/sample_runs.md`](eval/sample_runs.md): full runs of the demo requests, each with its step-by-step trace. Regenerate with `python -m eval.capture_samples`.
- [`eval/results.md`](eval/results.md): the evaluation table, including the scripted runs where the model invents a song, returns broken JSON, or errors.

Example trace (scripted model that first recommends a song outside the catalog):

```
input guardrail: passed
parse: genre=any, mood=chill, energy=0.40, acoustic=no preference from words {'mood': 'chill', 'activity': 'studying'}
retrieve: Midnight Coding (2.72), Library Rain (2.67), Spacewalk Thoughts (2.57), Focus Flow (1.75), Coffee Shop Stories (1.71)
retrieve: genre notes for ['lofi', 'ambient', 'jazz']
verify (attempt 1): 1 ok, rejected ["'Blinding Lights' is not one of the retrieved catalog songs."]
verify (attempt 2): PASSED, 3 picks all in catalog
done: mode=ai, confidence=0.78 (high)
```
