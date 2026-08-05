import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import api from '../utils/api'
import ParticleCanvas from '../components/ParticleCanvas'
import bgImage from '../assets/Image60.jpeg'

const S = {
  fontDisplay: "'Cormorant Garamond', Georgia, serif",
  fontSC: "'Cinzel', serif",
  fontBody: "'Playfair Display', Georgia, serif",
  fontMono: "'JetBrains Mono', monospace",
  textPrim: '#F4F7FA',
  textSec: 'rgba(244,247,250,0.60)',
  textMuted: 'rgba(244,247,250,0.32)',
  iris: '#D8E8F4',
  irisDim: '#8A9EAE',
  frost: 'rgba(200,214,230,0.06)',
  frostBorder: 'rgba(215,228,242,0.18)',
}

const TEST_META = {
  hexaco:     { name: 'Six-Trait Personality',     short: 'Six Traits',          roman: 'I',    accent: '#C8D8E8', metal: 'linear-gradient(135deg,#8090a2 0%,#c8d8e8 18%,#eef6fc 36%,#d8e8f4 54%,#f4f8fc 72%,#b8ccda 100%)', glow: 'rgba(200,220,244,0.22)' },
  sixteenpf:  { name: 'Sixteen Personality Traits',          short: '16 Traits',      roman: 'II',   accent: '#C0B8D0', metal: 'linear-gradient(135deg,#9088a8 0%,#c0b8d0 18%,#dcd8ec 36%,#ccc8e0 54%,#eceaf4 72%,#b8b0cc 100%)', glow: 'rgba(192,184,208,0.20)' },
  darktriad:  { name: 'Dark Traits',       short: 'Dark Traits',      roman: 'III',  accent: '#B0BCC8', metal: 'linear-gradient(135deg,#6a7a88 0%,#b0bcc8 18%,#d8e0e8 36%,#c4ccd6 54%,#eaecf0 72%,#a0aab4 100%)', glow: 'rgba(176,188,200,0.20)' },
  fti:        { name: 'Temperament Type',     short: 'Temperament',     roman: 'IV',   accent: '#CFC0DA', metal: 'linear-gradient(135deg,#7a6090 0%,#cfc0da 18%,#e8dcf0 36%,#d8c8e8 54%,#f0e8f8 72%,#b0a0c8 100%)', glow: 'rgba(220,200,232,0.20)' },
  npi:        { name: 'How You See Yourself',      short: 'Self-View',       roman: 'V',    accent: '#DCB8C8', metal: 'linear-gradient(135deg,#a06080 0%,#dcb8c8 18%,#f0d8e0 36%,#e0c8d4 54%,#f8e8ec 72%,#c098a8 100%)', glow: 'rgba(232,200,216,0.20)' },
  ambi:       { name: 'Broad Personality Scan', short: 'Broad Scan',      roman: 'VI',   accent: '#A8B0C8', metal: 'linear-gradient(135deg,#707890 0%,#a8b0c8 18%,#d8dcec 36%,#c4ccd8 54%,#e8eef4 72%,#9098b0 100%)', glow: 'rgba(200,208,228,0.20)' },
  pid5:       { name: 'Five Trait Styles', short: 'Five Styles',    roman: 'VII',  accent: '#B8C0D8', metal: 'linear-gradient(135deg,#7888a0 0%,#b8c0d8 18%,#dce4f0 36%,#c8d0e4 54%,#ecf0f8 72%,#9ca8c0 100%)', glow: 'rgba(206,216,232,0.20)' },
  hsq:        { name: 'Humor Style',           short: 'Humor',           roman: 'VIII', accent: '#DCC8A0', metal: 'linear-gradient(135deg,#b08840 0%,#dcc8a0 18%,#f4e8c8 36%,#e8d8b0 54%,#f8efce 72%,#c0a880 100%)', glow: 'rgba(232,216,176,0.20)' },
  kims:       { name: 'Mindfulness Skills',     short: 'Mindfulness',     roman: 'IX',   accent: '#B8D8B8', metal: 'linear-gradient(135deg,#609060 0%,#b8d8b8 18%,#dcecdc 36%,#c8e0c8 54%,#ecf6ec 72%,#90b890 100%)', glow: 'rgba(200,224,200,0.20)' },
  gcbs:       { name: 'Conspiracy Beliefs',   short: 'Conspiracy',       roman: 'X',    accent: '#D8B898', metal: 'linear-gradient(135deg,#a07840 0%,#d8b898 18%,#ecd8b8 36%,#e0c8a8 54%,#f4e8cc 72%,#b89878 100%)', glow: 'rgba(228,208,176,0.20)' },
  aesthetic:  { name: 'Aesthetic Taste',      short: 'Aesthetic',       roman: 'XI',   accent: '#C8C4D4', metal: 'linear-gradient(135deg,#9490a0 0%,#c8c4d4 18%,#e8e4f4 36%,#d4d0e4 54%,#f4f0fc 72%,#bab8cc 100%)', glow: 'rgba(200,196,212,0.20)' },
  riasec:     { name: 'Career Type',          short: 'Career',          roman: 'XII',  accent: '#C0CCD6', metal: 'linear-gradient(135deg,#8898a4 0%,#c0ccd6 18%,#dce8f0 36%,#ccdae6 54%,#e8f2f8 72%,#b4c4cc 100%)', glow: 'rgba(192,204,214,0.20)' },
  attachment: { name: 'Attachment Style',     short: 'Attachment',      roman: 'XIII', accent: '#BCC0D4', metal: 'linear-gradient(135deg,#9090a8 0%,#bcc0d4 18%,#dcdee8 36%,#cccee0 54%,#e8eaf4 72%,#b4b8cc 100%)', glow: 'rgba(188,192,212,0.20)' },
  pvq:        { name: 'Core Values',          short: 'Values',          roman: 'XIV',  accent: '#C8D8B0', metal: 'linear-gradient(135deg,#809060 0%,#c8d8b0 18%,#e8f0d8 36%,#d8e0c0 54%,#f0f4e0 72%,#a8b890 100%)', glow: 'rgba(216,224,192,0.20)' },
  bpnss:      { name: 'Inner Needs',        short: 'Inner Needs',           roman: 'XV',   accent: '#A8D8C8', metal: 'linear-gradient(135deg,#609088 0%,#a8d8c8 18%,#d0ecdc 36%,#bce0d0 54%,#e4f4e8 72%,#88b8a8 100%)', glow: 'rgba(196,224,208,0.20)' },
  dass:       { name: 'Mood and Stress',   short: 'Stress and Mood', roman: 'XVI',  accent: '#C0C0D0', metal: 'linear-gradient(135deg,#9090a2 0%,#c0c0d0 18%,#e0e0ec 36%,#cccce0 54%,#f0f0f8 72%,#b8b8cc 100%)', glow: 'rgba(192,192,208,0.20)' },
  who5:       { name: 'Wellbeing Check',      short: 'Wellbeing',       roman: 'XVII', accent: '#B8E0C8', metal: 'linear-gradient(135deg,#609880 0%,#b8e0c8 18%,#d8eed8 36%,#c4e4cc 54%,#e8f6e8 72%,#88c0a0 100%)', glow: 'rgba(208,232,216,0.20)' },
}
const DEFAULT_META = TEST_META.hexaco

// ─── Helpers ─────────────────────────────────────────────────────────────────
function gaussianY(x, mean, sigma) {
  return Math.exp(-0.5 * Math.pow((x - mean) / sigma, 2)) / (sigma * Math.sqrt(2 * Math.PI))
}

// Natural-language mapping from trait names to everyday-behaviour phrases.
// Used to turn a compatibility cluster's average-member profile into a plain
// two-sentence description a lay reader can understand, without dropping to
// psychology jargon like "elevated Machiavellianism" or "low Detachment".
const TRAIT_BEHAVIOR = {
  // HEXACO
  'Honesty-Humility': { high: 'plays fair and dislikes cutting corners', low: 'is willing to play strategically to get what they want' },
  Emotionality:        { high: 'feels things strongly and gets attached quickly', low: 'stays cool under pressure and rarely fusses' },
  Extraversion:        { high: 'lights up around other people', low: 'recharges best on their own' },
  Agreeableness:       { high: 'is patient, forgiving, and easy to get along with', low: 'holds their ground and pushes back when needed' },
  Conscientiousness:   { high: 'is organised, dependable, and gets things finished', low: 'is spontaneous and treats plans as loose suggestions' },
  Openness:            { high: 'is curious about new ideas and unusual experiences', low: 'knows what they like and sticks with the familiar' },
  // Dark triad
  Machiavellianism:    { high: 'thinks a few moves ahead and reads people strategically', low: 'takes situations at face value without much scheming' },
  Narcissism:          { high: 'carries a strong sense of their own importance', low: 'is comfortable letting others take the spotlight' },
  Psychopathy:         { high: 'stays emotionally detached and cool with risk', low: 'is empathic and cautious about hurting others' },
  // FTI
  Explorer:            { high: 'craves novelty and chases new experiences', low: 'prefers a familiar rhythm to constant change' },
  Builder:             { high: 'is steady, loyal, and follows through on commitments', low: 'is looser with routines and long-term plans' },
  Director:            { high: 'decides quickly and takes charge without hesitation', low: 'holds off on decisions and prefers to consult first' },
  Negotiator:          { high: 'reads a room intuitively and puts others at ease', low: 'takes a more direct, less mood-reading approach' },
  // NPI
  Authority:           { high: 'steps into leadership without needing a push', low: 'is happy in supporting rather than commanding roles' },
  'Self-Sufficiency':  { high: 'trusts their own judgement without needing outside approval', low: 'looks to others for validation and input' },
  Superiority:         { high: 'quietly believes they operate at a higher level than most', low: 'sees themselves as roughly on par with peers' },
  Exhibitionism:       { high: 'enjoys being noticed and knows how to make it happen', low: 'stays out of the spotlight by choice' },
  Exploitativeness:    { high: 'is willing to use an edge when they see one', low: 'is careful not to take advantage of anyone' },
  Vanity:              { high: 'puts real care into how they look and present themselves', low: 'gives image and appearance little thought' },
  Entitlement:         { high: 'has a strong sense of what they deserve from others', low: 'expects to earn things rather than be handed them' },
  // Attachment
  Secure:              { high: 'is comfortable being close without losing themselves', low: 'finds close relationships harder to relax into' },
  Anxious:             { high: 'worries about where they stand with the people they love', low: 'rarely stresses about what others think of them' },
  Avoidant:            { high: 'keeps some emotional distance even in close relationships', low: 'is happy to let people in fully' },
  // PID-5
  'Negative Affectivity': { high: 'feels difficult emotions strongly and holds them longer', low: 'lets bad moods pass without lingering' },
  Detachment:          { high: 'is content keeping their own company', low: 'seeks connection and gets energised by it' },
  Antagonism:          { high: 'is unbothered about managing what others think of them', low: 'works to keep relationships smooth' },
  Disinhibition:       { high: 'acts on impulse more than they plan', low: 'thinks things through before acting' },
  Psychoticism:        { high: 'thinks in unconventional ways others sometimes find hard to follow', low: 'thinks in fairly conventional, predictable ways' },
  // Wellbeing / DASS / WHO-5
  Depression:          { high: 'is carrying real emotional heaviness right now', low: 'feels emotionally settled and motivated' },
  Anxiety:             { high: 'is running with a lot of worry lately', low: 'takes life in stride without much anxious noise' },
  Stress:              { high: 'is dealing with more pressure than is comfortable', low: 'is under a manageable amount of pressure' },
  Wellbeing:           { high: 'is broadly thriving lately', low: 'is running low on energy and mood' },
  // RIASEC
  Realistic:           { high: 'would rather build or make than sit and discuss', low: 'is drawn away from hands-on, mechanical work' },
  Investigative:       { high: 'loves figuring out how things work', low: 'is less pulled toward analytical work' },
  Artistic:            { high: 'needs a creative outlet to feel like themselves', low: 'is less drawn to expressive, artistic work' },
  Social:              { high: 'is at their best when helping other people', low: 'is less energised by direct people-work' },
  Enterprising:        { high: 'is a natural persuader and enjoys leading initiatives', low: 'is less interested in selling or leading' },
  Conventional:        { high: 'thrives with structure, order, and clear systems', low: 'is less at home with strict procedures' },
  // KIMS
  Observing:           { high: 'notices small shifts in mood, body, and surroundings', low: 'pays less attention to inner and sensory detail' },
  Describing:          { high: 'puts inner experience into words easily', low: 'finds it hard to describe what they feel' },
  'Acting with Awareness': { high: 'is present in what they are doing rather than on autopilot', low: 'often runs through activities half-elsewhere' },
  'Accepting without Judgment': { high: 'lets experience be what it is instead of fighting it', low: 'tends to fight or judge their own reactions' },
  // Humor
  Affiliative:         { high: 'uses humor to bring people together', low: 'is less playful in group settings' },
  'Self-Enhancing':    { high: 'finds the funny angle when things get hard', low: 'processes difficulty without much humor buffer' },
  Aggressive:          { high: 'has a sharper, edgier sense of humor', low: 'keeps humor gentle and inclusive' },
  'Self-Defeating':    { high: 'often makes themselves the butt of the joke', low: 'protects their own dignity even in humor' },
  // 16PF
  Warmth:              { high: 'is instantly approachable and easy to be around', low: 'is more reserved and takes time to warm up' },
  Reasoning:           { high: 'moves quickly through abstract problems', low: 'prefers concrete, worked-out thinking' },
  Stability:           { high: 'is emotionally grounded and hard to rattle', low: 'is more reactive when things get stressful' },
  Dominance:           { high: 'takes charge naturally and directs the room', low: 'defers to others and prefers a supporting role' },
  Liveliness:          { high: 'brings energy and playfulness into a room', low: 'has a calmer, more serious presence' },
  Sensitivity:         { high: 'is emotionally attuned to nuance and mood', low: 'is more matter-of-fact and less mood-tracking' },
  Vigilance:           { high: 'is naturally cautious about people trusting too fast', low: 'gives people the benefit of the doubt easily' },
  Privateness:         { high: 'guards their inner world carefully', low: 'is open about what is going on inside' },
  Apprehension:        { high: 'second-guesses themselves and worries more than they show', low: 'is self-assured and stops replaying decisions' },
  'Openness-to-Change': { high: 'welcomes new ways of doing things', low: 'trusts what has worked before and resists change for its own sake' },
  'Self-Reliance':     { high: 'prefers to figure things out alone', low: 'draws heavily on their circle to think things through' },
  Perfectionism:       { high: 'holds a high bar for how work should turn out', low: 'is comfortable calling something good enough' },
  Tension:             { high: 'is often wound up under the surface', low: 'is relaxed and hard to rattle' },
  // Values
  'Self-Direction':    { high: 'needs to think for themselves and do things their own way', low: 'is comfortable working within others\' plans' },
  Universalism:        { high: 'cares about fairness at a broad, societal scale', low: 'focuses attention closer to home' },
  Achievement:         { high: 'is driven by concrete accomplishments', low: 'measures themselves less by outward achievement' },
  Security:            { high: 'prizes stability, predictability, and safety', low: 'is less bothered by uncertainty' },
  Stimulation:         { high: 'needs novelty and intensity to feel alive', low: 'is content with a lower-key life' },
  Conformity:          { high: 'respects the norms that hold groups together', low: 'is less concerned with social rules for their own sake' },
  Tradition:           { high: 'finds meaning in inherited practices and values', low: 'is not particularly attached to tradition' },
  Hedonism:            { high: 'is unapologetic about seeking pleasure and enjoyment', low: 'is more restrained about pleasure-seeking' },
  Power:               { high: 'wants status and influence over decisions', low: 'is not chasing rank or authority' },
  Benevolence:         { high: 'is deeply invested in the wellbeing of their inner circle', low: 'is more independent from close-group loyalties' },
  // Needs
  Autonomy:            { high: 'is getting to make their own choices day to day', low: 'feels boxed in by external demands' },
  Competence:          { high: 'feels effective and capable in what they do', low: 'is not currently using their skills fully' },
  Relatedness:         { high: 'feels genuinely connected to the people around them', low: 'is running low on real connection' },
  // Aesthetic
  Intense:             { high: 'is drawn to raw, powerful, edgy work', low: 'prefers softer, more polished aesthetics' },
  Mainstream:          { high: 'genuinely enjoys widely popular tastes', low: 'gravitates away from mainstream taste' },
  Traditional:         { high: 'is moved by classical, rooted forms of beauty', low: 'is less drawn to traditional aesthetic forms' },
  Visual:              { high: 'has a trained eye for design, colour, and composition', low: 'is less visually oriented in their tastes' },
  // Conspiracy beliefs
  'Government Malfeasance': { high: 'is skeptical of what governments say vs. do', low: 'gives official channels the benefit of the doubt' },
  'Malevolent Global':      { high: 'sees coordinated agendas behind big global events', low: 'is skeptical of grand-scheme explanations' },
  'Extraterrestrial Coverup': { high: 'suspects there is more to unexplained phenomena than admitted', low: 'trusts official science on unexplained phenomena' },
  'Personal Wellbeing Threats': { high: 'is alert to hidden threats that institutions downplay', low: 'trusts institutions to disclose real threats' },
  'Control of Information': { high: 'believes public information is managed to serve powerful interests', low: 'takes public information mostly at face value' },
  // AMBI
  'Affect Regulation':  { high: 'manages emotional state calmly under pressure', low: 'gets shaken by pressure more visibly' },
  'Social Drive':       { high: 'is pulled toward people and gets energy from them', low: 'is drained by heavy social exposure' },
  'Energy Drive':       { high: 'operates at high output and initiates things', low: 'moves at a lower-key, less driven pace' },
  'Identity Coherence': { high: 'has a stable sense of who they are under pressure', low: 'is still working out who they are in different rooms' },
}

