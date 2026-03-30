"""
FAQ Coverage Analyzer v2
Detects FAQs from JSON-LD, HTML structures, accordions, details/summary, dt/dd, and heading patterns.
"""
import re


class FAQAnalyzer:
    """Comprehensive FAQ detection across all page signals."""
    
    QUESTION_STARTERS = {
        "what": r"^what\b",
        "how": r"^how\b",
        "why": r"^why\b",
        "when": r"^when\b",
        "where": r"^where\b",
        "who": r"^who\b",
        "can/does/is": r"^(can|does|is|do|will|are|should|could|would)\b",
    }
    
    TOPIC_KEYWORDS = {
        "product": ["product", "platform", "software", "tool", "service", "solution", "app"],
        "features": ["feature", "capability", "function", "ability", "include", "offer"],
        "use_cases": ["use case", "example", "scenario", "workflow", "use for", "good for"],
        "pricing": ["price", "pricing", "cost", "plan", "subscription", "free", "tier", "pay"],
        "integration": ["integrat", "connect", "api", "plugin", "import", "export", "sync", "webhook"],
        "security": ["secure", "security", "privacy", "encrypt", "compliance", "gdpr", "soc", "hipaa"],
        "support": ["support", "help", "contact", "documentation", "docs", "guide", "tutorial"],
        "onboarding": ["getting started", "setup", "install", "onboard", "sign up", "register"],
        "comparison": ["vs", "versus", "compared", "alternative", "differ", "better than"],
    }
    
    def analyze(self, crawl_data: dict) -> dict:
        headings = crawl_data.get("headings", {})
        text = crawl_data.get("text_content", "")
        paragraphs = crawl_data.get("paragraphs", [])
        json_ld = crawl_data.get("json_ld", [])
        faq_html = crawl_data.get("faq_html_structures", [])
        details = crawl_data.get("details_elements", [])
        dl_items = crawl_data.get("definition_lists", [])
        accordions = crawl_data.get("accordions", [])
        
        # === 1. Collect all FAQ sources ===
        all_faqs = []
        
        # JSON-LD FAQPage
        schema_faqs = self._extract_schema_faqs(json_ld)
        all_faqs.extend(schema_faqs)
        has_faq_schema = len(schema_faqs) > 0
        
        # Question headings (h2/h3/h4 with ? or question pattern)
        question_headings = self._extract_question_headings(headings)
        all_faqs.extend(question_headings)
        
        # Heading + paragraph Q&A pairs from crawler
        qa_pairs = [f for f in faq_html if f.get("source") == "heading_qa"]
        all_faqs.extend([{"question": f["question"], "answer": f.get("answer", ""), "source": "heading_qa"} for f in qa_pairs])
        
        # Details/summary (accordion-like HTML)
        for d in details:
            if d.get("summary"):
                all_faqs.append({"question": d["summary"], "answer": d.get("content", ""), "source": "details_element"})
        
        # Definition lists
        for dl in dl_items:
            if dl.get("term"):
                all_faqs.append({"question": dl["term"], "answer": dl.get("definition", ""), "source": "definition_list"})
        
        # ARIA accordions
        for acc in accordions:
            if acc.get("text"):
                all_faqs.append({"question": acc["text"], "answer": "", "source": "accordion"})
        
        # CSS class/id based FAQ sections
        css_faqs = [f for f in faq_html if f.get("source") in ("css_class", "css_id")]
        
        # Inline text questions
        inline_qs = re.findall(r'([A-Z][^.!?]*\?)', text)
        inline_qs = [q.strip() for q in inline_qs if len(q.split()) >= 4 and len(q.split()) <= 30]
        
        # === 2. Deduplicate ===
        seen = set()
        unique_faqs = []
        for faq in all_faqs:
            q = faq.get("question", "").strip().lower()
            if q and q not in seen:
                seen.add(q)
                unique_faqs.append(faq)
        
        # === 3. Analyze question type coverage ===
        question_type_coverage = {}
        all_questions = [f.get("question", "") for f in unique_faqs]
        
        for qtype, pattern in self.QUESTION_STARTERS.items():
            matches = [q for q in all_questions if re.search(pattern, q.strip(), re.I)]
            question_type_coverage[qtype] = len(matches)
        
        missing_types = [qt for qt, count in question_type_coverage.items() if count == 0]
        
        # === 4. Answer quality ===
        answer_quality = self._assess_answer_quality(unique_faqs)
        
        # === 5. Topic coverage ===
        topic_coverage = self._assess_topic_coverage(text, all_questions)
        
        # === 6. FAQ depth ===
        faq_source_breakdown = {}
        for faq in unique_faqs:
            src = faq.get("source", "unknown")
            faq_source_breakdown[src] = faq_source_breakdown.get(src, 0) + 1
        
        total_faqs = len(unique_faqs)
        
        # === Score ===
        score = self._calc_score(total_faqs, question_type_coverage, answer_quality, has_faq_schema, topic_coverage, unique_faqs)
        
        findings = []
        recommendations = []
        
        findings.append(f"Total unique FAQ items detected: {total_faqs}")
        if faq_source_breakdown:
            sources_str = ", ".join(f"{k}: {v}" for k, v in faq_source_breakdown.items())
            findings.append(f"FAQ sources: {sources_str}")
        
        findings.append(f"Question types covered: {len(question_type_coverage) - len(missing_types)}/{len(question_type_coverage)}")
        findings.append(f"Has FAQPage schema: {'Yes' if has_faq_schema else 'No'}")
        findings.append(f"Topic coverage: {topic_coverage['coverage_pct']}% ({len(topic_coverage['covered_topics'])}/{len(self.TOPIC_KEYWORDS)} topics)")
        
        if total_faqs == 0:
            recommendations.append("Add at least 10-15 FAQs in a dedicated FAQ section — this is critical for LLM extraction")
        elif total_faqs < 5:
            recommendations.append(f"Only {total_faqs} FAQs found — expand to at least 10-15 covering core topics")
        elif total_faqs < 10:
            recommendations.append(f"{total_faqs} FAQs found — consider expanding to 15-20 for comprehensive coverage")
        
        if missing_types:
            type_examples = {
                "what": "What is [product]? What does [product] do?",
                "how": "How does [product] work? How do I get started?",
                "why": "Why should I use [product]? Why is [product] different?",
                "when": "When should I use [product]?",
                "who": "Who is [product] designed for?",
                "where": "Where can I find [feature]?",
                "can/does/is": "Can [product] integrate with X? Does [product] support Y? Is [product] free?",
            }
            for mt in missing_types:
                ex = type_examples.get(mt, "")
                recommendations.append(f"Add '{mt.upper()}' questions — e.g., {ex}")
        
        if not has_faq_schema:
            recommendations.append("Add FAQPage JSON-LD schema markup to your FAQ section for direct LLM extraction")
        
        if answer_quality["short_answers"] > 0:
            recommendations.append(f"{answer_quality['short_answers']} FAQ answers are too short — expand each to 2-5 clear sentences")
        
        if answer_quality["no_answer"] > 0:
            recommendations.append(f"{answer_quality['no_answer']} questions detected without visible answers — ensure each question has a direct answer")
        
        if answer_quality["indirect_pct"] > 40:
            recommendations.append("Many answers don't start with a direct statement — lead with the answer, then add context")
        
        gaps = topic_coverage.get("missing_topics", [])
        if gaps:
            recommendations.append(f"Add FAQs covering these topics: {', '.join(gaps)}")
        
        return {
            "name": "FAQ Coverage",
            "icon": "❓",
            "score": score,
            "weight": 20,
            "total_faqs": total_faqs,
            "faq_source_breakdown": faq_source_breakdown,
            "question_type_coverage": question_type_coverage,
            "missing_question_types": missing_types,
            "has_faq_schema": has_faq_schema,
            "answer_quality": answer_quality,
            "topic_coverage": topic_coverage,
            "sample_faqs": [{"q": f.get("question",""), "src": f.get("source","")} for f in unique_faqs[:10]],
            "findings": findings,
            "recommendations": recommendations
        }
    
    def _extract_schema_faqs(self, json_ld):
        """Extract FAQs from JSON-LD FAQPage schema."""
        faqs = []
        
        for item in json_ld:
            if not isinstance(item, dict):
                continue
            
            # Direct FAQPage
            if item.get("@type") == "FAQPage":
                for q in item.get("mainEntity", []):
                    if isinstance(q, dict):
                        question = q.get("name", "")
                        answer_obj = q.get("acceptedAnswer", {})
                        answer = answer_obj.get("text", "") if isinstance(answer_obj, dict) else ""
                        if question:
                            faqs.append({"question": question, "answer": answer, "source": "schema_faqpage"})
            
            # In @graph
            for g in item.get("@graph", []):
                if isinstance(g, dict) and g.get("@type") == "FAQPage":
                    for q in g.get("mainEntity", []):
                        if isinstance(q, dict):
                            question = q.get("name", "")
                            answer_obj = q.get("acceptedAnswer", {})
                            answer = answer_obj.get("text", "") if isinstance(answer_obj, dict) else ""
                            if question:
                                faqs.append({"question": question, "answer": answer, "source": "schema_faqpage"})
        
        return faqs
    
    def _extract_question_headings(self, headings):
        """Find headings that are questions."""
        questions = []
        for level in ["h2", "h3", "h4"]:
            for h in headings.get(level, []):
                if "?" in h:
                    questions.append({"question": h, "answer": "", "source": f"heading_{level}"})
                elif any(re.match(pat, h.strip(), re.I) for pat in self.QUESTION_STARTERS.values()):
                    questions.append({"question": h, "answer": "", "source": f"heading_{level}"})
        return questions
    
    def _assess_answer_quality(self, faqs):
        if not faqs:
            return {"avg_length": 0, "direct_pct": 0, "indirect_pct": 0, "short_answers": 0, "no_answer": 0}
        
        lengths = []
        direct = 0
        no_answer = 0
        short = 0
        
        direct_starters = re.compile(r"^(Yes|No|It is|This is|The |A |An |You can|We |Our |There |To )", re.I)
        
        for faq in faqs:
            answer = faq.get("answer", "").strip()
            if not answer:
                no_answer += 1
                continue
            
            word_count = len(answer.split())
            lengths.append(word_count)
            
            if word_count < 10:
                short += 1
            
            if direct_starters.match(answer):
                direct += 1
        
        answered = len(faqs) - no_answer
        avg_len = sum(lengths) / len(lengths) if lengths else 0
        direct_pct = round(direct / answered * 100, 1) if answered > 0 else 0
        
        return {
            "avg_length": round(avg_len, 1),
            "direct_pct": direct_pct,
            "indirect_pct": round(100 - direct_pct, 1),
            "short_answers": short,
            "no_answer": no_answer,
            "total_with_answers": answered
        }
    
    def _assess_topic_coverage(self, text, questions):
        text_lower = text.lower()
        q_text = " ".join(questions).lower()
        combined = text_lower + " " + q_text
        
        covered = []
        missing = []
        
        for topic, keywords in self.TOPIC_KEYWORDS.items():
            if any(kw in combined for kw in keywords):
                covered.append(topic)
            else:
                missing.append(topic)
        
        return {
            "covered_topics": covered,
            "missing_topics": missing,
            "coverage_pct": round(len(covered) / len(self.TOPIC_KEYWORDS) * 100, 1)
        }
    
    def _calc_score(self, total_faqs, type_coverage, answer_quality, has_schema, topic_coverage, faqs):
        score = 0
        
        # FAQ quantity (0-25)
        if total_faqs >= 20:
            score += 25
        elif total_faqs >= 15:
            score += 22
        elif total_faqs >= 10:
            score += 18
        elif total_faqs >= 5:
            score += 12
        elif total_faqs >= 1:
            score += 5
        
        # Question type diversity (0-20)
        types_covered = sum(1 for v in type_coverage.values() if v > 0)
        score += round((types_covered / len(type_coverage)) * 20)
        
        # Schema markup (0-10)
        if has_schema:
            score += 10
        
        # Answer quality (0-25)
        if answer_quality.get("total_with_answers", 0) > 0:
            score += answer_quality["direct_pct"] * 0.15
            # Penalize missing answers
            if total_faqs > 0:
                answered_ratio = answer_quality["total_with_answers"] / total_faqs
                score += answered_ratio * 10
        
        # Topic coverage (0-20)
        score += topic_coverage["coverage_pct"] * 0.2
        
        return min(100, max(0, round(score)))
