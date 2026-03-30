"""
Remaining analyzers v2 - hardened:
- Scenario & Context Detector
- Page Structure Validator  
- Technical Accessibility Checker
- Trust & Authority Signal Detector
- GEO/AI Answer Optimization Layer
"""
import re


class ScenarioAnalyzer:
    """Detects real-world usability content and contextual examples."""
    
    def analyze(self, crawl_data: dict) -> dict:
        text = crawl_data.get("text_content", "")
        paragraphs_raw = crawl_data.get("paragraphs", [])
        paragraphs = [p.get("text", "") for p in paragraphs_raw if not p.get("in_nav")]
        headings = crawl_data.get("headings", {})
        lists = crawl_data.get("lists", [])
        tables = crawl_data.get("tables", [])
        
        conditionals = self._detect_conditionals(text)
        workflows = self._detect_workflows(text, lists, headings)
        edge_cases = self._detect_edge_cases(text)
        examples = self._detect_examples(text, paragraphs)
        comparisons = self._detect_comparisons(text, tables, headings)
        
        scenario_score = self._calc_scenario_coverage(conditionals, workflows, edge_cases, examples, comparisons)
        practical_score = self._calc_practical_depth(workflows, examples, edge_cases, comparisons)
        
        score = round(scenario_score * 0.5 + practical_score * 0.5)
        
        findings = []
        recommendations = []
        
        findings.append(f"Conditional scenarios (if/when): {conditionals['count']}")
        findings.append(f"Step-by-step workflows: {workflows['count']}")
        findings.append(f"Contextual examples: {examples['count']}")
        findings.append(f"Edge case handling: {edge_cases['count']}")
        findings.append(f"Comparison content: {comparisons['count']}")
        
        if conditionals["count"] < 2:
            recommendations.append("Add conditional content: 'If you need X, use Y' / 'When Z happens, here\'s how to handle it'")
        if workflows["count"] < 1:
            recommendations.append("Add at least one step-by-step guide showing how to use your product")
        if examples["count"] < 3:
            recommendations.append("Add real-world examples with specific scenarios, numbers, and outcomes")
        if edge_cases["count"] < 1:
            recommendations.append("Document edge cases, limitations, and workarounds — LLMs cite this when answering nuanced queries")
        if comparisons["count"] == 0:
            recommendations.append("Add comparison content (vs. alternatives, before/after, different approaches)")
        
        return {
            "name": "Scenarios & Context",
            "icon": "🧪",
            "score": score,
            "weight": 0,
            "conditionals": conditionals,
            "workflows": workflows,
            "edge_cases": edge_cases,
            "examples": examples,
            "comparisons": comparisons,
            "findings": findings,
            "recommendations": recommendations
        }
    
    def _detect_conditionals(self, text):
        patterns = [
            r"\bif you\b", r"\bwhen you\b", r"\bin case\b",
            r"\bdepending on\b", r"\bassuming\b", r"\bwhether\b",
            r"\bif your (team|company|business|organization)\b",
        ]
        count = sum(len(re.findall(p, text, re.I)) for p in patterns)
        return {"count": min(count, 50)}
    
    def _detect_workflows(self, text, lists, headings):
        patterns = [
            r"\bstep \d+\b", r"\bfirst,?\b.*\bthen\b",
            r"\bhow to\b", r"\bgetting started\b",
            r"\bfollow these\b", r"\bcomplete the following\b",
        ]
        count = sum(len(re.findall(p, text, re.I)) for p in patterns)
        ordered = sum(1 for l in lists if l.get("type") == "ol")
        count += ordered
        all_h = [h for v in headings.values() for h in v]
        step_headings = sum(1 for h in all_h if re.search(r"(step|how to|guide|tutorial|workflow|getting started)", h, re.I))
        count += step_headings
        return {"count": min(count, 30)}
    
    def _detect_edge_cases(self, text):
        patterns = [
            r"\bhowever\b", r"\bnote that\b", r"\bkeep in mind\b",
            r"\blimitation\b", r"\bexception\b", r"\bunless\b",
            r"\bbe aware\b", r"\bcaveat\b", r"\bimportant(ly)?:\b",
            r"\bknown issue\b", r"\bdoes not (support|work|handle)\b",
            r"\bcurrently (not|doesn\'t|does not)\b",
        ]
        count = sum(len(re.findall(p, text, re.I)) for p in patterns)
        return {"count": min(count, 30)}
    
    def _detect_examples(self, text, paragraphs):
        patterns = [
            r"\bfor example\b", r"\bfor instance\b", r"\bsuch as\b",
            r"\be\.g\.\b", r"\buse case\b", r"\bscenario\b",
            r"\bin practice\b", r"\breal-world\b", r"\bhere\'s (how|an|a)\b",
            r"\blet\'s say\b", r"\bimagine\b", r"\bconsider\b",
        ]
        count = sum(len(re.findall(p, text, re.I)) for p in patterns)
        return {"count": min(count, 40)}
    
    def _detect_comparisons(self, text, tables, headings):
        patterns = [
            r"\bvs\.?\b", r"\bversus\b", r"\bcompared to\b",
            r"\bcomparison\b", r"\balternative\b", r"\bdifference between\b",
            r"\bbefore and after\b", r"\bwith and without\b",
            r"\bunlike\b", r"\bin contrast\b",
        ]
        count = sum(len(re.findall(p, text, re.I)) for p in patterns)
        count += len(tables)
        return {"count": min(count, 20)}
    
    def _calc_scenario_coverage(self, cond, work, edge, examples, comparisons):
        score = 0
        score += min(25, cond["count"] * 4)
        score += min(25, work["count"] * 8)
        score += min(20, edge["count"] * 4)
        score += min(20, examples["count"] * 4)
        score += min(10, comparisons["count"] * 3)
        return min(100, score)
    
    def _calc_practical_depth(self, workflows, examples, edge_cases, comparisons):
        total = workflows["count"] + examples["count"] + edge_cases["count"] + comparisons["count"]
        if total >= 15:
            return 95
        elif total >= 10:
            return 75
        elif total >= 5:
            return 55
        elif total >= 2:
            return 35
        elif total >= 1:
            return 15
        return 3


