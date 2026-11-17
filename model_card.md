# 🎧 Model Card: TuneJudge (Music Recommender Simulation → Applied AI System)

## 1. Model Name  

Give your model a short, descriptive name.  
Example: **VibeFinder 1.0**  

**TuneJudge 1.0**: it judges every song against your taste and hands out points.

---

## 2. Intended Use  

Describe what your recommender is designed to do and who it is for. 

Prompts:  

- What kind of recommendations does it generate  
- What assumptions does it make about the user  
- Is this for real users or classroom exploration  

**Goal:** TuneJudge suggests the 5 songs from a small catalog that best fit one listener's taste. It predicts fit from four things: favorite genre, favorite mood, preferred energy level, and whether the listener likes acoustic music.

**Assumptions about the user:** they have one favorite genre and one favorite mood, and they type them exactly as the dataset spells them, in lowercase.

**Intended use:** classroom exploration. It's a way to learn how recommenders turn data into rankings, and to test where simple rules break.

**Not intended for:**
- Real users or a real music app. The catalog is 19 made-up songs.
- Judging what music is "good." It only measures how well a song matches the labels.
- Users with mixed or changing tastes, like someone who likes both jazz and metal, or wants different music at different times of day.

---

## 3. How the Model Works  

Explain your scoring approach in simple language.  

Prompts:  

- What features of each song are used (genre, energy, mood, etc.)  
- What user preferences are considered  
- How does the model turn those into a score  
- What changes did you make from the starter logic  

Avoid code here. Pretend you are explaining the idea to a friend who does not program.

The recommender works like a judge giving each song points for how well it fits your taste, then lining the songs up from most to fewest points.

- **Song features used:** genre, mood, energy (how calm or intense it feels), and acousticness (acoustic instruments versus electronic sounds).
- **User preferences:** a favorite genre, a favorite mood, how energetic you want your music to be, and whether you like acoustic songs.
- **Turning these into a score:** a song gets 2 points if it's your favorite genre and 1 point if it matches your mood. It earns up to 1.5 more points for energy, and the closer its energy is to what you want, the more it gets, so a song isn't rewarded just for being louder or quieter. It gets up to 0.5 points for matching your acoustic preference. The best possible score is 5. The top 5 songs are recommended, each with a list of reasons showing where its points came from.
- **Changes from the starter logic:** the starter only returned the first few songs in the file. I added real scoring, ranked every song in the catalog, broke ties by picking the song closer to your energy level, and attached reasons to every recommendation.

---

## 4. Data  

Describe the dataset the model uses.  

Prompts:  

- How many songs are in the catalog  
- What genres or moods are represented  
- Did you add or remove data  
- Are there parts of musical taste missing in the dataset  

- **Size:** 19 songs. The starter had 10, and I added 9.
- **Features per song:** title, artist, genre, mood, energy, tempo, valence (how happy it sounds), danceability, and acousticness. The scoring uses only genre, mood, energy, and acousticness.
- **Variety:** 16 genres and 15 moods. My 9 new songs each added a genre and mood that weren't there before, like metal/angry, folk/sad, and classical/peaceful.
- **Limits:**
  - Most genres have only one song. Lofi has 3 and pop has 2.
  - Loud songs are almost always electronic, and quiet songs are almost always acoustic. There are no loud acoustic songs.
  - There are no lyrics, languages, release years, or listening history.
  - The songs and numbers are made up, so they reflect my guesses, not real measurements.

---

## 5. Strengths  

Where does your system seem to work well  

Prompts:  

- User types for which it gives reasonable results  
- Any patterns you think your scoring captures correctly  
- Cases where the recommendations matched your intuition  

