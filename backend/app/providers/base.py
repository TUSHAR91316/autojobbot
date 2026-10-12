from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseJobProvider(ABC):
    """
    Common provider interface for job discovery sources.
    Adapters transform source-specific payloads into unified JobListing dictionaries.
    """
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    async def fetch_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch listings and return list of standardized job dictionaries"""
        pass