class StructureAnalyzer:
    """Validates page structure including semantic HTML."""
    
    def analyze(self, crawl_data: dict) -> dict:
        headings = crawl_data.get("headings", {})
        paragraphs_raw = crawl_data.get("paragraphs", [])
        paragraphs = [p for p in paragraphs_raw if not p.get("in_nav")]
        lists = crawl_data.get("lists", [])
        tables = crawl_data.get("tables", [])
        text = crawl_data.get("text_content", "")
        meta = crawl_data.get("meta_tags", {})
        semantic = crawl_data.get("semantic_elements", {})
        breadcrumbs = crawl_data.get("breadcrumbs", [])
        
        # H1 analysis
        h1s = headings.get("h1", [])
        has_h1 = len(h1s) > 0
        h1_clear = has_h1 and len(h1s[0].split()) <= 12
        multiple_h1 = len(h1s) > 1
        
        # Heading hierarchy
        hierarchy = self._check_hierarchy(headings)
        
        # Key sections
        sections = self._detect_key_sections(headings, text)
        
        # Semantic HTML
        semantic_score = self._score_semantic_html(semantic)
        
        # Formatting quality
        formatting = self._analyze_formatting(paragraphs, lists, tables)
        
        # Table of contents
        has_toc = self._detect_toc(crawl_data.get("html", ""))
        
        score = self._calc_score(has_h1, h1_clear, multiple_h1, hierarchy, sections, semantic_score, formatting, has_toc, breadcrumbs)
        
        findings = []
        recommendations = []
        
        if has_h1:
            findings.append(f"H1: \"{h1s[0][:60]}\"")
        else:
            findings.append("No H1 tag found")
            recommendations.append("Add a clear, descriptive H1 that states what the page is about")
        
        if multiple_h1:
            findings.append(f"Multiple H1 tags ({len(h1s)}) — should have exactly one")
            recommendations.append("Use exactly one H1 per page")
        
        h_counts = ", ".join(f"H{i}({len(headings.get(f'h{i}', []))})" for i in range(1, 5))
        findings.append(f"Heading structure: {h_counts}")
        
        if not hierarchy["proper"]:
            findings.append(f"Hierarchy issue: {hierarchy['issue']}")
            recommendations.append(f"Fix heading hierarchy: {hierarchy['issue']}")
        
        sections_present = sum(1 for v in sections.values() if v)
        sections_total = len(sections)
        findings.append(f"Key sections present: {sections_present}/{sections_total}")
        for name, present in sections.items():
            if not present:
                recommendations.append(f"Add a '{name}' section — LLMs look for standard page structures")
        
        findings.append(f"Semantic HTML elements: {len(semantic)} types used ({', '.join(semantic.keys()) if semantic else 'none'})")
        if not semantic.get("main"):
            recommendations.append("Wrap main content in a <main> tag for better semantic clarity")
        if not semantic.get("article") and not semantic.get("section"):
            recommendations.append("Use <article> or <section> tags to define content blocks")
        
        if formatting["avg_paragraph_length"] > 120:
            recommendations.append(f"Average paragraph is {formatting['avg_paragraph_length']} words — break into 40-80 word paragraphs")
        
        if not formatting["uses_lists"]:
            recommendations.append("Add bullet or numbered lists — LLMs extract list content very effectively")
        
        if not has_toc and len(headings.get("h2", [])) > 4:
            recommendations.append("Add a table of contents for this long page — helps LLMs navigate section structure")
        
        return {
            "name": "Page Structure",
            "icon": "🏗️",
            "score": score,
            "weight": 10,
            "has_h1": has_h1,
            "h1_text": h1s[0] if h1s else "",
            "multiple_h1": multiple_h1,
            "heading_hierarchy": hierarchy,
            "key_sections": sections,
            "semantic_elements": semantic,
            "semantic_score": semantic_score,
            "formatting": formatting,
            "has_toc": has_toc,
            "has_breadcrumbs": len(breadcrumbs) > 0,
            "findings": findings,
            "recommendations": recommendations
        }
    
    def _check_hierarchy(self, headings):
        levels_present = []
        for i in range(1, 7):
            if headings.get(f"h{i}"):
                levels_present.append(i)
        
        if not levels_present:
            return {"proper": False, "issue": "No headings found", "depth": 0}
        if levels_present[0] != 1:
            return {"proper": False, "issue": "Page should start with an H1", "depth": max(levels_present)}
        for i in range(1, len(levels_present)):
            if levels_present[i] - levels_present[i-1] > 1:
                return {"proper": False, "issue": f"Skipped from H{levels_present[i-1]} to H{levels_present[i]}", "depth": max(levels_present)}
        return {"proper": True, "issue": "None", "depth": max(levels_present)}
    
    def _detect_key_sections(self, headings, text):
        all_h = [h.lower() for v in headings.values() for h in v]
        text_lower = text.lower()[:5000]
        combined = " ".join(all_h) + " " + text_lower
        
        return {
            "What it is": any(kw in combined for kw in ["what is", "what we", "about us", "about ", "overview", "introduction"]),
            "How it works": any(kw in combined for kw in ["how it works", "how we", "how to", "process", "methodology", "approach"]),
            "Who it's for": any(kw in combined for kw in ["who it", "for whom", "ideal for", "built for", "designed for", "target", "industries"]),
            "Features": any(kw in combined for kw in ["features", "capabilities", "what you get", "benefits", "included"]),
            "FAQ": any(kw in combined for kw in ["faq", "frequently asked", "questions", "q&a"]),
            "Pricing": any(kw in combined for kw in ["pricing", "plans", "cost", "free", "trial"]),
        }
    
    def _score_semantic_html(self, semantic):
        score = 0
        if semantic.get("main"): score += 20
        if semantic.get("article"): score += 15
        if semantic.get("section"): score += 15
        if semantic.get("nav"): score += 10
        if semantic.get("header"): score += 10
        if semantic.get("footer"): score += 10
        if semantic.get("figure"): score += 10
        if semantic.get("time"): score += 10
        return min(100, score)
    
    def _analyze_formatting(self, paragraphs, lists, tables):
        para_lengths = [p.get("word_count", 0) for p in paragraphs]
        return {
            "total_paragraphs": len(paragraphs),
            "avg_paragraph_length": round(sum(para_lengths) / len(para_lengths), 1) if para_lengths else 0,
            "max_paragraph_length": max(para_lengths) if para_lengths else 0,
            "list_count": len(lists),
            "table_count": len(tables),
            "uses_lists": len(lists) > 0,
            "uses_tables": len(tables) > 0
        }
    
    def _detect_toc(self, html):
        return bool(re.search(r'(table.of.content|toc|jump.to|on.this.page|contents)', html, re.I))
    
    def _calc_score(self, has_h1, h1_clear, multiple_h1, hierarchy, sections, semantic_score, formatting, has_toc, breadcrumbs):
        score = 0
        
        # H1 (0-15)
        if has_h1:
            score += 10
            if h1_clear: score += 5
        if multiple_h1:
            score -= 5
        
        # Hierarchy (0-15)
        if hierarchy["proper"]: score += 15
        elif hierarchy["depth"] > 0: score += 5
        
        # Key sections (0-25)
        sections_present = sum(1 for v in sections.values() if v)
        score += sections_present * 4
        
        # Semantic HTML (0-15)
        score += semantic_score * 0.15
        
        # Formatting (0-15)
        if formatting["uses_lists"]: score += 7
        if formatting["uses_tables"]: score += 3
        if formatting["avg_paragraph_length"] <= 80: score += 5
        elif formatting["avg_paragraph_length"] <= 120: score += 2
        
        # Extras (0-10)
        if has_toc: score += 5
        if breadcrumbs: score += 5
        
        return min(100, max(0, round(score)))


