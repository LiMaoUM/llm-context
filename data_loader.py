"""
Data loading and exploration utilities for the LLM Context experiment.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json


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
    
    def load_all(self) -> Dict[str, pd.DataFrame]:
        """Load all data files."""
        self.posts = pd.read_parquet(self.data_dir / "posts" / "posts.parquet")
        self.users = pd.read_parquet(self.data_dir / "users" / "users.parquet")
        self.interactions = pd.read_parquet(self.data_dir / "interactions" / "interactions.parquet")
        self.post_edges = pd.read_parquet(self.data_dir / "post_edges" / "post_edges.parquet")
        self.cascades = pd.read_parquet(self.data_dir / "cascades_nodes" / "cascades_nodes.parquet")
        self.tree_features = pd.read_parquet(self.data_dir / "tree_features" / "tree_features.parquet")
        
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
        user = self.users[self.users.get('id') == user_id] or \
                self.users[self.users.get('user_id') == user_id]
        
        if user.empty:
            return None
        
        user_data = user.iloc[0].to_dict()
        return {
            'bio': user_data.get('bio') or user_data.get('description'),
            'follower_count': user_data.get('followers_count') or user_data.get('follower_count'),
            'following_count': user_data.get('friends_count') or user_data.get('following_count'),
            'account_age_days': user_data.get('account_age_days'),
            'verified': user_data.get('verified'),
            'name': user_data.get('name'),
        }
    
    def get_conversation_context(self, post_id: str, depth: int = 2) -> Dict:
        """Get parent and child posts for a given post."""
        # Find parent posts through post_edges
        parents = []
        children = []
        
        if self.post_edges is not None:
            # Assuming post_edges has source and target columns
            parent_edges = self.post_edges[
                (self.post_edges.get('target_id') == post_id) | 
                (self.post_edges.get('target') == post_id)
            ]
            child_edges = self.post_edges[
                (self.post_edges.get('source_id') == post_id) | 
                (self.post_edges.get('source') == post_id)
            ]
            
            # Get actual post texts
            if not parent_edges.empty:
                parent_ids = parent_edges['source_id'] if 'source_id' in parent_edges.columns else parent_edges['source']
                parents = self.posts[self.posts['id'].isin(parent_ids)].to_dict('records')
            
            if not child_edges.empty:
                child_ids = child_edges['target_id'] if 'target_id' in child_edges.columns else child_edges['target']
                children = self.posts[self.posts['id'].isin(child_ids)].to_dict('records')
        
        return {
            'parent_posts': parents,
            'child_posts': children,
        }
    
    def get_post_with_all_context(self, post_id: str) -> Dict:
        """Assemble a complete sample with all available context."""
        post = self.posts[self.posts['id'] == post_id]
        
        if post.empty:
            return None
        
        post_data = post.iloc[0].to_dict()
        user_id = post_data.get('author_id') or post_data.get('user_id')
        
        context = {
            'post_id': post_id,
            'post_text': post_data.get('text') or post_data.get('content'),
            'post_timestamp': post_data.get('created_at') or post_data.get('timestamp'),
            'user_metadata': self.get_user_metadata(user_id),
            'conversation': self.get_conversation_context(post_id),
            'post_raw': post_data,
        }
        
        return context


class ContextVariantGenerator:
    """Generate context variants (T, T+C, T+B, T+M, FULL) for each sample."""
    
    def __init__(self, data_loader: DataLoader):
        self.loader = data_loader
    
    def generate_variants(self, sample: Dict) -> Dict[str, str]:
        """
        Generate all 8 context variants for a sample.
        
        Returns:
            {
                'T': 'post text only',
                'T+C': 'post + conversation',
                'T+B': 'post + background',
                'T+M': 'post + metadata',
                'T+C+B': 'post + conversation + background',
                'T+C+M': 'post + conversation + metadata',
                'T+B+M': 'post + background + metadata',
                'FULL': 'all contexts combined',
            }
        """
        variants = {}
        
        # T: Text only
        variants['T'] = self._format_text_only(sample)
        
        # T+C: Text + Conversation
        variants['T+C'] = self._format_text_conversation(sample)
        
        # T+B: Text + Background
        variants['T+B'] = self._format_text_background(sample)
        
        # T+M: Text + Metadata
        variants['T+M'] = self._format_text_metadata(sample)
        
        # T+C+B: Text + Conversation + Background
        variants['T+C+B'] = self._format_text_conversation_background(sample)
        
        # T+C+M: Text + Conversation + Metadata
        variants['T+C+M'] = self._format_text_conversation_metadata(sample)
        
        # T+B+M: Text + Background + Metadata
        variants['T+B+M'] = self._format_text_background_metadata(sample)
        
        # FULL: All contexts
        variants['FULL'] = self._format_full_context(sample)
        
        return variants
    
    def _format_text_only(self, sample: Dict) -> str:
        """T: Post text only."""
        return sample.get('post_text', '')
    
    def _format_text_conversation(self, sample: Dict) -> str:
        """T+C: Post + conversation history."""
        parts = []
        
        # Add parent posts
        for parent in sample.get('conversation', {}).get('parent_posts', []):
            text = parent.get('text') or parent.get('content', '')
            parts.append(f"[PARENT REPLY]\n{text}")
        
        # Add target post
        parts.append(f"[TARGET POST]\n{sample.get('post_text', '')}")
        
        # Add child replies
        for child in sample.get('conversation', {}).get('child_posts', []):
            text = child.get('text') or child.get('content', '')
            parts.append(f"[CHILD REPLY]\n{text}")
        
        return "\n\n".join(parts)
    
    def _format_text_background(self, sample: Dict) -> str:
        """T+B: Post + background context."""
        parts = []
        
        # Add background if available
        if sample.get('background_context'):
            parts.append(f"[BACKGROUND]\n{sample['background_context']}")
        
        # Add target post
        parts.append(f"[TARGET POST]\n{sample.get('post_text', '')}")
        
        return "\n\n".join(parts)
    
    def _format_text_metadata(self, sample: Dict) -> str:
        """T+M: Post + user metadata."""
        parts = []
        
        # Add user metadata
        metadata = sample.get('user_metadata', {})
        if metadata:
            meta_text = self._format_metadata_block(metadata)
            if meta_text:
                parts.append(f"[USER METADATA]\n{meta_text}")
        
        # Add target post
        parts.append(f"[TARGET POST]\n{sample.get('post_text', '')}")
        
        return "\n\n".join(parts)
    
    def _format_text_conversation_background(self, sample: Dict) -> str:
        """T+C+B: Post + conversation + background."""
        parts = []
        
        # Background
        if sample.get('background_context'):
            parts.append(f"[BACKGROUND]\n{sample['background_context']}")
        
        # Conversation
        for parent in sample.get('conversation', {}).get('parent_posts', []):
            text = parent.get('text') or parent.get('content', '')
            parts.append(f"[PARENT REPLY]\n{text}")
        
        # Target post
        parts.append(f"[TARGET POST]\n{sample.get('post_text', '')}")
        
        return "\n\n".join(parts)
    
    def _format_text_conversation_metadata(self, sample: Dict) -> str:
        """T+C+M: Post + conversation + metadata."""
        parts = []
        
        # Metadata
        metadata = sample.get('user_metadata', {})
        if metadata:
            meta_text = self._format_metadata_block(metadata)
            if meta_text:
                parts.append(f"[USER METADATA]\n{meta_text}")
        
        # Conversation
        for parent in sample.get('conversation', {}).get('parent_posts', []):
            text = parent.get('text') or parent.get('content', '')
            parts.append(f"[PARENT REPLY]\n{text}")
        
        # Target post
        parts.append(f"[TARGET POST]\n{sample.get('post_text', '')}")
        
        return "\n\n".join(parts)
    
    def _format_text_background_metadata(self, sample: Dict) -> str:
        """T+B+M: Post + background + metadata."""
        parts = []
        
        # Background
        if sample.get('background_context'):
            parts.append(f"[BACKGROUND]\n{sample['background_context']}")
        
        # Metadata
        metadata = sample.get('user_metadata', {})
        if metadata:
            meta_text = self._format_metadata_block(metadata)
            if meta_text:
                parts.append(f"[USER METADATA]\n{meta_text}")
        
        # Target post
        parts.append(f"[TARGET POST]\n{sample.get('post_text', '')}")
        
        return "\n\n".join(parts)
    
    def _format_full_context(self, sample: Dict) -> str:
        """FULL: All contexts (T+C+B+M)."""
        parts = []
        
        # Background
        if sample.get('background_context'):
            parts.append(f"[BACKGROUND]\n{sample['background_context']}")
        
        # Metadata
        metadata = sample.get('user_metadata', {})
        if metadata:
            meta_text = self._format_metadata_block(metadata)
            if meta_text:
                parts.append(f"[USER METADATA]\n{meta_text}")
        
        # Conversation
        for parent in sample.get('conversation', {}).get('parent_posts', []):
            text = parent.get('text') or parent.get('content', '')
            parts.append(f"[PARENT REPLY]\n{text}")
        
        # Target post
        parts.append(f"[TARGET POST]\n{sample.get('post_text', '')}")
        
        return "\n\n".join(parts)
    
    def _format_metadata_block(self, metadata: Dict) -> str:
        """Format user metadata into readable text."""
        lines = []
        if metadata.get('name'):
            lines.append(f"Name: {metadata['name']}")
        if metadata.get('bio'):
            lines.append(f"Bio: {metadata['bio']}")
        if metadata.get('follower_count'):
            lines.append(f"Followers: {metadata['follower_count']}")
        if metadata.get('verified'):
            lines.append(f"Verified: {metadata['verified']}")
        return "\n".join(lines)


if __name__ == "__main__":
    # Example usage
    loader = DataLoader("./data")
    summary = loader.get_data_summary()
    print(json.dumps(summary, indent=2, default=str))
