"""
Core crawler module v2 - Enhanced extraction for hardened analysis.
"""
import aiohttp
import asyncio
from bs4 import BeautifulSoup, Comment
from urllib.parse import urljoin, urlparse
import re
import json
import time


class SiteCrawler:
    """Crawls a URL and extracts all necessary data for analysis."""
    
    def __init__(self, url: str, timeout: int = 30):
        self.url = url
        self.timeout = timeout
        self.parsed_url = urlparse(url)
        self.base_domain = self.parsed_url.netloc
        self.html = ""
        self.soup = None
        self.raw_soup = None  # Unmodified soup for full HTML analysis
        self.text_content = ""
        self.headers = {}
        self.status_code = 0
        self.load_time = 0
        self.response_headers = {}
    
    async def crawl(self) -> dict:
        """Main crawl method - fetches page and extracts all data."""
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                headers_req = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                async with session.get(
                    self.url, 
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                    headers=headers_req,
                    ssl=False,
                    allow_redirects=True
                ) as response:
                    self.status_code = response.status
                    self.response_headers = dict(response.headers)
                    self.html = await response.text()
                    self.load_time = time.time() - start_time
                
                self.raw_soup = BeautifulSoup(self.html, 'lxml')
                
                # Build comprehensive extraction
                data = {
                    "success": True,
                    "url": self.url,
                    "final_url": str(response.url),
                    "status_code": self.status_code,
                    "load_time": round(self.load_time, 2),
                    "html": self.html,
                    "html_length": len(self.html),
                    "response_headers": self.response_headers,
                }
                
                # Text content (stripped of nav/footer/script)
                data["text_content"] = self._extract_text()
                data["text_length"] = len(data["text_content"])
                
                # Meta tags (comprehensive)
                data["meta_tags"] = self._extract_meta()
                
                # Open Graph tags
                data["og_tags"] = self._extract_og_tags()
                
                # Twitter card tags
                data["twitter_tags"] = self._extract_twitter_tags()
                
                # Canonical URL
                data["canonical_url"] = self._extract_canonical()
                
                # Headings
                data["headings"] = self._extract_headings()
                
                # Paragraphs (with position info)
                data["paragraphs"] = self._extract_paragraphs()
                
                # Links
                data["internal_links"], data["external_links"] = self._extract_links()
                
                # Navigation links (separate from content links)
                data["nav_links"] = self._extract_nav_links()
                
                # Images
                data["images"] = self._extract_images()
                
                # Scripts and stylesheets
                data["scripts"], data["stylesheets"] = self._extract_scripts_styles()
                
                # JSON-LD structured data
                data["json_ld"] = self._extract_json_ld()
                
                # Microdata
                data["microdata"] = self._extract_microdata()
                
                # Lists
                data["lists"] = self._extract_lists()
                
                # Tables
                data["tables"] = self._extract_tables()
                
                # FAQ structures (HTML-based)
                data["faq_html_structures"] = self._extract_faq_structures()
                
                # Semantic HTML elements
                data["semantic_elements"] = self._extract_semantic_elements()
                
                # Breadcrumbs
                data["breadcrumbs"] = self._extract_breadcrumbs()
                
                # Definition lists
                data["definition_lists"] = self._extract_definition_lists()
                
                # Accordion / collapsible content
                data["accordions"] = self._extract_accordions()
                
                # Details/summary elements
                data["details_elements"] = self._extract_details_elements()
                
                # Inline styles / hidden content
                data["hidden_content_count"] = self._count_hidden_content()
                
                # JS ratio
                data["js_rendered_ratio"] = self._calc_js_ratio()
                
                # Robots & sitemap
                robots, sitemap = await self._fetch_robots_sitemap(session)
                data["robots_txt"] = robots
                data["sitemap"] = sitemap
                
                return data
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _extract_text(self):
        soup = BeautifulSoup(self.html, 'lxml')
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
            comment.extract()
        return soup.get_text(separator=" ", strip=True)
    
    def _extract_meta(self):
        meta = {}
        title_tag = self.raw_soup.find("title")
        if title_tag:
            meta["title"] = title_tag.get_text(strip=True)
        
        for m in self.raw_soup.find_all("meta"):
            name = m.get("name", "")
            prop = m.get("property", "")
            content = m.get("content", "")
            http_equiv = m.get("http-equiv", "")
            
            key = name or prop or http_equiv
            if key and content:
                meta[key.lower()] = content
        
        return meta
    
    def _extract_og_tags(self):
        og = {}
        for m in self.raw_soup.find_all("meta", property=re.compile(r"^og:")):
            prop = m.get("property", "").replace("og:", "")
            content = m.get("content", "")
            if prop and content:
                og[prop] = content
        return og
    
    def _extract_twitter_tags(self):
        tw = {}
        for m in self.raw_soup.find_all("meta", attrs={"name": re.compile(r"^twitter:")}):
            name = m.get("name", "").replace("twitter:", "")
            content = m.get("content", "")
            if name and content:
                tw[name] = content
        return tw
    
    def _extract_canonical(self):
        link = self.raw_soup.find("link", rel="canonical")
        if link:
            return link.get("href", "")
        return ""
    
    def _extract_headings(self):
        headings = {}
        for level in range(1, 7):
            tag = f"h{level}"
            headings[tag] = []
            for h in self.raw_soup.find_all(tag):
                text = h.get_text(strip=True)
                if text:
                    headings[tag].append(text)
        return headings
    
    def _extract_paragraphs(self):
        paragraphs = []
        for i, p in enumerate(self.raw_soup.find_all("p")):
            text = p.get_text(strip=True)
            if text and len(text) > 10:
                # Determine if inside nav/footer/header
                parent_tags = [parent.name for parent in p.parents if parent.name]
                in_nav = any(t in parent_tags for t in ["nav", "footer", "header"])
                paragraphs.append({
                    "text": text,
                    "index": i,
                    "in_nav": in_nav,
                    "word_count": len(text.split())
                })
        return paragraphs
    
    def _extract_links(self):
        internal = []
        external = []
        
        for a in self.raw_soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True)
            full_url = urljoin(self.url, href)
            parsed = urlparse(full_url)
            
            # Determine if in nav/footer
            parent_tags = [parent.name for parent in a.parents if parent.name]
            in_nav = any(t in parent_tags for t in ["nav", "footer", "header"])
            
            link_data = {
                "url": full_url,
                "text": text,
                "raw_href": href,
                "in_nav": in_nav,
                "has_title": bool(a.get("title")),
                "rel": a.get("rel", []),
                "is_anchor": href.startswith("#"),
            }
            
            if parsed.netloc == self.base_domain or not parsed.netloc:
                internal.append(link_data)
            else:
                external.append(link_data)
        
        return internal, external
    
    def _extract_nav_links(self):
        nav_links = []
        for nav in self.raw_soup.find_all("nav"):
            for a in nav.find_all("a", href=True):
                nav_links.append({
                    "url": urljoin(self.url, a["href"]),
                    "text": a.get_text(strip=True)
                })
        return nav_links
    
    def _extract_images(self):
        images = []
        for img in self.raw_soup.find_all("img"):
            src = img.get("src", "") or img.get("data-src", "") or ""
            alt = img.get("alt", "")
            images.append({
                "src": src,
                "alt": alt,
                "has_alt": bool(alt.strip()),
                "is_lazy": bool(img.get("loading") == "lazy" or img.get("data-src")),
                "width": img.get("width", ""),
                "height": img.get("height", ""),
            })
        return images
    
    def _extract_scripts_styles(self):
        scripts = []
        for s in self.raw_soup.find_all("script"):
            scripts.append({
                "src": s.get("src", ""),
                "is_inline": not bool(s.get("src")),
                "type": s.get("type", ""),
                "async": bool(s.get("async")),
                "defer": bool(s.get("defer")),
                "size": len(s.string or "")
            })
        
        styles = []
        for l in self.raw_soup.find_all("link", rel="stylesheet"):
            styles.append(l.get("href", ""))
        
        return scripts, styles
    
    def _extract_json_ld(self):
        results = []
        for script in self.raw_soup.find_all("script", type="application/ld+json"):
            try:
                raw = script.string
                if raw:
                    data = json.loads(raw)
                    if isinstance(data, list):
                        results.extend(data)
                    else:
                        results.append(data)
            except (json.JSONDecodeError, TypeError):
                results.append({"_parse_error": True, "_raw": (script.string or "")[:200]})
        return results
    
    def _extract_microdata(self):
        items = []
        for elem in self.raw_soup.find_all(attrs={"itemscope": True}):
            item = {
                "type": elem.get("itemtype", ""),
                "properties": {}
            }
            for prop in elem.find_all(attrs={"itemprop": True}):
                name = prop.get("itemprop", "")
                value = prop.get("content") or prop.get("href") or prop.get_text(strip=True)
                if name:
                    item["properties"][name] = value[:200]
            items.append(item)
        return items
    
    def _extract_lists(self):
        lists = []
        for ul in self.raw_soup.find_all(["ul", "ol"]):
            parent_tags = [p.name for p in ul.parents if p.name]
            in_nav = any(t in parent_tags for t in ["nav", "footer", "header"])
            items = [li.get_text(strip=True) for li in ul.find_all("li", recursive=False)]
            if items and not in_nav:
                lists.append({"type": ul.name, "items": items, "count": len(items)})
        return lists
    
    def _extract_tables(self):
        tables = []
        for table in self.raw_soup.find_all("table"):
            rows = []
            headers = []
            for tr in table.find_all("tr"):
                ths = [th.get_text(strip=True) for th in tr.find_all("th")]
                tds = [td.get_text(strip=True) for td in tr.find_all("td")]
                if ths:
                    headers = ths
                if tds:
                    rows.append(tds)
            if rows or headers:
                tables.append({"headers": headers, "rows": rows, "row_count": len(rows)})
        return tables
    
    def _extract_faq_structures(self):
        """Detect FAQ-like HTML structures beyond JSON-LD."""
        faqs = []
        
        # 1. Elements with FAQ-related class/id names
        faq_patterns = re.compile(r"faq|frequently|question|accordion|collaps|toggle|expand", re.I)
        for elem in self.raw_soup.find_all(class_=faq_patterns):
            text = elem.get_text(strip=True)[:300]
            if text and len(text) > 10:
                faqs.append({"source": "css_class", "text": text})
        
        for elem in self.raw_soup.find_all(id=faq_patterns):
            text = elem.get_text(strip=True)[:300]
            if text and len(text) > 10:
                faqs.append({"source": "css_id", "text": text})
        
        # 2. Heading + paragraph pairs that look like Q&A
        for heading in self.raw_soup.find_all(["h2", "h3", "h4"]):
            h_text = heading.get_text(strip=True)
            if "?" in h_text or self._is_question_pattern(h_text):
                # Get the next sibling paragraph
                next_p = heading.find_next_sibling("p")
                answer = next_p.get_text(strip=True) if next_p else ""
                faqs.append({
                    "source": "heading_qa",
                    "question": h_text,
                    "answer": answer[:300],
                    "has_answer": bool(answer)
                })
        
        return faqs
    
    def _is_question_pattern(self, text):
        patterns = [
            r"^(what|how|why|when|where|who|can|does|is|do|will|are|should)\b",
        ]
        return any(re.match(p, text.strip(), re.I) for p in patterns)
    
    def _extract_details_elements(self):
        """Extract <details>/<summary> elements."""
        elements = []
        for details in self.raw_soup.find_all("details"):
            summary = details.find("summary")
            summary_text = summary.get_text(strip=True) if summary else ""
            content = details.get_text(strip=True)
            # Remove summary text from content
            if summary_text and content.startswith(summary_text):
                content = content[len(summary_text):].strip()
            elements.append({
                "summary": summary_text,
                "content": content[:300],
                "is_open": bool(details.get("open"))
            })
        return elements
    
    def _extract_definition_lists(self):
        """Extract <dl>/<dt>/<dd> pairs."""
        dl_items = []
        for dl in self.raw_soup.find_all("dl"):
            current_term = ""
            for child in dl.children:
                if hasattr(child, 'name'):
                    if child.name == "dt":
                        current_term = child.get_text(strip=True)
                    elif child.name == "dd" and current_term:
                        dl_items.append({
                            "term": current_term,
                            "definition": child.get_text(strip=True)[:300]
                        })
        return dl_items
    
    def _extract_accordions(self):
        """Detect accordion patterns via CSS classes and ARIA attributes."""
        accordions = []
        
        # ARIA-based accordions
        for elem in self.raw_soup.find_all(attrs={"role": "button", "aria-expanded": True}):
            text = elem.get_text(strip=True)
            if text:
                accordions.append({"source": "aria", "text": text})
        
        # Data-attribute toggles
        for elem in self.raw_soup.find_all(attrs={"data-toggle": re.compile(r"collapse|accordion", re.I)}):
            text = elem.get_text(strip=True)
            if text:
                accordions.append({"source": "data_toggle", "text": text})
        
        return accordions
    
    def _extract_semantic_elements(self):
        """Check for semantic HTML5 elements."""
        elements = {}
        for tag in ["article", "section", "main", "aside", "nav", "header", "footer", "figure", "figcaption", "time", "mark"]:
            count = len(self.raw_soup.find_all(tag))
            if count > 0:
                elements[tag] = count
        return elements
    
    def _extract_breadcrumbs(self):
        """Detect breadcrumb navigation."""
        breadcrumbs = []
        
        # ARIA breadcrumbs
        for nav in self.raw_soup.find_all("nav", attrs={"aria-label": re.compile(r"breadcrumb", re.I)}):
            items = [a.get_text(strip=True) for a in nav.find_all("a")]
            if items:
                breadcrumbs = items
        
        # Class-based breadcrumbs
        if not breadcrumbs:
            for elem in self.raw_soup.find_all(class_=re.compile(r"breadcrumb", re.I)):
                items = [a.get_text(strip=True) for a in elem.find_all("a")]
                if items:
                    breadcrumbs = items
                    break
        
        return breadcrumbs
    
    def _count_hidden_content(self):
        """Count elements hidden via inline styles."""
        count = 0
        for elem in self.raw_soup.find_all(style=re.compile(r"display\s*:\s*none|visibility\s*:\s*hidden", re.I)):
            text = elem.get_text(strip=True)
            if text and len(text) > 20:
                count += 1
        return count
    
    def _calc_js_ratio(self):
        if not self.html:
            return 0
        total_len = len(self.html)
        js_len = sum(len(s.string or "") for s in self.raw_soup.find_all("script"))
        if total_len == 0:
            return 0
        return round((total_len - js_len) / total_len * 100, 1)
    
    async def _fetch_robots_sitemap(self, session):
        base = f"{self.parsed_url.scheme}://{self.parsed_url.netloc}"
        robots = ""
        sitemap = ""
        
        try:
            async with session.get(f"{base}/robots.txt", timeout=aiohttp.ClientTimeout(total=8), ssl=False) as resp:
                if resp.status == 200:
                    robots = await resp.text()
        except:
            pass
        
        try:
            async with session.get(f"{base}/sitemap.xml", timeout=aiohttp.ClientTimeout(total=8), ssl=False) as resp:
                if resp.status == 200:
                    sitemap = await resp.text()
        except:
            pass
        
        return robots, sitemap
