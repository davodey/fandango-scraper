"""
Movie model matching TMDB structure for iOS app compatibility
"""
from dataclasses import dataclass, asdict
from typing import Optional
from datetime import datetime


@dataclass
class Movie:
    """
    Movie model matching TMDB structure

    Attributes:
        id: Unique identifier (required)
        title: Movie name (required)
        overview: Plot description (required)
        releaseDate: Format "yyyy-MM-dd" (optional)
        posterPath: Relative path to poster image (optional)
        backdropPath: Relative path to backdrop image (optional)
        voteAverage: Rating 0-10 scale (required)
        voteCount: Number of ratings (required)
        popularity: Popularity score (required)
        trailer: URL to movie trailer (optional)
    """
    id: int
    title: str
    overview: str
    voteAverage: float
    voteCount: int
    popularity: float
    releaseDate: Optional[str] = None
    posterPath: Optional[str] = None
    backdropPath: Optional[str] = None
    trailer: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert movie to dictionary for Firestore"""
        data = asdict(self)
        # Remove None values to keep Firestore clean
        return {k: v for k, v in data.items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict) -> 'Movie':
        """Create Movie from Firestore dictionary"""
        return cls(**data)

    def __hash__(self):
        """Make Movie hashable for comparison"""
        return hash(self.id)

    def has_changed(self, other: 'Movie') -> bool:
        """
        Check if this movie has changed compared to another
        Returns True if any field has changed
        """
        if not isinstance(other, Movie):
            return True

        return (
            self.title != other.title or
            self.overview != other.overview or
            self.releaseDate != other.releaseDate or
            self.posterPath != other.posterPath or
            self.backdropPath != other.backdropPath or
            self.voteAverage != other.voteAverage or
            self.voteCount != other.voteCount or
            self.popularity != other.popularity or
            self.trailer != other.trailer
        )