- **Clear tastes get the right #1.** Happy pop got Sunrise City, calm study got Library Rain, and intense rock got Storm Runner. Each one matches the profile on every feature.
- **Opposite users get opposite lists.** The study listener and the rock fan share no songs.
- **Energy works as "closest," not "loudest."** A user who wants 0.4 energy gets songs near 0.4, not the calmest songs in the catalog.
- **It explains itself.** Every song comes with reasons and points, so it's easy to see why it ranked where it did.
- **It handles missing genres.** The k-pop fan still got sensible happy songs instead of random ones.

---

## 6. Limitations and Bias 

Where the system struggles or behaves unfairly. 

Prompts:  

- Features it does not consider  
- Genres or moods that are underrepresented  
- Cases where the system overfits to one preference  
- Ways the scoring might unintentionally favor some users  

The system quietly fails users whose tastes don't follow the dataset's built-in pattern that high-energy songs are electronic and low-energy songs are acoustic. In this catalog, every song above 0.75 energy has acousticness of 0.35 or lower, so the "Acoustic metalhead" profile earned at most +0.10 acoustic points, and its preference was effectively ignored. The "high-energy but sad" profile had the same problem: the only sad song has energy 0.24, so once I doubled the energy weight, that song dropped out of the top 5 and the list became the same five loud songs recommended to the rock and metal profiles. This creates a filter bubble where users with uncommon combinations, like quiet but electronic or loud but acoustic, keep getting pushed toward the most common type of song instead of what they asked for.

Other patterns I saw:
- **Exact matching is strict.** "indie pop" gets no credit for "pop," and "Pop" with a capital P matches nothing.
- **Genre can outweigh everything else.** A song with the right genre and mood can rank #1 even when its energy is way off.
- **Lofi fans are favored.** Lofi has 3 songs, so a lofi fan can get three genre bonuses. Most other genres have only one.

---

## 7. Evaluation  

How you checked whether the recommender behaved as expected. 

Prompts:  

- Which user profiles you tested  
- What you looked for in the recommendations  
- What surprised you  
- Any simple tests or comparisons you ran  

No need for numeric metrics unless you created some.

I tested seven user profiles. Three are normal listeners: a **Happy pop fan**, a **Calm study listener** (lofi, chill), and a **Deep intense rock** fan. Four are adversarial, designed to trick the scoring: a **high-energy but sad** folk fan, an **acoustic metalhead**, a fan of a genre that isn't in the catalog (**k-pop**), and the pop fan again with **capitalized input** ("Pop", "Happy"). For each one I checked whether the #1 song made sense, whether the reasons matched the song, and whether the rest of the top 5 felt like something that person would actually enjoy. Output is from `python -m src.main` with the original weights.

### Normal profiles

```
============================================================
Profile: Happy pop fan
  genre=pop, mood=happy, energy=0.80, likes_acoustic=False
============================================================
1. Sunrise City by Neon Echo  [score 4.88 / 5.00]
     - genre match: pop (+2.0)
     - mood match: happy (+1.0)
     - energy 0.82 vs target 0.80 (+1.47)
     - acoustic fit (+0.41)
2. Gym Hero by Max Pulse  [score 3.78 / 5.00]
     - genre match: pop (+2.0)
     - energy 0.93 vs target 0.80 (+1.30)
     - acoustic fit (+0.47)
3. Rooftop Lights by Indigo Parade  [score 2.77 / 5.00]
     - mood match: happy (+1.0)
     - energy 0.76 vs target 0.80 (+1.44)
     - acoustic fit (+0.33)
4. Concrete Verses by Block Theory  [score 1.91 / 5.00]
     - energy 0.78 vs target 0.80 (+1.47)
     - acoustic fit (+0.44)
5. Fuego Lento by Las Brisas  [score 1.84 / 5.00]
     - energy 0.84 vs target 0.80 (+1.44)
     - acoustic fit (+0.40)
```