class TechnicalAnalyzer:
    """Technical accessibility including AI crawler compatibility."""
    
    AI_BOTS = ["gptbot", "chatgpt-user", "claudebot", "anthropic-ai", "google-extended", 
                "googleother", "cohere-ai", "bytespider", "perplexitybot", "ccbot"]
    
    def analyze(self, crawl_data: dict) -> dict:
        headers = crawl_data.get("response_headers", {})
        html = crawl_data.get("html", "")
        load_time = crawl_data.get("load_time", 0)
        status_code = crawl_data.get("status_code", 0)
        robots_txt = crawl_data.get("robots_txt", "")
        sitemap = crawl_data.get("sitemap", "")
        meta = crawl_data.get("meta_tags", {})
        og = crawl_data.get("og_tags", {})
        twitter = crawl_data.get("twitter_tags", {})
        images = crawl_data.get("images", [])
        js_ratio = crawl_data.get("js_rendered_ratio", 0)
        canonical = crawl_data.get("canonical_url", "")
        hidden_content = crawl_data.get("hidden_content_count", 0)
        url = crawl_data.get("url", "")
        
        speed = self._score_speed(load_time)
        mobile = bool(meta.get("viewport"))
        has_robots = bool(robots_txt)
        has_sitemap = bool(sitemap)
        has_https = url.startswith("https")
        has_description = bool(meta.get("description"))
        has_canonical = bool(canonical)
        
        # AI bot access
        ai_access = self._check_ai_bot_access(robots_txt)
        
        # OG completeness
        og_complete = self._check_og_completeness(og)
        
        # Twitter card
        tw_complete = self._check_twitter_completeness(twitter)
        
        # Image alt text
        total_images = len(images)
        img_missing_alt = sum(1 for img in images if not img.get("has_alt"))
        
        # Content type header
        content_type = headers.get("Content-Type", headers.get("content-type", ""))
        has_charset = "charset" in content_type.lower()
        
        # Hreflang
        has_hreflang = bool(re.search(r'hreflang', html, re.I))
        
        crawlability = self._calc_crawlability(has_robots, ai_access, has_sitemap, js_ratio, hidden_content)
        
        score = self._calc_score(speed, mobile, crawlability, has_https, has_description, has_canonical,
                                 og_complete, img_missing_alt, total_images, ai_access)
        
        findings = []
        recommendations = []
        
        findings.append(f"Load time: {load_time}s ({'Good' if load_time < 2 else 'Slow' if load_time < 4 else 'Very slow'})")
        findings.append(f"HTTPS: {'Yes' if has_https else 'No'}")
        findings.append(f"Mobile viewport: {'Yes' if mobile else 'No'}")
        findings.append(f"HTML content ratio: {js_ratio}%")
        findings.append(f"Robots.txt: {'Found' if has_robots else 'Missing'} | Sitemap: {'Found' if has_sitemap else 'Missing'}")
        findings.append(f"AI bot access: {ai_access['status']}")
        findings.append(f"Open Graph: {og_complete['present']}/{og_complete['total']} tags | Twitter Card: {tw_complete['present']}/{tw_complete['total']} tags")
        
        if load_time > 3:
            recommendations.append(f"Page loads in {load_time}s — optimize for under 2s. LLM crawlers may time out on slow pages.")
        
        if not mobile:
            recommendations.append("Add viewport meta tag for mobile responsiveness")
        
        if not has_robots:
            recommendations.append("Add a robots.txt file to control crawler access")
        
        if not has_sitemap:
            recommendations.append("Add an XML sitemap to help crawlers discover your content")
        
        if ai_access["blocked_bots"]:
            recommendations.append(f"Your robots.txt blocks these AI crawlers: {', '.join(ai_access['blocked_bots'])}. Consider allowing them for LLM visibility.")
        
        if not has_canonical:
            recommendations.append("Add a canonical URL tag to prevent duplicate content issues")
        
        if not has_description:
            recommendations.append("Add a meta description — this is often what LLMs use as a summary of your page")
        
        if og_complete["missing"]:
            recommendations.append(f"Add missing Open Graph tags: {', '.join(og_complete['missing'][:3])}")
        
        if img_missing_alt > 0:
            recommendations.append(f"Add alt text to {img_missing_alt} images — helps LLMs understand visual content")
        
        if js_ratio < 50:
            recommendations.append("Critical content may be JS-rendered. Ensure key text is in the HTML source, not dynamically loaded.")
        
        if hidden_content > 3:
            recommendations.append(f"Found {hidden_content} hidden content blocks (display:none). Ensure important content isn't hidden from crawlers.")
        
        return {
            "name": "Technical",
            "icon": "⚡",
            "score": score,
            "weight": 10,
            "load_time": load_time,
            "speed_score": speed,
            "has_https": has_https,
            "has_mobile_viewport": mobile,
            "has_robots": has_robots,
            "has_sitemap": has_sitemap,
            "has_canonical": has_canonical,
            "has_meta_description": has_description,
            "ai_bot_access": ai_access,
            "og_completeness": og_complete,
            "twitter_completeness": tw_complete,
            "image_alt_missing": img_missing_alt,
            "total_images": total_images,
            "html_content_ratio": js_ratio,
            "hidden_content_blocks": hidden_content,
            "crawlability_score": crawlability,
            "findings": findings,
            "recommendations": recommendations
        }
    
    def _score_speed(self, load_time):
        if load_time <= 1: return 100
        elif load_time <= 2: return 85
        elif load_time <= 3: return 65
        elif load_time <= 5: return 40
        else: return 15
    
    def _check_ai_bot_access(self, robots_txt):
        if not robots_txt:
            return {"status": "No robots.txt (all bots allowed)", "blocked_bots": [], "allowed": True}
        
        robots_lower = robots_txt.lower()
        blocked = []
        
        for bot in self.AI_BOTS:
            # Check if there's a specific user-agent section blocking this bot
            pattern = rf"user-agent:\s*{re.escape(bot)}[\s\S]*?disallow:\s*/\s*$"
            if re.search(pattern, robots_lower, re.MULTILINE):
                blocked.append(bot)
        
        # Check wildcard blocks
        wildcard_block = re.search(r"user-agent:\s*\*[\s\S]*?disallow:\s*/\s*$", robots_lower, re.MULTILINE)
        if wildcard_block and not blocked:
            blocked = ["* (all bots)"]
        
        status = f"{len(blocked)} AI bots blocked" if blocked else "All AI bots allowed"
        return {"status": status, "blocked_bots": blocked, "allowed": len(blocked) == 0}
    
    def _check_og_completeness(self, og):
        required = ["title", "description", "type", "image", "url"]
        present = [k for k in required if k in og]
        missing = [k for k in required if k not in og]
        return {"present": len(present), "total": len(required), "missing": missing}
    
    def _check_twitter_completeness(self, twitter):
        required = ["card", "title", "description"]
        present = [k for k in required if k in twitter]
        missing = [k for k in required if k not in twitter]
        return {"present": len(present), "total": len(required), "missing": missing}
    
    def _calc_crawlability(self, has_robots, ai_access, has_sitemap, js_ratio, hidden):
        score = 0
        if has_robots: score += 15
        if ai_access.get("allowed"): score += 30
        if has_sitemap: score += 15
        if js_ratio >= 70: score += 25
        elif js_ratio >= 50: score += 12
        if hidden <= 2: score += 15
        elif hidden <= 5: score += 8
        return min(100, score)
    
    def _calc_score(self, speed, mobile, crawlability, https, desc, canonical, og, img_issues, total_img, ai_access):
        score = 0
        score += speed * 0.15
        score += 10 if mobile else 0
        score += crawlability * 0.25
        score += 10 if https else 0
        score += 8 if desc else 0
        score += 7 if canonical else 0
        score += (og["present"] / og["total"]) * 10 if og["total"] else 0
        score += 5 if ai_access.get("allowed") else 0
        
        if total_img > 0:
            alt_pct = (total_img - img_issues) / total_img
            score += alt_pct * 10
        else:
            score += 5
        
        return min(100, max(0, round(score)))