// Natural-language behavioural sketch of a compatibility cluster, derived
// from the average member's trait percentiles. Prefers plain-English phrasing
// from TRAIT_BEHAVIOR over jargon so a lay reader can grasp the archetype
// without decoding trait names. Falls back to a generic trait-list phrasing
// only when no mapped phrases are available.
function behaviorSummary(profile) {
  if (!Array.isArray(profile) || profile.length === 0) return ''
  const sorted = [...profile].sort((a, b) => (b.percentile || 0) - (a.percentile || 0))
  const highs = []
  for (const t of sorted) {
    if ((t.percentile || 0) < 60) break
    const phrase = TRAIT_BEHAVIOR[t.trait]?.high
    if (phrase) highs.push(phrase)
    if (highs.length >= 2) break
  }
  const lows = []
  for (let i = sorted.length - 1; i >= 0 && lows.length < 1; i--) {
    if ((sorted[i].percentile || 0) > 40) break
    const phrase = TRAIT_BEHAVIOR[sorted[i].trait]?.low
    if (phrase) lows.push(phrase)
  }
  const parts = []
  if (highs.length) {
    const joined = highs.length === 2 ? `${highs[0]}, and ${highs[1]}` : highs[0]
    parts.push(`Usually ${joined}.`)
  }
  if (lows.length) {
    parts.push(`On the other hand, ${lows[0]}.`)
  }
  if (parts.length === 0) {
    // Fully moderate profile.
    return 'Runs a balanced profile without any single trait dominating how they show up.'
  }
  return parts.join(' ')
}

function computeStats(traitScores, percentiles) {
  const pctVals = Object.values(percentiles)
  if (!pctVals.length) return { topPct: 50, topTrait: '', medianPct: 50 }
  const sorted = [...pctVals].sort((a, b) => b - a)
  const topEntry = Object.entries(percentiles).sort((a, b) => b[1] - a[1])[0]
  const median = sorted[Math.floor(sorted.length / 2)]
  return { topPct: Math.round(topEntry[1]), topTrait: topEntry[0], medianPct: Math.round(median) }
}

function generatePlainEnglishSummary(testType, traitScores, percentiles, archetypeName, archetypeDesc, insights) {
  const sorted = Object.entries(percentiles).sort((a, b) => b[1] - a[1])
  const high = sorted.filter(([, v]) => v >= 70).map(([k]) => k)
  const low = sorted.filter(([, v]) => v <= 30).map(([k]) => k)
  const lines = []
  if (archetypeName) lines.push(`Your archetype is ${archetypeName}. ${archetypeDesc || ''}`.trim())
  if (high.length) lines.push(`You score unusually high in ${high.slice(0, 3).join(', ')}. These traits are genuinely prominent parts of how you show up.`)
  if (low.length) lines.push(`You score low in ${low.slice(0, 2).join(' and ')}. Low scores are not bad, they simply describe how you are wired.`)
  if (testType === 'hexaco') {
    const h = percentiles['Honesty-Humility'] || 50, e = percentiles['Extraversion'] || 50
    const o = percentiles['Openness'] || 50, c = percentiles['Conscientiousness'] || 50
    const em = percentiles['Emotionality'] || 50, a = percentiles['Agreeableness'] || 50
    if (h > 65) lines.push('You tend to be sincere, fair, and uninterested in working the system for your own gain.')
    else if (h < 35) lines.push('You are comfortable using strategic angles when they serve you. Pragmatism over principle in tight spots.')
    if (e > 65) lines.push('You tend to feel energized around people and seek out social situations naturally.')
    else if (e < 35) lines.push('You recharge best on your own. Social situations drain your energy more than they fill it.')
    if (o > 65) lines.push('You are drawn to new ideas, experiences, and ways of thinking. Curiosity drives you.')
    if (c > 65) lines.push('You get things done. You are organized and follow through on what you start.')
    if (em > 65) lines.push('You feel emotions intensely and are more sensitive to what is happening around you than most.')
    if (a > 65) lines.push('You genuinely care about others and tend to put people at ease.')
  } else if (testType === 'darktriad') {
    const m = percentiles['Machiavellianism'] || 50, na = percentiles['Narcissism'] || 50, p = percentiles['Psychopathy'] || 50
    if (m < 35 && na < 35 && p < 35) lines.push('Your scores are low across all three dark traits. You tend to be cooperative, straightforward, and warm.')
    if (m > 65) lines.push('You think strategically and are comfortable playing a longer game to get what you want.')
    if (na > 65) lines.push('You have a strong sense of your own importance and expect recognition.')
    if (p > 65) lines.push('You are calm in situations that would unsettle most people. You can detach emotionally when needed.')
  } else if (testType === 'dass') {
    const d = percentiles['Depression'] || 50, ax = percentiles['Anxiety'] || 50, st = percentiles['Stress'] || 50
    if (d < 35 && ax < 35 && st < 35) lines.push('Your emotional scores are low right now. You appear to be in a relatively stable and settled place.')
    if (d > 65) lines.push('Your depression score is elevated. You may be experiencing a flatness or lack of motivation worth paying attention to.')
    if (ax > 65) lines.push('You are carrying more anxiety than most people at the moment.')
    if (st > 65) lines.push('Your stress load is high. You are dealing with more pressure than is comfortable or sustainable.')
  } else if (testType === 'attachment') {
    const sec = percentiles['Secure'] || 50, anx = percentiles['Anxious'] || 50, avo = percentiles['Avoidant'] || 50
    if (sec > 60) lines.push('You are mostly secure in how you relate to others. You can be close without losing yourself.')
    if (anx > 65) lines.push('You tend to worry about relationships more than most, and may want more closeness than you feel comfortable asking for.')
    if (avo > 65) lines.push('You tend to keep emotional distance in close relationships. Vulnerability can feel unnecessary to you.')
  } else if (testType === 'aesthetic') {
    const top2 = sorted.slice(0, 2).map(([k]) => k)
    lines.push(`Your aesthetic is most strongly shaped by ${top2.join(' and ')}. These are the registers that move you without thinking about it.`)
  } else if (testType === 'riasec') {
    const top2 = sorted.slice(0, 2).map(([k]) => k)
    lines.push(`Your Holland code begins with ${top2.map(t => t[0]).join('')}. Work matching ${top2.join(' and ')} tends to bring out your best.`)
  } else if (testType === 'who5') {
    const w = percentiles['Wellbeing'] || 50
    if (w < 30) lines.push('Your wellbeing over the last two weeks reads as low. If this persists, it is worth taking seriously.')
    else if (w > 70) lines.push('Your wellbeing over the last two weeks reads as broadly healthy.')
    else lines.push('Your wellbeing over the last two weeks is in a moderate range.')
  } else if (testType === 'pvq') {
    const top3 = sorted.slice(0, 3).map(([k]) => k)
    if (top3.length) lines.push(`Your three strongest values are ${top3.join(', ')}. These are what you sort decisions by, even without thinking about it.`)
    const bottom = sorted.slice(-1)[0]
    if (bottom && bottom[1] < 30) lines.push(`Your lowest-ranked value is ${bottom[0]}. People who lead with this value may feel out of step with you.`)
  } else if (testType === 'bpnss') {
    for (const need of ['Autonomy', 'Competence', 'Relatedness']) {
      const p = percentiles[need] || 50
      if (p > 65) lines.push(`Your ${need.toLowerCase()} need is being well met right now. This is one of the foundations holding you up.`)
      else if (p < 35) lines.push(`Your ${need.toLowerCase()} need is currently under-fed. When this runs low for a long time, it drains motivation and mood.`)
    }
    if (!lines.length) lines.push('All three of your basic psychological needs are being moderately met.')
  } else if (testType === 'pid5') {
    const top = sorted[0]
    if (top && top[1] > 65) lines.push(`Your most pronounced trait pattern is ${top[0]}. This describes a style, not a clinical condition.`)
    if (sorted.every(([, v]) => v < 50)) lines.push('Your trait scores are uniformly low. This is a stable, low-intensity profile.')
    else if (!lines.length) lines.push('Your trait pattern is mixed across the five domains. None of these are diagnoses, only personality style descriptions.')
  }
  if (insights?.insights?.length) {
    for (const ins of insights.insights.slice(0, 2)) lines.push(ins)
  }
  return lines.filter(Boolean).slice(0, 6)
}