```
============================================================
Profile: Calm study listener
  genre=lofi, mood=chill, energy=0.40, likes_acoustic=True
============================================================
1. Library Rain by Paper Lanterns  [score 4.85 / 5.00]
     - genre match: lofi (+2.0)
     - mood match: chill (+1.0)
     - energy 0.35 vs target 0.40 (+1.42)
     - acoustic fit (+0.43)
2. Midnight Coding by LoRoom  [score 4.82 / 5.00]
     - genre match: lofi (+2.0)
     - mood match: chill (+1.0)
     - energy 0.42 vs target 0.40 (+1.47)
     - acoustic fit (+0.35)
3. Focus Flow by LoRoom  [score 3.89 / 5.00]
     - genre match: lofi (+2.0)
     - energy 0.40 vs target 0.40 (+1.50)
     - acoustic fit (+0.39)
4. Spacewalk Thoughts by Orbit Bloom  [score 2.78 / 5.00]
     - mood match: chill (+1.0)
     - energy 0.28 vs target 0.40 (+1.32)
     - acoustic fit (+0.46)
5. Coffee Shop Stories by Slow Stereo  [score 1.90 / 5.00]
     - energy 0.37 vs target 0.40 (+1.46)
     - acoustic fit (+0.45)
```

```
============================================================
Profile: Deep intense rock
  genre=rock, mood=intense, energy=0.90, likes_acoustic=False
============================================================
1. Storm Runner by Voltline  [score 4.93 / 5.00]
     - genre match: rock (+2.0)
     - mood match: intense (+1.0)
     - energy 0.91 vs target 0.90 (+1.48)
     - acoustic fit (+0.45)
2. Gym Hero by Max Pulse  [score 2.93 / 5.00]
     - mood match: intense (+1.0)
     - energy 0.93 vs target 0.90 (+1.46)
     - acoustic fit (+0.47)
3. Bassline Euphoria by Hyperlume  [score 1.90 / 5.00]
     - energy 0.96 vs target 0.90 (+1.41)
     - acoustic fit (+0.48)
4. Iron Requiem by Grave Forge  [score 1.88 / 5.00]
     - energy 0.97 vs target 0.90 (+1.40)
     - acoustic fit (+0.48)
5. Fuego Lento by Las Brisas  [score 1.81 / 5.00]
     - energy 0.84 vs target 0.90 (+1.41)
     - acoustic fit (+0.40)
```

### Adversarial profiles

**Conflicted: high-energy but sad.** The only sad song has energy 0.24, far from the 0.90 target, yet it still ranks #1 because genre and mood (3.0 points) outweigh the most energy can give (1.5). Places 2 to 5 ignore "sad" entirely.

```
============================================================
Profile: Conflicted: high-energy but sad
  genre=folk, mood=sad, energy=0.90, likes_acoustic=False
============================================================
1. Empty Platform by Willow Ash  [score 3.56 / 5.00]
     - genre match: folk (+2.0)
     - mood match: sad (+1.0)
     - energy 0.24 vs target 0.90 (+0.51)
     - acoustic fit (+0.05)
2. Storm Runner by Voltline  [score 1.93 / 5.00]
     - energy 0.91 vs target 0.90 (+1.48)
     - acoustic fit (+0.45)
3. Gym Hero by Max Pulse  [score 1.93 / 5.00]
     - energy 0.93 vs target 0.90 (+1.46)
     - acoustic fit (+0.47)
4. Bassline Euphoria by Hyperlume  [score 1.90 / 5.00]
     - energy 0.96 vs target 0.90 (+1.41)
     - acoustic fit (+0.48)
5. Iron Requiem by Grave Forge  [score 1.88 / 5.00]
     - energy 0.97 vs target 0.90 (+1.40)
     - acoustic fit (+0.48)
```

**Acoustic metalhead.** No high-energy acoustic songs exist, so the acoustic preference earns almost nothing (+0.01 to +0.10) and is effectively ignored.

