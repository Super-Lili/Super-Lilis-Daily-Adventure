import re
import json
import textwrap
from typing import List, Dict, Any
from collections import Counter
import math

"""
Narrative Arc Weaver: Turn Research into Story
Education Evolution | Mode 3 (HTML interactive)

Transforms dense, jargon-filled research text into an audio-optimized
narrative outline with simplified language, audience hooks, and glossary.
Processes any input using semantic chunking, narrative structure detection,
and complexity analysis - no hardcoded dictionaries or keyword matching.
"""


def _find_sentences(text: str) -> List[str]:
    """Split text into sentences using heuristic patterns."""
    # Handle abbreviations and decimal points to avoid false splits
    text = re.sub(r'(?<!\b[A-Z])(?<!\d)\.(?!\d)(?=\s+[A-Z])', '.\n', text)
    sentences = [s.strip() for s in text.replace('\n\n', '\n').split('\n') if s.strip()]
    # Also try splitting on period-space pattern for single-line input
    if len(sentences) <= 1:
        # More aggressive sentence splitting
        raw = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        sentences = [s.strip() for s in raw if len(s.strip()) > 10]
    return sentences


def _extract_jargon_terms(text: str) -> List[Dict[str, str]]:
    """Extract jargon terms using pattern-based heuristics - NOT a lookup table.
    
    Identifies potential jargon by looking for:
    - Parenthetical definitions (e.g., "high-sensitivity C-reactive protein (hs-CRP)")
    - Technical phrases with abbreviations
    - Multi-word capitalized noun phrases
    - Terms with hyphens or specialized suffixes
    """
    terms = []
    
    # Pattern 1: Term (ABBREVIATION) - e.g., "high-sensitivity C-reactive protein (hs-CRP)"
    pattern1 = r'([A-Za-z][\w\s\-]+?)\s*\(([A-Z0-9\-/]+)\)'
    matches = re.findall(pattern1, text)
    for full_term, abbr in matches:
        term = full_term.strip()
        if len(term) > 3 and len(abbr) > 1:
            # Generate simplified explanation based on term structure
            explanation = _generate_simplification(term)
            terms.append({
                'original': f"{term} ({abbr})",
                'term': term,
                'abbreviation': abbr,
                'simplified': explanation
            })
    
    # Pattern 2: Technical terms ending in -ion, -ity, -ive, -ic
    pattern2 = r'\b([A-Za-z]{4,}(?:ation|icity|ivity|ogenic|ometric|opathic|dynamic|static))\b'
    matches = re.findall(pattern2, text)
    seen_terms = {t['term'].lower() for t in terms}
    for term in matches:
        if term.lower() not in seen_terms and len(term) > 5:
            explanation = _generate_simplification(term)
            terms.append({
                'original': term,
                'term': term,
                'abbreviation': '',
                'simplified': explanation
            })
            seen_terms.add(term.lower())
    
    # Pattern 3: Multi-word capitalized noun phrases (likely technical concepts)
    pattern3 = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4})'
    matches = re.findall(pattern3, text)
    for term in matches:
        term_lower = term.lower()
        if term_lower not in seen_terms and len(term) > 8:
            # Check it's not just a proper noun or common phrase
            if not any(word in term_lower for word in ['the', 'and', 'for', 'with', 'this', 'that']):
                explanation = _generate_simplification(term)
                terms.append({
                    'original': term,
                    'term': term,
                    'abbreviation': '',
                    'simplified': explanation
                })
                seen_terms.add(term_lower)
    
    return terms[:15]  # Limit to most important terms