const TRAIT_FUN_FACTS = {
  hexaco: {
    'Honesty-Humility': { high: "You find it genuinely uncomfortable to cut corners or manipulate others, even when you could easily get away with it.", low: "You're pragmatic. If a situation calls for a little spin or strategy, you don't feel guilty using it." },
    Emotionality: { high: "You feel things at full volume. That sensitivity is also what makes you deeply perceptive.", low: "Emotions don't knock you off balance easily. You stay level-headed in situations that rattle others." },
    Extraversion: { high: "You literally get energy from being around people. Your social battery is solar-powered.", low: "Cancelled plans equal best plans. Your ideal Friday night involves zero obligations and you are completely fine with that." },
    Agreeableness: { high: "You're the friend everyone calls when they need someone to just listen and not judge.", low: "You say what you think and don't sugarcoat it. Some people need that honesty." },
    Conscientiousness: { high: "Your planner is color-coded and your inbox is under control. You're that person.", low: "Deadlines are more of a suggestion. Spontaneity is its own kind of genius." },
    Openness: { high: "You're the person who googles random things at 2am and calls it research.", low: "You know what you like and you stick with it. Comfort zones exist for a reason." },
  },
  darktriad: {
    Machiavellianism: { high: "You're playing chess while everyone else is playing checkers. Strategy is your love language.", low: "You'd rather be genuine than strategic. What people see is what they get." },
    Narcissism: { high: "You know your worth and you're not about to let anyone forget it.", low: "You're comfortable letting others take the spotlight. Ego doesn't run the show for you." },
    Psychopathy: { high: "You can detach from a situation and think clearly when everyone else is emotional. That's a real skill.", low: "You feel for people deeply and it genuinely affects your decisions. Empathy drives you." },
  },
  dass: {
    Depression: { high: "Things feel heavy right now. That's not a character flaw, it's a signal worth paying attention to.", low: "You're in a good headspace. That energy is something to protect." },
    Anxiety: { high: "Your brain is always running what-if simulations. It's tiring but it also means you're never caught completely off guard.", low: "You don't overthink things, you just do them. That's genuinely rare." },
    Stress: { high: "You're carrying a lot right now. Acknowledging that is step one.", low: "Pressure doesn't really faze you. You handle what comes without spiraling." },
  },
  attachment: {
    Secure: { high: "You can be close without being clingy and independent without being cold. That's the sweet spot.", low: "Close relationships feel complicated for you. That's more common than people admit." },
    Anxious: { high: "You care deeply and sometimes that comes with worrying if people care back just as much.", low: "You don't spend much energy worrying about where you stand with people." },
    Avoidant: { high: "You protect yourself by keeping a little distance. It works, but you know it has a cost.", low: "You're comfortable letting people in. Vulnerability doesn't scare you much." },
  },
  riasec: {
    Realistic: { high: "You'd rather build something with your hands than sit in another meeting about the meeting.", low: "" },
    Investigative: { high: "You're the one who googles how things work at 2am just because you were curious.", low: "" },
    Artistic: { high: "You see the world differently and you need to express that somehow.", low: "" },
    Social: { high: "Helping people isn't just nice for you, it's literally where you get your energy.", low: "" },
    Enterprising: { high: "You see opportunities where others see problems. Born to lead or convince.", low: "" },
    Conventional: { high: "Order, structure, systems. You're the one who actually reads the instructions.", low: "" },
  },
  aesthetic: {
    Intense: { high: "You're drawn to art that hits hard, the stuff that makes you feel something real.", low: "" },
    Mainstream: { high: "You appreciate what's popular because popular things resonate for a reason.", low: "" },
    Traditional: { high: "Classic beauty speaks to you. There's a reason some things never go out of style.", low: "" },
    Visual: { high: "You notice design, color, and composition everywhere. Your eye is trained.", low: "" },
  },
  fti: {
    Explorer: { high: "You're drawn to novelty the way others are drawn to routine. Boredom is the real enemy.", low: "" },
    Builder: { high: "You're the one who shows up, follows through, and actually finishes what others abandon.", low: "" },
    Director: { high: "You make decisions fast and own them. Ambiguity is where most people freeze, not you.", low: "" },
    Negotiator: { high: "You read a room intuitively and adjust without thinking about it. People feel understood around you.", low: "" },
  },
  hsq: {
    Affiliative: { high: "Your humor is the kind that makes a whole room relax. You use it to include, not exclude.", low: "" },
    'Self-Enhancing': { high: "You find the absurd angle in difficult moments. Humor is how you metabolize the hard stuff.", low: "" },
    Aggressive: { high: "Your wit has an edge. It can land brilliantly, and occasionally it lands a little harder than you intended.", low: "" },
    'Self-Defeating': { high: "You make yourself the punchline. Short-term, it earns warmth. Long-term, it costs something.", low: "" },
  },
  kims: {
    Observing: { high: "You notice the texture of the moment, sensations, shifts in mood, the temperature of a room. Most people miss all of that.", low: "" },
    Describing: { high: "You can put inner states into words easily. That's rarer than people think.", low: "" },
    'Acting with Awareness': { high: "You're actually present in what you're doing instead of half-elsewhere. That's a real practice.", low: "" },
    'Accepting without Judgment': { high: "You let experience be what it is rather than fighting it. This is the mindfulness facet most linked to lower anxiety.", low: "" },
  },
  npi: {
    Authority: { high: "You step into leadership naturally. Taking charge feels comfortable rather than effortful.", low: "" },
    Exhibitionism: { high: "You like being noticed and you're good at making that happen without seeming desperate.", low: "" },
    Entitlement: { high: "You have a strong sense of what you deserve. This fuels confidence but can create friction when expectations go unmet.", low: "" },
    'Self-Sufficiency': { high: "You don't need external validation to know your own worth. That's actually hard to come by.", low: "" },
    Superiority: { high: "You quietly believe you're operating at a higher level than most. Sometimes you're right.", low: "" },
    Vanity: { high: "You care about how you come across and you put effort into it. Aesthetics and image matter to you.", low: "" },
    Exploitativeness: { high: "You're willing to use an advantage if it's there. Strategic, not sentimental.", low: "" },
  },
  ambi: {
    'Affect Regulation': { high: "You manage your emotional state well. People look to you when things get intense.", low: "" },
    'Social Drive': { high: "You're pulled toward people. Social energy doesn't drain you, it fills you.", low: "" },
    Conscientiousness: { high: "You follow through. Plans aren't aspirational for you, they're commitments.", low: "" },
    Openness: { high: "You're intellectually restless. New angles, new ideas, new ways of seeing things.", low: "" },
    Agreeableness: { high: "You make space for others and it comes naturally rather than feeling like effort.", low: "" },
    'Energy Drive': { high: "You operate at a high output. You initiate, push, and rarely wait to be asked.", low: "" },
    'Identity Coherence': { high: "You have a stable sense of who you are that doesn't collapse under pressure or change.", low: "" },
  },
  gcbs: {
    'Government Malfeasance': { high: "You're skeptical of what governments say they're doing versus what they're actually doing.", low: "" },
    'Malevolent Global': { high: "You see coordinated agendas behind major world events that most people don't question.", low: "" },
    'Extraterrestrial Coverup': { high: "You think there's more going on with unexplained phenomena than official channels will admit.", low: "" },
    'Personal Wellbeing Threats': { high: "You're alert to hidden threats in everyday life that institutions downplay or deny.", low: "" },
    'Control of Information': { high: "You believe the flow of public information is managed by people with their own interests in mind.", low: "" },
  },
  pvq: {
    'Self-Direction': { high: "You need to think for yourself and do things your own way. External scripts don't sit well with you.", low: "" },
    Universalism: { high: "You care about fairness and wellbeing at a broad scale, not just for the people in your circle.", low: "" },
    Achievement: { high: "Success isn't just nice for you, it's a real driver. You measure yourself against meaningful outcomes.", low: "" },
    Security: { high: "Stability, predictability, safety. You'd rather build something solid than gamble on exciting.", low: "" },
    Stimulation: { high: "You need novelty and intensity to feel alive. Routine without variation drains you.", low: "" },
    Conformity: { high: "You respect the structures and norms that hold things together. Not everyone does.", low: "" },
    Tradition: { high: "You find meaning in practices and values that have been tested by time.", low: "" },
    Hedonism: { high: "You're unapologetic about enjoying life. Pleasure is a legitimate reason to do something.", low: "" },
    Power: { high: "Status and influence matter to you. You want to be in a position where your decisions carry weight.", low: "" },
    Benevolence: { high: "The people close to you matter a lot to you. You're invested in their wellbeing in a real way.", low: "" },
  },
  bpnss: {
    Autonomy: { high: "You need to make your own choices and that matters to your sense of self more than most people realize.", low: "" },
    Competence: { high: "You need to feel effective. Environments where you can't use your skills properly wear you down.", low: "" },
    Relatedness: { high: "Connection fuels you. When your relationships are good, everything else feels more manageable.", low: "" },
  },
  pid5: {
    'Negative Affectivity': { high: "You experience emotions intensely and stay with difficult feelings longer than most.", low: "" },
    Detachment: { high: "You're comfortable keeping your own company. Emotional distance feels natural, not isolating.", low: "" },
    Antagonism: { high: "You're not particularly interested in managing other people's feelings about you.", low: "" },
    Disinhibition: { high: "You act on impulse more than you plan. That spontaneity is also where your energy comes from.", low: "" },
    Psychoticism: { high: "Your thinking can get unconventional. Others sometimes find it hard to follow where you go.", low: "" },
  },
  who5: {
    Wellbeing: { high: "The last two weeks have been full. Energy, mood, and interest in daily life are all reading healthy.", low: "Things have been heavy lately. That's a signal worth taking seriously, not pushing through." },
  },
  sixteenpf: {
    Warmth: { high: "People feel comfortable around you immediately. You radiate approachability.", low: "" },
    Reasoning: { high: "Your brain works fast on abstract problems. These are puzzles to you, not headaches.", low: "" },
    Stability: { high: "You're emotionally grounded. Drama doesn't destabilize you.", low: "" },
    Dominance: { high: "You lead naturally. Authority isn't something you seek, it's something people give you.", low: "" },
    Liveliness: { high: "Your energy is contagious. You're the one who turns a boring situation into a story.", low: "" },
    Tension: { high: "You carry internal tension. It drives you forward but it also wears you down.", low: "" },
  },
}

const DARK_TRIAD_GUIDANCE = {
  Machiavellianism: {
    high: 'High Machiavellianism means you naturally think in terms of strategy, leverage, and long-term positioning. This is adaptive in competitive environments but can strain trust in close relationships.',
    moderate: 'You think strategically without being manipulative. When needed, consider whether your plans account for how others feel,not just what they do.',
  },
  Narcissism: {
    high: 'Elevated narcissism reflects strong self-belief and a need for recognition. Channel this into leadership rather than validation-seeking. Practice asking others about themselves without redirecting to your own experience.',
    moderate: 'Healthy self-regard with some grandiosity. Notice when conversations become one-sided,genuine curiosity about others strengthens your relationships.',
  },
  Psychopathy: {
    high: 'High psychopathy indicates emotional detachment and comfort with risk. This gives you clarity under pressure but can make you appear cold. Practicing active empathy,asking how someone feels and sitting with the answer,builds stronger bonds.',
    moderate: 'You can detach when needed but still connect emotionally. Be mindful that your calm under pressure can read as indifference to people who process emotions more openly.',
  },
}

// ─── Visualizations ───────────────────────────────────────────────────────────

function RadarChart({ traits, metal, accent }) {
  const entries = Object.entries(traits)
  if (entries.length < 3) return null
  const n = entries.length
  const cx = 160, cy = 160, r = 110
  const angleStep = (2 * Math.PI) / n
  const pts = (scale) => entries.map((_, i) => {
    const a = i * angleStep - Math.PI / 2
    return [cx + Math.cos(a) * r * scale, cy + Math.sin(a) * r * scale]
  })
  const polyStr = (pts) => pts.map(p => p.join(',')).join(' ')
  const dataPts = entries.map(([, v], i) => {
    const a = i * angleStep - Math.PI / 2
    const val = Math.max(0.04, Math.min(1, v))
    return [cx + Math.cos(a) * r * val, cy + Math.sin(a) * r * val]
  })
  return (
    <svg viewBox="0 0 320 320" style={{ width: '100%', maxWidth: 320, display: 'block', margin: '0 auto' }}>
      <defs>
        <linearGradient id="radarFill" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor={accent} stopOpacity="0.22" />
          <stop offset="100%" stopColor={accent} stopOpacity="0.06" />
        </linearGradient>
        <filter id="radarGlow">
          <feGaussianBlur stdDeviation="2.5" result="blur" />
          <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
      </defs>
      {[0.25, 0.5, 0.75, 1.0].map(s => (
        <polygon key={s} points={polyStr(pts(s))} fill="none" stroke="rgba(215,228,242,0.10)" strokeWidth="1" />
      ))}
      {entries.map((_, i) => {
        const [x, y] = pts(1)[i]
        return <line key={i} x1={cx} y1={cy} x2={x} y2={y} stroke="rgba(215,228,242,0.10)" strokeWidth="1" />
      })}
      <polygon points={polyStr(dataPts)} fill="url(#radarFill)" stroke={accent} strokeWidth="1.5" strokeOpacity="0.70" filter="url(#radarGlow)" />
      {dataPts.map(([x, y], i) => (
        <circle key={i} cx={x} cy={y} r="3.5" fill={accent} fillOpacity="0.85" stroke="rgba(255,255,255,0.20)" strokeWidth="1" />
      ))}
      {entries.map(([label], i) => {
        const a = i * angleStep - Math.PI / 2
        const lx = cx + Math.cos(a) * (r + 26)
        const ly = cy + Math.sin(a) * (r + 26)
        const fs = label.length > 14 ? '6' : label.length > 10 ? '7' : '8'
        return (
          <text key={i} x={lx} y={ly} textAnchor="middle" dominantBaseline="middle"
            fontSize={fs} letterSpacing="0.10em" fill="rgba(244,247,250,0.55)"
            fontFamily="'Cinzel', serif" style={{ textTransform: 'uppercase' }}>
            {label}
          </text>
        )
      })}
    </svg>
  )
}

