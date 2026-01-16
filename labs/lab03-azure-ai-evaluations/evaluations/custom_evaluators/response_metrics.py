"""
Custom Code-based Evaluators
Demonstrate how to create custom business-specific metrics
"""


class ResponseLengthEvaluator:
    """
    Custom code-based evaluator to measure response length.
    Useful for ensuring responses are within acceptable bounds.
    """
    
    def __init__(self, min_length: int = 50, max_length: int = 1000):
        """
        Initialize the response length evaluator.
        
        Args:
            min_length: Minimum acceptable response length
            max_length: Maximum acceptable response length
        """
        self.min_length = min_length
        self.max_length = max_length
    
    def __call__(self, *, response: str, **kwargs) -> dict:
        """
        Evaluate response length.
        
        Args:
            response: The generated response text
            
        Returns:
            Dictionary with length metrics
        """
        length = len(response)
        word_count = len(response.split())
        
        # Check if length is within acceptable range
        is_within_range = self.min_length <= length <= self.max_length
        
        # Calculate length score (0-5 scale)
        if length < self.min_length:
            score = max(0, (length / self.min_length) * 3)  # 0-3 for too short
        elif length > self.max_length:
            score = max(0, 5 - ((length - self.max_length) / self.max_length) * 2)  # 3-5, penalize excess
        else:
            score = 5.0  # Perfect score for within range
        
        return {
            "response_length_chars": length,
            "response_length_words": word_count,
            "response_length_within_range": is_within_range,
            "response_length_score": round(score, 2)
        }


class CitationCountEvaluator:
    """
    Custom evaluator to count citations in RAG responses.
    Ensures responses properly cite sources.
    """
    
    def __init__(self, min_citations: int = 1):
        """
        Initialize the citation count evaluator.
        
        Args:
            min_citations: Minimum number of citations expected
        """
        self.min_citations = min_citations
    
    def __call__(self, *, response: str, **kwargs) -> dict:
        """
        Count citations in response.
        
        Args:
            response: The generated response text
            
        Returns:
            Dictionary with citation metrics
        """
        # Simple heuristic: count references to "Document" or numbered citations
        import re
        
        # Count patterns like "Document 1", "[1]", "(Source 1)", etc.
        patterns = [
            r'Document\s+\d+',
            r'\[\d+\]',
            r'\(Source\s+\d+\)',
            r'\(Document\s+\d+\)'
        ]
        
        citation_count = 0
        for pattern in patterns:
            matches = re.findall(pattern, response)
            citation_count += len(matches)
        
        has_sufficient_citations = citation_count >= self.min_citations
        
        # Calculate score (0-5 scale)
        if citation_count == 0:
            score = 0
        elif citation_count < self.min_citations:
            score = (citation_count / self.min_citations) * 3
        else:
            score = min(5, 3 + (citation_count - self.min_citations) * 0.5)
        
        return {
            "citation_count": citation_count,
            "has_sufficient_citations": has_sufficient_citations,
            "citation_score": round(score, 2)
        }
