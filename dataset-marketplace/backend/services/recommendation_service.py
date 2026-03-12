# ============================================================================
# Dataset Marketplace - Recommendation Service
# Lightweight AI recommendations based on tag similarity
# ============================================================================

from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class RecommendationService:
    """
    Lightweight recommendation engine using tag-based similarity.
    
    Uses TF-IDF vectorization and cosine similarity for:
    - Finding similar datasets based on tags
    - Generating personalized recommendations
    - Tag-based search ranking
    
    This is a simple, pre-computed approach suitable for MVP.
    For production, consider integrating proper ML models.
    """
    
    def __init__(self):
        """
        Initialize recommendation service.
        
        The vectorizer is initialized on first use to allow
        lazy loading of datasets.
        """
        # TF-IDF vectorizer for converting tags to vectors
        self.vectorizer = None
        
        # Cache for dataset vectors
        self.dataset_vectors = None
        self.dataset_ids = []
    
    def _prepare_tag_text(self, tags):
        """
        Convert tags list or string to normalized text for vectorization.
        
        Args:
            tags: List of tags or comma-separated string
        
        Returns:
            str: Normalized space-separated tags string
        
        Example:
            ['Finance', 'stocks, Market'] -> 'finance stocks market'
        """
        # Handle both list and string inputs
        if isinstance(tags, list):
            # Join list elements
            tag_text = ' '.join(tags)
        else:
            # Replace commas with spaces for string input
            tag_text = str(tags).replace(',', ' ')
        
        # Convert to lowercase and strip whitespace
        return tag_text.lower().strip()
    
    def build_index(self, datasets):
        """
        Build TF-IDF index from list of datasets.
        
        Args:
            datasets: List of Dataset model instances
        
        This creates a vector representation of each dataset's tags
        for efficient similarity calculations.
        """
        # Extract tags text for each dataset
        tag_texts = []
        self.dataset_ids = []
        
        for dataset in datasets:
            # Get tags from dataset
            if hasattr(dataset, 'get_tags_list'):
                tags = dataset.get_tags_list()
            else:
                tags = dataset.tags or ''
            
            # Add dataset info
            tag_texts.append(self._prepare_tag_text(tags))
            self.dataset_ids.append(dataset.id)
        
        # Handle empty dataset list
        if not tag_texts:
            self.vectorizer = None
            self.dataset_vectors = None
            return
        
        # Initialize TF-IDF vectorizer
        # Using analyzer='word' for tag-based analysis
        self.vectorizer = TfidfVectorizer(
            analyzer='word',           # Split on words
            lowercase=True,            # Convert to lowercase
            stop_words=None,           # Keep all tags (they're meaningful)
            max_features=1000,         # Limit vocabulary size
            ngram_range=(1, 2)         # Include unigrams and bigrams
        )
        
        # Fit vectorizer and transform tags to TF-IDF matrix
        self.dataset_vectors = self.vectorizer.fit_transform(tag_texts)
    
    def get_similar_datasets(self, dataset_id, datasets, top_n=5):
        """
        Find datasets similar to a given dataset.
        
        Args:
            dataset_id: ID of reference dataset
            datasets: List of all Dataset instances
            top_n: Number of recommendations to return
        
        Returns:
            list: List of tuples (dataset_id, similarity_score)
                  sorted by similarity descending
        
        Uses cosine similarity between TF-IDF vectors.
        """
        # Build index if not already built
        if self.dataset_vectors is None or len(self.dataset_ids) != len(datasets):
            self.build_index(datasets)
        
        # Handle empty index
        if self.dataset_vectors is None:
            return []
        
        # Find index of target dataset
        try:
            target_idx = self.dataset_ids.index(dataset_id)
        except ValueError:
            # Dataset not in index
            return []
        
        # Get target dataset's vector
        target_vector = self.dataset_vectors[target_idx]
        
        # Calculate cosine similarity with all datasets
        similarities = cosine_similarity(target_vector, self.dataset_vectors).flatten()
        
        # Get indices of most similar datasets (excluding self)
        similar_indices = np.argsort(similarities)[::-1]  # Sort descending
        
        # Build result list excluding the target dataset
        results = []
        for idx in similar_indices:
            if self.dataset_ids[idx] != dataset_id:  # Exclude self
                results.append((self.dataset_ids[idx], float(similarities[idx])))
            
            if len(results) >= top_n:
                break
        
        return results
    
    def get_recommendations_for_tags(self, tags, datasets, top_n=5):
        """
        Get dataset recommendations based on input tags.
        
        Args:
            tags: List of tags or comma-separated string to match
            datasets: List of Dataset instances to search
            top_n: Number of recommendations to return
        
        Returns:
            list: List of tuples (dataset_id, similarity_score)
        
        Useful for search results ranking and tag-based discovery.
        """
        # Build index if needed
        if self.dataset_vectors is None or len(self.dataset_ids) != len(datasets):
            self.build_index(datasets)
        
        # Handle empty index or no vectorizer
        if self.vectorizer is None or self.dataset_vectors is None:
            return []
        
        # Convert input tags to TF-IDF vector
        query_text = self._prepare_tag_text(tags)
        query_vector = self.vectorizer.transform([query_text])
        
        # Calculate cosine similarity with all datasets
        similarities = cosine_similarity(query_vector, self.dataset_vectors).flatten()
        
        # Get top N results
        top_indices = np.argsort(similarities)[::-1][:top_n]
        
        # Build result list
        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            if score > 0:  # Only include positive matches
                results.append((self.dataset_ids[idx], score))
        
        return results
    
    def get_user_recommendations(self, user_downloads, datasets, top_n=5):
        """
        Get personalized recommendations based on user's download history.
        
        Args:
            user_downloads: List of Download instances for the user
            datasets: List of all Dataset instances
            top_n: Number of recommendations to return
        
        Returns:
            list: List of tuples (dataset_id, relevance_score)
        
        Aggregates tags from user's downloaded datasets and finds
        similar datasets they haven't downloaded yet.
        """
        # Collect all tags from user's downloaded datasets
        downloaded_ids = set()
        all_tags = []
        
        for download in user_downloads:
            if download.dataset:
                downloaded_ids.add(download.dataset_id)
                
                # Get tags from downloaded dataset
                if hasattr(download.dataset, 'get_tags_list'):
                    all_tags.extend(download.dataset.get_tags_list())
                elif download.dataset.tags:
                    all_tags.extend(download.dataset.tags.split(','))
        
        # Handle case with no download history
        if not all_tags:
            # Return most popular datasets instead
            return self.get_popular_datasets(datasets, downloaded_ids, top_n)
        
        # Get recommendations based on aggregated tags
        recommendations = self.get_recommendations_for_tags(all_tags, datasets, top_n * 2)
        
        # Filter out already downloaded datasets
        filtered = [(did, score) for did, score in recommendations 
                    if did not in downloaded_ids]
        
        return filtered[:top_n]
    
    def get_popular_datasets(self, datasets, exclude_ids=None, top_n=5):
        """
        Get most popular datasets by download count.
        
        Args:
            datasets: List of Dataset instances
            exclude_ids: Set of dataset IDs to exclude (optional)
            top_n: Number of results to return
        
        Returns:
            list: List of tuples (dataset_id, popularity_score)
        
        Fallback recommendation when no user history is available.
        """
        exclude_ids = exclude_ids or set()
        
        # Sort datasets by download count
        sorted_datasets = sorted(
            [d for d in datasets if d.id not in exclude_ids],
            key=lambda d: d.download_count or 0,
            reverse=True
        )
        
        # Return top N with normalized popularity scores
        max_downloads = max((d.download_count or 0) for d in datasets) if datasets else 1
        max_downloads = max(max_downloads, 1)  # Avoid division by zero
        
        results = []
        for dataset in sorted_datasets[:top_n]:
            score = (dataset.download_count or 0) / max_downloads
            results.append((dataset.id, score))
        
        return results
    
    def get_tag_suggestions(self, partial_tag, datasets, top_n=10):
        """
        Get tag suggestions based on partial input.
        
        Args:
            partial_tag: Partial tag string to match
            datasets: List of Dataset instances
            top_n: Number of suggestions to return
        
        Returns:
            list: List of matching tags sorted by frequency
        
        Useful for autocomplete in upload/search forms.
        """
        # Collect all tags from datasets
        tag_counts = Counter()
        
        for dataset in datasets:
            if hasattr(dataset, 'get_tags_list'):
                tags = dataset.get_tags_list()
            elif dataset.tags:
                tags = [t.strip().lower() for t in dataset.tags.split(',')]
            else:
                tags = []
            
            tag_counts.update(tags)
        
        # Filter tags that contain the partial string
        partial = partial_tag.lower().strip()
        matching = [(tag, count) for tag, count in tag_counts.items()
                    if partial in tag]
        
        # Sort by frequency and return top N
        matching.sort(key=lambda x: x[1], reverse=True)
        
        return [tag for tag, count in matching[:top_n]]
    
    def calculate_dataset_relevance(self, dataset, search_query):
        """
        Calculate relevance score for a dataset given a search query.
        
        Args:
            dataset: Dataset instance
            search_query: Search query string
        
        Returns:
            float: Relevance score between 0 and 1
        
        Combines multiple factors:
        - Tag match score
        - Title match score
        - Description match score
        - Popularity score
        """
        query_terms = search_query.lower().split()
        
        if not query_terms:
            return 0.0
        
        score = 0.0
        
        # Tag matching (highest weight: 0.5)
        if hasattr(dataset, 'get_tags_list'):
            tags = dataset.get_tags_list()
        else:
            tags = (dataset.tags or '').lower().split(',')
        
        tag_text = ' '.join(tags)
        tag_matches = sum(1 for term in query_terms if term in tag_text)
        score += 0.5 * (tag_matches / len(query_terms))
        
        # Title matching (weight: 0.3)
        title = (dataset.title or '').lower()
        title_matches = sum(1 for term in query_terms if term in title)
        score += 0.3 * (title_matches / len(query_terms))
        
        # Description matching (weight: 0.15)
        description = (dataset.description or '').lower()
        desc_matches = sum(1 for term in query_terms if term in description)
        score += 0.15 * (desc_matches / len(query_terms))
        
        # Popularity bonus (weight: 0.05)
        downloads = dataset.download_count or 0
        popularity = min(downloads / 100, 1.0)  # Cap at 100 downloads
        score += 0.05 * popularity
        
        return min(score, 1.0)  # Cap at 1.0


# Global instance (initialized in app.py)
recommendation_service = RecommendationService()