// Bell Curve visualization for a single trait
function BellCurveChart({ trait, percentile, accent, metal }) {
  const canvasRef = useRef()
  const pct = Math.round(percentile)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const dpr = window.devicePixelRatio || 1
    const W = 260, H = 80
    canvas.width = W * dpr
    canvas.height = H * dpr
    const ctx = canvas.getContext('2d')
    ctx.scale(dpr, dpr)
    ctx.clearRect(0, 0, W, H)

    const mean = 50, sigma = 18
    const xMin = 0, xMax = 100
    const pad = { left: 16, right: 16, top: 18, bottom: 28 }
    const cW = W - pad.left - pad.right
    const cH = H - pad.top - pad.bottom

    // Sample bell curve points
    const N = 300
    const points = []
    let maxY = 0
    for (let i = 0; i <= N; i++) {
      const x = xMin + (i / N) * (xMax - xMin)
      const y = gaussianY(x, mean, sigma)
      if (y > maxY) maxY = y
      points.push({ x, y })
    }

    const toCanvasX = x => pad.left + ((x - xMin) / (xMax - xMin)) * cW
    const toCanvasY = y => pad.top + cH - (y / maxY) * cH

    // Fill under curve
    ctx.beginPath()
    ctx.moveTo(toCanvasX(xMin), toCanvasY(0))
    for (const p of points) ctx.lineTo(toCanvasX(p.x), toCanvasY(p.y))
    ctx.lineTo(toCanvasX(xMax), toCanvasY(0))
    ctx.closePath()
    ctx.fillStyle = 'rgba(215,228,242,0.04)'
    ctx.fill()

    // Fill user's area (left of percentile) with accent
    const userPoints = points.filter(p => p.x <= pct)
    if (userPoints.length > 0) {
      ctx.beginPath()
      ctx.moveTo(toCanvasX(xMin), toCanvasY(0))
      for (const p of userPoints) ctx.lineTo(toCanvasX(p.x), toCanvasY(p.y))
      ctx.lineTo(toCanvasX(pct), toCanvasY(0))
      ctx.closePath()
      // Parse accent hex to rgb for fill
      const grad = ctx.createLinearGradient(pad.left, 0, toCanvasX(pct), 0)
      grad.addColorStop(0, 'rgba(215,228,242,0.03)')
      grad.addColorStop(1, accent + '55')
      ctx.fillStyle = grad
      ctx.fill()
    }

    // Curve stroke
    ctx.beginPath()
    for (let i = 0; i < points.length; i++) {
      const { x, y } = points[i]
      if (i === 0) ctx.moveTo(toCanvasX(x), toCanvasY(y))
      else ctx.lineTo(toCanvasX(x), toCanvasY(y))
    }
    ctx.strokeStyle = 'rgba(215,228,242,0.30)'
    ctx.lineWidth = 1.5
    ctx.stroke()

    // User marker line
    const ux = toCanvasX(pct)
    const uy = toCanvasY(gaussianY(pct, mean, sigma))
    ctx.beginPath()
    ctx.moveTo(ux, toCanvasY(0))
    ctx.lineTo(ux, uy)
    ctx.strokeStyle = accent
    ctx.lineWidth = 1.5
    ctx.shadowBlur = 8
    ctx.shadowColor = accent
    ctx.stroke()
    ctx.shadowBlur = 0

    // Marker dot
    ctx.beginPath()
    ctx.arc(ux, uy, 4, 0, Math.PI * 2)
    ctx.fillStyle = accent
    ctx.shadowBlur = 10
    ctx.shadowColor = accent
    ctx.fill()
    ctx.shadowBlur = 0

    // Percentile label
    ctx.font = `10px 'JetBrains Mono', monospace`
    ctx.fillStyle = 'rgba(244,247,250,0.45)'
    ctx.textAlign = 'center'
    ctx.fillText(`${pct}th`, ux, H - 8)

    // Axis ticks
    ctx.fillStyle = 'rgba(215,228,242,0.15)'
    for (const tick of [0, 25, 50, 75, 100]) {
      const tx = toCanvasX(tick)
      ctx.fillRect(tx, toCanvasY(0) + 2, 1, 4)
    }
  }, [percentile, accent])

  return (
    <canvas ref={canvasRef} width={260} height={80}
      style={{ width: '100%', maxWidth: 260, display: 'block' }} />
  )
}

// Trait Heatmap
function TraitHeatmap({ percentiles, accent, metal }) {
  const entries = Object.entries(percentiles)
  if (!entries.length) return null

  const getBandColor = (pct) => {
    if (pct >= 75) return { bg: 'rgba(120,200,150,0.22)', border: 'rgba(140,210,160,0.40)', label: 'High', text: 'rgba(160,230,180,0.85)' }
    if (pct >= 55) return { bg: 'rgba(180,200,220,0.16)', border: 'rgba(200,218,238,0.28)', label: 'Mid+', text: 'rgba(200,220,240,0.70)' }
    if (pct >= 40) return { bg: 'rgba(215,228,242,0.08)', border: 'rgba(215,228,242,0.16)', label: 'Mid', text: 'rgba(215,228,242,0.50)' }
    if (pct >= 25) return { bg: 'rgba(200,180,160,0.12)', border: 'rgba(210,190,170,0.22)', label: 'Mid-', text: 'rgba(210,190,170,0.60)' }
    return { bg: 'rgba(200,140,120,0.16)', border: 'rgba(210,150,130,0.28)', label: 'Low', text: 'rgba(225,170,155,0.80)' }
  }

  // Sort by percentile descending for heatmap display
  const sorted = [...entries].sort((a, b) => b[1] - a[1])

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 6 }}>
      {sorted.map(([trait, pct]) => {
        const pctVal = Math.round(pct)
        const band = getBandColor(pctVal)
        return (
          <div key={trait} style={{
            padding: '14px 16px',
            background: band.bg,
            border: `1px solid ${band.border}`,
            position: 'relative',
            overflow: 'hidden',
          }}>
            {/* Fill bar at bottom */}
            <div style={{
              position: 'absolute', bottom: 0, left: 0,
              width: `${pctVal}%`, height: 2,
              background: `linear-gradient(90deg, transparent, ${accent}88)`,
            }} />
            <div style={{
              fontFamily: S.fontSC, fontSize: 7, letterSpacing: '0.16em',
              color: band.text, textTransform: 'uppercase', marginBottom: 8,
            }}>
              {trait}
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
              <span style={{
                fontFamily: S.fontDisplay, fontSize: 28, fontWeight: 300, lineHeight: 1,
                color: band.text,
              }}>{pctVal}</span>
              <span style={{ fontFamily: S.fontSC, fontSize: 7, letterSpacing: '0.10em', color: band.text, opacity: 0.7 }}>th</span>
              <span style={{
                fontFamily: S.fontSC, fontSize: 7, letterSpacing: '0.12em',
                color: band.text, opacity: 0.6, marginLeft: 'auto',
              }}>{band.label}</span>
            </div>
          </div>
        )
      })}
    </div>
  )
}

// Archetype Constellation,star map of archetypes. When compatibility data
// is available, DISTANCE FROM YOUR STAR ENCODES COMPATIBILITY: the higher
// the score, the closer the star.
function ArchetypeConstellation({ testType, userArchetype, accent, names: providedNames, sameTest }) {
  const canvasRef = useRef()

  // Generate deterministic constellation of 8-14 archetypes per test
  const archetypeSeeds = {
    hexaco: ['The Principled Steward', 'The Warm Connector', 'The Thoughtful Observer', 'The Open Explorer', 'The Grounded Idealist', 'The Conscientious Anchor', 'The Empathic Strategist', 'The Bold Innovator'],
    sixteenpf: ['The Warm Strategist', 'The Bold Pioneer', 'The Grounded Analyst', 'The Expressive Idealist', 'The Vigilant Planner', 'The Social Catalyst', 'The Private Architect', 'The Tense Achiever'],
    darktriad: ['The Shadow', 'The Mirror', 'The Phantom', 'The Sovereign', 'The Diplomat', 'The Grounded Empath'],
    fti: ['The Explorer', 'The Builder', 'The Director', 'The Negotiator', 'The Curious Hybrid', 'The Grounded Visionary'],
    npi: ['The Self-Assured Lead', 'The Modest Collaborator', 'The Balanced Self-View', 'The Ambitious Authority', 'The Quiet Confidence', 'The Charming Exhibitor'],
    ambi: ['The Energized Organizer', 'The Reflective Artisan', 'The Warm Companion', 'The Freewheeling Seeker', 'The Diligent Achiever', 'The Open Connector', 'The Steady Contributor', 'The Creative Explorer'],
    pid5: ['The Steady Baseline', 'The Intense Responder', 'The Guarded Independent', 'The Impulsive Seeker', 'The Unconventional Mind'],
    hsq: ['The Warm Humorist', 'The Inner Resilient', 'The Edgy Jester', 'The Self-Deprecator', 'The Dry Observer', 'The Inclusive Comedian'],
    kims: ['The Embodied Noticer', 'The Articulate Observer', 'The Present Actor', 'The Accepting Witness', 'The Reflective Practitioner'],
    gcbs: ['The Trusting View', 'The Selective Skeptic', 'The Deep Skeptic', 'The Pattern Seeker', 'The Cautious Questioner'],
    aesthetic: ['The Raw Intensity', 'The Warm Traditionalist', 'The Visual Sensualist', 'The Broad Appreciator', 'The Mainstream Harmonist', 'The Refined Observer'],
    riasec: ['The Creative Investigator', 'The Social Builder', 'The Enterprising Mind', 'The Realistic Craftsman', 'The Conventional Architect', 'The Artistic Visionary'],
    attachment: ['The Secure Connector', 'The Anxious Heart', 'The Independent Spirit', 'The Guarded Warmth', 'The Trusting Opener', 'The Flexible Relator'],
    pvq: ['The Open to Change', 'The Self-Transcendent', 'The Self-Enhancing', 'The Conservation-Minded', 'The Benevolent Idealist', 'The Achievement Driver'],
    bpnss: ['The Deeply Resourced', 'The Competence-First', 'The Connection-Seeker', 'The Autonomous Achiever', 'The Balanced Nourisher'],
    dass: ['The Resilient Navigator', 'The Sensitive Processor', 'The Calm Center', 'The Stress-Carrier', 'The Anxious Thinker', 'The Weary Steady'],
    who5: ['Running Low', 'Steady', 'Thriving'],
  }

  // Prefer the REAL archetype names for this test (from the compatibility
  // endpoint). The hard-coded seeds are only a fallback.
  const names = (providedNames && providedNames.length >= 2)
    ? providedNames
    : (archetypeSeeds[testType] || archetypeSeeds.hexaco)

  const userNorm = (userArchetype || '').trim().toLowerCase()
  const hasScores = Array.isArray(sameTest) && sameTest.length > 0

  let stars
  if (hasScores) {
    // Score-driven layout: your archetype at the center, siblings placed at
    // a radius proportional to (100 - score). Closer star = more compatible.
    const GOLDEN = Math.PI * (3 - Math.sqrt(5))
    stars = sameTest.map((c, i) => {
      const radius = 52 + Math.min(96, Math.max(6, (100 - c.score) * 1.15))
      const angle = i * GOLDEN + 0.65
      return {
        name: c.name,
        score: c.score,
        x: Math.cos(angle) * radius,
        y: Math.sin(angle) * radius * 0.68,
        size: 2.5 + (c.score / 50),
        isUser: false,
      }
    })
    stars.unshift({ name: userArchetype || 'You', score: 100, x: 0, y: 0, size: 4.5, isUser: true })
  } else {
    // Fallback: seed-based ring layout, exact-name match for the user star.
    stars = names.map((name, i) => {
      const angle = (i / names.length) * Math.PI * 2 + (name.charCodeAt(0) % 10) * 0.1
      const dist = 60 + (name.length % 5) * 16 + (i % 3) * 12
      return {
        name,
        score: null,
        x: Math.cos(angle) * dist,
        y: Math.sin(angle) * dist,
        size: 2 + (name.charCodeAt(0) % 3),
        // Exact match only. A fuzzy prefix match ("The ") used to flag EVERY
        // star as the user's and label them all with the user's archetype.
        isUser: name.trim().toLowerCase() === userNorm,
      }
    })
    const fallbackUser = stars.find(s => s.isUser) || stars[0]
    stars.forEach(s => { s.isUser = (s === fallbackUser) })
  }
  const userStar = stars.find(s => s.isUser)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const dpr = window.devicePixelRatio || 1
    const W = 480, H = 320
    canvas.width = W * dpr
    canvas.height = H * dpr
    const ctx = canvas.getContext('2d')
    ctx.scale(dpr, dpr)
    ctx.clearRect(0, 0, W, H)

    const cx = W / 2, cy = H / 2

    // Draw a full (never cropped) label, clamped inside the canvas bounds.
    const drawLabel = (text, x, y, font, color) => {
      ctx.font = font
      ctx.fillStyle = color
      ctx.textAlign = 'center'
      const w = ctx.measureText(text).width
      const pad = 4
      const lx = Math.min(Math.max(x, pad + w / 2), W - pad - w / 2)
      const ly = Math.min(Math.max(y, 12), H - 4)
      ctx.fillText(text, lx, ly)
      return { lx, ly }
    }

    const ux = cx + userStar.x, uy = cy + userStar.y

    // Guide rings around the user star when distance encodes score.
    if (hasScores) {
      for (const band of [85, 70, 55]) {
        const radius = (52 + Math.min(96, Math.max(6, (100 - band) * 1.15)))
        ctx.beginPath()
        ctx.ellipse(ux, uy, radius, radius * 0.68, 0, 0, Math.PI * 2)
        ctx.strokeStyle = 'rgba(215,228,242,0.06)'
        ctx.lineWidth = 0.7
        ctx.setLineDash([3, 5])
        ctx.stroke()
        ctx.setLineDash([])
      }
    }

    // Connection lines from the user's star, brightness tracks the score.
    for (const star of stars) {
      if (star === userStar) continue
      const sx = cx + star.x, sy = cy + star.y
      const alpha = star.score != null ? 0.03 + (star.score / 100) * 0.22 : 0.05
      ctx.beginPath()
      ctx.moveTo(ux, uy)
      ctx.lineTo(sx, sy)
      ctx.strokeStyle = `rgba(215,228,242,${alpha.toFixed(3)})`
      ctx.lineWidth = star.score != null && star.score >= 70 ? 1 : 0.5
      ctx.stroke()
    }

    // Stars + labels. Every star gets its full name, never cropped.
    for (const star of stars) {
      const sx = cx + star.x, sy = cy + star.y

      if (star.isUser) {
        for (let ring = 3; ring >= 1; ring--) {
          ctx.beginPath()
          ctx.arc(sx, sy, ring * 7, 0, Math.PI * 2)
          ctx.strokeStyle = `${accent}${Math.round(ring * 12).toString(16).padStart(2, '0')}`
          ctx.lineWidth = 0.8
          ctx.stroke()
        }
        ctx.beginPath()
        ctx.arc(sx, sy, star.size + 2, 0, Math.PI * 2)
        ctx.fillStyle = accent
        ctx.shadowBlur = 18
        ctx.shadowColor = accent
        ctx.fill()
        ctx.shadowBlur = 0

        drawLabel(userArchetype || star.name, sx, sy - star.size - 12, `bold 9px 'Cinzel', serif`, accent)
        drawLabel('YOU', sx, sy + star.size + 14, `7px 'Cinzel', serif`, `${accent}AA`)
      } else {
        const bright = star.score != null ? 0.22 + (star.score / 100) * 0.35 : 0.30
        ctx.beginPath()
        ctx.arc(sx, sy, star.size, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(215,228,242,${bright.toFixed(2)})`
        ctx.shadowBlur = 4
        ctx.shadowColor = 'rgba(215,228,242,0.20)'
        ctx.fill()
        ctx.shadowBlur = 0

        // No score labels here , the numbers live in the dedicated
        // compatibility sections below. Distance already encodes the score.
        drawLabel(star.name, sx, sy - star.size - 8, `7.5px 'Cinzel', serif`, 'rgba(215,228,242,0.55)')
      }
    }
  }, [testType, userArchetype, accent, names.join('|'), hasScores, JSON.stringify(sameTest || null)])

  return (
    <canvas ref={canvasRef} width={480} height={320}
      style={{ width: '100%', maxWidth: 480, display: 'block', margin: '0 auto' }} />
  )
}

function PersonalityMap({ coords, userX, userY, accent }) {
  const canvasRef = useRef()
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || !coords.length) return
    const dpr = window.devicePixelRatio || 1
    const W = 480, H = 280
    canvas.width = W * dpr
    canvas.height = H * dpr
    const ctx = canvas.getContext('2d')
    ctx.scale(dpr, dpr)
    const xs = coords.map(c => c[0]), ys = coords.map(c => c[1])
    const minX = Math.min(...xs), maxX = Math.max(...xs)
    const minY = Math.min(...ys), maxY = Math.max(...ys)
    const pad = 32
    const tx = x => pad + ((x - minX) / (maxX - minX)) * (W - pad * 2)
    const ty = y => pad + ((y - minY) / (maxY - minY)) * (H - pad * 2)
    ctx.clearRect(0, 0, W, H)

    // Density-based coloring,compute density for each dot
    const sample = coords.length > 2000 ? coords.filter((_, i) => i % Math.ceil(coords.length / 2000) === 0) : coords

    // Draw dots with slight color variation for depth
    sample.forEach(([x, y], i) => {
      const alpha = 0.08 + (i % 7) * 0.01
      ctx.beginPath()
      ctx.arc(tx(x), ty(y), 1.8, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(200,218,236,${alpha})`
      ctx.fill()
    })

    if (userX !== undefined && userY !== undefined) {
      const ux = tx(userX), uy = ty(userY)
      // Pulse rings
      for (let ring = 3; ring >= 1; ring--) {
        ctx.beginPath()
        ctx.arc(ux, uy, ring * 10, 0, Math.PI * 2)
        ctx.strokeStyle = `rgba(215,228,242,${0.08 * ring})`
        ctx.lineWidth = 1
        ctx.stroke()
      }
      // User marker
      ctx.beginPath()
      ctx.arc(ux, uy, 6, 0, Math.PI * 2)
      ctx.fillStyle = accent
      ctx.shadowBlur = 20
      ctx.shadowColor = accent
      ctx.fill()
      ctx.shadowBlur = 0

      // Inner dot
      ctx.beginPath()
      ctx.arc(ux, uy, 2.5, 0, Math.PI * 2)
      ctx.fillStyle = 'rgba(255,255,255,0.85)'
      ctx.fill()
    }
  }, [coords, userX, userY, accent])
  return (
    <canvas ref={canvasRef} width={480} height={280}
      style={{ width: '100%', maxWidth: 480, display: 'block', margin: '0 auto' }} />
  )
}