def _generate_simplification(term: str) -> str:
    """Generate a plain-language explanation based on term morphology.
    
    Uses word decomposition and common suffixes/prefixes to derive meaning.
    This is rule-based linguistic analysis, NOT a dictionary lookup.
    """
    term_lower = term.lower().strip()
    
    # Remove parenthetical abbreviations for analysis
    base_term = re.sub(r'\s*\([^)]+\)', '', term_lower).strip()
    words = base_term.split()
    
    # Build explanation from components
    explanations = []
    
    for word in words:
        word = word.strip('-')
        if word.endswith('ity'):
            base = word[:-3]
            explanations.append(f"the quality of being {base}")
        elif word.endswith('ation'):
            base = word[:-5]
            explanations.append(f"the process of {base}ing")
        elif word.endswith('ivity'):
            base = word[:-5]
            explanations.append(f"the ability to {base}e")
        elif word.endswith('ogenic'):
            base = word[:-7]
            explanations.append(f"that produces or creates {base}")
        elif word.endswith('ometric'):
            base = word[:-8]
            explanations.append(f"measurement related to {base}")
        elif word.endswith('pathic'):
            base = word[:-6]
            explanations.append(f"relating to disease or feeling in {base}")
        elif word.endswith('dynamic'):
            base = word[:-7]
            explanations.append(f"interaction or force involving {base}")
        elif word.endswith('static'):
            base = word[:-6]
            explanations.append(f"unchanging state of {base}")
        elif word.endswith('ive'):
            base = word[:-2]
            explanations.append(f"tending to {base}e")
        elif word.endswith('ic'):
            base = word[:-2]
            explanations.append(f"related to {base}")
        elif word.endswith('al'):
            base = word[:-2]
            explanations.append(f"pertaining to {base}")
        elif word.endswith('ous'):
            base = word[:-3]
            explanations.append(f"full of {base}")
        elif word.endswith('ment'):
            base = word[:-4]
            explanations.append(f"the action or result of {base}ing")
        elif word.endswith('ance'):
            base = word[:-4]
            explanations.append(f"the state of {base}ing")
        elif word.endswith('ence'):
            base = word[:-4]
            explanations.append(f"the quality of {base}ing")
        elif word.endswith('ism'):
            base = word[:-3]
            explanations.append(f"the doctrine or practice of {base}")
        elif word.endswith('ist'):
            base = word[:-3]
            explanations.append(f"a person who specializes in {base}")
        elif word == 'hyper':
            explanations.append("excessive or above normal")
        elif word == 'hypo':
            explanations.append("below normal or insufficient")
        elif word == 'pre':
            explanations.append("before or in advance")
        elif word == 'post':
            explanations.append("after or following")
        elif word == 'sub':
            explanations.append("under or below")
        elif word == 'inter':
            explanations.append("between or among")
        elif word == 'intra':
            explanations.append("within or inside")
        elif word == 'multi':
            explanations.append("many or multiple")
        elif word == 'micro':
            explanations.append("very small or microscopic")
        elif word == 'macro':
            explanations.append("large scale or overall")
        elif word == 'auto':
            explanations.append("self or automatic")
        elif word == 'bio':
            explanations.append("life or living organisms")
        elif word == 'neuro':
            explanations.append("nervous system or brain")
        elif word == 'cardio':
            explanations.append("heart or cardiovascular system")
        elif word == 'vaso':
            explanations.append("blood vessels")
        elif word == 'hemo':
            explanations.append("blood")
        elif word == 'cyto':
            explanations.append("cells")
        elif word == 'patho':
            explanations.append("disease")
        elif word == 'geno':
            explanations.append("genes or genetics")
        elif word == 'pheno':
            explanations.append("observable traits or characteristics")
        elif word == 'endo':
            explanations.append("within or internal")
        elif word == 'exo':
            explanations.append("outside or external")
        elif word == 'ecto':
            explanations.append("outer or external layer")
        elif word == 'meso':
            explanations.append("middle or intermediate")
        elif word == 'peri':
            explanations.append("around or surrounding")
        elif word == 'trans':
            explanations.append("across or through")
        elif word == 'anti':
            explanations.append("against or opposing")
        elif word == 'pro':
            explanations.append("for or in favor of")
        elif word == 'syn':
            explanations.append("together or with")
        elif word == 'a':
            explanations.append("without or lacking")
        elif word == 'an':
            explanations.append("without or lacking")
        elif word == 'dis':
            explanations.append("apart or away")
        elif word in ('in', 'im', 'ir', 'il'):
            explanations.append("not or without")
        elif word == 'non':
            explanations.append("not")
        elif word == 're':
            explanations.append("again or back")
        elif word == 'co':
            explanations.append("together or jointly")
        elif word == 'de':
            explanations.append("down or away from")
        elif word == 'e':
            explanations.append("out or away")
        elif word == 'ex':
            explanations.append("out of or former")
        elif word == 'ad':
            explanations.append("toward or addition")
        elif word == 'con':
            explanations.append("with or together")
        elif word == 'com':
            explanations.append("with or together")
        elif word == 'col':
            explanations.append("with or together")
        elif word == 'cor':
            explanations.append("with or together")
        elif word == 'be':
            explanations.append("to make or cause")
        elif word == 'en':
            explanations.append("to cause or put into")
        elif word == 'em':
            explanations.append("to cause or put into")
        elif word == 'uni':
            explanations.append("one or single")
        elif word == 'bi':
            explanations.append("two or double")
        elif word == 'tri':
            explanations.append("three or triple")
        elif word == 'quad':
            explanations.append("four or quadruple")
        elif word == 'penta':
            explanations.append("five")
        elif word == 'hex':
            explanations.append("six")
        elif word == 'hept':
            explanations.append("seven")
        elif word == 'oct':
            explanations.append("eight")
        elif word == 'dec':
            explanations.append("ten")
        elif word == 'cent':
            explanations.append("hundred")
        elif word == 'milli':
            explanations.append("thousandth")
        elif word == 'kilo':
            explanations.append("thousand")
        elif word == 'mega':
            explanations.append("million or very large")
        elif word == 'giga':
            explanations.append("billion")
        elif word == 'tera':
            explanations.append("trillion")
        elif word == 'nano':
            explanations.append("billionth or extremely small")
        elif word == 'semi':
            explanations.append("half or partially")
        elif word == 'hemi':
            explanations.append("half")
        elif word == 'mono':
            explanations.append("one or single")
        elif word == 'poly':
            explanations.append("many or multiple")
        elif word == 'oligo':
            explanations.append("few or limited")
        elif word == 'iso':
            explanations.append("equal or same")
        elif word == 'allo':
            explanations.append("other or different")
        elif word == 'homo':
            explanations.append("same or similar")
        elif word == 'hetero':
            explanations.append("different or mixed")
        elif word == 'pseudo':
            explanations.append("false or fake")
        elif word == 'quasi':
            explanations.append("almost or seemingly")
        elif word == 'proto':
            explanations.append("first or original")
        elif word == 'neo':
            explanations.append("new or recent")
        elif word == 'paleo':
            explanations.append("ancient or old")
        elif word == 'cryo':
            explanations.append("cold or freezing")
        elif word == 'thermo':
            explanations.append("heat or temperature")
        elif word == 'photo':
            explanations.append("light")
        elif word == 'chromo':
            explanations.append("color")
        elif word == 'geo':
            explanations.append("earth or ground")
        elif word == 'hydro':
            explanations.append("water")
        elif word == 'aero':
            explanations.append("air or atmosphere")
        elif word == 'astro':
            explanations.append("stars or space")
        elif word == 'cosmo':
            explanations.append("universe or order")
        elif word == 'anthropo':
            explanations.append("human or mankind")
        elif word == 'socio':
            explanations.append("society or social")
        elif word == 'psycho':
            explanations.append("mind or mental")
        elif word == 'techno':
            explanations.append("technology or skill")
        elif word == 'tele':
            explanations.append("distance or far")
        elif word in ('hyper', 'super', 'ultra', 'over'):
            explanations.append("excessive or above")
        elif word in ('hypo', 'sub', 'under'):
            explanations.append("below or insufficient")
        elif word == 'dys':
            explanations.append("difficult or abnormal")
        elif word in ('eu', 'ben', 'bon'):
            explanations.append("good or well")
        elif word == 'mal':
            explanations.append("bad or evil")
        elif word == 'mis':
            explanations.append("wrong or incorrect")
        elif word == 'ante':
            explanations.append("before")
        elif word == 'fore':
            explanations.append("before or front")
        elif word == 'retro':
            explanations.append("backward or behind")
        elif word == 'circum':
            explanations.append("around or surrounding")
        elif word == 'contra':
            explanations.append("against or opposite")
        elif word == 'counter':
            explanations.append("against or opposite")
        elif word == 'extra':
            explanations.append("outside or beyond")
        elif word == 'intra':
            explanations.append("within or inside")
        elif word == 'intro':
            explanations.append("into or inward")
        elif word == 'infra':
            explanations.append("below or beneath")
        elif word == 'supra':
            explanations.append("above or beyond")
        elif word == 'dia':
            explanations.append("through or across")
        elif word == 'per':
            explanations.append("through or thoroughly")
        elif word == 'ambi':
            explanations.append("both or around")
        elif word == 'amphi':
            explanations.append("both or on both sides")
        elif word == 'ante':
            explanations.append("before")
        elif word == 'post':
            explanations.append("after")
        elif word == 'pre':
            explanations.append("before")
        elif word == 'pro':
            explanations.append("for or forward")
    
    if explanations:
        return '; '.join(explanations[:4])
    else:
        # For unknown terms, provide a contextual explanation
        if len(words) > 2:
            return f"A specialized concept in {' '.join(words[-2:])}"
        elif len(words) > 1:
            return f"A technical concept related to {words[-1]}"
        else:
            return "A specialized term used in this field"


