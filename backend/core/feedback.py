"""
Federated Feedback System

Receives and processes feedback from external agents about knowledge usefulness.
This feedback comes from end-users of external agents, allowing DKMES to 
assess real-world knowledge quality.
"""

import sqlite3
import json
import time
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from core.kep import KEPFeedback, FeedbackType


@dataclass
class FeedbackStats:
    """Aggregated feedback statistics for a domain or agent."""
    total_feedback: int
    avg_rating: float
    useful_rate: float  # % of feedback marked as useful
    correction_rate: float  # % of feedback with corrections
    

class FeedbackStore:
    """
    Stores and retrieves feedback from external agents.
    
    Feedback is linked to knowledge exchange requests via request_id.
    """
    
    def __init__(self, db_path: str = "feedback.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database for feedback storage."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT,
                sender_agent_id TEXT,
                feedback_type TEXT,
                rating REAL,
                was_useful INTEGER,
                correction TEXT,
                comments TEXT,
                user_context TEXT,
                timestamp REAL,
                processed INTEGER DEFAULT 0
            )
        """)
        
        # Index for fast lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_feedback_request 
            ON feedback(request_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_feedback_agent 
            ON feedback(sender_agent_id)
        """)
        
        conn.commit()
        conn.close()
    
    def store_feedback(self, feedback: KEPFeedback) -> int:
        """Store a piece of feedback. Returns the feedback ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO feedback 
            (request_id, sender_agent_id, feedback_type, rating, was_useful, 
             correction, comments, user_context, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            feedback.request_id,
            feedback.sender_agent_id,
            feedback.feedback_type.value,
            feedback.rating,
            1 if feedback.was_useful else 0,
            feedback.correction,
            feedback.comments,
            json.dumps(feedback.user_context),
            time.time()
        ))
        
        feedback_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return feedback_id
    
    def get_feedback_for_request(self, request_id: str) -> List[Dict]:
        """Get all feedback for a specific knowledge exchange request."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM feedback WHERE request_id = ? ORDER BY timestamp DESC",
            (request_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_dict(row) for row in rows]
    
    def get_feedback_for_agent(self, agent_id: str, limit: int = 100) -> List[Dict]:
        """Get feedback from a specific agent."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM feedback WHERE sender_agent_id = ? ORDER BY timestamp DESC LIMIT ?",
            (agent_id, limit)
        )
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_dict(row) for row in rows]
    
    def get_recent_feedback(self, limit: int = 50) -> List[Dict]:
        """Get recent feedback across all agents."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM feedback ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_dict(row) for row in rows]
    
    def _row_to_dict(self, row) -> Dict:
        """Convert a database row to a dictionary."""
        return {
            "id": row["id"],
            "request_id": row["request_id"],
            "sender_agent_id": row["sender_agent_id"],
            "feedback_type": row["feedback_type"],
            "rating": row["rating"],
            "was_useful": bool(row["was_useful"]),
            "correction": row["correction"],
            "comments": row["comments"],
            "user_context": json.loads(row["user_context"]) if row["user_context"] else {},
            "timestamp": datetime.fromtimestamp(row["timestamp"]).isoformat()
        }