function TraitBar({ trait, score, percentile, metal, accent, glow, index }) {
  const [animated, setAnimated] = useState(false)
  useEffect(() => {
    const t = setTimeout(() => setAnimated(true), 200 + index * 80)
    return () => clearTimeout(t)
  }, [index])
  const pct = Math.round(percentile)
  const band = pct >= 75 ? 'High' : pct >= 40 ? 'Mid' : 'Low'
  const bandColor = pct >= 75 ? 'rgba(180,220,190,0.70)' : pct >= 40 ? 'rgba(215,228,242,0.50)' : 'rgba(220,190,180,0.65)'
  return (
    <div style={{ marginBottom: 28 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontFamily: S.fontDisplay, fontStyle: 'italic', fontSize: 19, fontWeight: 300, color: S.textPrim, letterSpacing: '0.01em' }}>{trait}</span>
          <span style={{ fontFamily: S.fontSC, fontSize: 7, letterSpacing: '0.14em', color: bandColor, padding: '2px 7px', border: `1px solid ${bandColor}`, opacity: 0.9 }}>{band}</span>
        </div>
        <div style={{ textAlign: 'right' }}>
          <span style={{ fontFamily: S.fontDisplay, fontSize: 28, fontWeight: 300, background: metal, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text', backgroundSize: '200% 200%', animation: 'metal-sweep 6s ease-in-out infinite', letterSpacing: '-0.02em', lineHeight: 1 }}>{pct}</span>
          <span style={{ fontFamily: S.fontSC, fontSize: 7, letterSpacing: '0.12em', color: S.textMuted, marginLeft: 3 }}>th pct</span>
        </div>
      </div>
      <div style={{ position: 'relative', height: 3, background: 'rgba(215,228,242,0.08)' }}>
        <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: animated ? `${pct}%` : '0%', background: metal, backgroundSize: '300% 100%', animation: 'metal-sweep 5s ease-in-out infinite', transition: 'width 1.1s cubic-bezier(0.4,0,0.2,1)', boxShadow: `0 0 10px ${glow}` }} />
        <div style={{ position: 'absolute', top: -3, bottom: -3, left: animated ? `${pct}%` : '0%', width: 1, background: accent, opacity: 0.60, transition: 'left 1.1s cubic-bezier(0.4,0,0.2,1)', boxShadow: `0 0 6px ${accent}` }} />
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6 }}>
        <span style={{ fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 11, color: S.textMuted }}>Low</span>
        <span style={{ fontFamily: S.fontSC, fontSize: 7, letterSpacing: '0.12em', color: S.textMuted }}>{pct}th percentile · your score is above {pct}% of the sample on this trait</span>
        <span style={{ fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 11, color: S.textMuted }}>High</span>
      </div>
    </div>
  )
}