class TrustAnalyzer:
    """Detects trust and authority signals."""
    
    def analyze(self, crawl_data: dict) -> dict:
        text = crawl_data.get("text_content", "")
        paragraphs_raw = crawl_data.get("paragraphs", [])
        headings = crawl_data.get("headings", {})
        images = crawl_data.get("images", [])
        external_links = crawl_data.get("external_links", [])
        
        case_studies = self._detect_case_studies(text, headings)
        testimonials = self._detect_testimonials(text, headings)
        metrics = self._detect_metrics(text)
        named_refs = self._detect_named_references(text)
        logos = self._detect_logos(images)
        certifications = self._detect_certifications(text, images)
        specificity = self._assess_specificity(text)
        
        trust_score = self._calc_trust_score(case_studies, testimonials, metrics, named_refs, logos, certifications)
        evidence_score = self._calc_evidence_score(metrics, named_refs, specificity, certifications)
        
        score = round(trust_score * 0.5 + evidence_score * 0.5)
        
        findings = []
        recommendations = []
        
        findings.append(f"Case studies/success stories: {case_studies['count']}")
        findings.append(f"Testimonials: {testimonials['count']}")
        findings.append(f"Data points/metrics: {metrics['count']}")
        findings.append(f"Named references (people/companies): {named_refs['count']}")
        findings.append(f"Logo images detected: {logos['count']}")
        findings.append(f"Certification/compliance mentions: {certifications['count']}")
        findings.append(f"Specificity: {round((1-specificity['generic_ratio'])*100)}% specific vs {round(specificity['generic_ratio']*100)}% generic")
        
        if case_studies["count"] == 0:
            recommendations.append("Add case studies with specific results — 'Company X increased Y by Z%' is what LLMs cite")
        if testimonials["count"] == 0:
            recommendations.append("Add named customer testimonials with job title and company")
        if metrics["count"] < 3:
            recommendations.append("Add at least 5 specific metrics (e.g., '47% faster', '10,000+ users', '$2M ARR saved')")
        if named_refs["count"] < 2:
            recommendations.append("Name specific customers, partners, or industry experts — unnamed claims get less LLM weight")
        if certifications["count"] == 0:
            recommendations.append("Mention relevant certifications, compliance standards (SOC 2, GDPR, ISO) or industry awards")
        if specificity["generic_ratio"] > 0.3:
            recommendations.append("Replace generic claims with data: 'fast' → '47ms response time', 'many customers' → '2,400+ companies'")
        
        return {
            "name": "Trust & Authority",
            "icon": "🧠",
            "score": score,
            "weight": 10,
            "case_studies": case_studies,
            "testimonials": testimonials,
            "metrics": metrics,
            "named_references": named_refs,
            "logos": logos,
            "certifications": certifications,
            "specificity": specificity,
            "findings": findings,
            "recommendations": recommendations
        }
    
    def _detect_case_studies(self, text, headings):
        all_h = [h.lower() for v in headings.values() for h in v]
        combined = text.lower() + " " + " ".join(all_h)
        patterns = [r"case study", r"success story", r"customer story", r"how .+ uses?", r"results for", r"customer spotlight"]
        count = sum(len(re.findall(p, combined, re.I)) for p in patterns)
        return {"count": min(count, 10)}
    
    def _detect_testimonials(self, text, headings):
        patterns = [
            r'"[^"]{30,200}"',
            r"\u201c[^\u201d]{30,200}\u201d",
            r"testimonial", r"what (our )?customers? say",
            r"customer review", r"rated \d",
        ]
        count = sum(len(re.findall(p, text, re.I)) for p in patterns)
        # Detect attribution patterns (Name, Title at Company)
        attributions = len(re.findall(r'[A-Z][a-z]+ [A-Z][a-z]+,?\s+(CEO|CTO|VP|Director|Manager|Head|Lead|Founder|Co-founder)', text))
        return {"count": min(count + attributions, 20)}
    
    def _detect_metrics(self, text):
        patterns = [
            r"\d+%", r"\$[\d,.]+[KMBkmb]?", r"\d+x\b",
            r"\d{1,3}(,\d{3})+\+?",
            r"\d+\+ (customers|users|companies|clients|teams|organizations)",
            r"\d+ (hours|minutes|seconds|days|weeks|months)",
            r"\d+(\.\d+)?\s*(million|billion|thousand|M|B|K)",
        ]
        count = sum(len(re.findall(p, text)) for p in patterns)
        return {"count": min(count, 30)}
    
    def _detect_named_references(self, text):
        patterns = [
            r"(?:CEO|CTO|VP|Director|Manager|Founder|Head of|Lead) (?:of|at) [A-Z][a-z]+",
            r"[A-Z][a-z]+ [A-Z][a-z]+,? (?:CEO|CTO|VP|Director|Founder)",
            r"(?:trusted by|used by|chosen by|partnered with) [A-Z][a-z]+(?: [A-Z][a-z]+)*",
            r"(?:featured in|as seen in|mentioned by) [A-Z][a-z]+",
        ]
        count = sum(len(re.findall(p, text)) for p in patterns)
        return {"count": min(count, 15)}
    
    def _detect_logos(self, images):
        count = sum(1 for img in images if re.search(r"logo|brand|partner|client|trust|customer", 
                    (img.get("alt", "") + " " + img.get("src", "")).lower()))
        return {"count": count}
    
    def _detect_certifications(self, text, images):
        patterns = [
            r"\b(SOC 2|SOC2|GDPR|HIPAA|ISO \d+|PCI|CCPA|FedRAMP)\b",
            r"\b(certified|certification|compliant|compliance|accredited|audited)\b",
            r"\b(award|winner|recognized|rated|ranked)\b",
        ]
        count = sum(len(re.findall(p, text, re.I)) for p in patterns)
        return {"count": min(count, 10)}
    
    def _assess_specificity(self, text):
        generic_phrases = [
            "industry-leading", "best-in-class", "world-class",
            "trusted by thousands", "many companies", "various industries",
            "top-notch", "unparalleled", "unmatched", "premier",
        ]
        specific_patterns = [r"\d+%", r"\d+ companies", r"\d+ users", r"specifically", r"exactly", r"for example"]
        
        generic_count = sum(1 for p in generic_phrases if p.lower() in text.lower())
        specific_count = sum(len(re.findall(p, text, re.I)) for p in specific_patterns)
        total = generic_count + specific_count
        ratio = generic_count / total if total > 0 else 0.5
        
        return {"generic_ratio": round(ratio, 2), "specific_count": specific_count, "generic_count": generic_count}
    
    def _calc_trust_score(self, case_studies, testimonials, metrics, named_refs, logos, certs):
        score = 0
        score += min(20, case_studies["count"] * 12)
        score += min(20, testimonials["count"] * 8)
        score += min(20, metrics["count"] * 3)
        score += min(15, named_refs["count"] * 7)
        score += min(10, logos["count"] * 3)
        score += min(15, certs["count"] * 5)
        return min(100, score)
    
    def _calc_evidence_score(self, metrics, named_refs, specificity, certs):
        score = 0
        score += min(35, metrics["count"] * 5)
        score += min(25, named_refs["count"] * 10)
        score += (1 - specificity["generic_ratio"]) * 25
        score += min(15, certs["count"] * 5)
        return min(100, max(0, round(score)))