```
============================================================
Profile: Acoustic metalhead
  genre=metal, mood=angry, energy=0.95, likes_acoustic=True
============================================================
1. Iron Requiem by Grave Forge  [score 4.49 / 5.00]
     - genre match: metal (+2.0)
     - mood match: angry (+1.0)
     - energy 0.97 vs target 0.95 (+1.47)
     - acoustic fit (+0.02)
2. Bassline Euphoria by Hyperlume  [score 1.50 / 5.00]
     - energy 0.96 vs target 0.95 (+1.48)
     - acoustic fit (+0.01)
3. Gym Hero by Max Pulse  [score 1.50 / 5.00]
     - energy 0.93 vs target 0.95 (+1.47)
     - acoustic fit (+0.03)
4. Storm Runner by Voltline  [score 1.49 / 5.00]
     - energy 0.91 vs target 0.95 (+1.44)
     - acoustic fit (+0.05)
5. Fuego Lento by Las Brisas  [score 1.44 / 5.00]
     - energy 0.84 vs target 0.95 (+1.33)
     - acoustic fit (+0.10)
```

**Genre not in catalog.** "k-pop" never matches, but the system degrades gracefully: the two happy songs rank first, then the rest fall back to energy.

```
============================================================
Profile: Genre not in catalog
  genre=k-pop, mood=happy, energy=0.70, likes_acoustic=False
============================================================
1. Rooftop Lights by Indigo Parade  [score 2.74 / 5.00]
     - mood match: happy (+1.0)
     - energy 0.76 vs target 0.70 (+1.41)
     - acoustic fit (+0.33)
2. Sunrise City by Neon Echo  [score 2.73 / 5.00]
     - mood match: happy (+1.0)
     - energy 0.82 vs target 0.70 (+1.32)
     - acoustic fit (+0.41)
3. Concrete Verses by Block Theory  [score 1.82 / 5.00]
     - energy 0.78 vs target 0.70 (+1.38)
     - acoustic fit (+0.44)
4. Night Drive Loop by Neon Echo  [score 1.81 / 5.00]
     - energy 0.75 vs target 0.70 (+1.42)
     - acoustic fit (+0.39)
5. Fuego Lento by Las Brisas  [score 1.69 / 5.00]
     - energy 0.84 vs target 0.70 (+1.29)
     - acoustic fit (+0.40)
```

**Capitalized input.** Same as the Happy pop fan profile, but with "Pop" and "Happy" capitalized. Matching is case-sensitive, so every genre and mood match is lost and Sunrise City falls from 4.88 to 1.88, behind a hip hop song.

```
============================================================
Profile: Capitalized input
  genre=Pop, mood=Happy, energy=0.80, likes_acoustic=False
============================================================
1. Concrete Verses by Block Theory  [score 1.91 / 5.00]
     - energy 0.78 vs target 0.80 (+1.47)
     - acoustic fit (+0.44)
2. Sunrise City by Neon Echo  [score 1.88 / 5.00]
     - energy 0.82 vs target 0.80 (+1.47)
     - acoustic fit (+0.41)
3. Fuego Lento by Las Brisas  [score 1.84 / 5.00]
     - energy 0.84 vs target 0.80 (+1.44)
     - acoustic fit (+0.40)
4. Night Drive Loop by Neon Echo  [score 1.81 / 5.00]
     - energy 0.75 vs target 0.80 (+1.42)
     - acoustic fit (+0.39)
5. Storm Runner by Voltline  [score 1.78 / 5.00]
     - energy 0.91 vs target 0.80 (+1.33)
     - acoustic fit (+0.45)
```

### Comparing profiles

