"""
Structured Data Validator v2
Deep validation of JSON-LD, microdata, @context, nested types, content alignment, duplicates.
"""
import json
import re
from difflib import SequenceMatcher


class SchemaAnalyzer:
    """Validates structured data with deep inspection."""
    
    IMPORTANT_TYPES = {
        "Organization": {"required": ["name", "url"], "recommended": ["logo", "description", "sameAs", "contactPoint"]},
        "LocalBusiness": {"required": ["name", "address"], "recommended": ["telephone", "openingHours", "priceRange"]},
        "Corporation": {"required": ["name", "url"], "recommended": ["logo", "description"]},
        "Product": {"required": ["name"], "recommended": ["description", "image", "offers", "brand", "review"]},
        "Service": {"required": ["name"], "recommended": ["description", "provider", "serviceType"]},
        "SoftwareApplication": {"required": ["name", "applicationCategory"], "recommended": ["operatingSystem", "offers", "description"]},
        "FAQPage": {"required": ["mainEntity"], "recommended": []},
        "HowTo": {"required": ["name", "step"], "recommended": ["description", "totalTime"]},
        "WebSite": {"required": ["name", "url"], "recommended": ["potentialAction"]},
        "WebPage": {"required": ["name"], "recommended": ["description", "breadcrumb"]},
        "BreadcrumbList": {"required": ["itemListElement"], "recommended": []},
        "Article": {"required": ["headline", "author"], "recommended": ["datePublished", "image", "publisher"]},
        "BlogPosting": {"required": ["headline", "author"], "recommended": ["datePublished", "image", "publisher"]},
    }
    
    def analyze(self, crawl_data: dict) -> dict:
        json_ld = crawl_data.get("json_ld", [])
        microdata = crawl_data.get("microdata", [])
        html = crawl_data.get("html", "")
        text = crawl_data.get("text_content", "")
        meta = crawl_data.get("meta_tags", {})
        og = crawl_data.get("og_tags", {})
        headings = crawl_data.get("headings", {})
        
        # === 1. Parse all JSON-LD blocks ===
        all_schemas = self._flatten_json_ld(json_ld)
        
        # === 2. Check for parse errors ===
        parse_errors = [s for s in json_ld if isinstance(s, dict) and s.get("_parse_error")]
        
        # === 3. Validate each schema ===
        validations = []
        found_types = []
        
        for schema in all_schemas:
            v = self._validate_schema(schema)
            validations.append(v)
            if v["type"]:
                found_types.append(v["type"])
        
        # === 4. Check for @context ===
        context_issues = self._check_contexts(json_ld)
        
        # === 5. Detect duplicates ===
        duplicates = self._detect_duplicates(all_schemas)
        
        # === 6. Content alignment ===
        alignment = self._deep_alignment_check(all_schemas, meta, og, headings, text)
        
        # === 7. FAQPage validation (deep) ===
        faq_validation = self._validate_faq_schema(all_schemas)
        
        # === 8. Microdata analysis ===
        microdata_types = [m.get("type", "").split("/")[-1] for m in microdata if m.get("type")]
        
        # === 9. Missing recommended schemas ===
        recommended = self._get_missing_schemas(found_types, text, headings)
        
        # === Scores ===
        completeness = self._calc_completeness(found_types, validations)
        accuracy = alignment["score"]
        
        score = self._calc_score(completeness, accuracy, len(json_ld), parse_errors, context_issues, duplicates, faq_validation)
        
        findings = []
        recommendations = []
        
        if not json_ld:
            findings.append("No JSON-LD structured data found")
            recommendations.append("Add JSON-LD structured data — this is the primary way LLMs understand your site's entities")
        else:
            findings.append(f"Found {len(json_ld)} JSON-LD block(s) containing {len(all_schemas)} schema(s)")
            findings.append(f"Schema types: {', '.join(found_types) if found_types else 'None identified'}")
        
        if parse_errors:
            findings.append(f"{len(parse_errors)} JSON-LD block(s) have syntax errors")
            recommendations.append("Fix JSON-LD syntax errors — malformed schema is worse than no schema")
        
        if context_issues:
            for issue in context_issues:
                findings.append(f"Schema context issue: {issue}")
            recommendations.append("Ensure all JSON-LD blocks include '@context': 'https://schema.org'")
        
        if duplicates:
            findings.append(f"Duplicate schema types detected: {', '.join(duplicates)}")
            recommendations.append(f"Remove duplicate {', '.join(duplicates)} schemas — duplicates can confuse parsers")
        
        if microdata_types:
            findings.append(f"Microdata types found: {', '.join(microdata_types)}")
        
        # Validation details
        for v in validations:
            if v["missing_required"]:
                recommendations.append(f"{v['type']} schema missing required fields: {', '.join(v['missing_required'])}")
            if v["missing_recommended"]:
                recommendations.append(f"{v['type']} schema: consider adding {', '.join(v['missing_recommended'][:3])}")
        
        if not alignment["issues"]:
            findings.append("Schema content aligns with page content")
        else:
            for issue in alignment["issues"][:3]:
                findings.append(f"Alignment issue: {issue}")
                recommendations.append(f"Fix: {issue}")
        
        if faq_validation.get("issues"):
            for issue in faq_validation["issues"]:
                recommendations.append(f"FAQPage schema: {issue}")
        
        for rec in recommended:
            recommendations.append(rec)
        
        return {
            "name": "Structured Data",
            "icon": "🧱",
            "score": score,
            "weight": 10,
            "json_ld_count": len(json_ld),
            "total_schemas": len(all_schemas),
            "found_types": found_types,
            "parse_errors": len(parse_errors),
            "context_issues": context_issues,
            "duplicates": duplicates,
            "validations": [{
                "type": v["type"],
                "missing_required": v["missing_required"],
                "missing_recommended": v["missing_recommended"]
            } for v in validations],
            "alignment_score": alignment["score"],
            "microdata_types": microdata_types,
            "completeness_score": completeness,
            "findings": findings,
            "recommendations": recommendations
        }
    
    def _flatten_json_ld(self, json_ld):
        """Flatten @graph items into individual schemas."""
        schemas = []
        for item in json_ld:
            if not isinstance(item, dict) or item.get("_parse_error"):
                continue
            if "@graph" in item and isinstance(item["@graph"], list):
                for g in item["@graph"]:
                    if isinstance(g, dict):
                        schemas.append(g)
            else:
                schemas.append(item)
        return schemas
    
    def _validate_schema(self, schema):
        """Validate a single schema against known requirements."""
        schema_type = schema.get("@type", "")
        if isinstance(schema_type, list):
            schema_type = schema_type[0] if schema_type else ""
        
        result = {
            "type": schema_type,
            "fields_present": [k for k in schema.keys() if not k.startswith("@")],
            "missing_required": [],
            "missing_recommended": [],
            "has_context": "@context" in schema,
        }
        
        if schema_type in self.IMPORTANT_TYPES:
            spec = self.IMPORTANT_TYPES[schema_type]
            for field in spec["required"]:
                if field not in schema or not schema[field]:
                    result["missing_required"].append(field)
            for field in spec["recommended"]:
                if field not in schema:
                    result["missing_recommended"].append(field)
        
        return result
    
    def _check_contexts(self, json_ld):
        """Check for missing or incorrect @context."""
        issues = []
        for i, item in enumerate(json_ld):
            if not isinstance(item, dict) or item.get("_parse_error"):
                continue
            context = item.get("@context", "")
            if not context:
                issues.append(f"JSON-LD block {i+1} missing @context")
            elif "schema.org" not in str(context).lower():
                issues.append(f"JSON-LD block {i+1} has non-schema.org context: {context}")
        return issues
    
    def _detect_duplicates(self, schemas):
        """Find duplicate @type entries."""
        type_counts = {}
        for s in schemas:
            t = s.get("@type", "")
            if isinstance(t, list):
                t = t[0] if t else ""
            if t:
                type_counts[t] = type_counts.get(t, 0) + 1
        
        return [t for t, c in type_counts.items() if c > 1]
    
    def _deep_alignment_check(self, schemas, meta, og, headings, text):
        """Check if schema content matches actual page content."""
        issues = []
        score = 70  # Start at 70, adjust up/down
        
        page_title = meta.get("title", "")
        h1 = headings.get("h1", [""])[0] if headings.get("h1") else ""
        og_title = og.get("title", "")
        
        for schema in schemas:
            schema_type = schema.get("@type", "")
            schema_name = schema.get("name", "")
            schema_desc = schema.get("description", "")
            schema_url = schema.get("url", "")
            
            # Name alignment
            if schema_name:
                # Check if schema name appears anywhere in page
                if schema_name.lower() not in text.lower():
                    issues.append(f"{schema_type}.name (\"{schema_name}\") not found in page text")
                    score -= 10
                else:
                    score += 5
                
                # Check against title/H1
                if page_title and schema_name.lower() not in page_title.lower() and page_title.lower().split("|")[0].strip().lower() not in schema_name.lower():
                    if h1 and schema_name.lower() not in h1.lower():
                        issues.append(f"{schema_type}.name (\"{schema_name}\") doesn't match page title or H1")
                        score -= 5
            
            # Description alignment
            if schema_desc and len(schema_desc) > 20:
                # Check first 100 chars appear somewhere in text
                desc_snippet = schema_desc[:100].lower()
                if desc_snippet not in text.lower()[:5000]:
                    # Fuzzy match
                    sim = SequenceMatcher(None, desc_snippet, text.lower()[:5000]).ratio()
                    if sim < 0.3:
                        issues.append(f"{schema_type}.description doesn't match any visible page content")
                        score -= 5
        
        score = min(100, max(0, score))
        return {"score": score, "issues": issues}
    
    def _validate_faq_schema(self, schemas):
        """Deep validation of FAQPage schema."""
        issues = []
        
        for schema in schemas:
            if schema.get("@type") != "FAQPage":
                continue
            
            main_entity = schema.get("mainEntity", [])
            
            if not main_entity:
                issues.append("FAQPage exists but mainEntity is empty — add Question items")
                continue
            
            if not isinstance(main_entity, list):
                issues.append("FAQPage.mainEntity should be an array of Question objects")
                continue
            
            for i, q in enumerate(main_entity):
                if not isinstance(q, dict):
                    continue
                if q.get("@type") != "Question":
                    issues.append(f"FAQ item {i+1} should have @type: 'Question'")
                if not q.get("name"):
                    issues.append(f"FAQ item {i+1} missing 'name' (the question text)")
                accepted = q.get("acceptedAnswer", {})
                if not accepted:
                    issues.append(f"FAQ item {i+1} missing 'acceptedAnswer'")
                elif isinstance(accepted, dict):
                    if accepted.get("@type") != "Answer":
                        issues.append(f"FAQ item {i+1} acceptedAnswer should have @type: 'Answer'")
                    if not accepted.get("text"):
                        issues.append(f"FAQ item {i+1} acceptedAnswer missing 'text'")
        
        return {"issues": issues[:5]}  # Limit to 5 most important
    
    def _get_missing_schemas(self, found_types, text, headings):
        """Recommend missing schemas based on page content."""
        recommendations = []
        text_lower = text.lower()
        
        checklist = {
            "Organization": {
                "indicators": True,  # Always recommended
                "message": "Add Organization schema with name, url, logo, and description"
            },
            "FAQPage": {
                "indicators": any(kw in text_lower for kw in ["faq", "frequently asked", "question"]) or 
                              any("?" in h for hs in headings.values() for h in hs),
                "message": "Your page has FAQ content — add FAQPage schema to make it machine-readable"
            },
            "BreadcrumbList": {
                "indicators": True,
                "message": "Add BreadcrumbList schema to help LLMs understand your site hierarchy"
            },
            "HowTo": {
                "indicators": any(kw in text_lower for kw in ["how to", "step 1", "step 2", "steps to"]),
                "message": "Your page has instructional content — add HowTo schema"
            },
        }
        
        for schema_type, info in checklist.items():
            if schema_type not in found_types and info["indicators"]:
                recommendations.append(info["message"])
        
        return recommendations[:4]
    
    def _calc_completeness(self, found_types, validations):
        if not found_types:
            return 0
        
        score = 15  # Base for having any schema
        
        # Important types present
        important = ["Organization", "Corporation", "LocalBusiness", "WebSite", "FAQPage", "BreadcrumbList", "Product", "Service", "SoftwareApplication"]
        for t in found_types:
            if t in important:
                score += 12
        
        # Penalize missing required fields
        for v in validations:
            score -= len(v.get("missing_required", [])) * 5
        
        return min(100, max(0, score))
    
    def _calc_score(self, completeness, accuracy, ld_count, parse_errors, context_issues, duplicates, faq_val):
        if ld_count == 0:
            return 3  # Almost zero if no schema at all
        
        score = completeness * 0.45 + accuracy * 0.35
        
        # Bonuses
        if not parse_errors:
            score += 5
        else:
            score -= len(parse_errors) * 8
        
        if not context_issues:
            score += 5
        else:
            score -= len(context_issues) * 3
        
        if not duplicates:
            score += 5
        else:
            score -= len(duplicates) * 3
        
        if faq_val.get("issues"):
            score -= len(faq_val["issues"]) * 2
        
        return min(100, max(0, round(score)))