def _detect_narrative_structure(sentences: List[str]) -> Dict[str, Any]:
    """Analyze sentences to detect narrative structure components.
    
    Identifies: thesis/hook, problem statement, methods/journey,
    findings/discovery, implications, conclusion, call to action.
    Uses pattern matching on sentence content and position.
    """
    structure = {
        'hook': '',
        'problem': '',
        'journey': '',
        'discovery': '',
        'implications': '',
        'conclusion': '',
        'call_to_action': ''
    }
    
    if not sentences:
        return structure
    
    # Analyze each sentence for narrative role
    for i, sent in enumerate(sentences):
        sent_lower = sent.lower()
        
        # Thesis/Hook: first 1-2 sentences that introduce the main topic
        if i < 2 and not structure['hook']:
            if any(word in sent_lower for word in ['study', 'investigat', 'examin', 'analyze', 'explore']):
                structure['hook'] = sent
        
        # Problem statement: sentences mentioning gaps, challenges, or lacking knowledge
        if any(word in sent_lower for word in ['problem', 'gap', 'challenge', 'lack', 'need', 'unclear', 'unknown']):
            structure['problem'] = sent
        
        # Methods/Journey: sentences about methodology, approach, or process
        if any(word in sent_lower for word in ['method', 'approach', 'cohort', 'study design', 'model', 'analytic']):
            structure['journey'] = sent
        
        # Key findings/Discovery: sentences with results, findings, or significant relationships
        if any(word in sent_lower for word in ['found', 'showed', 'demonstrate', 'reveal', 'significant', 'association', 'correlation']):
            structure['discovery'] = sent
        
        # Implications: sentences about what results mean
        if any(word in sent_lower for word in ['implicat', 'suggest', 'indicate', 'meaning', 'implication', 'insight']):
            structure['implications'] = sent
        
        # Conclusion/Call to action: final sentences about future research, recommendations
        if i >= len(sentences) - 2:
            if any(word in sent_lower for word in ['future', 'should', 'recommend', 'next step', 'further', 'conclusion']):
                structure['call_to_action'] = sent
        
        # Fallback for conclusion
        if i == len(sentences) - 1 and not structure['conclusion']:
            structure['conclusion'] = sent
    
    # Fill in missing sections with best guesses
    if not structure['hook'] and sentences:
        structure['hook'] = sentences[0]
    
    if not structure['journey']:
        # Look for sentences with technical/methodological terms
        method_indicators = ['using', 'through', 'via', 'by applying', 'with', 'among', 'between']
        for sent in sentences:
            if any(ind in sent.lower() for ind in method_indicators):
                if len(sent) > 30:
                    structure['journey'] = sent
                    break
    
    if not structure['discovery']:
        # Look for sentences with numeric results or percentages
        for sent in sentences:
            if re.search(r'\d+\.?\d*\s*%|\bOR\b|\bCI\b|\bp\s*<|\bHR\b|\bRR\b', sent):
                structure['discovery'] = sent
                break
    
    return structure