class GEOAnalyzer:
    """Optimizes for direct AI extraction and answer generation."""
    
    def analyze(self, crawl_data: dict) -> dict:
        text = crawl_data.get("text_content", "")
        paragraphs_raw = crawl_data.get("paragraphs", [])
        paragraphs = [p.get("text", "") for p in paragraphs_raw if not p.get("in_nav")]
        headings = crawl_data.get("headings", {})
        lists = crawl_data.get("lists", [])
        tables = crawl_data.get("tables", [])
        
        answer_blocks = self._detect_answer_blocks(paragraphs)
        definitions = self._detect_definitions(paragraphs)
        summaries = self._detect_summaries(text, headings)
        comparisons = self._detect_comparisons(text, tables, headings)
        pros_cons = self._detect_pros_cons(text, headings, lists)
        limitations = self._detect_limitations(text, headings)
        best_for = self._detect_best_for(text)
        
        completeness = self._calc_completeness(answer_blocks, definitions, summaries, comparisons, pros_cons, limitations, best_for)
        extractability = self._calc_extractability(paragraphs, lists, answer_blocks, definitions)
        
        score = round(completeness * 0.6 + extractability * 0.4)
        
        findings = []
        recommendations = []
        
        findings.append(f"Direct answer blocks: {answer_blocks['count']}")
        findings.append(f"Definition sentences: {definitions['count']}")
        findings.append(f"Summary/TL;DR sections: {summaries['count']}")
        findings.append(f"Comparison content: {comparisons['count']}")
        findings.append(f"Pros/cons present: {'Yes' if pros_cons['found'] else 'No'}")
        findings.append(f"Limitations documented: {'Yes' if limitations['found'] else 'No'}")
        
        if answer_blocks["count"] < 3:
            recommendations.append("Add more direct-answer paragraphs. Start with the key fact, then elaborate. LLMs extract the first sentence first.")
        if definitions["count"] < 2:
            recommendations.append("Add definition sentences: '[Product] is a [type] that [does X] for [audience]' — this is what LLMs quote most")
        if summaries["count"] == 0:
            recommendations.append("Add a TL;DR or 'Key Takeaways' section at the top of long content")
        if comparisons["count"] == 0:
            recommendations.append("Add comparison content: '[Product] vs [Alternative]' tables or sections — LLMs are asked comparison questions constantly")
        if not pros_cons["found"]:
            recommendations.append("Add a pros/cons or advantages/limitations section — LLMs prefer balanced content")
        if not limitations["found"]:
            recommendations.append("Document your limitations honestly — paradoxically, this makes LLMs trust and cite your content more")
        if not best_for["found"]:
            recommendations.append("Add 'Best for...' content: 'Best for teams that need X' / 'Ideal for companies with Y'")
        
        return {
            "name": "GEO / AI Optimization",
            "icon": "🔍",
            "score": score,
            "weight": 0,
            "answer_blocks": answer_blocks,
            "definitions": definitions,
            "summaries": summaries,
            "comparisons": comparisons,
            "pros_cons": pros_cons,
            "limitations": limitations,
            "best_for": best_for,
            "answer_completeness": completeness,
            "extractability_score": extractability,
            "findings": findings,
            "recommendations": recommendations
        }
    
    def _detect_answer_blocks(self, paragraphs):
        patterns = [
            r"^(Yes|No|It is|This is|That is|There are|There is)",
            r"^[A-Z][a-z]+\s+(is|are|provides|offers|helps|enables|allows|means)\s",
            r"^To [a-z]+,? you (can|should|need|must)",
            r"^The (main|primary|key|best|most|biggest|simplest)\b",
            r"^\d+",
        ]
        count = 0
        for p in paragraphs:
            for pattern in patterns:
                if re.match(pattern, p.strip(), re.I):
                    count += 1
                    break
        return {"count": count}
    
    def _detect_definitions(self, paragraphs):
        patterns = [
            r"[A-Z][a-z]+(?:\s+[A-Z]?[a-z]+)*\s+is\s+(?:a|an|the)\s+",
            r"[A-Z][a-z]+(?:\s+[A-Z]?[a-z]+)*\s+(?:refers to|means|describes)\s+",
        ]
        count = 0
        for p in paragraphs:
            for pattern in patterns:
                if re.search(pattern, p) and 10 <= len(p.split()) <= 50:
                    count += 1
                    break
        return {"count": count}
    
    def _detect_summaries(self, text, headings):
        patterns = [r"\b(tl;dr|tldr|summary|overview|in short|in brief|key takeaway|at a glance|bottom line)\b"]
        count = sum(len(re.findall(p, text, re.I)) for p in patterns)
        all_h = [h for v in headings.values() for h in v]
        count += sum(1 for h in all_h if re.search(r"(summary|overview|tl;dr|key (points|takeaway))", h, re.I))
        return {"count": count}
    
    def _detect_comparisons(self, text, tables, headings):
        patterns = [r"\bvs\.?\b", r"\bversus\b", r"\bcompared to\b", r"\bcomparison\b", r"\balternative\b", r"\bdifference between\b"]
        count = sum(len(re.findall(p, text, re.I)) for p in patterns)
        count += len(tables)
        return {"count": count}
    
    def _detect_pros_cons(self, text, headings, lists):
        patterns = [r"\b(pros?\s+and\s+cons?)\b", r"\b(advantages?\s+and\s+disadvantages?)\b", r"\b(benefits?\s+and\s+drawbacks?)\b", r"\b(strengths?\s+and\s+weaknesses?)\b"]
        return {"found": any(re.search(p, text, re.I) for p in patterns)}
    
    def _detect_limitations(self, text, headings):
        patterns = [r"\b(limitation|known issue|trade-?off|downside|caveat)\b", r"\b(does not|doesn.t|cannot|can.t)\b.*\b(support|work|handle|process)\b"]
        return {"found": any(re.search(p, text, re.I) for p in patterns)}
    
    def _detect_best_for(self, text):
        patterns = [r"\b(best for|ideal for|perfect for|great for|designed for|built for)\b"]
        return {"found": any(re.search(p, text, re.I) for p in patterns)}
    
    def _calc_completeness(self, answers, defs, summaries, comparisons, pros, limits, best):
        score = 0
        score += min(25, answers["count"] * 4)
        score += min(15, defs["count"] * 5)
        score += min(15, summaries["count"] * 8)
        score += min(15, comparisons["count"] * 4)
        score += 10 if pros["found"] else 0
        score += 10 if limits["found"] else 0
        score += 10 if best["found"] else 0
        return min(100, score)
    
    def _calc_extractability(self, paragraphs, lists, answers, defs):
        score = 20
        if paragraphs:
            avg = sum(len(p.split()) for p in paragraphs) / len(paragraphs)
            if avg <= 50: score += 25
            elif avg <= 80: score += 15
            elif avg <= 120: score += 5
        score += min(20, len(lists) * 4)
        score += min(20, answers["count"] * 4)
        score += min(15, defs["count"] * 5)
        return min(100, score)
