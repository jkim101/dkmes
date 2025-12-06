"""
Self-Assessment Engine

Enables DKMES to evaluate its own knowledge quality based on:
1. Federated Feedback (from external agent's end-users)
2. Knowledge Graph analysis (coverage, consistency)
3. Document freshness
"""

import sqlite3
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

from core.feedback import get_feedback_aggregator, FeedbackStats


class AssessmentDimension(str, Enum):
    """Dimensions of knowledge quality assessment."""
    USEFULNESS = "usefulness"  # From federated feedback
    COVERAGE = "coverage"  # Knowledge graph completeness
    CONSISTENCY = "consistency"  # Internal consistency
    FRESHNESS = "freshness"  # Age of knowledge


@dataclass
class DimensionScore:
    """Score for a single assessment dimension."""
    dimension: str
    score: float  # 0.0 to 1.0
    details: str
    recommendations: List[str]


@dataclass
class AssessmentReport:
    """Complete self-assessment report."""
    timestamp: str
    domain: Optional[str]
    overall_score: float
    dimensions: Dict[str, float]
    dimension_details: List[DimensionScore]
    recommendations: List[str]
    metadata: Dict[str, Any]


class SelfAssessmentEngine:
    """
    Evaluates DKMES's own knowledge quality.
    
    Uses data from:
    - FeedbackAggregator: Real-world usage feedback
    - KEP exchange history: Request patterns
    - Knowledge sources: Coverage and freshness
    """
    
    def __init__(
        self, 
        vector_provider=None, 
        graph_provider=None,
        kep_handler=None,
        db_path: str = "assessment.db"
    ):
        self.vector_provider = vector_provider
        self.graph_provider = graph_provider
        self.kep_handler = kep_handler
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database for storing assessment history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                domain TEXT,
                overall_score REAL,
                dimensions TEXT,
                recommendations TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    async def run_assessment(self, domain: Optional[str] = None) -> AssessmentReport:
        """
        Run a complete self-assessment.
        
        Args:
            domain: Optional domain to focus on. If None, assesses all domains.
        
        Returns:
            AssessmentReport with scores and recommendations.
        """
        timestamp = datetime.now().isoformat()
        
        # Assess each dimension
        usefulness = await self._assess_usefulness(domain)
        coverage = await self._assess_coverage(domain)
        consistency = await self._assess_consistency(domain)
        freshness = await self._assess_freshness(domain)
        
        dimension_scores = [usefulness, coverage, consistency, freshness]
        
        # Calculate overall score (weighted average)
        weights = {
            AssessmentDimension.USEFULNESS: 0.4,  # Most important
            AssessmentDimension.COVERAGE: 0.25,
            AssessmentDimension.CONSISTENCY: 0.2,
            AssessmentDimension.FRESHNESS: 0.15
        }
        
        overall_score = sum(
            d.score * weights.get(AssessmentDimension(d.dimension), 0.25)
            for d in dimension_scores
        )
        
        # Collect all recommendations
        all_recommendations = []
        for d in dimension_scores:
            all_recommendations.extend(d.recommendations)
        
        # Create report
        report = AssessmentReport(
            timestamp=timestamp,
            domain=domain,
            overall_score=round(overall_score, 2),
            dimensions={d.dimension: d.score for d in dimension_scores},
            dimension_details=dimension_scores,
            recommendations=all_recommendations[:5],  # Top 5 recommendations
            metadata={
                "assessment_version": "1.0",
                "weights": {k.value: v for k, v in weights.items()}
            }
        )
        
        # Store assessment in history
        self._store_assessment(report)
        
        return report
    
    async def _assess_usefulness(self, domain: Optional[str]) -> DimensionScore:
        """Assess usefulness based on federated feedback."""
        aggregator = get_feedback_aggregator()
        stats = aggregator.get_overall_stats(days=30)
        
        recommendations = []
        
        if stats.total_feedback == 0:
            score = 0.5  # Neutral when no feedback
            details = "No feedback received yet"
            recommendations.append("Encourage external agents to send feedback")
        else:
            # Normalize rating (1-5) to score (0-1)
            rating_score = (stats.avg_rating - 1) / 4 if stats.avg_rating else 0.5
            useful_score = stats.useful_rate / 100
            
            # Combine rating and usefulness
            score = (rating_score * 0.6 + useful_score * 0.4)
            
            details = f"Avg rating: {stats.avg_rating}/5, {stats.useful_rate}% marked useful"
            
            if stats.avg_rating < 3.5:
                recommendations.append("Knowledge quality needs improvement - avg rating below 3.5")
            if stats.correction_rate > 10:
                recommendations.append(f"High correction rate ({stats.correction_rate}%) - review frequently corrected answers")
        
        return DimensionScore(
            dimension=AssessmentDimension.USEFULNESS.value,
            score=round(score, 2),
            details=details,
            recommendations=recommendations
        )
    
    async def _assess_coverage(self, domain: Optional[str]) -> DimensionScore:
        """Assess knowledge coverage based on graph and vector stats."""
        recommendations = []
        
        try:
            # Get stats from providers
            vector_stats = await self.vector_provider.get_stats() if self.vector_provider else {}
            graph_stats = await self.graph_provider.get_stats() if self.graph_provider else {}
            
            chunk_count = vector_stats.get("vector_chunks", 0)
            node_count = graph_stats.get("graph_nodes", 0)
            edge_count = graph_stats.get("graph_edges", 0)
            
            # Simple scoring based on content volume
            # These thresholds can be adjusted
            if chunk_count == 0 and node_count == 0:
                score = 0.0
                details = "No knowledge ingested yet"
                recommendations.append("Upload documents to build knowledge base")
            else:
                chunk_score = min(chunk_count / 100, 1.0)  # Max at 100 chunks
                node_score = min(node_count / 200, 1.0)  # Max at 200 nodes
                edge_score = min(edge_count / 300, 1.0)  # Max at 300 edges
                
                score = (chunk_score * 0.4 + node_score * 0.3 + edge_score * 0.3)
                details = f"{chunk_count} chunks, {node_count} nodes, {edge_count} edges"
                
                if chunk_count < 50:
                    recommendations.append("Consider adding more documents for broader coverage")
                if node_count < 100:
                    recommendations.append("Knowledge graph could benefit from more entities")
        
        except Exception as e:
            score = 0.5
            details = f"Could not assess coverage: {str(e)}"
            recommendations.append("Ensure vector and graph providers are properly initialized")
        
        return DimensionScore(
            dimension=AssessmentDimension.COVERAGE.value,
            score=round(score, 2),
            details=details,
            recommendations=recommendations
        )
    
    async def _assess_consistency(self, domain: Optional[str]) -> DimensionScore:
        """
        Assess internal consistency of knowledge.
        
        This is a simplified version - a full implementation would:
        - Check for contradicting facts in the knowledge base
        - Verify entity relationships are bidirectional
        - Detect duplicate or conflicting information
        """
        recommendations = []
        
        # For now, use a heuristic based on feedback corrections
        aggregator = get_feedback_aggregator()
        stats = aggregator.get_overall_stats(days=30)
        
        if stats.total_feedback == 0:
            score = 0.8  # Assume consistent when no data
            details = "No inconsistencies detected (limited data)"
        else:
            # Lower correction rate = higher consistency
            correction_penalty = min(stats.correction_rate / 20, 0.5)  # Max 50% penalty
            score = 1.0 - correction_penalty
            
            details = f"Correction rate: {stats.correction_rate}%"
            
            if stats.correction_rate > 5:
                recommendations.append("Review and update frequently corrected knowledge areas")
        
        return DimensionScore(
            dimension=AssessmentDimension.CONSISTENCY.value,
            score=round(score, 2),
            details=details,
            recommendations=recommendations
        )
    
    async def _assess_freshness(self, domain: Optional[str]) -> DimensionScore:
        """
        Assess freshness of knowledge based on document ages.
        
        Simplified version - checks exchange history to estimate activity.
        Full implementation would track document ingestion timestamps.
        """
        recommendations = []
        
        if self.kep_handler:
            # Check recent exchange activity as proxy for freshness
            recent_exchanges = self.kep_handler.get_exchange_history(limit=100)
            
            if not recent_exchanges:
                score = 0.5
                details = "No recent knowledge exchanges"
                recommendations.append("Knowledge base may be stale - consider updating documents")
            else:
                # Check how recent the exchanges are
                now = time.time()
                recent_count = 0
                for ex in recent_exchanges:
                    # Parse timestamp
                    try:
                        ex_time = datetime.fromisoformat(ex["timestamp"]).timestamp()
                        age_days = (now - ex_time) / (24 * 3600)
                        if age_days < 7:
                            recent_count += 1
                    except:
                        pass
                
                recent_ratio = recent_count / len(recent_exchanges) if recent_exchanges else 0
                score = 0.5 + (recent_ratio * 0.5)  # 0.5 to 1.0
                
                details = f"{recent_count}/{len(recent_exchanges)} exchanges in last 7 days"
                
                if recent_ratio < 0.3:
                    recommendations.append("Low recent activity - consider promoting knowledge exchange")
        else:
            score = 0.7
            details = "Freshness data unavailable"
        
        return DimensionScore(
            dimension=AssessmentDimension.FRESHNESS.value,
            score=round(score, 2),
            details=details,
            recommendations=recommendations
        )
    
    def _store_assessment(self, report: AssessmentReport):
        """Store assessment in history database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO assessments 
            (timestamp, domain, overall_score, dimensions, recommendations)
            VALUES (?, ?, ?, ?, ?)
        """, (
            time.time(),
            report.domain,
            report.overall_score,
            json.dumps(report.dimensions),
            json.dumps(report.recommendations)
        ))
        
        conn.commit()
        conn.close()
    
    def get_assessment_history(self, limit: int = 20) -> List[Dict]:
        """Get history of past assessments."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM assessments ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": row["id"],
                "timestamp": datetime.fromtimestamp(row["timestamp"]).isoformat(),
                "domain": row["domain"],
                "overall_score": row["overall_score"],
                "dimensions": json.loads(row["dimensions"]) if row["dimensions"] else {},
                "recommendations": json.loads(row["recommendations"]) if row["recommendations"] else []
            }
            for row in rows
        ]
    
    def get_score_trend(self, days: int = 30) -> List[Dict]:
        """Get score trend over time."""
        cutoff = time.time() - (days * 24 * 3600)
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT timestamp, overall_score, dimensions
            FROM assessments 
            WHERE timestamp > ?
            ORDER BY timestamp ASC
        """, (cutoff,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "timestamp": datetime.fromtimestamp(row["timestamp"]).isoformat(),
                "overall_score": row["overall_score"],
                "dimensions": json.loads(row["dimensions"]) if row["dimensions"] else {}
            }
            for row in rows
        ]


# Global instance
_assessment_engine = None


def get_assessment_engine(vector_provider=None, graph_provider=None, kep_handler=None) -> SelfAssessmentEngine:
    """Get the global assessment engine instance."""
    global _assessment_engine
    if _assessment_engine is None:
        _assessment_engine = SelfAssessmentEngine(
            vector_provider=vector_provider,
            graph_provider=graph_provider,
            kep_handler=kep_handler
        )
    return _assessment_engine
