"""
Internal Link Graph Analyzer v3
SPA detection with partial anchor credit, nav vs content separation, breadcrumbs, keyword anchors.
"""
import re
from urllib.parse import urlparse
from collections import Counter


class LinkAnalyzer:
    """Deep internal link structure analysis with SPA awareness."""
    
    GENERIC_ANCHORS = {
        "click here", "learn more", "read more", "here", "link", "more", 
        "this", "see more", "view", "go", "visit", "check it out",
        "find out", "discover", "explore", "details", "info",
    }
    
    # Anchor links get partial credit (0.35x what a real page link gets)
    ANCHOR_LINK_WEIGHT = 0.35
    
    def analyze(self, crawl_data: dict) -> dict:
        internal_links = crawl_data.get("internal_links", [])
        external_links = crawl_data.get("external_links", [])
        nav_links = crawl_data.get("nav_links", [])
        headings = crawl_data.get("headings", {})
        text = crawl_data.get("text_content", "")
        url = crawl_data.get("url", "")
        breadcrumbs = crawl_data.get("breadcrumbs", [])
        
        # === 1. Classify all links ===
        page_links = [l for l in internal_links if not l.get("is_anchor")]
        anchor_links = [l for l in internal_links if l.get("is_anchor")]
        
        content_page_links = [l for l in page_links if not l.get("in_nav")]
        content_anchor_links = [l for l in anchor_links if not l.get("in_nav")]
        nav_only = [l for l in internal_links if l.get("in_nav")]
        
        total_internal = len(internal_links)
        total_page_links = len(content_page_links)
        total_anchor_links = len(content_anchor_links)
        total_external = len(external_links)
        
        # === 2. SPA Detection ===
        spa_detection = self._detect_spa(content_page_links, content_anchor_links, anchor_links, page_links)
        is_spa = spa_detection["is_spa"]
        
        # === 3. Effective content links (page links + weighted anchor links) ===
        effective_content_count = total_page_links + (total_anchor_links * self.ANCHOR_LINK_WEIGHT)
        
        # === 4. Anchor text quality (all content links including anchors) ===
        all_content_links = content_page_links + (content_anchor_links if is_spa else [])
        anchor_quality = self._analyze_anchor_quality(all_content_links)
        
        # === 5. Anchor link section analysis (for SPAs) ===
        anchor_sections = self._analyze_anchor_sections(content_anchor_links) if is_spa else {}
        
        # === 6. Link depth (page links only) ===
        depth = self._analyze_depth(page_links, url)
        
        # === 7. Breadcrumbs ===
        has_breadcrumbs = len(breadcrumbs) > 0
        
        # === 8. Topic clusters ===
        clusters = self._analyze_clusters(content_page_links, content_anchor_links, headings, text, is_spa)
        
        # === 9. Keyword anchors ===
        keyword_anchors = self._analyze_keyword_anchors(all_content_links, headings)
        
        # === 10. External link quality ===
        ext_quality = self._analyze_external_links(external_links)
        
        # === 11. Connectivity ===
        connectivity = self._calc_connectivity(
            effective_content_count, anchor_quality, depth, 
            has_breadcrumbs, clusters, is_spa, anchor_sections
        )
        
        # === Score ===
        score = self._calc_score(
            effective_content_count, total_page_links, total_anchor_links,
            total_external, anchor_quality, depth, connectivity,
            has_breadcrumbs, keyword_anchors, ext_quality, is_spa, anchor_sections
        )
        
        findings = []
        recommendations = []
        
        # SPA finding (prominent)
        if is_spa:
            findings.append(f"⚠ Single-page site detected — {spa_detection['anchor_ratio']}% of internal links are anchor links (#sections)")
            findings.append(f"Section navigation: {total_anchor_links} anchor links to {anchor_sections.get('unique_sections', 0)} distinct sections")
        
        findings.append(f"Total links: {total_internal} internal ({total_page_links} page links, {total_anchor_links} anchor links, {len(nav_only)} nav), {total_external} external")
        
        if all_content_links:
            findings.append(f"Anchor text: {anchor_quality['descriptive_pct']}% descriptive, {anchor_quality['generic_pct']}% generic, {anchor_quality['empty_pct']}% empty")
        
        findings.append(f"Unique page destinations: {depth['unique_destinations']}")
        findings.append(f"Breadcrumb navigation: {'Present' if has_breadcrumbs else 'Not found'}")
        findings.append(f"Topic cluster coverage: {clusters['coverage_pct']}%")
        
        # SPA-specific recommendations
        if is_spa:
            recommendations.append(
                f"Single-page site: Your {total_anchor_links} section links show good content structure, "
                f"but LLMs strongly prefer separate pages per topic. When AI answers a question about one of your "
                f"services, it needs a distinct URL to cite — anchor sections on one page can't be individually referenced. "
                f"Consider creating dedicated pages for your major topics."
            )
            
            if anchor_sections.get("unique_sections", 0) >= 3:
                section_names = anchor_sections.get("section_names", [])[:5]
                if section_names:
                    examples = ", ".join(f"/{s.replace(' ', '-').lower()}" for s in section_names[:4])
                    recommendations.append(f"Suggested pages to create: {examples}")
        else:
            if total_page_links < 3:
                recommendations.append(f"Only {total_page_links} content page links found. Add 5-15 contextual internal links within your content (not just nav)")
            elif total_page_links < 8:
                recommendations.append(f"{total_page_links} content links found — aim for 10-15 for stronger topic authority")
        
        if anchor_quality.get("generic_count", 0) > 0:
            recommendations.append(f"Replace {anchor_quality['generic_count']} generic anchor texts ('click here', 'learn more') with descriptive, keyword-rich text")
        
        if anchor_quality.get("empty_count", 0) > 0:
            recommendations.append(f"{anchor_quality['empty_count']} links have no anchor text — add descriptive text to every link")
        
        if not has_breadcrumbs:
            recommendations.append("Add breadcrumb navigation to show page hierarchy — LLMs use this to understand content relationships")
        
        if keyword_anchors.get("keyword_rich_pct", 0) < 40 and len(all_content_links) > 0:
            recommendations.append("Use more keyword-rich anchor text that describes the destination content")
        
        missing = clusters.get("missing_connections", [])
        if missing and not is_spa:
            for path in missing[:3]:
                recommendations.append(f"Add internal link: {path}")
        
        if total_external == 0:
            recommendations.append("Add external links to authoritative sources — this signals credibility to LLMs")
        
        if not is_spa and len(anchor_links) == 0:
            recommendations.append("Add anchor links (jump-to-section links) for long pages — helps LLMs map content structure")
        
        return {
            "name": "Internal Linking",
            "icon": "🔗",
            "score": score,
            "weight": 10,
            "is_spa": is_spa,
            "spa_detection": spa_detection,
            "total_internal": total_internal,
            "content_page_links": total_page_links,
            "content_anchor_links": total_anchor_links,
            "effective_content_links": round(effective_content_count, 1),
            "nav_links": len(nav_only),
            "external_links": total_external,
            "anchor_quality": anchor_quality,
            "anchor_sections": anchor_sections,
            "depth": depth,
            "has_breadcrumbs": has_breadcrumbs,
            "breadcrumb_items": breadcrumbs,
            "cluster_analysis": clusters,
            "keyword_anchors": keyword_anchors,
            "connectivity_score": connectivity,
            "findings": findings,
            "recommendations": recommendations
        }
    
    def _detect_spa(self, content_page_links, content_anchor_links, all_anchor, all_page):
        """Detect if this is a single-page application/site."""
        total_anchor = len(all_anchor)
        total_page = len(all_page)
        total = total_anchor + total_page
        
        if total == 0:
            return {"is_spa": False, "anchor_ratio": 0, "reason": "No links found"}
        
        anchor_ratio = round(total_anchor / total * 100, 1)
        
        # SPA indicators:
        # 1. More than 50% of all internal links are anchor links
        # 2. Fewer than 5 distinct page destinations
        # 3. Content body has anchor links but few/no page links
        
        content_anchor_count = len(content_anchor_links)
        content_page_count = len(content_page_links)
        
        is_spa = False
        reason = ""
        
        if anchor_ratio >= 50:
            is_spa = True
            reason = f"{anchor_ratio}% of internal links are anchor (#) links"
        elif content_anchor_count > 3 and content_page_count <= 1:
            is_spa = True
            reason = f"Content has {content_anchor_count} section links but only {content_page_count} page links"
        
        return {
            "is_spa": is_spa,
            "anchor_ratio": anchor_ratio,
            "reason": reason,
            "total_anchor_links": total_anchor,
            "total_page_links": total_page
        }
    
    def _analyze_anchor_sections(self, anchor_links):
        """Analyze the quality of anchor-link section navigation."""
        if not anchor_links:
            return {"unique_sections": 0, "section_names": []}
        
        sections = set()
        section_names = []
        
        for link in anchor_links:
            href = link.get("raw_href", "")
            text = link.get("text", "").strip()
            
            if href.startswith("#") and len(href) > 1:
                section_id = href[1:]
                if section_id not in sections:
                    sections.add(section_id)
                    # Use anchor text as section name, fallback to section ID
                    name = text if text else section_id.replace("-", " ").replace("_", " ").title()
                    section_names.append(name)
        
        return {
            "unique_sections": len(sections),
            "section_names": section_names,
            "has_good_structure": len(sections) >= 3
        }
    
    def _analyze_anchor_quality(self, links):
        if not links:
            return {"generic_pct": 0, "empty_pct": 0, "descriptive_pct": 100, "generic_count": 0, "empty_count": 0, "descriptive_count": 0}
        
        empty = 0
        generic = 0
        descriptive = 0
        
        for link in links:
            text = link.get("text", "").strip().lower()
            if not text:
                empty += 1
            elif text in self.GENERIC_ANCHORS or len(text) < 3:
                generic += 1
            else:
                descriptive += 1
        
        total = len(links)
        return {
            "generic_pct": round(generic / total * 100, 1),
            "empty_pct": round(empty / total * 100, 1),
            "descriptive_pct": round(descriptive / total * 100, 1),
            "generic_count": generic,
            "empty_count": empty,
            "descriptive_count": descriptive,
        }
    
    def _analyze_depth(self, links, base_url):
        destinations = set()
        depths = []
        
        for link in links:
            link_url = link.get("url", "")
            parsed = urlparse(link_url)
            path = parsed.path.strip("/")
            destinations.add(path or "(root)")
            depth = len(path.split("/")) if path else 0
            depths.append(depth)
        
        return {
            "unique_destinations": len(destinations),
            "avg_depth": round(sum(depths) / len(depths), 1) if depths else 0,
            "max_depth": max(depths) if depths else 0,
        }
    
    def _analyze_clusters(self, page_links, anchor_links, headings, text, is_spa):
        """For SPAs, check if anchor sections cover key topic clusters."""
        
        if is_spa:
            # Use anchor link hrefs and text to evaluate clusters
            link_refs = [l.get("raw_href", "").lower() for l in anchor_links]
            link_texts = " ".join(l.get("text", "").lower() for l in anchor_links)
        else:
            link_refs = [l.get("url", "").lower() for l in page_links]
            link_texts = " ".join(l.get("text", "").lower() for l in page_links)
        
        text_lower = text.lower()
        combined = " ".join(link_refs) + " " + link_texts
        
        cluster_checks = {
            "Homepage → Product": {"keywords": ["product", "platform", "solution", "about"], "paths": ["product", "platform", "about"]},
            "Product → Features": {"keywords": ["features", "capabilities", "how-it-works", "how it works"], "paths": ["features", "capabilities", "how-it-works"]},
            "Features → Use Cases": {"keywords": ["use case", "use-case", "customer", "stories", "solutions", "who-we-serve"], "paths": ["use-cases", "customers", "solutions", "who-we-serve"]},
            "Use Cases → FAQ": {"keywords": ["faq", "frequently asked", "help", "questions"], "paths": ["faq", "help"]},
            "Product → Pricing": {"keywords": ["pricing", "plans", "cost"], "paths": ["pricing", "plans"]},
            "Product → Docs": {"keywords": ["docs", "documentation", "guide"], "paths": ["docs", "documentation"]},
            "Blog → Product": {"keywords": ["blog", "resources", "articles"], "paths": ["blog", "resources"]},
        }
        
        found = []
        missing = []
        
        for name, info in cluster_checks.items():
            has_link = any(any(p in ref for p in info["paths"]) for ref in link_refs)
            has_keyword = any(kw in combined for kw in info["keywords"])
            
            if has_link or has_keyword:
                found.append(name)
            else:
                has_in_text = any(kw in text_lower[:5000] for kw in info["keywords"])
                if has_in_text:
                    missing.append(f"{name} (content exists but no link)")
                else:
                    missing.append(name)
        
        total = len(cluster_checks)
        return {
            "found_connections": found,
            "missing_connections": missing,
            "coverage_pct": round(len(found) / total * 100, 1)
        }
    
    def _analyze_keyword_anchors(self, links, headings):
        all_h = [h.lower() for v in headings.values() for h in v]
        heading_words = set()
        for h in all_h:
            heading_words.update(w for w in h.split() if len(w) > 4)
        
        keyword_rich = 0
        total = 0
        
        for link in links:
            text = link.get("text", "").strip().lower()
            if not text or text in self.GENERIC_ANCHORS:
                continue
            total += 1
            words = set(w for w in text.split() if len(w) > 3)
            if words & heading_words or len(words) >= 2:
                keyword_rich += 1
        
        return {
            "keyword_rich_count": keyword_rich,
            "total_checked": total,
            "keyword_rich_pct": round(keyword_rich / total * 100, 1) if total else 0
        }
    
    def _analyze_external_links(self, links):
        if not links:
            return {"total": 0, "nofollow_all": False}
        nofollow_count = sum(1 for l in links if "nofollow" in (l.get("rel") or []))
        return {
            "total": len(links),
            "nofollow_count": nofollow_count,
            "nofollow_all": nofollow_count == len(links) and len(links) > 0
        }
    
    def _calc_connectivity(self, effective_links, anchor_quality, depth, breadcrumbs, clusters, is_spa, anchor_sections):
        score = 0
        
        # Effective links (page links + weighted anchor links)
        if effective_links >= 10:
            score += 25
        elif effective_links >= 5:
            score += 18
        elif effective_links >= 2:
            score += 12
        elif effective_links >= 1:
            score += 6
        
        score += anchor_quality.get("descriptive_pct", 0) * 0.3
        
        if breadcrumbs:
            score += 10
        
        score += clusters.get("coverage_pct", 0) * 0.2
        
        # SPA bonus for good section structure
        if is_spa and anchor_sections.get("has_good_structure"):
            score += 8
        
        unique = depth.get("unique_destinations", 0)
        score += min(15, unique * 2)
        
        return min(100, max(0, round(score)))
    
    def _calc_score(self, effective_links, page_links, anchor_links, external, 
                    anchors, depth, connectivity, breadcrumbs, keyword_anchors, 
                    ext_quality, is_spa, anchor_sections):
        score = 0
        
        # Content links — use effective count (0-25)
        if effective_links >= 10:
            score += 25
        elif effective_links >= 5:
            score += 18
        elif effective_links >= 3:
            score += 13
        elif effective_links >= 1:
            score += 7
        
        # Anchor text quality (0-20)
        score += anchors.get("descriptive_pct", 0) * 0.2
        
        # External links (0-10)
        if external >= 3:
            score += 10
        elif external >= 1:
            score += 6
        
        # Breadcrumbs (0-10)
        if breadcrumbs:
            score += 10
        
        # Keyword anchors (0-10)
        score += keyword_anchors.get("keyword_rich_pct", 0) * 0.1
        
        # Connectivity (0-15)
        score += connectivity * 0.15
        
        # Depth diversity (0-10)
        unique = depth.get("unique_destinations", 0)
        score += min(10, unique * 2)
        
        # SPA adjustments
        if is_spa:
            # Bonus for good section structure (up to +8)
            section_count = anchor_sections.get("unique_sections", 0)
            if section_count >= 5:
                score += 8
            elif section_count >= 3:
                score += 5
            elif section_count >= 1:
                score += 2
            
            # Bonus for descriptive section links (up to +5)
            if anchor_links > 0 and anchors.get("descriptive_pct", 0) > 60:
                score += 5
        
        return min(100, max(0, round(score)))
