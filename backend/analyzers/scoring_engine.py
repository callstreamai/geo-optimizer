"""
Scoring Engine v2 - Better weighted scoring with diminishing returns and nuanced grades.
"""


class ScoringEngine:
    """Aggregates all analysis into a final LLM SEO score."""
    
    WEIGHTS = {
        "Entity Clarity": 15,
        "FAQ Coverage": 20,
        "Content Clarity": 15,
        "Page Structure": 10,
        "Internal Linking": 10,
        "Structured Data": 10,
        "Technical": 10,
        "Trust & Authority": 10,
    }
    
    GRADE_BOUNDARIES = [
        (92, "A+"), (85, "A"), (78, "A-"),
        (72, "B+"), (65, "B"), (58, "B-"),
        (52, "C+"), (45, "C"), (38, "C-"),
        (30, "D+"), (22, "D"), (15, "D-"),
        (0, "F"),
    ]
    
    def calculate(self, analysis_results: list) -> dict:
        category_scores = {}
        weighted_sum = 0
        total_weight = 0
        
        all_recommendations = []
        
        for result in analysis_results:
            name = result.get("name", "Unknown")
            score = result.get("score", 0)
            weight = self.WEIGHTS.get(name, 0)
            
            grade = self._score_to_grade(score)
            
            category_scores[name] = {
                "score": score,
                "weight": weight,
                "icon": result.get("icon", "📊"),
                "grade": grade,
                "findings": result.get("findings", []),
                "recommendations": result.get("recommendations", [])
            }
            
            if weight > 0:
                weighted_sum += score * weight
                total_weight += weight
            
            for r in result.get("recommendations", []):
                # Impact = how much this fix could improve the overall score
                max_gain = weight * (100 - score) / 100
                all_recommendations.append({
                    "category": name,
                    "recommendation": r,
                    "impact": round(max_gain, 1),
                    "category_score": score,
                    "category_weight": weight
                })
        
        overall_score = round(weighted_sum / total_weight) if total_weight > 0 else 0
        overall_grade = self._score_to_grade(overall_score)
        
        # Sort by impact, then by category weight
        all_recommendations.sort(key=lambda x: (x["impact"], x["category_weight"]), reverse=True)
        priority_fixes = all_recommendations[:10]
        
        summary = self._generate_summary(overall_score, overall_grade, category_scores)
        breakdown = self._get_score_breakdown(category_scores)
        
        return {
            "overall_score": overall_score,
            "overall_grade": overall_grade,
            "category_scores": category_scores,
            "priority_fixes": priority_fixes,
            "all_recommendations": all_recommendations,
            "summary": summary,
            "score_breakdown": breakdown
        }
    
    def _score_to_grade(self, score):
        for threshold, grade in self.GRADE_BOUNDARIES:
            if score >= threshold:
                return grade
        return "F"
    
    def _generate_summary(self, score, grade, categories):
        if score >= 80:
            status = f"Your site scores {score}/100 (Grade {grade}) — well-optimized for LLM discovery."
        elif score >= 60:
            status = f"Your site scores {score}/100 (Grade {grade}) — solid foundation but clear opportunities to improve LLM visibility."
        elif score >= 40:
            status = f"Your site scores {score}/100 (Grade {grade}) — significant improvements needed to rank in AI-generated responses."
        else:
            status = f"Your site scores {score}/100 (Grade {grade}) — poorly optimized for LLMs. Most AI assistants would struggle to accurately describe your product."
        
        scored = [(name, data["score"], data["weight"]) for name, data in categories.items() if data.get("weight", 0) > 0]
        if scored:
            strongest = max(scored, key=lambda x: x[1])
            weakest = min(scored, key=lambda x: x[1])
            status += f" Strongest: {strongest[0]} ({strongest[1]}/100). Biggest opportunity: {weakest[0]} ({weakest[1]}/100)."
        
        return status
    
    def _get_score_breakdown(self, categories):
        breakdown = []
        for name, data in categories.items():
            breakdown.append({
                "name": name,
                "icon": data.get("icon", ""),
                "score": data["score"],
                "weight": data["weight"],
                "grade": data["grade"],
                "weighted_contribution": round(data["score"] * data["weight"] / 100, 1) if data["weight"] > 0 else 0
            })
        breakdown.sort(key=lambda x: x["weight"], reverse=True)
        return breakdown