class FeedbackAggregator:
    """
    Aggregates feedback to produce quality metrics.
    
    Used by the Self-Assessment Engine to evaluate knowledge quality.
    """
    
    def __init__(self, feedback_store: FeedbackStore):
        self.store = feedback_store
    
    def get_overall_stats(self, days: int = 30) -> FeedbackStats:
        """Get overall feedback statistics for the past N days."""
        cutoff = time.time() - (days * 24 * 3600)
        
        conn = sqlite3.connect(self.store.db_path)
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute(
            "SELECT COUNT(*) FROM feedback WHERE timestamp > ?",
            (cutoff,)
        )
        total = cursor.fetchone()[0]
        
        if total == 0:
            conn.close()
            return FeedbackStats(
                total_feedback=0,
                avg_rating=0.0,
                useful_rate=0.0,
                correction_rate=0.0
            )
        
        # Get average rating (only for feedback with ratings)
        cursor.execute(
            "SELECT AVG(rating) FROM feedback WHERE timestamp > ? AND rating IS NOT NULL",
            (cutoff,)
        )
        avg_rating = cursor.fetchone()[0] or 0.0
        
        # Get useful rate
        cursor.execute(
            "SELECT COUNT(*) FROM feedback WHERE timestamp > ? AND was_useful = 1",
            (cutoff,)
        )
        useful_count = cursor.fetchone()[0]
        
        # Get correction rate
        cursor.execute(
            "SELECT COUNT(*) FROM feedback WHERE timestamp > ? AND correction IS NOT NULL AND correction != ''",
            (cutoff,)
        )
        correction_count = cursor.fetchone()[0]
        
        conn.close()
        
        return FeedbackStats(
            total_feedback=total,
            avg_rating=round(avg_rating, 2),
            useful_rate=round(useful_count / total * 100, 1),
            correction_rate=round(correction_count / total * 100, 1)
        )
    
    def get_stats_by_domain(self, domain: str = None, days: int = 30) -> Dict[str, FeedbackStats]:
        """Get feedback statistics grouped by domain."""
        cutoff = time.time() - (days * 24 * 3600)
        
        conn = sqlite3.connect(self.store.db_path)
        cursor = conn.cursor()
        
        # Join with exchanges to get domain info
        # Note: This requires the kep.db to be accessible
        # For now, we'll use user_context which may contain domain
        
        cursor.execute("""
            SELECT user_context, COUNT(*) as cnt, 
                   AVG(rating) as avg_r,
                   SUM(was_useful) as useful_cnt
            FROM feedback 
            WHERE timestamp > ?
            GROUP BY user_context
        """, (cutoff,))
        
        rows = cursor.fetchall()
        conn.close()
        
        result = {}
        for row in rows:
            ctx = json.loads(row[0]) if row[0] else {}
            domain_name = ctx.get("domain", "unknown")
            
            result[domain_name] = FeedbackStats(
                total_feedback=row[1],
                avg_rating=round(row[2] or 0, 2),
                useful_rate=round((row[3] or 0) / row[1] * 100, 1),
                correction_rate=0.0  # Would need separate query
            )
        
        return result
    
    def get_stats_by_agent(self, days: int = 30) -> Dict[str, FeedbackStats]:
        """Get feedback statistics grouped by sender agent."""
        cutoff = time.time() - (days * 24 * 3600)
        
        conn = sqlite3.connect(self.store.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT sender_agent_id, COUNT(*) as cnt, 
                   AVG(rating) as avg_r,
                   SUM(was_useful) as useful_cnt,
                   SUM(CASE WHEN correction IS NOT NULL AND correction != '' THEN 1 ELSE 0 END) as corr_cnt
            FROM feedback 
            WHERE timestamp > ?
            GROUP BY sender_agent_id
        """, (cutoff,))
        
        rows = cursor.fetchall()
        conn.close()
        
        result = {}
        for row in rows:
            agent_id = row[0]
            total = row[1]
            
            result[agent_id] = FeedbackStats(
                total_feedback=total,
                avg_rating=round(row[2] or 0, 2),
                useful_rate=round((row[3] or 0) / total * 100, 1),
                correction_rate=round((row[4] or 0) / total * 100, 1)
            )
        
        return result
    
    def get_low_rated_requests(self, threshold: float = 2.5, limit: int = 10) -> List[Dict]:
        """Get requests that received low ratings - candidates for improvement."""
        conn = sqlite3.connect(self.store.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT request_id, AVG(rating) as avg_rating, COUNT(*) as feedback_count
            FROM feedback 
            WHERE rating IS NOT NULL
            GROUP BY request_id
            HAVING AVG(rating) < ?
            ORDER BY avg_rating ASC
            LIMIT ?
        """, (threshold, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "request_id": row["request_id"],
                "avg_rating": round(row["avg_rating"], 2),
                "feedback_count": row["feedback_count"]
            }
            for row in rows
        ]


# Global instances
_feedback_store = None
_feedback_aggregator = None


def get_feedback_store() -> FeedbackStore:
    """Get the global feedback store instance."""
    global _feedback_store
    if _feedback_store is None:
        _feedback_store = FeedbackStore()
    return _feedback_store


def get_feedback_aggregator() -> FeedbackAggregator:
    """Get the global feedback aggregator instance."""
    global _feedback_aggregator
    if _feedback_aggregator is None:
        _feedback_aggregator = FeedbackAggregator(get_feedback_store())
    return _feedback_aggregator