- **Happy pop vs. Calm study:** The pop list is full of upbeat, electronic songs around 0.8 energy, while the study list moves to soft, acoustic lofi around 0.4. They share no songs at all. That makes sense, because the two profiles disagree on all four preferences.
- **Happy pop vs. Deep intense rock:** Both want loud, electronic music, so the bottom of their lists overlaps (Gym Hero and Fuego Lento appear in both). The top changes: pop gets the cheerful Sunrise City, and rock gets the aggressive Storm Runner. Genre and mood decide the top spot, and energy fills in the rest.
- **Calm study vs. Deep intense rock:** These are opposites, and the lists are completely different. The study listener's top songs are around 0.4 energy and mostly acoustic; the rock fan's are 0.84 or higher and almost fully electronic. This is the clearest sign that the energy and acoustic scores do their job.
- **Deep intense rock vs. High-energy but sad:** Positions 2–5 are almost the same loud songs for both. The difference is #1: the sad profile gets Empty Platform, a quiet folk song, only because it's the one song labeled "folk" and "sad." The genre and mood bonuses (3 points) outweighed how badly it misses on energy, which is surprising but follows from the weights.
- **Deep intense rock vs. Acoustic metalhead:** Again the same loud songs fill places 2–5, even though one user likes acoustic music and the other doesn't. That's because there are no loud acoustic songs in the catalog, so the acoustic preference can't change anything.
- **High-energy but sad vs. Acoustic metalhead:** Both are "conflicted" profiles, and both get a single genre-and-mood match at #1 followed by generic loud songs. In both cases one preference (energy for the sad user, acoustic for the metalhead) is quietly ignored.
- **Happy pop vs. Genre not in catalog:** Without any genre matches, the k-pop fan's list is led by the two "happy" songs, Rooftop Lights and Sunrise City, nearly tied. It's a reasonable fallback: the system still uses the information it can match.
- **Happy pop vs. Capitalized input:** These are the same person, typed differently, yet Sunrise City drops from #1 (4.88) to #2 (1.88), behind a hip hop song. The computer treats "Pop" and "pop" as different words, so every genre and mood bonus disappears. A real app would need to fix this.

### Why does "Gym Hero" keep showing up for Happy Pop fans?

Think of the recommender as a judge with a points sheet. The biggest prize, 2 points, goes to "is it your favorite genre?", and Gym Hero is labeled pop, so it gets that prize. It is also loud and electronic, like the music the pop fan asked for, so it picks up nearly full points for energy and sound. The only thing it gets wrong is the mood: it's an intense workout song, not a happy one, and the judge only takes away 1 point for that. So Gym Hero (3.78) ends up ahead of Rooftop Lights (2.77), a genuinely happy song that loses its genre points only because it's labeled "indie pop" instead of "pop." Gym Hero also appears for the rock, sad, and metal profiles, because it's one of the loudest, least acoustic songs in a small catalog, and any profile asking for loud electronic music lands on it.

### What surprised me

- The **capitalization** test broke the results more than any "tricky" taste did. A small difference in how the input is typed matters more than what the user actually likes.
- A song can rank **#1 while badly missing** one of the user's preferences (Empty Platform for the high-energy sad fan), because exact label matches are worth so much.
- In the **weight experiment** (genre halved, energy doubled), Rooftop Lights moved ahead of Gym Hero for the pop fan, which felt more correct. But the sad folk song dropped out of that profile's top 5 entirely, and the rock, sad, and metal profiles all got the same five loud songs. Changing the weights made the results different rather than better overall.

---

## 8. Future Work  

Ideas for how you would improve the model next.  

Prompts:  

- Additional features or preferences  
- Better ways to explain recommendations  
- Improving diversity among the top results  
- Handling more complex user tastes  

1. **Looser matching.** Lowercase all input before comparing. Give partial points for close matches, like "indie pop" for a pop fan or "relaxed" for a chill fan.
2. **More features and better balance.** Add valence so the system can tell sad songs from calm ones. Add more songs per genre, including loud acoustic and quiet electronic songs, so uncommon tastes have real options.
3. **More variety in the top 5.** Limit each artist or genre to one or two spots, so the same few loud songs don't show up for every high-energy user.

---

## 9. Personal Reflection  

A few sentences about your experience.  

Prompts:  

