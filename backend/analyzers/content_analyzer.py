"""
Content Clarity Analyzer v2
Sentence-level direct answer scoring, contextual fluff detection, marketing vs information ratio.
"""
import re
import textstat


class ContentAnalyzer:
    """Deep content analysis for LLM extractability."""
    
    FLUFF_PHRASES = [
        "cutting-edge", "innovative", "revolutionary", "game-changing",
        "best-in-class", "world-class", "next-generation", "next-gen",
        "state-of-the-art", "industry-leading", "market-leading",
        "seamless", "robust", "scalable", "enterprise-grade",
        "one-stop", "end-to-end", "turnkey", "mission-critical",
        "disruptive", "transformative", "supercharge",
        "unlock the power", "unleash", "elevate your",
        "take it to the next level", "paradigm shift",
        "holistic approach", "synergies", "leverage",
        "reimagine", "redefine", "future-proof",
    ]
    
    VAGUE_CLAIMS = [
        r"\bthe best\b(?!.*\b(because|due to|since|as shown)\b)",
        r"\b(#1|number one|number 1)\b(?!.*\b(in|by|according)\b)",
        r"\bleading\b\s+(provider|platform|solution|tool|software)(?!.*\b(with|serving|processing)\b.*\d)",
        r"\btrusted by\b\s+(thousands|millions|many|countless)(?!.*\d)",
        r"\b(saves? time|saves? money)\b(?!.*\d)",
        r"\b(increase|improve|boost|enhance)s?\b\s+(productivity|efficiency|performance|results)(?!.*\d)",
        r"\b(fast|quick|easy|simple|powerful)\b(?!.*\b(than|compared|benchmark|example)\b)",
    ]
    
    def analyze(self, crawl_data: dict) -> dict:
        text = crawl_data.get("text_content", "")
        paragraphs_raw = crawl_data.get("paragraphs", [])
        
        # Filter to content paragraphs only (not nav/footer)
        paragraphs = [p for p in paragraphs_raw if not p.get("in_nav")]
        para_texts = [p.get("text", "") for p in paragraphs if p.get("word_count", 0) > 5]
        
        if not text or len(text) < 100:
            return self._empty_result()
        
        # === 1. Readability ===
        readability = self._analyze_readability(text)
        
        # === 2. Sentence-level analysis ===
        sentence_analysis = self._analyze_sentences(text)
        
        # === 3. Direct answer scoring (paragraph-level) ===
        direct_answer = self._score_direct_answers(para_texts)
        
        # === 4. Fluff detection (contextual) ===
        fluff = self._detect_fluff(text)
        
        # === 5. Vague claims ===
        vague = self._detect_vague_claims(text)
        
        # === 6. Voice analysis ===
        voice = self._analyze_voice(text)
        
        # === 7. Definition sentences (LLM gold) ===
        definitions = self._detect_definition_sentences(para_texts)
        
        # === 8. Marketing vs information ratio ===
        content_ratio = self._marketing_info_ratio(para_texts)
        
        # === 9. Extractability (combined) ===
        extractability = self._calc_extractability(readability, fluff, direct_answer, definitions, sentence_analysis)
        
        # === Score ===
        score = self._calc_score(readability, fluff, vague, direct_answer, extractability, voice, definitions, content_ratio)
        
        findings = []
        recommendations = []
        
        findings.append(f"Readability: Grade {readability['grade_level']} (Flesch score: {readability['flesch_reading_ease']})")
        findings.append(f"Avg sentence length: {sentence_analysis['avg_words_per_sentence']} words")
        findings.append(f"Direct answer paragraphs: {direct_answer['direct_count']}/{direct_answer['total']} ({direct_answer['pct']}%)")
        findings.append(f"Definition sentences found: {definitions['count']}")
        findings.append(f"Fluff phrases: {fluff['count']} | Vague claims: {vague['count']}")
        findings.append(f"Passive voice: {voice['passive_pct']}% | Content ratio: {content_ratio['info_pct']}% informational")
        
        # Readability
        if readability["grade_level"] > 14:
            recommendations.append(f"Readability is at grade {readability['grade_level']} — simplify to grade 8-10 for optimal LLM extraction. Use shorter sentences and simpler vocabulary.")
        elif readability["grade_level"] > 12:
            recommendations.append(f"Readability at grade {readability['grade_level']} — consider simplifying. LLMs extract cleaner answers from grade 8-10 content.")
        
        # Sentence length
        if sentence_analysis["avg_words_per_sentence"] > 25:
            recommendations.append(f"Average sentence is {sentence_analysis['avg_words_per_sentence']} words — break into 15-20 word sentences for clearer LLM extraction")
        
        if sentence_analysis["long_sentence_pct"] > 30:
            recommendations.append(f"{sentence_analysis['long_sentence_pct']}% of sentences exceed 30 words — rewrite the longest ones")
        
        # Direct answers
        if direct_answer["pct"] < 30:
            recommendations.append("Most paragraphs don't lead with a direct answer. Start paragraphs with the key point, then add context.")
        elif direct_answer["pct"] < 50:
            recommendations.append("Increase direct-answer paragraphs. Begin each paragraph with the core statement — LLMs extract the first sentence preferentially.")
        
        # Definitions
        if definitions["count"] < 2:
            recommendations.append("Add more definition-style sentences ('[X] is a [type] that [does Y]') — these are what LLMs extract most reliably")
        
        # Fluff
        if fluff["count"] > 5:
            top_fluff = ', '.join(f"\"{p}\"" for p in fluff["phrases"][:4])
            recommendations.append(f"Replace {fluff['count']} fluff phrases with specific claims. Found: {top_fluff}")
        elif fluff["count"] > 2:
            recommendations.append(f"Found {fluff['count']} fluff phrases — replace with concrete, measurable claims")
        
        # Vague claims
        if vague["count"] > 3:
            recommendations.append(f"Found {vague['count']} vague claims without evidence. Add specific numbers: '47% faster' instead of 'faster'")
        elif vague["count"] > 0:
            recommendations.append(f"Replace {vague['count']} vague claims with data-backed statements")
        
        # Voice
        if voice["passive_pct"] > 25:
            recommendations.append(f"{voice['passive_pct']}% passive voice — convert to active voice for direct, extractable statements")
        
        # Marketing ratio
        if content_ratio["marketing_pct"] > 50:
            recommendations.append(f"{content_ratio['marketing_pct']}% of content is marketing language vs informational. Shift toward factual, specific content.")
        
        return {
            "name": "Content Clarity",
            "icon": "🗣️",
            "score": score,
            "weight": 15,
            "readability": readability,
            "sentence_analysis": sentence_analysis,
            "direct_answers": direct_answer,
            "definitions": definitions,
            "fluff_detected": fluff,
            "vague_claims": vague,
            "voice_analysis": voice,
            "content_ratio": content_ratio,
            "extractability_score": extractability,
            "findings": findings,
            "recommendations": recommendations
        }
    
    def _empty_result(self):
        return {
            "name": "Content Clarity", "icon": "🗣️", "score": 0, "weight": 15,
            "findings": ["Insufficient text content (< 100 characters)"],
            "recommendations": ["Add substantial text content — LLMs need text to extract answers from"]
        }
    
    def _analyze_readability(self, text):
        try:
            return {
                "flesch_reading_ease": round(textstat.flesch_reading_ease(text), 1),
                "grade_level": round(textstat.flesch_kincaid_grade(text), 1),
                "gunning_fog": round(textstat.gunning_fog(text), 1),
                "smog_index": round(textstat.smog_index(text), 1),
                "avg_syllables_per_word": round(textstat.avg_syllables_per_word(text), 2),
            }
        except:
            return {"flesch_reading_ease": 50, "grade_level": 10, "gunning_fog": 10, "smog_index": 10, "avg_syllables_per_word": 1.5}
    
    def _analyze_sentences(self, text):
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if len(s.strip().split()) >= 3]
        
        if not sentences:
            return {"avg_words_per_sentence": 0, "total_sentences": 0, "long_sentence_pct": 0}
        
        word_counts = [len(s.split()) for s in sentences]
        long = sum(1 for wc in word_counts if wc > 30)
        
        return {
            "avg_words_per_sentence": round(sum(word_counts) / len(word_counts), 1),
            "total_sentences": len(sentences),
            "long_sentence_pct": round(long / len(sentences) * 100, 1),
            "max_words": max(word_counts),
            "min_words": min(word_counts),
        }
    
    def _score_direct_answers(self, paragraphs):
        """Score each paragraph on whether it starts with a direct answer."""
        if not paragraphs:
            return {"direct_count": 0, "total": 0, "pct": 0}
        
        direct_starters = [
            # Definitive statements
            r"^(Yes|No|It is|This is|That is|These are|There are|There is)",
            # Entity definitions
            r"^[A-Z][a-z]+\s+(is|are|was|were|has|provides|offers|helps|enables|allows)\b",
            # Instructional
            r"^(To|You can|You should|The (best|first|main|primary|easiest|simplest) (way|step|thing))\b",
            # Quantified
            r"^(\d|About \d|Over \d|More than \d|Up to \d|At least \d)",
            # Direct subject
            r"^(Our|The|This|We|Your)\s+\w+\s+(is|are|helps|provides|includes|offers|supports|allows|enables)",
        ]
        
        direct_count = 0
        for p in paragraphs:
            p_stripped = p.strip()
            for pattern in direct_starters:
                if re.match(pattern, p_stripped, re.I):
                    direct_count += 1
                    break
        
        total = len(paragraphs)
        return {
            "direct_count": direct_count,
            "total": total,
            "pct": round(direct_count / total * 100, 1) if total else 0
        }
    
    def _detect_definition_sentences(self, paragraphs):
        """Find sentences that follow the '[X] is a [Y] that [Z]' pattern — LLM gold."""
        patterns = [
            r"[A-Z][a-z]+(?:\s+[A-Z]?[a-z]+)*\s+is\s+(?:a|an|the)\s+\w+",
            r"[A-Z][a-z]+(?:\s+[A-Z]?[a-z]+)*\s+(?:provides|offers|delivers|enables)\s+",
            r"^(?:A|An|The)\s+\w+(?:\s+\w+){0,3}\s+(?:is|are)\s+(?:a|an|the)?\s*\w+",
        ]
        
        count = 0
        examples = []
        
        for p in paragraphs:
            sentences = re.split(r'(?<=[.!?])\s+', p)
            for s in sentences:
                for pattern in patterns:
                    if re.search(pattern, s) and len(s.split()) >= 6 and len(s.split()) <= 40:
                        count += 1
                        if len(examples) < 3:
                            examples.append(s[:150])
                        break
        
        return {"count": count, "examples": examples}
    
    def _detect_fluff(self, text):
        text_lower = text.lower()
        found = []
        for phrase in self.FLUFF_PHRASES:
            occurrences = text_lower.count(phrase.lower())
            if occurrences > 0:
                found.append(phrase)
        return {"count": len(found), "phrases": found}
    
    def _detect_vague_claims(self, text):
        found = []
        for pattern in self.VAGUE_CLAIMS:
            matches = re.findall(pattern, text, re.I)
            if matches:
                found.extend(matches if isinstance(matches[0], str) else [m[0] if isinstance(m, tuple) else m for m in matches])
        return {"count": len(found), "examples": [str(f)[:60] for f in found[:5]]}
    
    def _analyze_voice(self, text):
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if len(s.strip().split()) >= 3]
        
        if not sentences:
            return {"passive_pct": 0, "active_pct": 100}
        
        passive_pattern = r"\b(is|are|was|were|be|been|being|get|got|gets)\b\s+\w+(ed|en|t)\b"
        passive_count = sum(1 for s in sentences if re.search(passive_pattern, s, re.I))
        
        pct = round(passive_count / len(sentences) * 100, 1)
        return {"passive_pct": pct, "active_pct": round(100 - pct, 1)}
    
    def _marketing_info_ratio(self, paragraphs):
        """Classify paragraphs as marketing vs informational."""
        if not paragraphs:
            return {"marketing_pct": 0, "info_pct": 0}
        
        marketing_signals = re.compile(
            r"\b(get started|sign up|try|free trial|contact us|learn more|"
            r"request|demo|schedule|book a|start your|join|subscribe|"
            r"don.t miss|limited|exclusive|offer|discount)\b", re.I
        )
        
        info_signals = re.compile(
            r"\b(how|what|why|when|step|process|feature|works|includes|supports|"
            r"integrates|requires|provides|consists|contains|allows|enables|"
            r"according to|data shows|research|for example|specifically)\b", re.I
        )
        
        marketing = 0
        info = 0
        
        for p in paragraphs:
            m_count = len(marketing_signals.findall(p))
            i_count = len(info_signals.findall(p))
            
            if m_count > i_count:
                marketing += 1
            else:
                info += 1
        
        total = len(paragraphs)
        return {
            "marketing_pct": round(marketing / total * 100, 1) if total else 0,
            "info_pct": round(info / total * 100, 1) if total else 0,
        }
    
    def _calc_extractability(self, readability, fluff, direct_answer, definitions, sentences):
        score = 25  # Base
        
        # Readability (0-25)
        fre = readability.get("flesch_reading_ease", 50)
        if fre >= 60:
            score += 25
        elif fre >= 45:
            score += 15
        elif fre >= 30:
            score += 8
        
        # Low fluff (0-15)
        if fluff["count"] == 0:
            score += 15
        elif fluff["count"] <= 2:
            score += 10
        elif fluff["count"] <= 5:
            score += 5
        
        # Direct answers (0-20)
        score += min(20, direct_answer["pct"] * 0.2)
        
        # Definitions (0-15)
        score += min(15, definitions["count"] * 3)
        
        return min(100, max(0, round(score)))
    
    def _calc_score(self, readability, fluff, vague, direct_answer, extractability, voice, definitions, content_ratio):
        score = 0
        
        # Readability (0-25)
        fre = readability.get("flesch_reading_ease", 50)
        if fre >= 70:
            score += 25
        elif fre >= 55:
            score += 20
        elif fre >= 40:
            score += 14
        elif fre >= 25:
            score += 8
        else:
            score += 3
        
        # Low fluff (0-15)
        score += max(0, 15 - fluff["count"] * 2)
        
        # Low vague claims (0-10)
        score += max(0, 10 - vague["count"] * 2)
        
        # Direct answers (0-20)
        score += min(20, direct_answer["pct"] * 0.2)
        
        # Definitions (0-10)
        score += min(10, definitions["count"] * 2)
        
        # Active voice (0-10)
        if voice["passive_pct"] <= 15:
            score += 10
        elif voice["passive_pct"] <= 25:
            score += 7
        elif voice["passive_pct"] <= 40:
            score += 3
        
        # Content ratio (0-10)
        score += min(10, content_ratio["info_pct"] * 0.1)
        
        return min(100, max(0, round(score)))
