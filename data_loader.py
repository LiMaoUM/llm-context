"""
Data loading and exploration utilities for the LLM Context experiment.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
from datetime import datetime, date
from background_context import BackgroundContextManager, format_background_for_llm


class DataLoader:
    """Load and explore social media data from Parquet files."""
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.posts = None
        self.users = None
        self.interactions = None
        self.post_edges = None
        self.cascades = None
        self.tree_features = None
        self.user_history_posts = None  # Recent posts by each user
        self.background_manager = BackgroundContextManager()
    
    def load_all(self) -> Dict[str, pd.DataFrame]:
        """Load all data files."""
        self.posts = pd.read_parquet(self.data_dir / "posts" / "posts.parquet")
        self.users = pd.read_parquet(self.data_dir / "users" / "users.parquet")
        self.interactions = pd.read_parquet(self.data_dir / "interactions" / "interactions.parquet")
        self.post_edges = pd.read_parquet(self.data_dir / "post_edges" / "post_edges.parquet")
        self.cascades = pd.read_parquet(self.data_dir / "cascades_nodes" / "cascades_nodes.parquet")
        self.tree_features = pd.read_parquet(self.data_dir / "tree_features" / "tree_features.parquet")
        
        # Load user history posts if available
        try:
            self.user_history_posts = pd.read_parquet(self.data_dir / "users" / "users_history_posts.parquet")
        except Exception:
            self.user_history_posts = None
        
        return {
            "posts": self.posts,
            "users": self.users,
            "interactions": self.interactions,
            "post_edges": self.post_edges,
            "cascades": self.cascades,
            "tree_features": self.tree_features,
        }
    
    def get_data_summary(self) -> Dict:
        """Get summary statistics of loaded data."""
        if self.posts is None:
            self.load_all()
        
        summary = {
            "posts": {
                "total_count": len(self.posts),
                "columns": list(self.posts.columns),
                "schema": str(self.posts.dtypes),
                "sample": self.posts.head(2).to_dict(),
            },
            "users": {
                "total_count": len(self.users),
                "columns": list(self.users.columns),
                "sample": self.users.head(2).to_dict(),
            },
            "interactions": {
                "total_count": len(self.interactions),
                "columns": list(self.interactions.columns),
                "sample": self.interactions.head(2).to_dict(),
            },
            "post_edges": {
                "total_count": len(self.post_edges),
                "columns": list(self.post_edges.columns),
                "sample": self.post_edges.head(2).to_dict(),
            },
            "cascades": {
                "total_count": len(self.cascades),
                "columns": list(self.cascades.columns),
            },
            "tree_features": {
                "total_count": len(self.tree_features),
                "columns": list(self.tree_features.columns),
            },
        }
        return summary
    
    def get_user_metadata(self, user_id: str) -> Dict:
        """Get metadata for a specific user."""
        user = None
        if 'id' in self.users.columns:
            user = self.users[self.users['id'] == user_id]
        if user is None or user.empty:
            if 'user_id' in self.users.columns:
                user = self.users[self.users['user_id'] == user_id]
        
        if user is None or user.empty:
            return None
        
        user_data = user.iloc[0].to_dict()
        return {
            'bio': user_data.get('profile_bio') or user_data.get('bio') or user_data.get('description'),
            'name': user_data.get('display_name') or user_data.get('name'),
            'handle': user_data.get('handle'),
            'follower_count': user_data.get('followers_count') or user_data.get('follower_count'),
            'following_count': user_data.get('friends_count') or user_data.get('following_count'),
            'account_age_days': user_data.get('account_age_days'),
            'verified': user_data.get('verified'),
            'platform': user_data.get('platform'),
            'n_posts': user_data.get('n_posts_current'),
        }
    
    def get_user_recent_posts(self, user_id: str, num_posts: int = 5, exclude_post_id: str = None) -> List[Dict]:
        """Get recent posts from a specific user (excluding the target post)."""
        if self.user_history_posts is None:
            return []
        
        # Filter posts by user_id and sort by date (newest first)
        user_posts = self.user_history_posts[self.user_history_posts['user_id'] == user_id]
        
        if user_posts.empty:
            return []
        
        # Sort by created_at descending (newest first)
        user_posts = user_posts.sort_values('created_at', ascending=False)
        
        # Exclude the target post
        if exclude_post_id:
            user_posts = user_posts[user_posts['post_id'] != exclude_post_id]
        
        # Get top N posts
        recent_posts = []
        for _, post in user_posts.head(num_posts).iterrows():
            # Handle NaN values safely
            likes = post.get('likes', 0)
            reposts = post.get('reposts', 0)
            
            # Convert NaN to 0
            if pd.isna(likes):
                likes = 0
            if pd.isna(reposts):
                reposts = 0
            
            recent_posts.append({
                'text': post.get('text'),
                'created_at': str(post.get('created_at')),
                'likes': int(likes),
                'reposts': int(reposts),
            })
        
        return recent_posts
    
    def get_conversation_context(self, post_id: str, depth: int = 2) -> Dict:
        """Get parent and child posts for a given post.
        
        In post_edges:
        - src_post_id: The reply post
        - dst_post_id: The post being replied to
        
        So for a given post_id:
        - Parents (posts this replies to): where src_post_id == post_id, get dst_post_id
        - Children (replies to this): where dst_post_id == post_id, get src_post_id
        """
        parents = []
        children = []
        
        if self.post_edges is not None and not self.post_edges.empty:
            # Find parent posts (posts this one replies to)
            # src_post_id (this post) -> dst_post_id (parent post)
            parent_edges = self.post_edges[self.post_edges['src_post_id'] == post_id]
            
            # Find child posts (posts that reply to this one)
            # src_post_id (child post) -> dst_post_id (this post)
            child_edges = self.post_edges[self.post_edges['dst_post_id'] == post_id]
            
            # Get actual post texts for parents
            if not parent_edges.empty:
                parent_ids = parent_edges['dst_post_id'].tolist()
                parent_posts = self.posts[self.posts['post_id'].isin(parent_ids)]
                if not parent_posts.empty:
                    parents = parent_posts.to_dict('records')
            
            # Get actual post texts for children
            if not child_edges.empty:
                child_ids = child_edges['src_post_id'].tolist()
                child_posts = self.posts[self.posts['post_id'].isin(child_ids)]
                if not child_posts.empty:
                    children = child_posts.to_dict('records')
        
        return {
            'parent_posts': parents,
            'child_posts': children,
        }
    
    def get_background_context(self, post_date: Optional[date] = None) -> str:
        """
        Get background context for the study period.
        
        Args:
            post_date: Optional post date to get context up to that date
        
        Returns:
            Formatted background context text
        """
        return format_background_for_llm(post_date=post_date)
    
    def get_post_with_all_context(self, post_id: str) -> Dict:
        """Assemble a complete sample with all available context."""
        post = self.posts[self.posts['post_id'] == post_id]
        
        if post.empty:
            return None
        
        post_data = post.iloc[0].to_dict()
        user_id = post_data.get('author_id') or post_data.get('user_id')
        
        # Try to parse post date
        post_date = None
        try:
            timestamp_str = post_data.get('created_at') or post_data.get('timestamp')
            if timestamp_str:
                if isinstance(timestamp_str, str):
                    post_date = datetime.fromisoformat(timestamp_str).date()
                elif isinstance(timestamp_str, datetime):
                    post_date = timestamp_str.date()
        except Exception:
            pass
        
        context = {
            'post_id': post_id,
            'post_text': post_data.get('text') or post_data.get('content'),
            'post_timestamp': post_data.get('created_at') or post_data.get('timestamp'),
            'post_date': post_date,
            'user_metadata': self.get_user_metadata(user_id),
            'user_recent_posts': self.get_user_recent_posts(user_id, num_posts=5, exclude_post_id=post_id),
            'conversation': self.get_conversation_context(post_id),
            'background_context': self.get_background_context(post_date),
            'post_raw': post_data,
        }
        
        return context


class ContextVariantGenerator:
    """Generate context variants (T, T+B, T+B+C, T+B+C+M) for each sample."""
    
    def __init__(self, data_loader: DataLoader):
        self.loader = data_loader
    
    def generate_variants(self, sample: Dict) -> Dict[str, str]:
        """
        Generate 4 cumulative context variants for a sample.
        
        Returns:
            {
                'T': 'post text only',
                'T+B': 'post + background',
                'T+B+C': 'post + background + conversation',
                'T+B+C+M': 'post + background + conversation + metadata',
            }
        """
        variants = {}
        
        # T: Text only
        variants['T'] = self._format_text_only(sample)
        
        # T+B: Text + Background
        variants['T+B'] = self._format_text_background(sample)
        
        # T+B+C: Text + Background + Conversation
        variants['T+B+C'] = self._format_text_background_conversation(sample)
        
        # T+B+C+M: Text + Background + Conversation + Metadata (FULL)
        variants['T+B+C+M'] = self._format_full_context(sample)
        
        return variants
    
    def _format_text_only(self, sample: Dict) -> str:
        """T: Post text only."""
        return sample.get('post_text', '')
    
    def _format_text_background(self, sample: Dict) -> str:
        """T+B: Post + background context."""
        parts = []
        
        # Add background if available
        if sample.get('background_context'):
            parts.append(f"[BACKGROUND]\n{sample['background_context']}")
        
        # Add target post
        parts.append(f"[TARGET POST]\n{sample.get('post_text', '')}")
        
        return "\n\n".join(parts)
    
    def _format_text_background_conversation(self, sample: Dict) -> str:
        """T+B+C: Post + background + conversation."""
        parts = []
        
        # Background
        if sample.get('background_context'):
            parts.append(f"[BACKGROUND]\n{sample['background_context']}")
        
        # Conversation history
        conversation = sample.get('conversation', {})
        
        # Add parent posts
        for parent in conversation.get('parent_posts', []):
            text = parent.get('text') or parent.get('content', '')
            if text:
                parts.append(f"[PARENT REPLY]\n{text}")
        
        # Target post
        parts.append(f"[TARGET POST]\n{sample.get('post_text', '')}")
        
        # Add child replies
        for child in conversation.get('child_posts', []):
            text = child.get('text') or child.get('content', '')
            if text:
                parts.append(f"[CHILD REPLY]\n{text}")
        
        return "\n\n".join(parts)
    
    def _format_full_context(self, sample: Dict) -> str:
        """T+B+C+M: All contexts combined."""
        parts = []
        
        # Background
        if sample.get('background_context'):
            parts.append(f"[BACKGROUND]\n{sample['background_context']}")
        
        # Metadata
        metadata = sample.get('user_metadata', {})
        if metadata:
            recent_posts = sample.get('user_recent_posts', [])
            meta_text = self._format_metadata_block(metadata, recent_posts)
            if meta_text:
                parts.append(f"[USER METADATA]\n{meta_text}")
        
        # Conversation history
        conversation = sample.get('conversation', {})
        
        # Add parent posts
        for parent in conversation.get('parent_posts', []):
            text = parent.get('text') or parent.get('content', '')
            if text:
                parts.append(f"[PARENT REPLY]\n{text}")
        
        # Target post
        parts.append(f"[TARGET POST]\n{sample.get('post_text', '')}")
        
        # Add child replies
        for child in conversation.get('child_posts', []):
            text = child.get('text') or child.get('content', '')
            if text:
                parts.append(f"[CHILD REPLY]\n{text}")
        
        return "\n\n".join(parts)
    
    def _format_metadata_block(self, metadata: Dict, recent_posts: List[Dict] = None) -> str:
        """Format user metadata into readable text."""
        lines = []
        if metadata.get('name'):
            lines.append(f"Name: {metadata['name']}")
        if metadata.get('handle'):
            lines.append(f"Handle: {metadata['handle']}")
        if metadata.get('bio'):
            lines.append(f"Bio: {metadata['bio']}")
        if metadata.get('platform'):
            lines.append(f"Platform: {metadata['platform']}")
        if metadata.get('follower_count'):
            lines.append(f"Followers: {metadata['follower_count']}")
        if metadata.get('following_count'):
            lines.append(f"Following: {metadata['following_count']}")
        if metadata.get('verified'):
            lines.append(f"Verified: {metadata['verified']}")
        if metadata.get('n_posts'):
            lines.append(f"Total Posts: {metadata['n_posts']}")
        
        # Add recent posts if available
        if recent_posts:
            lines.append(f"\nRecent Posts:")
            for i, post in enumerate(recent_posts[:5], 1):
                post_text = post.get('text', '')  # Full text, no truncation
                posted_date = post.get('created_at', '')
                likes = post.get('likes', 0)
                lines.append(f"  Post {i} ({posted_date}): {post_text} [{likes} likes]")
        
        return "\n".join(lines)


if __name__ == "__main__":
    # Example usage
    loader = DataLoader("./data")
    summary = loader.get_data_summary()
    print(json.dumps(summary, indent=2, default=str))