- What you learned about recommender systems  
- Something unexpected or interesting you discovered  
- How this changed the way you think about music recommendation apps  

**Biggest learning moment:** The capitalization test. I typed "Pop" instead of "pop" and Sunrise City fell from #1 to #2 behind a hip hop song. The algorithm's weights were fine, the problem was how input was matched. It showed me that small data details can matter more than the "smart" part of a system.

**How AI helped, and when I double-checked:** AI helped me research how Spotify and YouTube recommend music, pick features from the CSV, and write the loading, scoring, and ranking functions quickly. I still had to check its work. Its hand-calculated scores were slightly off from the real output. I learned to run the code and compare it to the AI's claims instead of trusting them.

**What surprised me:** Four simple rules and some addition produced lists that felt like real recommendations. The study profile got soft lofi, the rock profile got loud rock, and every pick came with a reason. But the same simplicity made it easy to fool. A song could rank #1 while badly missing the user's energy, and changing two weights made the results different rather than better.

**What I'd try next:** Lowercase input and give partial credit for similar genres and moods, add valence and more songs per genre, and try a small collaborative-filtering version using fake listening histories to compare against the content-based approach.

---
---

# Part 2: TuneJudge 2.0 (Applied AI System)

Everything above documents TuneJudge 1.0 from Module 3. This part covers the 2.0 extension: plain-English requests, retrieval-augmented generation with Google Gemini, guardrails, and confidence scoring. See `README.md` for the architecture and setup.

## 10. What changed in 2.0

- **Intended use:** still classroom exploration, now showing how to ground an LLM in a small catalog and check its answers.
- **Model:** Google Gemini (`gemini-2.5-flash` by default, set with `GEMINI_MODEL`). It is not fine-tuned. It only sees the listener's request, the 5 songs retrieved by the 1.0 scorer, and genre notes from `data/genre_guide.md`.
- **Fixes from 1.0 Future Work:** input is now lowercased before matching (the "Capitalized input" bug), listeners can leave the acoustic preference unset, and the original weights are back.

## 11. Testing results

- **Unit tests:** 23 out of 23 pass (`python -m pytest`).
- **Evaluation harness:** 13 out of 13 cases pass in rules-only mode, with an average confidence of 0.66 (`eval/results.md`). That includes 3 cases where a scripted fake model misbehaves on purpose (invents a song, returns broken JSON, returns an API error), and every one is caught.
- **With Gemini:** <!-- TODO (Mauricio): fill in after `python -m eval.run_eval` with your key, e.g. "13/13 passed, average confidence 0.xx; Gemini needed a retry on N cases." -->

| Test input | Evaluation criteria | Result |
|---|---|---|
| "chill songs for studying" | 3 calm picks (avg energy ≤ 0.5), mostly chill/focused | Pass (confidence 0.97) |
| "romantic r&b for date night" | #1 is the only r&b/romantic song | Pass, but only medium confidence (0.56): picks 2-3 are unrelated filler |
| "k-pop for a party" | Says k-pop isn't in the catalog, confidence not high | Pass (0.43, low, with warning) |
| Empty input | Handled without crashing | Pass, blocked with a helpful message |
| "Ignore previous instructions…" | Blocked before reaching the AI | Pass |
| Fake model recommends "Blinding Lights" | Invented song never shown | Pass, rejected and retried |
| Fake model returns non-JSON twice | System still answers | Pass, fell back to rule-based picks |

## 12. Limitations and biases