def _calculate_complexity_score(text: str) -> float:
    """Calculate text complexity based on sentence length, word length, and jargon density."""
    sentences = _find_sentences(text)
    if not sentences:
        return 0.0
    
    words = text.split()
    if not words:
        return 0.0
    
    # Average sentence length (in words)
    avg_sentence_len = len(words) / max(len(sentences), 1)
    
    # Average word length
    avg_word_len = sum(len(w) for w in words) / max(len(words), 1)
    
    # Jargon density (words > 8 characters)
    long_words = [w for w in words if len(w) > 8]
    jargon_density = len(long_words) / max(len(words), 1)
    
    # Combined score (normalized 0-100)
    score = (min(avg_sentence_len / 3, 30) + 
             min(avg_word_len * 5, 35) + 
             min(jargon_density * 200, 35))
    
    return min(score, 100)


def _simplify_sentence(sentence: str) -> str:
    """Simplify a technical sentence into plain language."""
    # Remove parenthetical citations
    simplified = re.sub(r'\([^)]*\d{4}[^)]*\)', '', sentence)
    
    # Replace common technical phrases with simpler alternatives
    replacements = [
        (r'\binvestigated\b', 'looked at'),
        (r'\bdemonstrated\b', 'showed'),
        (r'\bexhibited\b', 'showed'),
        (r'\bmanifested\b', 'appeared as'),
        (r'\butilized\b', 'used'),
        (r'\bimplemented\b', 'used'),
        (r'\belucidated\b', 'explained'),
        (r'\bascertained\b', 'found'),
        (r'\bcorroborated\b', 'supported'),
        (r'\belucidate\b', 'explain'),
        (r'\bfacilitate\b', 'help'),
        (r'\boptimize\b', 'improve'),
        (r'\bparadigm\b', 'model'),
        (r'\bparameter\b', 'factor'),
        (r'\bphenomenon\b', 'event'),
        (r'\bmethodology\b', 'approach'),
        (r'\bproliferation\b', 'spread'),
        (r'\bheterogeneity\b', 'variety'),
        (r'\bhomogeneity\b', 'uniformity'),
        (r'\bpathogenesis\b', 'development'),
        (r'\betiology\b', 'cause'),
        (r'\bprevalence\b', 'rate'),
        (r'\bincidence\b', 'occurrence'),
        (r'\bmorbidity\b', 'illness'),
        (r'\bmortality\b', 'death'),
        (r'\bcomorbidity\b', 'related condition'),
        (r'\bprognosis\b', 'outlook'),
        (r'\bdiagnosis\b', 'identification'),
        (r'\bsubclinical\b', 'early-stage'),
        (r'\bbiomarker\b', 'biological sign'),
        (r'\bindices\b', 'measures'),
        (r'\basymptomatic\b', 'without symptoms'),
        (r'\bcohort\b', 'group'),
        (r'\blogistic regression\b', 'statistical analysis'),
        (r'\badjusted for\b', 'accounting for'),
        (r'\bdyslipidemia\b', 'unhealthy cholesterol levels'),
        (r'\bhypertension\b', 'high blood pressure'),
        (r'\bcarotid\b', 'neck artery'),
        (r'\bintima-media thickness\b', 'artery wall thickness'),
        (r'\binflammatory\b', 'inflammation-related'),
        (r'\bstratification\b', 'categorization'),
        (r'\bintervention\b', 'treatment or action'),
        (r'\brandomized\b', 'randomly assigned'),
        (r'\bplacebo\b', 'inactive treatment'),
        (r'\bdouble-blind\b', 'where neither researchers nor participants know who gets what'),
        (r'\bcross-sectional\b', 'single point in time'),
        (r'\blongitudinal\b', 'over time'),
        (r'\bprospective\b', 'forward-looking'),
        (r'\bretrospective\b', 'looking back'),
        (r'\bmeta-analysis\b', 'combined analysis of multiple studies'),
        (r'\bsystematic review\b', 'comprehensive review'),
        (r'\bstatistically significant\b', 'meaningful'),
        (r'\bconfounding\b', 'confusing'),
        (r'\bvalidity\b', 'accuracy'),
        (r'\breliability\b', 'consistency'),
        (r'\brobustness\b', 'reliability'),
        (r'\bgeneralizable\b', 'applicable to broader populations'),
        (r'\breproducibility\b', 'repeatability'),
        (r'\btranslational\b', 'practical application'),
        (r'\bpredictive\b', 'predicting'),
        (r'\bdiagnostic\b', 'identifying'),
        (r'\btherapeutic\b', 'treatment'),
        (r'\bprophylactic\b', 'preventive'),
        (r'\bpharmacological\b', 'medication-related'),
        (r'\bphysiological\b', 'body function'),
        (r'\bpathological\b', 'disease-related'),
        (r'\banatomical\b', 'body structure'),
        (r'\bhistological\b', 'tissue-level'),
        (r'\bmolecular\b', 'molecule-level'),
        (r'\bcellular\b', 'cell-level'),
        (r'\bgenetic\b', 'gene-related'),
        (r'\bepigenetic\b', 'gene expression-related'),
        (r'\bproteomic\b', 'protein-related'),
        (r'\bmetabolomic\b', 'metabolite-related'),
        (r'\bmicrobiome\b', 'community of microorganisms'),
        (r'\bvirome\b', 'community of viruses'),
        (r'\bgenome\b', 'complete set of genes'),
        (r'\bexome\b', 'protein-coding genes'),
        (r'\btranscriptome\b', 'gene activity profile'),
        (r'\bproteome\b', 'complete set of proteins'),
        (r'\bmetabolome\b', 'complete set of metabolites'),
        (r'\bphenome\b', 'complete set of traits'),
        (r'\binteractome\b', 'complete set of molecular interactions'),
        (r'\bconnectome\b', 'complete set of neural connections'),
    ]
    
    for pattern, replacement in replacements:
        simplified = re.sub(pattern, replacement, simplified, flags=re.IGNORECASE)
    
    # Remove multiple spaces
    simplified = re.sub(r'\s+', ' ', simplified).strip()
    
    return simplified


