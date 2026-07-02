export const meta = {
  name: 'paraphrase-questions',
  description: 'Paraphrase all 17 psychometric question files for an Indian audience, in parallel, one agent per chunk',
  phases: [
    { title: 'Paraphrase', detail: 'one agent per ~28-item chunk' },
  ],
}

// Read the manifest of chunk ids that the splitter produced.
const manifest = args.manifest

const RUBRIC = `
You are paraphrasing items from a validated psychometric test so they are easy and vivid for a general INDIAN audience (English-medium, mixed regional backgrounds). You will receive a JSON chunk and must return paraphrased text for EVERY item.

ABSOLUTE INTEGRITY RULES (breaking any of these corrupts the test scoring):
1. Return EXACTLY one output entry per input item, using the SAME "id". Never invent, drop, merge, reorder, or rename ids.
2. NEVER change the psychological meaning or the DIRECTION of an item. If the original says you do something rarely/never, the paraphrase must still mean rarely/never. If it is a negative or reverse-worded statement, keep it negative. Reverse-keyed items depend on this exactly.
3. For forced_choice items: paraphrase BOTH options, and keep each "value" attached to the SAME meaning it had. Do not swap option meanings between values. Keep the two options as genuine opposites/contrasts, just like the original.
4. Keep the grammatical PERSON exactly as instructed (first person "I", second person "You", or third person "They"). Do not switch person.
5. NO EM-DASHES. Never use the — character. Use commas, "and", or split into a short second clause. Avoid semicolons too; prefer commas.
6. Keep it ONE sentence per item wherever possible (two short sentences max only if a concrete example needs it).

PARAPHRASING STYLE (this is the whole point):
- MEDIUM paraphrase depth: genuinely reword for clarity, do not just swap one word.
- Break down hard or academic vocabulary into plain words a 13-year-old would understand. Examples: "exhilarating" -> "thrilling", "I get a kick out of" -> "I really enjoy", "metabolise" -> "deal with", "vigorous" -> "full of energy", "rumination" -> "going over things again and again".
- Replace culture-specific or American references (Halloween, fraternities, dollars, baseball, prom) with neutral or Indian-relatable equivalents (a festival, college groups, money, a cricket match, a wedding). Keep money examples generic unless the item is about wealth.
- Use Indian ENGLISH register: professionally neutral, friendly, not slang, not Hinglish. Do not use north-Indian-only colloquialisms. It should read naturally to a Tamil, Bengali, Marathi, Telugu, or Punjabi English speaker alike.
- Where it genuinely helps the reader picture the item and go "ohhh, I get it now", add a SHORT concrete everyday example inside the sentence, set off by commas. Example: "I like to be the center of attention" -> "I enjoy being the center of attention, like being the one telling the story at a get-together." Keep examples brief and natural. Do NOT add examples to every single item; use them where an abstract item needs grounding. Never let an example change the meaning or narrow it too much.
- Keep the item answerable on its rating scale. Do not turn a statement into a question.
- Keep roughly the original length; do not write essays.

You will be given: the construct, the required voice/person, the rating scale meaning, and the items.

Return ONLY the structured output via the tool: an array "items", each with "id" and either "text" (for likert) or "options" (array of {value, text}) for forced_choice. Match the input kinds exactly.
`

const LIKERT_SCHEMA = {
  type: 'object',
  required: ['items'],
  additionalProperties: false,
  properties: {
    items: {
      type: 'array',
      items: {
        type: 'object',
        required: ['id'],
        additionalProperties: false,
        properties: {
          id: { type: 'string' },
          text: { type: 'string' },
          options: {
            type: 'array',
            items: {
              type: 'object',
              required: ['value', 'text'],
              additionalProperties: false,
              properties: {
                value: { type: 'integer' },
                text: { type: 'string' },
              },
            },
          },
        },
      },
    },
  },
}

phase('Paraphrase')

const results = await parallel(manifest.map((chunkId) => async () => {
  const prompt = `${RUBRIC}

Read the chunk file at this absolute path and paraphrase every item in it:
/tmp/para_in/${chunkId}.json

The file contains: test id, fmt (likert or forced_choice), construct, voice (the person/voice you MUST keep), scale, and items.

Process:
1. Read the file.
2. For each item, produce a paraphrase following ALL integrity rules and the style guide.
3. Double-check before returning: same count, same ids, same forced-choice values mapped to the same meanings, no em-dashes, correct person.
4. Return the structured output.

Return ONLY the structured array. Your "items" must have exactly the same ids as the input, in the same order.`

  const out = await agent(prompt, {
    label: `para:${chunkId}`,
    phase: 'Paraphrase',
    schema: LIKERT_SCHEMA,
    agentType: 'general-purpose',
  })
  return { chunkId, out }
}))

// Write each agent's raw structured output to /tmp/para_out for the deterministic merge step.
let ok = 0, fail = 0
for (const r of results) {
  if (!r || !r.out || !Array.isArray(r.out.items)) { fail++; continue }
  ok++
}
log(`Paraphrase phase done: ${ok} chunks returned, ${fail} failed/empty`)

return { results: results.filter(Boolean).map(r => ({ chunkId: r.chunkId, items: r.out?.items || null })) }