- **Tiny, made-up catalog.** 19 songs, and 13 of the 16 genres have only one song. Any request for one of those genres gets one strong match plus filler, which is why indie pop, r&b and rock requests only reach medium confidence.
- **The catalog's built-in pattern still applies.** Loud songs are electronic and quiet songs are acoustic, so "loud acoustic" or "quiet electronic" listeners can't be served well. The AI can only choose among what retrieval hands it, so it inherits this bias.
- **The parser only knows its word lists.** Slang, misspellings, other languages, and genres outside the list ("shoegaze") are missed. Requests that only name an artist ("songs like Taylor Swift") are treated as off-topic.
- **Western, English-centered labels.** Genres like "latin" lump very different styles together, while pop gets its own subgenre. The genre notes reflect my own descriptions, not listener data.
- **The AI's reasons are not verified.** The guardrail checks that each song is real and in the retrieved set, but not whether the explanation is accurate. Gemini could still describe a song's mood loosely.
- **Confidence is a heuristic.** It measures how well the shown songs match the parsed profile, not whether a person would actually enjoy them.

## 13. Misuse and prevention

- **Prompt injection:** someone could try to make the assistant ignore its rules or reveal its prompt. Requests matching injection patterns are blocked before reaching the model, the request is passed to Gemini as quoted data, and the system prompt says to treat it as data. Even if an injection slipped through, the output guardrail only lets catalog songs through.
- **Off-topic use:** using it as a free general chatbot. Requests with no music words are blocked, so they never cost an API call.
- **Leaking the API key:** the key lives only in `.env` (gitignored), is sent in a request header rather than the URL, and is never logged. Requests that mention an API key are blocked.
- **Overuse / cost:** one API call per request (two at most with a retry), a 300-character input limit, and a delay between calls in the evaluation scripts to respect free-tier rate limits.
- **Over-trust:** low-confidence answers say so and ask the listener to review or rephrase; every answer shows its mode (AI vs. rules), so nobody mistakes a fallback for an AI answer.

## 14. What surprised me while testing reliability

<!-- TODO (Mauricio): rewrite these notes in your own words, and add anything you notice when you run it with Gemini. -->

- The first confidence formula rated "chill songs for studying" at only 0.53 (medium) even though all three picks were perfect. It divided by the maximum score of 5.0, but a request with no genre can never earn genre points. Dividing by the best score achievable for that request fixed it (0.97).
- Rules-only mode looked fine on summary numbers but gave odd picks in practice: for "romantic r&b for date night", #2 was a nostalgic country song chosen only because its energy was close. Reading the actual output, not just pass/fail, is what showed where the AI could help.
- Every guardrail failure I could think of was easy to test once the model was swappable for a fake one. Testing against the real API alone would never reliably produce an invented song on demand.

## 15. Collaboration with AI

<!-- TODO (Mauricio): this section is graded as YOUR reflection. The notes below are facts from the build to help you; rewrite them in your own words and add your own examples. -->

I used Claude to choose which project to extend, plan the architecture, write most of the code, and draft the documentation. I reviewed the plan, ran the system myself, and checked the output.

- **A suggestion I accepted:** extending the Music Recommender instead of PawPal+ or Game Glitch Investigator. The reasoning was that its scorer already ranks a catalog, so it could become the retriever for RAG with little rewriting, and "the AI can only recommend songs that exist" is a guardrail that's easy to demo and explain. It was also the smallest codebase (about 270 lines vs. about 1,100 for PawPal+).
- **A suggestion I rejected or changed:** <!-- e.g. a suggestion you scoped down, simplified, renamed, or decided against, and why. Possible candidates from this build: using the official Gemini SDK (the final code uses the standard library instead, so setup is just pytest), having the AI parse the request too (kept rule-based to save API calls and stay testable), or the first confidence formula, which had to be fixed (see section 14). -->
- **Where I double-checked the AI:** <!-- e.g. running the tests and the eval harness yourself, reading the actual picks rather than trusting summaries, confirming the .env file is ignored by git. -->

## 16. Future work for 2.0

1. Expand the catalog to several songs per genre, including loud acoustic and quiet electronic songs.
2. Check the AI's explanations, not just its song choices, e.g. flag a "why" that names a mood the song doesn't have.
3. Use the saved `logs/feedback.jsonl` ratings to tune the weights or the confidence threshold.