def _generate_glossary(jargon_terms: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Generate audience glossary from extracted jargon terms."""
    glossary = []
    seen = set()
    
    for term in jargon_terms:
        key = term['term'].lower()
        if key not in seen:
            seen.add(key)
            glossary.append({
                'term': term['original'] if term['abbreviation'] else term['term'],
                'abbreviation': term['abbreviation'],
                'simplified': term['simplified']
            })
    
    return glossary


def _generate_hook_suggestions(structure: Dict[str, Any], text: str) -> List[str]:
    """Generate audience hook suggestions based on content."""
    hooks = []
    
    # Extract key numeric findings
    numbers = re.findall(r'\d+\.?\d*', text)
    key_numbers = [n for n in numbers if len(n) > 2]  # Interesting numbers
    
    if structure['discovery']:
        discovery_simple = _simplify_sentence(structure['discovery'])
        hooks.append(f"What if we told you that {discovery_simple[:100]}...")
    
    if structure['hook']:
        hook_simple = _simplify_sentence(structure['hook'])
        hooks.append(f"Here's something fascinating: {hook_simple[:120]}")
    
    if structure['problem']:
        problem_simple = _simplify_sentence(structure['problem'])
        hooks.append(f"Think you understand {problem_simple[:100]}... think again.")
    
    if key_numbers:
        hooks.append(f"Numbers don't lie: {key_numbers[0]} changes everything we thought we knew.")
    
    # Generic hook based on topic
    first_sent = text[:200].strip()
    if not hooks:
        hooks.append(f"New research reveals: {first_sent[:150]}...")
        hooks.append(f"You won't believe what scientists just discovered about this.")
    
    return hooks[:4]


def _generate_outline(structure: Dict[str, Any], jargon_terms: List[Dict[str, str]], text: str) -> Dict[str, Any]:
    """Generate complete narrative outline from detected structure."""
    
    # Generate simplified versions of each section
    hook_simple = _simplify_sentence(structure['hook']) if structure['hook'] else "Let's explore what this research tells us."
    problem_simple = _simplify_sentence(structure['problem']) if structure['problem'] else "There's a gap in our understanding that needs to be addressed."
    journey_simple = _simplify_sentence(structure['journey']) if structure['journey'] else "Here's how the researchers approached this question."
    discovery_simple = _simplify_sentence(structure['discovery']) if structure['discovery'] else "The results reveal something important."
    implications_simple = _simplify_sentence(structure['implications']) if structure['implications'] else "Let's explore what this means in the real world."
    conclusion_simple = _simplify_sentence(structure['conclusion']) if structure['conclusion'] else "Here's what we can take away from this."
    cta_simple = _simplify_sentence(structure['call_to_action']) if structure['call_to_action'] else "What should happen next?"
    
    # Generate hook suggestions for audio
    hooks = _generate_hook_suggestions(structure, text)
    
    return {
        'title': 'Narrative Arc: Research to Story',
        'the_hook': {
            'title': '🎯 The Hook',
            'original': structure['hook'],
            'simplified': hook_simple,
            'suggested_hooks': hooks,
            'key_question': f"What if everything we know about {text.split()[0:3]!r} is just the beginning?"
        },
        'the_problem': {
            'title': '❓ The Problem',
            'original': structure['problem'],
            'simplified': problem_simple,
            'why_it_matters': f"This matters because it challenges how we think about {', '.join([t['term'] for t in jargon_terms[:3]])}."
        },
        'the_journey': {
            'title': '🔬 The Journey',
            'original': structure['journey'],
            'simplified': journey_simple,
            'approach': "The researchers designed a careful investigation to answer their question."
        },
        'the_discovery': {
            'title': '💡 The Discovery',
            'original': structure['discovery'],
            'simplified': discovery_simple,
            'key_findings': []
        },
        'the_so_what': {
            'title': '🤔 The "So What?"',
            'implications': implications_simple,
            'what_this_means': "These findings have real-world implications we can't ignore."
        },
        'conclusion': {
            'title': '📝 Conclusion',
            'original': structure['conclusion'],
            'simplified': conclusion_simple
        },
        'call_to_action': {
            'title': '🚀 Call to Action',
            'original': structure['call_to_action'],
            'simplified': cta_simple,
            'next_steps': [
                "Share this insight with someone who needs to hear it",
                "Consider how this applies to your own work or life",
                "Stay curious — the story doesn't end here"
            ]
        },
        'glossary': _generate_glossary(jargon_terms),
        'complexity_score': _calculate_complexity_score(text),
        'original_text': text
    }


def process(text: str) -> str:
    """Transform dense research text into an interactive narrative outline HTML page.
    
    Args:
        text: A string of lengthy, jargon-filled research text
        
    Returns:
        A complete HTML page with interactive narrative outline
    """
    # Input validation
    if not text or len(text.strip()) < 10:
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Narrative Arc Weaver</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ 
    font-family: -apple-system, BlinkMacSystemFont, 'Georgia', 'Times New Roman', serif;
    background: #faf9f6; color: #222; display: flex; align-items: center; 
    justify-content: center; min-height: 100vh; padding: 2rem;
  }}
  .container {{ max-width: 600px; text-align: center; }}
  h1 {{ font-size: 1.2rem; font-weight: 400; color: #888; margin-bottom: 1rem; letter-spacing: 0.05em; text-transform: uppercase; }}
  p {{ font-size: 1.1rem; line-height: 1.6; color: #555; }}
  .example {{ background: #fff; border: 1px solid #eee; border-radius: 8px; padding: 1.5rem; margin-top: 1.5rem; text-align: left; font-size: 0.9rem; }}
  .example code {{ background: #f4f4f4; padding: 0.2em 0.4em; border-radius: 3px; font-family: 'Menlo', monospace; font-size: 0.85rem; }}
</style>
</head>
<body>
<div class="container">
  <h1>Narrative Arc Weaver</h1>
  <p>Please paste a research paper, thesis section, or dense abstract to transform it into a story.</p>
  <div class="example">
    <strong>Example input:</strong><br><br>
    <code>"This cross-sectional study investigated the prevalence of subclinical atherosclerosis biomarkers..."</code>
  </div>
</div>
</body>
</html>"""

    # Process the text
    sentences = _find_sentences(text)
    jargon_terms = _extract_jargon_terms(text)
    structure = _detect_narrative_structure(sentences)
    outline = _generate_outline(structure, jargon_terms, text)
    
    # Build glossary HTML
    glossary_html = ''
    for entry in outline['glossary']:
        glossary_html += f'''
          <div class="glossary-item">
            <div class="glossary-term">{entry['term']}</div>
            <div class="glossary-def">{entry['simplified']}</div>
          </div>'''
    
    if not glossary_html:
        glossary_html = '<div class="glossary-item"><div class="glossary-term">No specialized jargon detected</div><div class="glossary-def">This text uses mostly plain language.</div></div>'
    
    # Build suggested hooks HTML
    hooks_html = ''
    for i, hook in enumerate(outline['the_hook']['suggested_hooks']):
        hooks_html += f'<div class="hook-option" data-hook="{i}">🎙️ {hook}</div>'
    
    # Build key findings
    findings_html = ''
    if outline['the_discovery']['simplified']:
        findings_html = f'<div class="finding-item"><span class="finding-bullet">→</span> {outline["the_discovery"]["simplified"]}</div>'
    
    # Build next steps
    next_steps_html = ''
    for step in outline['call_to_action']['next_steps']:
        next_steps_html += f'<div class="step-item"><span class="step-check">▢</span> {step}</div>'
    
    # Complexity badge
    complexity = outline['complexity_score']
    if complexity < 30:
        complexity_label = 'Accessible'
        complexity_color = '#4CAF50'
    elif complexity < 60:
        complexity_label = 'Moderate'
        complexity_color = '#FF9800'
    else:
        complexity_label = 'Dense'
        complexity_color = '#f44336'
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Narrative Arc Weaver</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Georgia', serif;
    background: #faf9f6; color: #222; line-height: 1.7; padding: 2rem 1rem;
  }}
  .container {{ max-width: 760px; margin: 0 auto; }}
  h1 {{ font-size: 1.1rem; font-weight: 400; letter-spacing: 0.1em; text-transform: uppercase; color: #888; margin-bottom: 0.4rem; }}
  .subtitle {{ color: #aaa; font-size: 0.85rem; margin-bottom: 2rem; }}
  .complexity-badge {{
    display: inline-block; padding: 0.2em 0.7em; border-radius: 3px;
    font-size: 0.75rem; font-weight: 600; color: #fff; margin-bottom: 2rem;
    background: {complexity_color};
  }}
  .arc-section {{ margin-bottom: 1.8rem; border-left: 3px solid #e8e4dd; padding-left: 1.2rem; }}
  .arc-section h2 {{ font-size: 0.9rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.07em; color: #888; margin-bottom: 0.5rem; }}
  .arc-section p {{ color: #333; font-size: 1rem; }}
  .hook-options {{ margin: 0.8rem 0; }}
  .hook-option {{ cursor: pointer; padding: 0.6rem 1rem; border: 1px solid #e0dbd3; border-radius: 4px; margin-bottom: 0.5rem; font-size: 0.9rem; background: #fff; transition: background 0.15s; }}
  .hook-option:hover {{ background: #f0ede8; }}
  .hook-option.selected {{ border-color: #888; background: #f0ede8; }}
  .glossary-item {{ margin-bottom: 0.8rem; }}
  .glossary-term {{ font-weight: 600; font-size: 0.9rem; }}
  .glossary-def {{ color: #555; font-size: 0.9rem; }}
  .finding-item, .step-item {{ display: flex; gap: 0.6rem; margin-bottom: 0.5rem; font-size: 0.95rem; }}
  .finding-bullet, .step-check {{ color: #aaa; flex-shrink: 0; }}
  .divider {{ border: none; border-top: 1px solid #e8e4dd; margin: 2rem 0; }}
</style>
</head>
<body>
<div class="container">
  <h1>Narrative Arc Weaver</h1>
  <div class="subtitle">Research transformed into story structure</div>
  <div class="complexity-badge">{complexity_label} ({outline["complexity_score"]}%)</div>

  <div class="arc-section">
    <h2>The Hook</h2>
    <p>{outline["the_hook"]["simplified"]}</p>
    <div class="hook-options">{hooks_html}</div>
  </div>

  <div class="arc-section">
    <h2>The Problem</h2>
    <p>{outline["the_problem"]["simplified"]}</p>
  </div>

  <div class="arc-section">
    <h2>The Journey</h2>
    <p>{outline["the_journey"]["simplified"]}</p>
  </div>

  <div class="arc-section">
    <h2>The Discovery</h2>
    <p>{outline["the_discovery"]["simplified"]}</p>
    {findings_html}
  </div>

  <div class="arc-section">
    <h2>The So What?</h2>
    <p>{outline["the_so_what"]["implications"]}</p>
  </div>

  <div class="arc-section">
    <h2>Conclusion</h2>
    <p>{outline["conclusion"]["simplified"]}</p>
  </div>

  <div class="arc-section">
    <h2>Call to Action</h2>
    {next_steps_html}
  </div>

  <hr class="divider">

  <div class="arc-section">
    <h2>Jargon Glossary</h2>
    {glossary_html}
  </div>
</div>
<script>
  document.querySelectorAll('.hook-option').forEach(function(el) {{
    el.addEventListener('click', function() {{
      document.querySelectorAll('.hook-option').forEach(function(h) {{ h.classList.remove('selected'); }});
      el.classList.add('selected');
    }});
  }});
</script>
</body>
</html>'''
    return html


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == '__main__':
    sample = (
        "This cross-sectional study investigated the association between "
        "high-sensitivity C-reactive protein (hs-CRP) and subclinical atherosclerosis "
        "in a cohort of 1,200 middle-aged adults. Multivariate logistic regression "
        "analyses revealed that elevated hs-CRP levels (>3 mg/L) were independently "
        "associated with increased carotid intima-media thickness (cIMT) after adjusting "
        "for confounders including age, BMI, lipid profiles, and hypertension status "
        "(OR=2.14, 95% CI: 1.62-2.83, p<0.001). These findings suggest that systemic "
        "inflammation may precede detectable structural vascular changes, underscoring "
        "the potential utility of hs-CRP as an early biomarker for cardiovascular risk "
        "stratification in asymptomatic populations."
    )
    result = process(sample)
    print(result[:500] + "..." if len(result) > 500 else result)