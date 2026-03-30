"""
Entity Extraction & Clarity Engine v2
Cross-references title, H1, meta, OG, Twitter, JSON-LD to build entity profile.
"""
import re
from collections import Counter
from difflib import SequenceMatcher


class EntityAnalyzer:
    """Analyzes entity clarity and consistency using all available signals."""
    
    def analyze(self, crawl_data: dict) -> dict:
        text = crawl_data.get("text_content", "")
        headings = crawl_data.get("headings", {})
        meta = crawl_data.get("meta_tags", {})
        og = crawl_data.get("og_tags", {})
        twitter = crawl_data.get("twitter_tags", {})
        json_ld = crawl_data.get("json_ld", [])
        paragraphs = crawl_data.get("paragraphs", [])
        
        # === 1. Build entity profile from all sources ===
        entity_sources = self._build_entity_sources(meta, og, twitter, json_ld, headings, paragraphs)
        
        # === 2. Identify primary entity ===
        primary = self._identify_primary_entity(entity_sources)
        
        # === 3. Cross-reference consistency ===
        consistency = self._cross_reference_consistency(entity_sources)
        
        # === 4. Detect "what this is" statement ===
        what_statement = self._find_what_statement(paragraphs, headings, primary, meta)
        
        # === 5. Entity ambiguity ===
        ambiguity = self._detect_ambiguity(text, what_statement, entity_sources)
        
        # === 6. Schema entity alignment ===
        schema_alignment = self._check_schema_entity_alignment(json_ld, primary)
        
        # === 7. Secondary entities ===
        secondary = self._extract_secondary_entities(text, headings)
        
        # === Score ===
        score = self._calc_score(what_statement, consistency, ambiguity, schema_alignment, entity_sources)
        
        findings = []
        recommendations = []
        
        # Entity profile findings
        if primary["name"]:
            findings.append(f"Primary entity identified: \"{primary['name']}\"")
        else:
            findings.append("Could not clearly identify the primary entity (product/company name)")
            recommendations.append("Make sure your H1, title tag, and meta description all reference your product/company by name")
        
        if what_statement["found"]:
            findings.append(f"Clear definition found: \"{what_statement['statement'][:120]}...\"")
        else:
            findings.append("No clear 'what this is' definition found in the first content paragraphs")
            recommendations.append("Add a clear, one-sentence definition in the first paragraph: '[Name] is a [type] that [what it does] for [who]'")
        
        # Consistency findings
        findings.append(f"Naming consistency across sources: {consistency['score']}/100")
        if consistency["mismatches"]:
            for m in consistency["mismatches"][:3]:
                findings.append(f"  Name mismatch: {m['source_a']} (\"{m['name_a']}\") vs {m['source_b']} (\"{m['name_b']}\")")
            recommendations.append("Standardize your product/company name across title tag, H1, meta description, OG tags, and schema markup")
        
        # Ambiguity
        if ambiguity["level"] == "high":
            findings.append(f"High entity ambiguity — {ambiguity['reason']}")
            recommendations.append("Replace vague language with specific descriptions of what your product does and the problem it solves")
        elif ambiguity["level"] == "medium":
            findings.append(f"Moderate entity ambiguity detected")
            recommendations.append("Add more concrete explanations of your specific capabilities and use cases")
        
        # Schema alignment
        if not schema_alignment["has_org_schema"]:
            recommendations.append("Add Organization or Product schema with a 'name' that matches your H1/title")
        elif not schema_alignment["name_matches"]:
            recommendations.append(f"Schema name (\"{schema_alignment['schema_name']}\") doesn't match your page title — align them")
        
        # Source coverage
        missing_sources = entity_sources.get("missing", [])
        if missing_sources:
            recommendations.append(f"Add entity name to missing tags: {', '.join(missing_sources)}")
        
        return {
            "name": "Entity Clarity",
            "icon": "🧩",
            "score": score,
            "weight": 15,
            "primary_entity": primary,
            "entity_sources": {k: v for k, v in entity_sources.items() if k != "missing"},
            "what_statement": what_statement,
            "consistency": consistency,
            "ambiguity_level": ambiguity["level"],
            "schema_alignment": schema_alignment,
            "secondary_entities": secondary,
            "findings": findings,
            "recommendations": recommendations
        }
    
    def _build_entity_sources(self, meta, og, twitter, json_ld, headings, paragraphs):
        """Pull entity name from every available source."""
        sources = {}
        missing = []
        
        # Title tag
        title = meta.get("title", "")
        if title:
            # Extract likely entity name from title (usually before | or - or :)
            name = re.split(r'[|\-–—:]', title)[0].strip()
            sources["title"] = name
        else:
            missing.append("title tag")
        
        # H1
        h1s = headings.get("h1", [])
        if h1s:
            sources["h1"] = h1s[0]
        else:
            missing.append("H1 tag")
        
        # Meta description
        desc = meta.get("description", "")
        if desc:
            # Try to extract entity name from description
            name_match = re.match(r'^([A-Z][\w\s]+?)\s+(is|helps|provides|offers|enables|—|–|-)', desc)
            if name_match:
                sources["meta_description"] = name_match.group(1).strip()
        else:
            missing.append("meta description")
        
        # OG title
        og_title = og.get("title", "")
        if og_title:
            name = re.split(r'[|\-–—:]', og_title)[0].strip()
            sources["og:title"] = name
        else:
            missing.append("og:title")
        
        # OG site_name
        og_site = og.get("site_name", "")
        if og_site:
            sources["og:site_name"] = og_site
        
        # Twitter title
        tw_title = twitter.get("title", "")
        if tw_title:
            name = re.split(r'[|\-–—:]', tw_title)[0].strip()
            sources["twitter:title"] = name
        
        # JSON-LD Organization/Product name
        for item in json_ld:
            if not isinstance(item, dict):
                continue
            schema_name = item.get("name", "")
            schema_type = item.get("@type", "")
            if schema_name and schema_type in ["Organization", "Corporation", "LocalBusiness", "Product", "SoftwareApplication", "WebSite", "Service"]:
                sources[f"schema:{schema_type}"] = schema_name
                break
            # Check @graph
            for g in item.get("@graph", []):
                if isinstance(g, dict):
                    gname = g.get("name", "")
                    gtype = g.get("@type", "")
                    if gname and gtype in ["Organization", "Corporation", "LocalBusiness", "Product", "SoftwareApplication", "WebSite", "Service"]:
                        sources[f"schema:{gtype}"] = gname
                        break
        
        sources["missing"] = missing
        return sources
    
    def _identify_primary_entity(self, sources):
        """Determine the primary entity name from all sources."""
        candidates = []
        # Priority order: schema > og:site_name > title > h1
        priority = ["og:site_name", "schema:Organization", "schema:Corporation", "schema:Product",
                     "schema:SoftwareApplication", "schema:Service", "schema:WebSite",
                     "title", "h1", "og:title", "twitter:title", "meta_description"]
        
        for key in priority:
            if key in sources and sources[key]:
                candidates.append({"source": key, "name": sources[key]})
        
        if not candidates:
            return {"name": "", "source": "", "confidence": "low"}
        
        # Use the highest-priority name
        best = candidates[0]
        
        # If multiple candidates agree, confidence is higher
        names_lower = [c["name"].lower().strip() for c in candidates]
        agreement = sum(1 for n in names_lower if SequenceMatcher(None, n, best["name"].lower()).ratio() > 0.7)
        confidence = "high" if agreement >= 3 else "medium" if agreement >= 2 else "low"
        
        return {"name": best["name"], "source": best["source"], "confidence": confidence}
    
    def _cross_reference_consistency(self, sources):
        """Check if the entity name is consistent across all sources."""
        names = {k: v for k, v in sources.items() if k != "missing" and v}
        
        if len(names) <= 1:
            return {"score": 50, "mismatches": [], "sources_checked": len(names)}
        
        # Compare each pair
        items = list(names.items())
        mismatches = []
        total_comparisons = 0
        matches = 0
        
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                src_a, name_a = items[i]
                src_b, name_b = items[j]
                total_comparisons += 1
                
                similarity = SequenceMatcher(None, name_a.lower().strip(), name_b.lower().strip()).ratio()
                
                if similarity > 0.65:
                    matches += 1
                else:
                    # Check if one contains the other
                    if name_a.lower() in name_b.lower() or name_b.lower() in name_a.lower():
                        matches += 0.7
                    else:
                        mismatches.append({
                            "source_a": src_a, "name_a": name_a,
                            "source_b": src_b, "name_b": name_b,
                            "similarity": round(similarity, 2)
                        })
        
        score = round(matches / total_comparisons * 100) if total_comparisons > 0 else 50
        return {"score": score, "mismatches": mismatches, "sources_checked": len(names)}
    
    def _find_what_statement(self, paragraphs, headings, primary, meta):
        """Find a clear 'what this is' definition statement."""
        entity_name = primary.get("name", "").lower()
        
        # Check meta description first
        desc = meta.get("description", "")
        if desc and self._is_definition(desc, entity_name):
            return {"found": True, "statement": desc, "source": "meta_description"}
        
        # Check first 5 content paragraphs (not in nav)
        content_paras = [p for p in paragraphs if not p.get("in_nav")][:7]
        
        for p in content_paras:
            text = p.get("text", "")
            if self._is_definition(text, entity_name):
                return {"found": True, "statement": text, "source": f"paragraph_{p.get('index', 0)}"}
        
        # Check H1 + first paragraph combo
        h1s = headings.get("h1", [])
        if h1s and content_paras:
            combined = h1s[0] + " " + content_paras[0].get("text", "")
            if self._is_definition(combined, entity_name):
                return {"found": True, "statement": content_paras[0]["text"], "source": "h1_context"}
        
        return {"found": False, "statement": "", "source": ""}
    
    def _is_definition(self, text, entity_name=""):
        """Check if text contains a definition-style statement."""
        patterns = [
            # "[Name] is a ..."
            r"\b(is a|is an|is the)\b.{5,}\b(that|which|for|platform|tool|service|software|solution|app)\b",
            # "We are / We help / We provide"
            r"\b(we are|we help|we provide|we offer|we build|we make|we enable)\b",
            # "[Name] helps / enables / provides
            r"\b(helps|enables|provides|offers|delivers|empowers|allows)\b.{5,}\b(to|by|with|for)\b",
            # Platform/tool/service that...
            r"\b(platform|tool|service|solution|software|app|application|product)\b.{0,30}\b(that|which|for|designed|built)\b",
        ]
        
        for pattern in patterns:
            if re.search(pattern, text, re.I):
                return True
        
        # Check if entity name is at the start followed by a verb
        if entity_name and len(entity_name) > 2:
            name_pattern = re.escape(entity_name)
            if re.search(rf"\b{name_pattern}\b.{{0,20}}\b(is|helps|provides|offers|enables)\b", text, re.I):
                return True
        
        return False
    
    def _detect_ambiguity(self, text, what_statement, sources):
        """Assess how ambiguous the entity definition is."""
        vague_indicators = [
            r"\b(innovative|cutting-edge|revolutionary|best-in-class|world-class|next-gen)\b",
            r"\b(solutions|synergies|leverage|paradigm|ecosystem|holistic)\b",
            r"\b(empower|supercharge|unlock|unleash|elevate|transform)\b",
        ]
        
        specific_indicators = [
            r"\b(reduces|increases|saves|automates|connects|tracks|measures|analyzes|monitors|reports)\b",
            r"\b(\d+%|\$[\d,.]+|\d+ (hours|minutes|seconds|days))\b",
            r"\b(API|dashboard|database|integration|workflow|pipeline|report|analytics)\b",
            r"\b(for|designed for|built for|helps)\b.{5,}\b(teams|companies|developers|marketers|sales)\b",
        ]
        
        vague_count = sum(len(re.findall(p, text[:3000], re.I)) for p in vague_indicators)
        specific_count = sum(len(re.findall(p, text[:3000], re.I)) for p in specific_indicators)
        
        has_definition = what_statement.get("found", False)
        source_count = len([v for k, v in sources.items() if k != "missing" and v])
        
        if not has_definition and vague_count > specific_count:
            return {"level": "high", "reason": "No clear definition and content uses vague marketing language over specifics"}
        elif not has_definition and source_count < 3:
            return {"level": "high", "reason": "No definition found and entity name appears in fewer than 3 meta sources"}
        elif vague_count > specific_count * 2:
            return {"level": "medium", "reason": "Marketing language outweighs specific product descriptions"}
        elif not has_definition:
            return {"level": "medium", "reason": "No explicit 'what this is' definition in first few paragraphs"}
        else:
            return {"level": "low", "reason": ""}
    
    def _check_schema_entity_alignment(self, json_ld, primary):
        """Check if schema.org entity name matches page content."""
        has_org = False
        schema_name = ""
        
        for item in json_ld:
            if not isinstance(item, dict):
                continue
            
            t = item.get("@type", "")
            types_to_check = ["Organization", "Corporation", "LocalBusiness", "Product", "SoftwareApplication", "Service"]
            
            if t in types_to_check:
                has_org = True
                schema_name = item.get("name", "")
                break
            
            for g in item.get("@graph", []):
                if isinstance(g, dict) and g.get("@type") in types_to_check:
                    has_org = True
                    schema_name = g.get("name", "")
                    break
            if has_org:
                break
        
        name_matches = False
        if schema_name and primary.get("name"):
            sim = SequenceMatcher(None, schema_name.lower(), primary["name"].lower()).ratio()
            name_matches = sim > 0.5 or schema_name.lower() in primary["name"].lower() or primary["name"].lower() in schema_name.lower()
        
        return {
            "has_org_schema": has_org,
            "schema_name": schema_name,
            "name_matches": name_matches
        }
    
    def _extract_secondary_entities(self, text, headings):
        """Extract feature/product/service entities from headings."""
        all_h = []
        for level in ["h2", "h3"]:
            all_h.extend(headings.get(level, []))
        
        # Filter to meaningful headings (not generic)
        generic = {"home", "about", "contact", "blog", "menu", "navigation", "footer", "header", "search"}
        entities = [h for h in all_h if h.lower().strip() not in generic and len(h.split()) <= 8]
        
        return entities[:15]
    
    def _calc_score(self, what_statement, consistency, ambiguity, schema_alignment, sources):
        score = 0
        
        # "What this is" definition (0-30)
        if what_statement["found"]:
            score += 30
        
        # Naming consistency (0-25)
        score += consistency["score"] * 0.25
        
        # Ambiguity (0-20)
        ambiguity_map = {"low": 20, "medium": 8, "high": 0}
        score += ambiguity_map.get(ambiguity["level"], 0)
        
        # Schema alignment (0-15)
        if schema_alignment["has_org_schema"]:
            score += 8
            if schema_alignment["name_matches"]:
                score += 7
        
        # Source coverage (0-10)
        source_count = len([v for k, v in sources.items() if k != "missing" and v])
        score += min(10, source_count * 2)
        
        return min(100, max(0, round(score)))
