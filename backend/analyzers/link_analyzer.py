"""
Internal Link Graph Analyzer v2
Nav vs content link separation, breadcrumb detection, keyword-rich anchors, semantic clusters.
"""
import re
from urllib.parse import urlparse
from collections import Counter


class LinkAnalyzer:
    """Deep internal link structure analysis."""
    
    GENERIC_ANCHORS = {
        "click here", "learn more", "read more", "here", "link", "more", 
        "this", "see more", "view", "go", "visit", "check it out",
        "find out", "discover", "explore", "details", "info",
    }
    
    def analyze(self, crawl_data: dict) -> dict:
        internal_links = crawl_data.get("internal_links", [])
        external_links = crawl_data.get("external_links", [])
        nav_links = crawl_data.get("nav_links", [])
        headings = crawl_data.get("headings", {})
        text = crawl_data.get("text_content", "")
        url = crawl_data.get("url", "")
        breadcrumbs = crawl_data.get("breadcrumbs", [])
        
        # === 1. Separate nav links from content links ===
        content_links = [l for l in internal_links if not l.get("in_nav") and not l.get("is_anchor")]
        nav_only = [l for l in internal_links if l.get("in_nav")]
        anchor_links = [l for l in internal_links if l.get("is_anchor")]
        
        total_internal = len(internal_links)
        total_content_links = len(content_links)
        total_external = len(external_links)
        
        # === 2. Anchor text quality ===
        anchor_quality = self._analyze_anchor_quality(content_links)
        
        # === 3. Link depth ===
        depth = self._analyze_depth(internal_links, url)
        
        # === 4. Breadcrumb analysis ===
        has_breadcrumbs = len(breadcrumbs) > 0
        
        # === 5. Topic cluster analysis ===
        clusters = self._analyze_clusters(content_links, headings, text)
        
        # === 6. Keyword richness of anchors ===
        keyword_anchors = self._analyze_keyword_anchors(content_links, headings)
        
        # === 7. External link quality ===
        ext_quality = self._analyze_external_links(external_links)
        
        # === 8. Connectivity ===
        connectivity = self._calc_connectivity(total_content_links, anchor_quality, depth, has_breadcrumbs, clusters)
        
        score = self._calc_score(total_content_links, total_external, anchor_quality, depth, connectivity, has_breadcrumbs, keyword_anchors, ext_quality)
        
        findings = []
        recommendations = []
        
        findings.append(f"Total links: {total_internal} internal ({total_content_links} in content, {len(nav_only)} in nav), {total_external} external")
        findings.append(f"Anchor text: {anchor_quality['descriptive_pct']}% descriptive, {anchor_quality['generic_pct']}% generic, {anchor_quality['empty_pct']}% empty")
        findings.append(f"Unique destinations: {depth['unique_destinations']}")
        findings.append(f"Breadcrumb navigation: {'Present' if has_breadcrumbs else 'Not found'}")
        findings.append(f"Topic cluster coverage: {clusters['coverage_pct']}%")
        
        if total_content_links < 3:
            recommendations.append(f"Only {total_content_links} content links found. Add 5-15 contextual internal links within your page content (not just nav)")
        elif total_content_links < 8:
            recommendations.append(f"{total_content_links} content links found — aim for 10-15 for stronger topic authority")
        
        if anchor_quality["generic_count"] > 0:
            recommendations.append(f"Replace {anchor_quality['generic_count']} generic anchor texts ('click here', 'learn more') with descriptive, keyword-rich text")
        
        if anchor_quality["empty_count"] > 0:
            recommendations.append(f"{anchor_quality['empty_count']} links have no anchor text — add descriptive text to every link")
        
        if not has_breadcrumbs:
            recommendations.append("Add breadcrumb navigation to show page hierarchy — LLMs use this to understand content relationships")
        
        if keyword_anchors["keyword_rich_pct"] < 40 and total_content_links > 0:
            recommendations.append("Use more keyword-rich anchor text that describes the destination page topic")
        
        missing = clusters.get("missing_connections", [])
        if missing:
            for path in missing[:3]:
                recommendations.append(f"Add internal link: {path}")
        
        if total_external == 0:
            recommendations.append("Add external links to authoritative sources — this signals credibility to LLMs")
        elif ext_quality.get("nofollow_all", False):
            recommendations.append("Not all external links need rel=nofollow — allow some dofollow links to authoritative sources")
        
        if len(anchor_links) == 0:
            recommendations.append("Add anchor links (jump-to-section links) for long pages — helps LLMs map content structure")
        
        return {
            "name": "Internal Linking",
            "icon": "🔗",
            "score": score,
            "weight": 10,
            "total_internal": total_internal,
            "content_links": total_content_links,
            "nav_links": len(nav_only),
            "external_links": total_external,
            "anchor_links": len(anchor_links),
            "anchor_quality": anchor_quality,
            "depth": depth,
            "has_breadcrumbs": has_breadcrumbs,
            "breadcrumb_items": breadcrumbs,
            "cluster_analysis": clusters,
            "keyword_anchors": keyword_anchors,
            "connectivity_score": connectivity,
            "findings": findings,
            "recommendations": recommendations
        }
    
    def _analyze_anchor_quality(self, links):
        if not links:
            return {"generic_pct": 0, "empty_pct": 0, "descriptive_pct": 0, "generic_count": 0, "empty_count": 0}
        
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
            destinations.add(path)
            depth = len(path.split("/")) if path else 0
            depths.append(depth)
        
        return {
            "unique_destinations": len(destinations),
            "avg_depth": round(sum(depths) / len(depths), 1) if depths else 0,
            "max_depth": max(depths) if depths else 0,
        }
    
    def _analyze_clusters(self, links, headings, text):
        link_urls = [l.get("url", "").lower() for l in links]
        link_texts = " ".join(l.get("text", "").lower() for l in links)
        text_lower = text.lower()
        
        cluster_paths = {
            "Homepage → Product": {"keywords": ["product", "platform", "solution"], "paths": ["/product", "/platform"]},
            "Product → Features": {"keywords": ["features", "capabilities"], "paths": ["/features", "/capabilities"]},
            "Features → Use Cases": {"keywords": ["use case", "use-case", "customer stories"], "paths": ["/use-cases", "/customers"]},
            "Use Cases → FAQ": {"keywords": ["faq", "frequently asked", "help"], "paths": ["/faq", "/help"]},
            "Product → Pricing": {"keywords": ["pricing", "plans", "cost"], "paths": ["/pricing", "/plans"]},
            "Product → Docs": {"keywords": ["docs", "documentation", "guide"], "paths": ["/docs", "/documentation"]},
            "Blog → Product": {"keywords": ["blog", "resources"], "paths": ["/blog", "/resources"]},
        }
        
        found = []
        missing = []
        
        for name, info in cluster_paths.items():
            has_link = any(any(p in url for p in info["paths"]) for url in link_urls)
            has_keyword = any(kw in link_texts or kw in text_lower[:3000] for kw in info["keywords"])
            
            if has_link:
                found.append(name)
            elif has_keyword:
                missing.append(f"{name} (content exists but no link)")
            else:
                missing.append(name)
        
        total = len(cluster_paths)
        return {
            "found_connections": found,
            "missing_connections": missing,
            "coverage_pct": round(len(found) / total * 100, 1)
        }
    
    def _analyze_keyword_anchors(self, links, headings):
        """Check if anchor text contains relevant keywords."""
        all_h = []
        for v in headings.values():
            all_h.extend([h.lower() for h in v])
        
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
            # Has 4+ char words or matches heading keywords
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
    
    def _calc_connectivity(self, content_links, anchor_quality, depth, breadcrumbs, clusters):
        score = 0
        
        if content_links >= 10:
            score += 25
        elif content_links >= 5:
            score += 18
        elif content_links >= 2:
            score += 10
        elif content_links >= 1:
            score += 5
        
        score += anchor_quality.get("descriptive_pct", 0) * 0.3
        
        if breadcrumbs:
            score += 10
        
        score += clusters.get("coverage_pct", 0) * 0.2
        
        unique = depth.get("unique_destinations", 0)
        score += min(15, unique * 2)
        
        return min(100, max(0, round(score)))
    
    def _calc_score(self, content_links, external, anchors, depth, connectivity, breadcrumbs, keyword_anchors, ext_quality):
        score = 0
        
        # Content links (0-25)
        if content_links >= 10:
            score += 25
        elif content_links >= 5:
            score += 18
        elif content_links >= 2:
            score += 10
        elif content_links >= 1:
            score += 5
        
        # Anchor quality (0-20)
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
        
        return min(100, max(0, round(score)))
