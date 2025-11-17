"""
Coverage Analyzer
Analyzes test case coverage against requirements and generates visual coverage data
"""
from typing import Dict, List, Any, Set, Tuple
import re


class CoverageAnalyzer:
    """
    Analyzes test case coverage and generates coverage metrics and visualization data.
    """

    def __init__(self):
        pass

    def analyze_coverage(
        self,
        test_cases: List[Dict[str, Any]],
        requirements: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze coverage of requirements by test cases.

        Args:
            test_cases: List of test case dictionaries
            requirements: List of requirement dictionaries

        Returns:
            Dictionary containing coverage analysis results
        """
        print(f"DEBUG CoverageAnalyzer: Analyzing {len(test_cases)} test cases against {len(requirements)} requirements")

        # Build coverage matrix
        coverage_matrix = self._build_coverage_matrix(test_cases, requirements)

        # Calculate coverage metrics
        metrics = self._calculate_metrics(coverage_matrix, test_cases, requirements)

        # Identify gaps and redundancies
        gaps = self._identify_gaps(coverage_matrix, requirements)
        redundancies = self._identify_redundancies(coverage_matrix, test_cases)

        # Build heatmap data
        heatmap_data = self._build_heatmap_data(coverage_matrix, test_cases, requirements)

        return {
            "coverage_matrix": coverage_matrix,
            "metrics": metrics,
            "gaps": gaps,
            "redundancies": redundancies,
            "heatmap_data": heatmap_data,
            "summary": self._generate_summary(metrics, gaps, redundancies)
        }

    def _build_coverage_matrix(
        self,
        test_cases: List[Dict[str, Any]],
        requirements: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        """
        Build a matrix mapping test cases to requirements.

        Returns:
            Matrix where each cell represents the relationship between a test case and requirement
        """
        matrix = []

        for req_idx, requirement in enumerate(requirements):
            row = []
            req_id = requirement.get('id', f'REQ-{req_idx + 1}')
            req_text = requirement.get('requirement', requirement.get('text', requirement.get('description', '')))

            for tc_idx, test_case in enumerate(test_cases):
                # Determine coverage level
                coverage = self._determine_coverage(test_case, requirement)

                row.append({
                    "requirement_id": req_id,
                    "test_case_index": tc_idx,
                    "coverage_level": coverage["level"],  # "full", "partial", "none"
                    "confidence": coverage["confidence"],  # 0.0 to 1.0
                    "matched_keywords": coverage.get("matched_keywords", []),
                    "reasoning": coverage.get("reasoning", "")
                })

            matrix.append(row)

        return matrix

    def _determine_coverage(
        self,
        test_case: Dict[str, Any],
        requirement: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Determine how well a test case covers a requirement.

        Returns:
            Dictionary with coverage level, confidence, and reasoning
        """
        req_id = requirement.get('id', '')
        req_text = requirement.get('requirement', requirement.get('text', requirement.get('description', ''))).lower()

        # Extract test case text
        tc_text = self._extract_test_case_text(test_case).lower()

        # Check for explicit requirement ID references
        if req_id and req_id.lower() in tc_text:
            return {
                "level": "full",
                "confidence": 1.0,
                "reasoning": f"Explicit reference to {req_id}",
                "matched_keywords": [req_id]
            }

        # Check for keyword matching
        req_keywords = self._extract_keywords(req_text)
        tc_keywords = self._extract_keywords(tc_text)

        matched_keywords = req_keywords & tc_keywords
        match_ratio = len(matched_keywords) / len(req_keywords) if req_keywords else 0

        if match_ratio >= 0.7:
            return {
                "level": "full",
                "confidence": match_ratio,
                "reasoning": f"High keyword match ({int(match_ratio * 100)}%)",
                "matched_keywords": list(matched_keywords)
            }
        elif match_ratio >= 0.3:
            return {
                "level": "partial",
                "confidence": match_ratio,
                "reasoning": f"Partial keyword match ({int(match_ratio * 100)}%)",
                "matched_keywords": list(matched_keywords)
            }
        else:
            return {
                "level": "none",
                "confidence": 0.0,
                "reasoning": "No significant match found",
                "matched_keywords": []
            }

    def _extract_test_case_text(self, test_case: Dict[str, Any]) -> str:
        """Extract all text from a test case for analysis."""
        parts = []

        # Add various fields
        for field in ['name', 'title', 'objective', 'description', 'expected_result', 'expected_results']:
            if test_case.get(field):
                parts.append(str(test_case[field]))

        # Add steps
        if test_case.get('steps'):
            for step in test_case['steps']:
                if isinstance(step, str):
                    parts.append(step)
                elif isinstance(step, dict):
                    for key in ['description', 'action', 'step', 'expected_result']:
                        if step.get(key):
                            parts.append(str(step[key]))

        # Add preconditions
        if test_case.get('preconditions'):
            parts.extend([str(p) for p in test_case['preconditions']])

        # Add tags
        if test_case.get('tags'):
            parts.extend([str(t) for t in test_case['tags']])

        return ' '.join(parts)

    def _extract_keywords(self, text: str) -> Set[str]:
        """Extract meaningful keywords from text."""
        # Remove common words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
            'that', 'these', 'those', 'it', 'its', 'they', 'them', 'their'
        }

        # Extract words (3+ characters, alphanumeric)
        words = re.findall(r'\b[a-z0-9]{3,}\b', text.lower())

        # Filter out stop words
        keywords = {w for w in words if w not in stop_words}

        return keywords

    def _calculate_metrics(
        self,
        coverage_matrix: List[List[Dict[str, Any]]],
        test_cases: List[Dict[str, Any]],
        requirements: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate coverage metrics."""
        if not requirements:
            return {
                "overall_coverage": 0.0,
                "fully_covered": 0,
                "partially_covered": 0,
                "not_covered": 0,
                "total_requirements": 0,
                "total_test_cases": len(test_cases),
                "avg_tests_per_requirement": 0.0,
                "requirements_with_multiple_tests": 0
            }

        fully_covered = 0
        partially_covered = 0
        not_covered = 0
        tests_per_requirement = []

        for row in coverage_matrix:
            full_coverage_count = sum(1 for cell in row if cell["coverage_level"] == "full")
            partial_coverage_count = sum(1 for cell in row if cell["coverage_level"] == "partial")

            if full_coverage_count > 0:
                fully_covered += 1
                tests_per_requirement.append(full_coverage_count)
            elif partial_coverage_count > 0:
                partially_covered += 1
                tests_per_requirement.append(partial_coverage_count)
            else:
                not_covered += 1
                tests_per_requirement.append(0)

        total_reqs = len(requirements)
        overall_coverage = (fully_covered + (partially_covered * 0.5)) / total_reqs if total_reqs > 0 else 0.0

        return {
            "overall_coverage": round(overall_coverage * 100, 1),
            "fully_covered": fully_covered,
            "partially_covered": partially_covered,
            "not_covered": not_covered,
            "total_requirements": total_reqs,
            "total_test_cases": len(test_cases),
            "avg_tests_per_requirement": round(sum(tests_per_requirement) / total_reqs, 1) if total_reqs > 0 else 0.0,
            "requirements_with_multiple_tests": sum(1 for count in tests_per_requirement if count > 1)
        }

    def _identify_gaps(
        self,
        coverage_matrix: List[List[Dict[str, Any]]],
        requirements: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify requirements with no or poor coverage."""
        gaps = []

        for req_idx, row in enumerate(coverage_matrix):
            full_coverage_count = sum(1 for cell in row if cell["coverage_level"] == "full")
            partial_coverage_count = sum(1 for cell in row if cell["coverage_level"] == "partial")

            if req_idx < len(requirements):
                requirement = requirements[req_idx]
                req_id = requirement.get('id', f'REQ-{req_idx + 1}')
                req_text = requirement.get('requirement', requirement.get('text', requirement.get('description', '')))

                if full_coverage_count == 0 and partial_coverage_count == 0:
                    gaps.append({
                        "requirement_id": req_id,
                        "requirement": req_text,
                        "severity": "critical",
                        "coverage_level": "none",
                        "recommendation": "Create test cases to cover this requirement"
                    })
                elif full_coverage_count == 0 and partial_coverage_count > 0:
                    gaps.append({
                        "requirement_id": req_id,
                        "requirement": req_text,
                        "severity": "high",
                        "coverage_level": "partial",
                        "recommendation": "Improve existing test cases for full coverage"
                    })

        return gaps

    def _identify_redundancies(
        self,
        coverage_matrix: List[List[Dict[str, Any]]],
        test_cases: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify test cases that may be redundant (covering the same requirements)."""
        redundancies = []

        # Transpose matrix to group by test cases
        if not coverage_matrix or not coverage_matrix[0]:
            return redundancies

        num_test_cases = len(coverage_matrix[0])

        # Build coverage signatures for each test case
        tc_signatures = []
        for tc_idx in range(num_test_cases):
            covered_reqs = set()
            for row_idx, row in enumerate(coverage_matrix):
                if row[tc_idx]["coverage_level"] in ["full", "partial"]:
                    covered_reqs.add(row[tc_idx]["requirement_id"])
            tc_signatures.append(covered_reqs)

        # Find overlapping test cases
        for i in range(num_test_cases):
            for j in range(i + 1, num_test_cases):
                overlap = tc_signatures[i] & tc_signatures[j]
                if overlap and len(overlap) >= 2:  # At least 2 shared requirements
                    tc_i_name = test_cases[i].get('name', test_cases[i].get('title', f'Test Case {i + 1}'))
                    tc_j_name = test_cases[j].get('name', test_cases[j].get('title', f'Test Case {j + 1}'))

                    redundancies.append({
                        "test_case_1": tc_i_name,
                        "test_case_1_index": i,
                        "test_case_2": tc_j_name,
                        "test_case_2_index": j,
                        "shared_requirements": list(overlap),
                        "overlap_count": len(overlap),
                        "recommendation": f"Review for potential consolidation or differentiation"
                    })

        return redundancies

    def _build_heatmap_data(
        self,
        coverage_matrix: List[List[Dict[str, Any]]],
        test_cases: List[Dict[str, Any]],
        requirements: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build data structure optimized for heatmap visualization."""
        cells = []

        for req_idx, row in enumerate(coverage_matrix):
            for tc_idx, cell in enumerate(row):
                # Map coverage level to intensity
                intensity = 0
                if cell["coverage_level"] == "full":
                    intensity = 100
                elif cell["coverage_level"] == "partial":
                    intensity = 50

                cells.append({
                    "requirement_index": req_idx,
                    "test_case_index": tc_idx,
                    "requirement_id": cell["requirement_id"],
                    "coverage_level": cell["coverage_level"],
                    "confidence": cell["confidence"],
                    "intensity": intensity,
                    "tooltip": self._build_cell_tooltip(cell, test_cases[tc_idx] if tc_idx < len(test_cases) else None)
                })

        # Debug: Print first requirement to see its structure
        if requirements:
            print(f"DEBUG: First requirement structure: {requirements[0]}")
            print(f"DEBUG: Keys in first requirement: {list(requirements[0].keys()) if isinstance(requirements[0], dict) else 'Not a dict'}")

        # Build requirements list for heatmap
        heatmap_requirements = []
        for idx, req in enumerate(requirements):
            req_text = req.get('requirement', req.get('text', req.get('description', '')))
            print(f"DEBUG: Requirement {idx}: id={req.get('id', 'NO ID')}, text_length={len(req_text)}, text_preview={req_text[:50] if req_text else 'EMPTY'}")

            heatmap_requirements.append({
                "index": idx,
                "id": req.get('id', f'REQ-{idx + 1}'),
                "text": req_text[:100] + ('...' if len(req_text) > 100 else '')
            })

        return {
            "cells": cells,
            "requirements": heatmap_requirements,
            "test_cases": [
                {
                    "index": idx,
                    "name": tc.get('name', tc.get('title', f'Test Case {idx + 1}'))
                }
                for idx, tc in enumerate(test_cases)
            ]
        }

    def _build_cell_tooltip(self, cell: Dict[str, Any], test_case: Dict[str, Any]) -> str:
        """Build tooltip text for a heatmap cell."""
        parts = []

        parts.append(f"Coverage: {cell['coverage_level'].capitalize()}")
        parts.append(f"Confidence: {int(cell['confidence'] * 100)}%")

        if cell.get('matched_keywords'):
            parts.append(f"Matched: {', '.join(cell['matched_keywords'][:3])}")

        if cell.get('reasoning'):
            parts.append(cell['reasoning'])

        return ' | '.join(parts)

    def _generate_summary(
        self,
        metrics: Dict[str, Any],
        gaps: List[Dict[str, Any]],
        redundancies: List[Dict[str, Any]]
    ) -> str:
        """Generate a human-readable summary of coverage."""
        parts = []

        coverage_pct = metrics.get('overall_coverage', 0)
        if coverage_pct >= 80:
            parts.append(f"Excellent coverage at {coverage_pct}%.")
        elif coverage_pct >= 60:
            parts.append(f"Good coverage at {coverage_pct}%.")
        elif coverage_pct >= 40:
            parts.append(f"Fair coverage at {coverage_pct}%.")
        else:
            parts.append(f"Low coverage at {coverage_pct}%.")

        if gaps:
            critical_gaps = [g for g in gaps if g['severity'] == 'critical']
            if critical_gaps:
                parts.append(f"{len(critical_gaps)} requirement(s) have no test coverage.")
            else:
                parts.append(f"{len(gaps)} requirement(s) need better coverage.")

        if redundancies:
            parts.append(f"{len(redundancies)} potential redundancies detected.")

        if metrics.get('requirements_with_multiple_tests', 0) > 0:
            parts.append(f"{metrics['requirements_with_multiple_tests']} requirements have multiple test cases.")

        return ' '.join(parts)


# Global instance
coverage_analyzer = CoverageAnalyzer()