function Section({ label, roman, children, accent }) {
  return (
    <div style={{ marginBottom: 3, background: S.frost, backdropFilter: 'blur(32px) saturate(1.4)', WebkitBackdropFilter: 'blur(32px) saturate(1.4)', border: `1px solid ${S.frostBorder}`, boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.05)', position: 'relative', overflow: 'hidden' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, padding: '16px 32px 14px', borderBottom: '1px solid rgba(215,228,242,0.08)' }}>
        {roman && <span style={{ fontFamily: S.fontDisplay, fontSize: 13, fontWeight: 300, color: 'rgba(215,228,242,0.18)', letterSpacing: '0.04em', flexShrink: 0 }}>{roman}</span>}
        <span style={{ fontFamily: S.fontSC, fontSize: 9, letterSpacing: '0.24em', color: S.irisDim, textTransform: 'uppercase' }}>{label}</span>
        <div style={{ flex: 1, height: 1, background: `linear-gradient(90deg, ${accent}33, transparent)` }} />
      </div>
      <div style={{ padding: '28px 32px' }}>{children}</div>
    </div>
  )
}

function StatPill({ value, label, metal, suffix = '' }) {
  const lines = label.split('\n')
  return (
    <div style={{ textAlign: 'center', padding: '0 20px' }}>
      <div style={{ fontFamily: S.fontDisplay, fontSize: 48, fontWeight: 300, letterSpacing: '-0.03em', lineHeight: 1, background: metal, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text', backgroundSize: '200% 200%', animation: 'metal-sweep 7s ease-in-out infinite' }}>
        {value}{suffix}
      </div>
      <div style={{ fontFamily: S.fontSC, fontSize: 8, letterSpacing: '0.20em', color: S.textMuted, textTransform: 'uppercase', marginTop: 8, lineHeight: 1.6 }}>
        {lines.map((l, i) => <div key={i}>{l}</div>)}
      </div>
    </div>
  )
}

// Average-member profile of a cluster: trait score + population percentile
// for the typical person belonging to that cluster.
function ClusterProfileTable({ profile, accent }) {
  if (!profile?.length) return null
  return (
    <div style={{ marginTop: 10 }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 44px 44px', gap: '2px 10px', alignItems: 'baseline' }}>
        <span style={{ fontFamily: S.fontSC, fontSize: 6.5, letterSpacing: '0.14em', color: S.textMuted, textTransform: 'uppercase' }}>Avg member trait</span>
        <span style={{ fontFamily: S.fontSC, fontSize: 6.5, letterSpacing: '0.14em', color: S.textMuted, textTransform: 'uppercase', textAlign: 'right' }}>Score</span>
        <span style={{ fontFamily: S.fontSC, fontSize: 6.5, letterSpacing: '0.14em', color: S.textMuted, textTransform: 'uppercase', textAlign: 'right' }}>Pctile</span>
        {profile.map(t => (
          <FragmentRow key={t.trait} t={t} accent={accent} />
        ))}
      </div>
    </div>
  )
}

function FragmentRow({ t, accent }) {
  return (
    <>
      <span style={{ fontFamily: S.fontSC, fontSize: 8, letterSpacing: '0.08em', color: 'rgba(244,247,250,0.45)', textTransform: 'uppercase', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{t.trait}</span>
      <span style={{ fontFamily: S.fontMono, fontSize: 10, color: 'rgba(244,247,250,0.55)', textAlign: 'right' }}>{Number(t.score).toFixed(2)}</span>
      <span style={{ fontFamily: S.fontMono, fontSize: 10, color: accent, textAlign: 'right' }}>{t.percentile}th</span>
    </>
  )
}

// ─── Report Generation ─────────────────────────────────────────────────────
// Produces a standalone HTML file that is a 1:1 clone of the on-screen results
// page, same components, same CSS, same rendering, correct aspect ratio,
// with the action buttons stripped out. No rasterisation, no distortion.
// Open it in any browser; print to PDF from there if a PDF is ever needed.
async function generateHTMLReport(rootEl, meta, short, result) {
  if (!rootEl) throw new Error('No element to capture')

  if (document.fonts && document.fonts.ready) {
    try { await document.fonts.ready } catch (_) { /* noop */ }
  }

  // Embed the results screen's background image as a data URI so the
  // downloaded report is fully self-contained and looks identical.
  let bgData = ''
  try {
    const resp = await fetch(bgImage)
    const blob = await resp.blob()
    bgData = await new Promise(resolve => {
      const fr = new FileReader()
      fr.onload = () => resolve(fr.result)
      fr.onerror = () => resolve('')
      fr.readAsDataURL(blob)
    })
  } catch (_) { /* falls back to plain dark background */ }

  const clone = rootEl.cloneNode(true)

  // Strip anything flagged as screen-only (action buttons, nav links).
  clone.querySelectorAll('[data-report-exclude]').forEach(el => el.remove())

  // Canvases lose their bitmap on cloneNode, swap each cloned canvas for an
  // <img> snapshot of the live one so charts render identically.
  const liveCanvases = rootEl.querySelectorAll('canvas')
  const cloneCanvases = clone.querySelectorAll('canvas')
  cloneCanvases.forEach((c, i) => {
    const live = liveCanvases[i]
    if (!live) { c.remove(); return }
    const img = document.createElement('img')
    try { img.src = live.toDataURL('image/png') } catch (_) { c.remove(); return }
    img.setAttribute('style', c.getAttribute('style') || '')
    img.alt = ''
    c.replaceWith(img)
  })

  const dateStr = new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })
  const title = `Valence, ${result?.archetype_name || meta?.name || 'Personality'} Report`

  const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>${title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;0,700;1,300;1,400&family=Cinzel:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&family=JetBrains+Mono:wght@400;500&family=Libre+Baskerville:ital@0;1&display=swap" rel="stylesheet">
<style>
  * , *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  html { -webkit-font-smoothing: antialiased; text-rendering: optimizeLegibility; }
  body {
    background: #040406;
    color: #F4F7FA;
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 16px; line-height: 1.6; min-height: 100vh;
    overflow-x: hidden; position: relative;
  }
  /* Identical background treatment to the on-screen results page */
  .report-bg {
    position: fixed; inset: 0; z-index: 0; pointer-events: none; overflow: hidden;
  }
  .report-bg img {
    position: absolute; top: 50%; left: 50%;
    transform: translate(-50%, -50%) rotate(-90deg) scale(1.5);
    width: 100vh; height: 100vw; object-fit: cover;
    filter: brightness(0.85) contrast(1.05);
  }
  .report-bg .veil-radial {
    position: absolute; inset: 0;
    background: radial-gradient(ellipse 80% 70% at 50% 50%, rgba(4,4,6,0.55) 0%, rgba(4,4,6,0.82) 70%, rgba(4,4,6,0.96) 100%);
  }
  .report-bg .veil-bottom {
    position: absolute; inset: 0;
    background: linear-gradient(to bottom, rgba(4,4,6,0.0) 0%, rgba(4,4,6,0.0) 60%, rgba(4,4,6,0.9) 100%);
  }
  #report-root { position: relative; z-index: 1; padding-top: 24px; }
  a { color: inherit; text-decoration: none; pointer-events: none; }
  @keyframes metal-sweep { 0%,100% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } }
  @keyframes pulse-ring { 0% { opacity: 0.7; transform: scale(1); } 100% { opacity: 0; transform: scale(1.6); } }
  @keyframes fadeUp { from { opacity: 0; transform: translateY(24px); } to { opacity: 1; transform: translateY(0); } }
  @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
  @keyframes scaleIn { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }
  .animate-fade-up { animation: fadeUp 0.8s cubic-bezier(0.4,0,0.2,1) both; }
  .animate-fade-in { animation: fadeIn 0.4s ease both; }
  .animate-scale-in { animation: scaleIn 0.4s cubic-bezier(0.4,0,0.2,1) both; }
  .report-footer {
    max-width: 780px; margin: 0 auto; padding: 28px 24px 48px;
    text-align: center; font-family: 'Cinzel', serif; font-size: 9px;
    letter-spacing: 0.24em; text-transform: uppercase; color: rgba(244,247,250,0.32);
  }
  @media print {
    body { background: #040406 !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  }
</style>
</head>
<body>
${bgData ? `<div class="report-bg"><img src="${bgData}" alt="" /><div class="veil-radial"></div><div class="veil-bottom"></div></div>` : ''}
<div id="report-root">${clone.outerHTML}</div>
<div class="report-footer">Valence · Personality Analytics · Generated ${dateStr}</div>
</body>
</html>`

  const blob = new Blob([html], { type: 'text/html;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  const safeShort = (short || meta?.short || 'report').toLowerCase().replace(/\s+/g, '-')
  a.href = url
  a.download = `valence-${safeShort}-report-${dateStr.replace(/\s+/g, '-')}.html`
  a.click()
  URL.revokeObjectURL(url)
}

// ─── Main Component ───────────────────────────────────────────────────────────
export default function Results() {
  const { resultId } = useParams()
  const navigate = useNavigate()
  const [result, setResult] = useState(null)
  const [mapCoords, setMapCoords] = useState([])
  const [compat, setCompat] = useState() // undefined = loading, null = failed
  const [revealing, setRevealing] = useState(true)
  const [downloading, setDownloading] = useState(false)
  const resultPageRef = useRef()

  useEffect(() => {
    api.get(`/results/${resultId}`)
      .then(res => {
        setResult(res.data)
        return api.get(`/results/map/${res.data.test_type}`)
      })
      .then(res => setMapCoords(res.data.coords || []))
      .catch(() => navigate('/dashboard'))
    api.get(`/results/compatibility/${resultId}`)
      .then(res => setCompat(res.data?.available ? res.data : null))
      .catch(() => setCompat(null))
    setTimeout(() => setRevealing(false), 2200)
  }, [resultId])

  // Specialty-model enrichment lands asynchronously after submit. While the
  // row is still 'pending', poll for the enriched insights (bounded).
  useEffect(() => {
    if (!result || result.enrichment_status !== 'pending') return
    let tries = 0
    const iv = setInterval(() => {
      tries += 1
      if (tries > 50) { clearInterval(iv); return }
      api.get(`/results/${resultId}`)
        .then(res => {
          if (res.data.enrichment_status !== 'pending') {
            clearInterval(iv)
            setResult(res.data)
          }
        })
        .catch(() => clearInterval(iv))
    }, 6000)
    return () => clearInterval(iv)
  }, [resultId, result?.enrichment_status])

  if (revealing || !result) return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 36, position: 'relative' }}>
      <ParticleCanvas count={50} />
      <div style={{ position: 'relative', zIndex: 1, textAlign: 'center' }}>
        <div style={{ position: 'relative', width: 72, height: 72, margin: '0 auto 32px' }}>
          <div className="spinner" style={{ width: 72, height: 72, borderWidth: 1.5 }} />
          {[1, 2, 3].map(r => (
            <div key={r} style={{ position: 'absolute', inset: -(r * 14), borderRadius: '50%', border: `1px solid rgba(215,232,248,${0.12 - r * 0.03})`, animation: `pulse-ring ${1.4 + r * 0.3}s ease-out infinite`, animationDelay: `${r * 0.2}s` }} />
          ))}
        </div>
        <div style={{ fontFamily: S.fontDisplay, fontSize: 'clamp(24px,4vw,36px)', fontWeight: 300, letterSpacing: '-0.01em', background: 'linear-gradient(135deg,#8090a2,#c8d8e8,#eef6fc,#d8e8f4)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text', backgroundSize: '200% 200%', animation: 'metal-sweep 6s ease-in-out infinite', marginBottom: 14 }}>
          Composing your portrait
        </div>
        <div style={{ fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 14, color: S.textMuted, lineHeight: 1.8 }}>
          Running inference across personality dimensions
        </div>
      </div>
      <style>{`@keyframes metal-sweep{0%,100%{background-position:0% 50%}50%{background-position:100% 50%}}@keyframes pulse-ring{0%{opacity:0.7;transform:scale(1)}100%{opacity:0;transform:scale(1.6)}}`}</style>
    </div>
  )

  const testType = result.test_type
  const meta = TEST_META[testType] || DEFAULT_META
  const { accent, metal, glow, roman, name, short } = meta
  const traitScores = result.trait_scores || {}
  const percentiles = result.percentiles || {}
  const insights = (() => {
    try { const r = result.insights; if (!r) return {}; if (typeof r === 'object') return r; return JSON.parse(r) } catch { return {} }
  })()
  const neighborhood = (() => {
    try { const r = result.neighborhood_traits; if (!r) return null; if (typeof r === 'object') return r; return JSON.parse(r) } catch { return null }
  })()

  // Deep Dive: the specialty psychology-model enrichment lands in the
  // background after submit and is held separately from the base insights.
  const deepDiveData = insights.deep_dive
  const enrichPending = result.enrichment_status === 'pending'
  const deepDiveReady = deepDiveData?.status === 'ok' && (deepDiveData?.insights?.length > 0)

  const stats = computeStats(traitScores, percentiles)
  const plainLines = generatePlainEnglishSummary(testType, traitScores, percentiles, result.archetype_name, result.archetype_description, insights)
  const traitCount = Object.keys(traitScores).length

  const handleDownload = async () => {
    setDownloading(true)
    try {
      await generateHTMLReport(resultPageRef.current, meta, short, result)
    } catch (e) {
      console.error('Report generation failed:', e)
      // Fallback: text report
      const report = [
        'VALENCE', `${short} - Personality Report`, '',
        `Archetype: ${result.archetype_name || 'Unknown'}`, '',
        'WHAT THIS MEANS',
        ...plainLines.map((l, i) => `${i + 1}. ${l}`), '',
        'TRAIT BREAKDOWN',
        ...Object.entries(traitScores).map(([t]) => `  ${t}: ${Math.round(percentiles[t] || 50)}th percentile`),
      ].join('\n')
      const blob = new Blob([report], { type: 'text/plain;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `valence-${short.toLowerCase().replace(/\s+/g, '-')}-report.txt`
      a.click()
      URL.revokeObjectURL(url)
    }
    setDownloading(false)
  }

  return (
    <div className="page" style={{ paddingBottom: 100, position: 'relative', minHeight: '100vh' }}>
      {/* Background */}
      <div style={{ position: 'fixed', inset: 0, zIndex: 0, pointerEvents: 'none', overflow: 'hidden' }}>
        <img src={bgImage} alt="" style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%) rotate(-90deg) scale(1.5)', width: '100vh', height: '100vw', objectFit: 'cover', filter: 'brightness(0.85) contrast(1.05)' }} />
        <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse 80% 70% at 50% 50%, rgba(4,4,6,0.55) 0%, rgba(4,4,6,0.82) 70%, rgba(4,4,6,0.96) 100%)' }} />
        <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(to bottom, rgba(4,4,6,0.0) 0%, rgba(4,4,6,0.0) 60%, rgba(4,4,6,0.9) 100%)' }} />
      </div>
      <ParticleCanvas count={30} />

      {/* Capturable results area */}
      <div ref={resultPageRef} style={{ position: 'relative', zIndex: 1 }}>
        <div style={{ maxWidth: 780, margin: '0 auto', padding: '64px 24px 0' }}>

          {/* Hero card */}
          <div className="animate-scale-in" style={{ marginBottom: 3, padding: '60px 48px 52px', background: S.frost, backdropFilter: 'blur(40px) saturate(1.6)', WebkitBackdropFilter: 'blur(40px) saturate(1.6)', border: `1px solid ${S.frostBorder}`, boxShadow: `inset 0 1px 0 rgba(255,255,255,0.07), 0 0 100px ${glow}`, position: 'relative', overflow: 'hidden', textAlign: 'center' }}>
            <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%,-50%)', width: 400, height: 400, borderRadius: '50%', background: `radial-gradient(circle, ${glow}, transparent 65%)`, filter: 'blur(80px)', pointerEvents: 'none' }} />
            <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 1, background: `linear-gradient(90deg, transparent, ${accent}66, transparent)` }} />
            <div style={{ position: 'relative' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12, marginBottom: 28 }}>
                <span style={{ fontFamily: S.fontDisplay, fontSize: 15, fontWeight: 300, color: 'rgba(215,228,242,0.20)', letterSpacing: '0.06em' }}>{roman}</span>
                <span style={{ fontFamily: S.fontSC, fontSize: 8, letterSpacing: '0.26em', color: S.irisDim, textTransform: 'uppercase', padding: '4px 14px', border: '1px solid rgba(215,228,242,0.14)' }}>{short} · Personality Archetype</span>
                <span style={{ fontFamily: S.fontDisplay, fontSize: 15, fontWeight: 300, color: 'rgba(215,228,242,0.20)', letterSpacing: '0.06em' }}>{roman}</span>
              </div>
              <h1 style={{ fontFamily: S.fontDisplay, fontSize: 'clamp(40px,6vw,68px)', fontWeight: 300, letterSpacing: '-0.02em', lineHeight: 1.0, background: metal, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text', backgroundSize: '200% 200%', animation: 'metal-sweep 9s ease-in-out infinite', marginBottom: 16 }}>
                {result.archetype_name || name}
              </h1>
              <p style={{ fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 18, color: S.textSec, marginBottom: 44, lineHeight: 1.75, maxWidth: 480, margin: '0 auto 44px' }}>
                {result.archetype_description || insights.summary || ''}
              </p>
              <div style={{ display: 'flex', justifyContent: 'center', gap: 0, flexWrap: 'wrap' }}>
                <StatPill value={`${result.similarity_pct?.toFixed(1) || '?'}%`} label={'of the population\nshares your archetype'} metal={metal} />
                <div style={{ width: 1, background: 'rgba(215,228,242,0.10)', margin: '8px 0' }} />
                <StatPill value={`${stats.medianPct}th`} label={'median percentile\nrank across traits'} metal={metal} />
                <div style={{ width: 1, background: 'rgba(215,228,242,0.10)', margin: '8px 0' }} />
                <StatPill value={`${stats.topPct}th`} label={`highest trait\n${stats.topTrait.slice(0, 14)}`} metal={metal} />
              </div>
            </div>
          </div>

          {/* In Plain Terms */}
          <Section label="In Plain Terms" roman="i" accent={accent}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {plainLines.map((line, i) => (
                <div key={i} style={{ display: 'flex', gap: 18, alignItems: 'flex-start', padding: '14px 18px', background: i === 0 ? 'rgba(215,228,242,0.05)' : 'rgba(215,228,242,0.02)', border: `1px solid rgba(215,228,242,0.07)`, borderLeft: i === 0 ? `2px solid ${accent}77` : `2px solid ${accent}33` }}>
                  <span style={{ fontFamily: S.fontDisplay, fontSize: 16, fontWeight: 300, color: accent, opacity: i === 0 ? 0.8 : 0.45, flexShrink: 0, marginTop: 1 }}>{String(i + 1).padStart(2, '0')}</span>
                  <p style={{ fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 15, color: i === 0 ? S.textSec : 'rgba(244,247,250,0.48)', lineHeight: 1.80 }}>{line}</p>
                </div>
              ))}
            </div>
          </Section>

          {/* Portrait */}
          {insights.summary && (
            <Section label="Portrait" roman="ii" accent={accent}>
              <p style={{ fontFamily: S.fontDisplay, fontStyle: 'italic', fontSize: 20, fontWeight: 300, lineHeight: 1.80, color: S.textSec, marginBottom: insights.insights?.length ? 28 : 0, letterSpacing: '0.005em' }}>
                {insights.summary}
              </p>
              {insights.insights?.length > 0 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 14, marginTop: 20 }}>
                  {insights.insights.map((ins, i) => (
                    <div key={i} style={{ display: 'flex', gap: 18, alignItems: 'flex-start', padding: '14px 18px', background: 'rgba(215,228,242,0.03)', border: `1px solid rgba(215,228,242,0.07)`, borderLeft: `2px solid ${accent}44` }}>
                      <span style={{ fontFamily: S.fontDisplay, fontSize: 16, fontWeight: 300, color: accent, opacity: 0.5, flexShrink: 0, marginTop: 1 }}>{String(i + 1).padStart(2, '0')}</span>
                      <p style={{ fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 14, color: 'rgba(244,247,250,0.50)', lineHeight: 1.80 }}>{ins}</p>
                    </div>
                  ))}
                </div>
              )}
            </Section>
          )}

          {/* Trait Breakdown */}
          <Section label="Trait Breakdown" roman="iii" accent={accent}>
            <div style={{ marginBottom: 20 }}>
              {Object.entries(traitScores).map(([trait, score], i) => (
                <TraitBar key={trait} trait={trait} score={score} percentile={percentiles[trait] || 50} metal={metal} accent={accent} glow={glow} index={i} />
              ))}
            </div>
            <div style={{ padding: '14px 18px', background: 'rgba(215,228,242,0.03)', border: '1px solid rgba(215,228,242,0.08)' }}>
              <p style={{ fontFamily: S.fontSC, fontSize: 11, letterSpacing: '0.04em', color: S.textMuted, lineHeight: 1.75 }}>
                Percentiles compare your scores against {
                  testType === 'hexaco' ? '22,786' :
                  testType === 'sixteenpf' ? '49,159' :
                  testType === 'darktriad' ? '18,192' :
                  testType === 'dass' ? '39,775' :
                  testType === 'attachment' ? '51,492' :
                  testType === 'riasec' ? '145,828' :
                  testType === 'aesthetic' ? '18,575' :
                  testType === 'hsq' ? '1,071' :
                  testType === 'kims' ? '601' :
                  testType === 'fti' ? '4,967' :
                  testType === 'npi' ? '11,243' :
                  testType === 'ambi' ? '2,017' :
                  testType === 'gcbs' ? '2,495' :
                  'thousands of'
                } real participants.
              </p>
            </div>
          </Section>

          {/* Trait Heatmap,new */}
          {traitCount >= 2 && (
            <Section label="Trait Heatmap" roman="iv" accent={accent}>
              <TraitHeatmap percentiles={percentiles} accent={accent} metal={metal} />
              <p style={{ fontFamily: S.fontSC, fontSize: 11, letterSpacing: '0.04em', color: S.textMuted, lineHeight: 1.75, marginTop: 18 }}>
                Each tile shows your percentile across traits. Color signals your band relative to the population.
              </p>
            </Section>
          )}

          {/* Bell Curves,new */}
          {traitCount >= 1 && (
            <Section label="Population Curves" roman="v" accent={accent}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 20 }}>
                {Object.entries(percentiles).map(([trait, pct]) => (
                  <div key={trait} style={{ padding: '16px', background: 'rgba(215,228,242,0.03)', border: '1px solid rgba(215,228,242,0.08)' }}>
                    <div style={{ fontFamily: S.fontSC, fontSize: 8, letterSpacing: '0.16em', color: S.irisDim, textTransform: 'uppercase', marginBottom: 10 }}>
                      {trait}
                    </div>
                    <BellCurveChart trait={trait} percentile={pct} accent={accent} metal={metal} />
                  </div>
                ))}
              </div>
              <p style={{ fontFamily: S.fontSC, fontSize: 11, letterSpacing: '0.04em', color: S.textMuted, lineHeight: 1.75, marginTop: 18 }}>
                The curve shows the normal distribution of this trait across the population. The marker shows where you land.
              </p>
            </Section>
          )}

          {/* Radar Chart */}
          {traitCount >= 3 && (
            <Section label="Trait Radar" roman="vi" accent={accent}>
              <div style={{ padding: '8px 0' }}>
                <RadarChart traits={traitScores} metal={metal} accent={accent} />
              </div>
              <p style={{ fontFamily: S.fontSC, fontSize: 11, letterSpacing: '0.04em', color: S.textMuted, lineHeight: 1.75, marginTop: 16, textAlign: 'center' }}>
                The shape of your profile. Each axis is a trait. Distance from center reflects score magnitude.
              </p>
            </Section>
          )}

          {/* Archetype Constellation + Compatibility */}
          <Section label="Archetype Constellation" roman="vii" accent={accent}>
            <ArchetypeConstellation
              testType={testType}
              userArchetype={compat?.user?.name || result.archetype_name}
              accent={accent}
              names={compat?.all_names}
              sameTest={compat?.same_test}
            />
            <p style={{ fontFamily: S.fontSC, fontSize: 12, letterSpacing: '0.06em', color: S.textSec, lineHeight: 1.75, marginTop: 20, textAlign: 'center' }}>
              {compat?.available
                ? 'Distance encodes compatibility: the closer a star sits to yours, the higher your compatibility score with that archetype.'
                : 'Your archetype lit up within the full map of personality types for this assessment.'}
            </p>

            {compat === null && (
              <div style={{ marginTop: 16, padding: '14px 18px', background: 'rgba(200,170,140,0.06)', border: '1px solid rgba(210,180,150,0.18)', borderLeft: '2px solid rgba(220,190,160,0.45)' }}>
                <p style={{ fontFamily: S.fontSC, fontSize: 11, letterSpacing: '0.04em', color: 'rgba(230,205,180,0.85)', lineHeight: 1.75 }}>
                  Compatibility scores could not be loaded. The backend needs a restart to serve the compatibility endpoint. Once it is running, this section shows your top 5 most compatible and bottom 5 least compatible clusters, each scored out of 100.
                </p>
              </div>
            )}

            {compat?.available && compat.user?.definition && (
              <div style={{ marginTop: 20, padding: '14px 18px', background: 'rgba(215,228,242,0.04)', border: `1px solid rgba(215,228,242,0.08)`, borderLeft: `2px solid ${accent}66` }}>
                <div style={{ fontFamily: S.fontSC, fontSize: 7, letterSpacing: '0.18em', color: S.irisDim, textTransform: 'uppercase', marginBottom: 6 }}>
                  Your Cluster, In One Line
                </div>
                <p style={{ fontFamily: S.fontSC, fontSize: 12, letterSpacing: '0.03em', color: 'rgba(244,247,250,0.60)', lineHeight: 1.75 }}>
                  <span style={{ color: accent, opacity: 0.85 }}>{compat.user.name}</span> , {compat.user.definition}
                </p>
              </div>
            )}

            {compat?.available && (
              <div style={{ marginTop: 28 }}>
                {/* Top 5 compatibilities overall */}
                <div style={{ fontFamily: S.fontSC, fontSize: 8, letterSpacing: '0.20em', color: S.irisDim, textTransform: 'uppercase', marginBottom: 12 }}>
                  Top 5 Compatibilities
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {(compat.top5 || []).map((c, i) => (
                    <div key={`top-${c.test_id}-${c.name}`} style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '13px 18px', background: i === 0 ? 'rgba(215,228,242,0.06)' : 'rgba(215,228,242,0.03)', border: `1px solid rgba(215,228,242,0.08)`, borderLeft: `2px solid ${accent}${i === 0 ? '88' : '44'}` }}>
                      <span style={{ fontFamily: S.fontDisplay, fontSize: 20, fontWeight: 300, color: accent, opacity: i === 0 ? 0.9 : 0.5, minWidth: 24, lineHeight: 1 }}>{i + 1}</span>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontFamily: S.fontDisplay, fontStyle: 'italic', fontSize: 16, fontWeight: 300, color: S.textPrim, lineHeight: 1.3 }}>{c.name}</div>
                        <div style={{ fontFamily: S.fontSC, fontSize: 7, letterSpacing: '0.16em', color: S.textMuted, textTransform: 'uppercase', marginTop: 3 }}>
                          {c.kind === 'within' ? 'This test' : c.test_name}
                        </div>
                      </div>
                      <div style={{ width: 90, flexShrink: 0 }}>
                        <div style={{ height: 3, background: 'rgba(215,228,242,0.08)' }}>
                          <div style={{ height: '100%', width: `${c.score}%`, background: metal, backgroundSize: '200% 100%', animation: 'metal-sweep 5s ease-in-out infinite' }} />
                        </div>
                      </div>
                      <span style={{ fontFamily: S.fontMono, fontSize: 12, color: S.textSec, minWidth: 58, textAlign: 'right', flexShrink: 0 }}>
                        {c.score} <span style={{ fontSize: 9, color: S.textMuted }}>/ 100</span>
                      </span>
                    </div>
                  ))}
                </div>

                {/* Bottom 5 compatibilities overall , least compatible clusters */}
                {(compat.bottom5 || []).length > 0 && (
                  <div style={{ marginTop: 24 }}>
                    <div style={{ fontFamily: S.fontSC, fontSize: 8, letterSpacing: '0.20em', color: S.irisDim, textTransform: 'uppercase', marginBottom: 12 }}>
                      Bottom 5 · Least Compatible
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                      {(compat.bottom5 || []).map((c, i) => (
                        <div key={`bot-${c.test_id}-${c.name}`} style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '13px 18px', background: 'rgba(200,170,150,0.03)', border: `1px solid rgba(215,228,242,0.06)`, borderLeft: `2px solid rgba(214,150,150,${i === 0 ? '0.55' : '0.28'})` }}>
                          <span style={{ fontFamily: S.fontDisplay, fontSize: 20, fontWeight: 300, color: 'rgba(214,160,150,0.85)', opacity: i === 0 ? 0.9 : 0.5, minWidth: 24, lineHeight: 1 }}>{i + 1}</span>
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <div style={{ fontFamily: S.fontDisplay, fontStyle: 'italic', fontSize: 16, fontWeight: 300, color: S.textSec, lineHeight: 1.3 }}>{c.name}</div>
                            <div style={{ fontFamily: S.fontSC, fontSize: 7, letterSpacing: '0.16em', color: S.textMuted, textTransform: 'uppercase', marginTop: 3 }}>
                              {c.kind === 'within' ? 'This test' : c.test_name}
                            </div>
                          </div>
                          <div style={{ width: 90, flexShrink: 0 }}>
                            <div style={{ height: 3, background: 'rgba(215,228,242,0.08)' }}>
                              <div style={{ height: '100%', width: `${c.score}%`, background: 'rgba(214,150,150,0.55)' }} />
                            </div>
                          </div>
                          <span style={{ fontFamily: S.fontMono, fontSize: 12, color: S.textSec, minWidth: 58, textAlign: 'right', flexShrink: 0 }}>
                            {c.score} <span style={{ fontSize: 9, color: S.textMuted }}>/ 100</span>
                          </span>
                        </div>
                      ))}
                    </div>
                    <p style={{ fontFamily: S.fontSC, fontSize: 11, letterSpacing: '0.04em', color: S.textMuted, lineHeight: 1.7, marginTop: 10 }}>
                      Low scores mark opposing profile shapes. These pairings are complementary rather than "bad" , in research they create the strongest growth dynamics by challenging each other's blind spots.
                    </p>
                  </div>
                )}

                {/* Within this test */}
                {compat.same_test.length > 0 && (
                  <div style={{ marginTop: 24 }}>
                    <div style={{ fontFamily: S.fontSC, fontSize: 8, letterSpacing: '0.20em', color: S.irisDim, textTransform: 'uppercase', marginBottom: 12 }}>
                      Within This Test
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 8 }}>
                      {compat.same_test.map(c => {
                        const behavior = behaviorSummary(c.avg_profile)
                        return (
                        <div key={c.name} style={{ padding: '12px 16px', background: 'rgba(215,228,242,0.03)', border: '1px solid rgba(215,228,242,0.08)' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 8 }}>
                            <span style={{ fontFamily: S.fontDisplay, fontStyle: 'italic', fontSize: 14, fontWeight: 300, color: S.textSec, lineHeight: 1.35 }}>{c.name}</span>
                            <span style={{ fontFamily: S.fontMono, fontSize: 12, color: accent, flexShrink: 0 }}>{c.score}<span style={{ fontSize: 8, color: S.textMuted }}>/100</span></span>
                          </div>
                          <div style={{ height: 2, background: 'rgba(215,228,242,0.07)', marginTop: 8 }}>
                            <div style={{ height: '100%', width: `${c.score}%`, background: accent, opacity: 0.55 }} />
                          </div>
                          {behavior && (
                            <p style={{ fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 12, color: 'rgba(244,247,250,0.55)', lineHeight: 1.65, marginTop: 10 }}>
                              {behavior}
                            </p>
                          )}
                          <ClusterProfileTable profile={c.avg_profile} accent={accent} />
                        </div>
                        )
                      })}
                    </div>
                  </div>
                )}

                {/* Across other tests */}
                {compat.cross_test.length > 0 && (
                  <div style={{ marginTop: 24 }}>
                    <div style={{ fontFamily: S.fontSC, fontSize: 8, letterSpacing: '0.20em', color: S.irisDim, textTransform: 'uppercase', marginBottom: 12 }}>
                      Across Other Tests
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 8 }}>
                      {compat.cross_test.map(c => {
                        const behavior = behaviorSummary(c.avg_profile)
                        return (
                        <div key={`${c.test_id}-${c.name}`} style={{ padding: '12px 16px', background: 'rgba(215,228,242,0.03)', border: '1px solid rgba(215,228,242,0.08)' }}>
                          <div style={{ fontFamily: S.fontSC, fontSize: 7, letterSpacing: '0.16em', color: S.textMuted, textTransform: 'uppercase', marginBottom: 5 }}>{c.test_name}</div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 8 }}>
                            <span style={{ fontFamily: S.fontDisplay, fontStyle: 'italic', fontSize: 14, fontWeight: 300, color: S.textSec, lineHeight: 1.35 }}>{c.name}</span>
                            <span style={{ fontFamily: S.fontMono, fontSize: 12, color: accent, flexShrink: 0 }}>{c.score}<span style={{ fontSize: 8, color: S.textMuted }}>/100</span></span>
                          </div>
                          <div style={{ height: 2, background: 'rgba(215,228,242,0.07)', marginTop: 8 }}>
                            <div style={{ height: '100%', width: `${c.score}%`, background: accent, opacity: 0.55 }} />
                          </div>
                          {behavior && (
                            <p style={{ fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 12, color: 'rgba(244,247,250,0.55)', lineHeight: 1.65, marginTop: 10 }}>
                              {behavior}
                            </p>
                          )}
                          <ClusterProfileTable profile={c.avg_profile} accent={accent} />
                        </div>
                        )
                      })}
                    </div>
                  </div>
                )}
              </div>
            )}

            <div style={{ marginTop: 24, display: 'flex', flexDirection: 'column', gap: 10 }}>
              <div style={{ fontFamily: S.fontSC, fontSize: 8, letterSpacing: '0.20em', color: S.irisDim, textTransform: 'uppercase', marginBottom: 4 }}>How To Read This</div>
              <div style={{ padding: '14px 18px', background: 'rgba(215,228,242,0.03)', border: `1px solid rgba(215,228,242,0.07)`, borderLeft: `2px solid ${accent}55` }}>
                <p style={{ fontFamily: S.fontSC, fontSize: 12, letterSpacing: '0.04em', color: 'rgba(244,247,250,0.50)', lineHeight: 1.80 }}>
                  Scores compare the shape of trait profiles. 100 means an almost identical profile shape, 50 means unrelated, and lower scores mean opposing profiles. High scorers within this test are the people who "just get you" without explanation.
                </p>
              </div>
              <div style={{ padding: '14px 18px', background: 'rgba(215,228,242,0.03)', border: `1px solid rgba(215,228,242,0.07)`, borderLeft: `2px solid ${accent}33` }}>
                <p style={{ fontFamily: S.fontSC, fontSize: 12, letterSpacing: '0.04em', color: 'rgba(244,247,250,0.45)', lineHeight: 1.80 }}>
                  Cross-test rows show, for each other assessment, the archetype whose profile shape sits closest to yours. Lower-scoring archetypes are complementary rather than incompatible; in research those pairings create the strongest growth dynamics, since they challenge your blind spots while you challenge theirs.
                </p>
              </div>
              {compat?.method?.summary && (
                <div style={{ padding: '14px 18px', background: 'rgba(215,228,242,0.03)', border: `1px solid rgba(215,228,242,0.07)`, borderLeft: `2px solid ${accent}22` }}>
                  <div style={{ fontFamily: S.fontSC, fontSize: 7, letterSpacing: '0.18em', color: S.textMuted, textTransform: 'uppercase', marginBottom: 6 }}>Scoring Model</div>
                  <p style={{ fontFamily: S.fontSC, fontSize: 11, letterSpacing: '0.03em', color: 'rgba(244,247,250,0.42)', lineHeight: 1.80 }}>
                    {compat.method.summary}
                  </p>
                </div>
              )}
            </div>
          </Section>

          {/* Notable Strengths */}
          {insights.strengths?.length > 0 && (
            <Section label="Notable Strengths" roman="viii" accent={accent}>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {insights.strengths.map((str, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 18px', background: 'rgba(215,232,244,0.05)', border: `1px solid ${accent}33` }}>
                    <span style={{ color: accent, fontSize: 10, opacity: 0.7 }}>✦</span>
                    <span style={{ fontFamily: S.fontSC, fontSize: 8, letterSpacing: '0.16em', color: S.textSec, textTransform: 'uppercase' }}>{str}</span>
                  </div>
                ))}
              </div>
            </Section>
          )}

          {/* Fun Facts,relatable trait observations */}
          {(() => {
            const facts = TRAIT_FUN_FACTS[testType]
            if (!facts) return null
            const items = Object.entries(percentiles).map(([trait, pct]) => {
              const f = facts[trait]
              if (!f) return null
              if (pct >= 65 && f.high) return { trait, fact: f.high, type: 'high' }
              if (pct <= 35 && f.low) return { trait, fact: f.low, type: 'low' }
              return null
            }).filter(Boolean)
            if (!items.length) return null
            return (
              <Section label="That's So You" roman="ix" accent={accent}>
                <p style={{ fontFamily: S.fontSC, fontSize: 12, letterSpacing: '0.06em', color: S.textMuted, lineHeight: 1.75, marginBottom: 20 }}>
                  Relatable observations based on your most distinctive scores,backed by personality science.
                </p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {items.map((item, i) => (
                    <div key={i} style={{ padding: '16px 20px', background: 'rgba(215,228,242,0.04)', border: `1px solid rgba(215,228,242,0.08)`, borderLeft: `2px solid ${accent}${item.type === 'high' ? '66' : '33'}` }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                        <span style={{ fontFamily: S.fontSC, fontSize: 7, letterSpacing: '0.16em', color: accent, textTransform: 'uppercase', opacity: 0.7 }}>{item.trait}</span>
                        <span style={{ fontFamily: S.fontSC, fontSize: 7, letterSpacing: '0.12em', color: S.textMuted, textTransform: 'uppercase' }}>{item.type === 'high' ? '▲ high' : '▽ low'}</span>
                      </div>
                      <p style={{ fontFamily: S.fontSC, fontSize: 13, letterSpacing: '0.02em', color: S.textSec, lineHeight: 1.75 }}>{item.fact}</p>
                    </div>
                  ))}
                </div>
              </Section>
            )
          })()}

          {/* Dark Triad Self-Assessment */}
          {testType === 'darktriad' && (() => {
            const guidance = Object.entries(percentiles).map(([trait, pct]) => {
              const g = DARK_TRIAD_GUIDANCE[trait]
              if (!g) return null
              if (pct >= 70) return { trait, text: g.high, level: 'elevated' }
              if (pct >= 50) return { trait, text: g.moderate, level: 'moderate' }
              return null
            }).filter(Boolean)
            if (!guidance.length) return null
            return (
              <Section label="Self-Assessment" roman="x" accent={accent}>
                <p style={{ fontFamily: S.fontSC, fontSize: 12, letterSpacing: '0.06em', color: S.textSec, lineHeight: 1.75, marginBottom: 20 }}>
                  These are not diagnoses. They are observations about where you fall on validated personality dimensions, with practical guidance for self-awareness.
                </p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {guidance.map((g, i) => (
                    <div key={i} style={{ padding: '18px 22px', background: g.level === 'elevated' ? 'rgba(200,160,140,0.06)' : 'rgba(215,228,242,0.03)', border: `1px solid ${g.level === 'elevated' ? 'rgba(200,160,140,0.15)' : 'rgba(215,228,242,0.08)'}`, borderLeft: `2px solid ${g.level === 'elevated' ? 'rgba(200,160,140,0.40)' : accent + '33'}` }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                        <span style={{ fontFamily: S.fontSC, fontSize: 8, letterSpacing: '0.18em', color: g.level === 'elevated' ? 'rgba(220,180,160,0.80)' : S.irisDim, textTransform: 'uppercase' }}>{g.trait}</span>
                        <span style={{ fontFamily: S.fontSC, fontSize: 7, letterSpacing: '0.12em', color: g.level === 'elevated' ? 'rgba(220,180,160,0.55)' : S.textMuted, textTransform: 'uppercase', padding: '2px 8px', border: `1px solid ${g.level === 'elevated' ? 'rgba(200,160,140,0.20)' : 'rgba(215,228,242,0.10)'}` }}>{g.level}</span>
                      </div>
                      <p style={{ fontFamily: S.fontSC, fontSize: 13, letterSpacing: '0.02em', color: 'rgba(244,247,250,0.55)', lineHeight: 1.80 }}>{g.text}</p>
                    </div>
                  ))}
                </div>
                <p style={{ fontFamily: S.fontSC, fontSize: 11, letterSpacing: '0.04em', color: S.textMuted, lineHeight: 1.75, marginTop: 18 }}>
                  Personality traits exist on a spectrum. High scores in dark triad dimensions are not inherently pathological,they describe tendencies that can be channeled constructively with self-awareness.
                </p>
              </Section>
            )
          })()}

          {/* Personality Map */}
          {mapCoords.length > 0 && (
            <Section label="Personality Space" roman="ix" accent={accent}>
              <PersonalityMap coords={mapCoords} userX={result.umap_x} userY={result.umap_y} accent={accent} />
              <p style={{ fontFamily: S.fontSC, fontSize: 11, letterSpacing: '0.04em', color: S.textMuted, lineHeight: 1.75, marginTop: 16, textAlign: 'center' }}>
                Each point is a real participant. Your position shows where your unique profile sits within the full distribution.
              </p>
            </Section>
          )}

          {/* Neighborhood */}
          {neighborhood?.top_traits?.length > 0 && (
            <Section label="Personality Neighborhood" roman="x" accent={accent}>
              <p style={{ fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 15, color: S.textSec, lineHeight: 1.75, marginBottom: 24 }}>
                People with profiles similar to yours score highest in these traits. Scores represent the average normalized trait strength within your personality cluster (0-100 scale).
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {neighborhood.top_traits.map((t, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 16, padding: '12px 16px', background: i === 0 ? 'rgba(215,228,242,0.05)' : 'transparent', border: i === 0 ? `1px solid ${accent}22` : '1px solid transparent' }}>
                    <span style={{ fontFamily: S.fontDisplay, fontSize: 22, fontWeight: 300, color: i === 0 ? accent : S.textMuted, opacity: i === 0 ? 0.9 : 0.5, minWidth: 28, lineHeight: 1 }}>{i + 1}</span>
                    <span style={{ flex: 1, fontFamily: S.fontDisplay, fontStyle: 'italic', fontSize: 17, fontWeight: 300, color: S.textSec }}>{t.trait}</span>
                    <div style={{ width: 80, height: 2, background: 'rgba(215,228,242,0.08)' }}>
                      <div style={{ height: '100%', width: `${t.score * 100}%`, background: metal, backgroundSize: '200% 100%', animation: 'metal-sweep 5s ease-in-out infinite' }} />
                    </div>
                    <span style={{ fontFamily: S.fontMono, fontSize: 11, color: S.textMuted, minWidth: 36, textAlign: 'right' }}>{Math.round(t.score * 100)}</span>
                  </div>
                ))}
              </div>
              <p style={{ fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 12, color: S.textMuted, lineHeight: 1.75, marginTop: 18 }}>
                These are the defining traits of your personality neighborhood,the cluster of people whose profiles most closely resemble yours.
              </p>
            </Section>
          )}

          {/* Deep Dive Mode , psychology-model enrichment lives on its own
              page (/deep-dive/:id). If it's still generating, that page runs
              an arcade minigame while the user waits. */}
          <div style={{ marginTop: 3 }} data-report-exclude="true">
            <button
              onClick={() => { if (deepDiveReady || enrichPending) navigate(`/deep-dive/${resultId}`) }}
              disabled={!deepDiveReady && !enrichPending}
              style={{ width: '100%', padding: '18px 32px', background: (deepDiveReady || enrichPending) ? `${accent}14` : 'rgba(215,228,242,0.03)', border: `1px solid ${(deepDiveReady || enrichPending) ? accent + '77' : 'rgba(215,228,242,0.14)'}`, color: (deepDiveReady || enrichPending) ? S.textPrim : S.textMuted, cursor: (deepDiveReady || enrichPending) ? 'pointer' : 'default', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 14, transition: 'all 220ms', fontFamily: S.fontSC, fontSize: 9, letterSpacing: '0.22em', opacity: (deepDiveReady || enrichPending) ? 1 : 0.65 }}
              onMouseEnter={e => { if (deepDiveReady || enrichPending) { e.currentTarget.style.background = `${accent}22`; e.currentTarget.style.borderColor = accent } }}
              onMouseLeave={e => { if (deepDiveReady || enrichPending) { e.currentTarget.style.background = `${accent}14`; e.currentTarget.style.borderColor = `${accent}77` } }}
            >
              <span style={{ fontSize: 13, opacity: 0.85 }}>✦</span>
              {deepDiveReady ? 'ENTER DEEP DIVE MODE'
                : enrichPending ? 'DEEP DIVE · GENERATING, PLAY WHILE YOU WAIT'
                : 'DEEP DIVE · UNAVAILABLE'}
            </button>
            {enrichPending && !deepDiveReady && (
              <p style={{ fontFamily: S.fontSC, fontSize: 10, letterSpacing: '0.04em', color: S.textMuted, lineHeight: 1.7, marginTop: 8, textAlign: 'center' }}>
                Deep Dive gives a more psychology-compliant read on your profile. Enter now and play the arcade while it finishes, or come back later from your dashboard.
              </p>
            )}
          </div>

          {/* Actions, excluded from the downloaded report */}
          <div data-report-exclude="true" style={{ marginTop: 3, display: 'flex', flexDirection: 'column', gap: 3 }}>
            <button
              onClick={handleDownload}
              disabled={downloading}
              style={{ width: '100%', padding: '18px 32px', background: 'rgba(215,228,242,0.04)', border: `1px solid ${accent}44`, color: S.textSec, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 14, transition: 'all 220ms', fontFamily: S.fontSC, fontSize: 9, letterSpacing: '0.22em' }}
              onMouseEnter={e => { e.currentTarget.style.background = 'rgba(215,228,242,0.08)'; e.currentTarget.style.borderColor = `${accent}88`; e.currentTarget.style.color = S.textPrim }}
              onMouseLeave={e => { e.currentTarget.style.background = 'rgba(215,228,242,0.04)'; e.currentTarget.style.borderColor = `${accent}44`; e.currentTarget.style.color = S.textSec }}
            >
              <span style={{ fontSize: 14, opacity: 0.7 }}>↓</span>
              {downloading ? 'Preparing Report...' : 'Download Report'}
            </button>
            <div style={{ display: 'flex', gap: 3 }}>
              <Link to="/dashboard" className="btn btn-secondary" style={{ flex: 1, justifyContent: 'center' }}>Dashboard</Link>
              <Link to="/tests" className="btn btn-primary" style={{ flex: 1, justifyContent: 'center' }}>Take Another Test</Link>
            </div>
          </div>

          <div style={{ height: 40 }} />
        </div>
      </div>

      <style>{`
        @keyframes metal-sweep { 0%,100%{background-position:0% 50%} 50%{background-position:100% 50%} }
        @keyframes pulse-ring { 0%{opacity:0.7;transform:scale(1)} 100%{opacity:0;transform:scale(1.6)} }
      `}</style>
    </div>
  )
}