"""
URL context handler module.

This module provides a framework for handling different types of URLs
and extracting relevant context for code reviews.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
import re
from urllib.parse import urlparse


class URLHandler(ABC):
    """Abstract base class for URL handlers."""
    
    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """Check if this handler can process the given URL."""
        pass
    
    @abstractmethod
    def extract_context(self, url: str) -> Dict[str, Any]:
        """Extract context from the URL."""
        pass


class GitHubIssueHandler(URLHandler):
    """Handler for GitHub issue URLs."""
    
    def can_handle(self, url: str) -> bool:
        """Check if URL is a GitHub issue."""
        pattern = r'github\.com/.+/.+/issues/\d+'
        return bool(re.search(pattern, url))
    
    def extract_context(self, url: str) -> Dict[str, Any]:
        """Extract context from GitHub issue URL."""
        # TODO: Implement GitHub issue context extraction
        return {
            "type": "github_issue",
            "url": url,
            "content": f"GitHub issue context from {url} (not implemented yet)"
        }


class GitHubCommitHandler(URLHandler):
    """Handler for GitHub commit URLs."""
    
    def can_handle(self, url: str) -> bool:
        """Check if URL is a GitHub commit."""
        pattern = r'github\.com/.+/.+/commit/[a-f0-9]+'
        return bool(re.search(pattern, url))
    
    def extract_context(self, url: str) -> Dict[str, Any]:
        """Extract context from GitHub commit URL."""
        # TODO: Implement GitHub commit context extraction
        return {
            "type": "github_commit", 
            "url": url,
            "content": f"GitHub commit context from {url} (not implemented yet)"
        }


class DocumentationHandler(URLHandler):
    """Handler for documentation URLs."""
    
    def can_handle(self, url: str) -> bool:
        """Check if URL is a documentation site."""
        doc_patterns = [
            r'\.readthedocs\.io',
            r'docs\.python\.org',
            r'developer\.mozilla\.org',
            r'docs\.github\.com',
        ]
        return any(re.search(pattern, url) for pattern in doc_patterns)
    
    def extract_context(self, url: str) -> Dict[str, Any]:
        """Extract context from documentation URL."""
        # TODO: Implement documentation context extraction
        return {
            "type": "documentation",
            "url": url,
            "content": f"Documentation context from {url} (not implemented yet)"
        }


class GenericWebHandler(URLHandler):
    """Fallback handler for generic web URLs."""
    
    def can_handle(self, url: str) -> bool:
        """Can handle any valid URL."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def extract_context(self, url: str) -> Dict[str, Any]:
        """Extract context from generic web URL."""
        # TODO: Implement generic web content extraction
        return {
            "type": "generic_web",
            "url": url,
            "content": f"Web content from {url} (not implemented yet)"
        }


class URLContextManager:
    """Manager for handling multiple URL types."""
    
    def __init__(self):
        """Initialize with default handlers."""
        self.handlers: List[URLHandler] = [
            GitHubIssueHandler(),
            GitHubCommitHandler(),
            DocumentationHandler(),
            GenericWebHandler(),  # Must be last as fallback
        ]
    
    def process_urls(self, urls: Union[str, List[str]]) -> List[Dict[str, Any]]:
        """Process one or more URLs and extract context."""
        if isinstance(urls, str):
            urls = [urls]
        
        contexts: List[Dict[str, Any]] = []
        for url in urls:
            handler = self._find_handler(url)
            if handler:
                try:
                    context = handler.extract_context(url)
                    contexts.append(context)
                except Exception as e:
                    contexts.append({
                        "type": "error",
                        "url": url,
                        "error": str(e)
                    })
        
        return contexts
    
    def _find_handler(self, url: str) -> Optional[URLHandler]:
        """Find the appropriate handler for a URL."""
        for handler in self.handlers:
            if handler.can_handle(url):
                return handler
        return None


# Singleton instance
url_context_manager = URLContextManager()


def process_url_context(urls: Optional[Union[str, List[str]]]) -> Optional[str]:
    """
    Process URL context and return formatted string for inclusion in review.
    
    Args:
        urls: Single URL or list of URLs to process
        
    Returns:
        Formatted context string or None if no URLs provided
    """
    if not urls:
        return None
    
    contexts = url_context_manager.process_urls(urls)
    if not contexts:
        return None
    
    # Format contexts into a string
    formatted_parts = ["## Additional URL Context\n"]
    for ctx in contexts:
        formatted_parts.append(f"### {ctx.get('type', 'Unknown').replace('_', ' ').title()}: {ctx['url']}")
        if 'error' in ctx:
            formatted_parts.append(f"⚠️ Error: {ctx['error']}")
        else:
            formatted_parts.append(ctx.get('content', 'No content extracted'))
        formatted_parts.append("")
    
    return "\n".join(formatted_parts)