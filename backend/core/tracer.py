import sqlite3
import json
import time
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

class TraceLogger:
    def __init__(self, db_path: str = "traces.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the SQLite database for traces."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Traces table (High-level requests)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS traces (
                id TEXT PRIMARY KEY,
                timestamp REAL,
                query TEXT,
                metadata TEXT,
                status TEXT,
                latency REAL
            )
        """)
        
        # Steps table (Detailed events within a trace)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trace_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trace_id TEXT,
                timestamp REAL,
                step_name TEXT,
                input TEXT,
                output TEXT,
                metadata TEXT,
                FOREIGN KEY(trace_id) REFERENCES traces(id)
            )
        """)
        
        conn.commit()
        conn.close()

    def start_trace(self, query: str, metadata: Dict[str, Any] = None) -> str:
        """Start a new trace for a user query."""
        trace_id = str(uuid.uuid4())
        timestamp = time.time()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO traces (id, timestamp, query, metadata, status, latency) VALUES (?, ?, ?, ?, ?, ?)",
            (trace_id, timestamp, query, json.dumps(metadata or {}), "running", 0.0)
        )
        conn.commit()
        conn.close()
        
        return trace_id

    def log_step(self, trace_id: str, step_name: str, input_data: Any, output_data: Any, metadata: Dict[str, Any] = None):
        """Log a specific step within a trace (e.g., Retrieval, LLM Call)."""
        timestamp = time.time()
        
        # Serialize complex objects to string/JSON
        def serialize(obj):
            if isinstance(obj, (str, int, float, bool, type(None))):
                return str(obj)
            try:
                return json.dumps(obj)
            except:
                return str(obj)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO trace_steps (trace_id, timestamp, step_name, input, output, metadata) VALUES (?, ?, ?, ?, ?, ?)",
            (trace_id, timestamp, step_name, serialize(input_data), serialize(output_data), json.dumps(metadata or {}))
        )
        conn.commit()
        conn.close()

    def end_trace(self, trace_id: str, status: str = "success", latency: float = 0.0):
        """Mark a trace as completed."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE traces SET status = ?, latency = ? WHERE id = ?",
            (status, latency, trace_id)
        )
        conn.commit()
        conn.close()

    def get_recent_traces(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent traces for the UI list view."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM traces ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        
        traces = []
        for row in rows:
            traces.append({
                "id": row["id"],
                "timestamp": datetime.fromtimestamp(row["timestamp"]).isoformat(),
                "query": row["query"],
                "status": row["status"],
                "latency": row["latency"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
            })
            
        conn.close()
        return traces

    def get_trace_details(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve full details and steps for a specific trace."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get Trace Info
        cursor.execute("SELECT * FROM traces WHERE id = ?", (trace_id,))
        trace_row = cursor.fetchone()
        
        if not trace_row:
            conn.close()
            return None
            
        # Get Steps
        cursor.execute("SELECT * FROM trace_steps WHERE trace_id = ? ORDER BY timestamp ASC", (trace_id,))
        step_rows = cursor.fetchall()
        
        steps = []
        for row in step_rows:
            steps.append({
                "step_name": row["step_name"],
                "timestamp": datetime.fromtimestamp(row["timestamp"]).isoformat(),
                "input": row["input"],
                "output": row["output"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
            })
            
        result = {
            "id": trace_row["id"],
            "timestamp": datetime.fromtimestamp(trace_row["timestamp"]).isoformat(),
            "query": trace_row["query"],
            "status": trace_row["status"],
            "latency": trace_row["latency"],
            "metadata": json.loads(trace_row["metadata"]) if trace_row["metadata"] else {},
            "steps": steps
        }
        
        conn.close()
        return result

    def get_activity_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get aggregated activity statistics for dashboard charts."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Calculate cutoff timestamp
        cutoff = time.time() - (days * 24 * 60 * 60)
        
        # 1. Query Activity by Hour (last 24h for hourly, or daily for weekly)
        if days <= 1:
            # Hourly breakdown for last 24 hours
            cursor.execute("""
                SELECT 
                    strftime('%H', datetime(timestamp, 'unixepoch', 'localtime')) as period,
                    COUNT(*) as count
                FROM traces 
                WHERE timestamp > ?
                GROUP BY period
                ORDER BY period
            """, (cutoff,))
        else:
            # Daily breakdown
            cursor.execute("""
                SELECT 
                    strftime('%Y-%m-%d', datetime(timestamp, 'unixepoch', 'localtime')) as period,
                    COUNT(*) as count
                FROM traces 
                WHERE timestamp > ?
                GROUP BY period
                ORDER BY period
            """, (cutoff,))
        
        query_timeline = [{"period": row["period"], "count": row["count"]} for row in cursor.fetchall()]
        
        # 2. RAG Strategy Distribution (from metadata)
        cursor.execute("""
            SELECT metadata FROM traces WHERE timestamp > ?
        """, (cutoff,))
        
        strategy_counts = {"vector": 0, "graph": 0, "hybrid": 0, "unknown": 0}
        for row in cursor.fetchall():
            try:
                meta = json.loads(row["metadata"]) if row["metadata"] else {}
                strategy = meta.get("strategy", meta.get("rag_strategy", "unknown"))
                if strategy in strategy_counts:
                    strategy_counts[strategy] += 1
                else:
                    strategy_counts["unknown"] += 1
            except:
                strategy_counts["unknown"] += 1
        
        strategy_distribution = [
            {"name": k, "value": v} for k, v in strategy_counts.items() if v > 0
        ]
        
        # 3. Latency Statistics
        cursor.execute("""
            SELECT 
                AVG(latency) as avg_latency,
                MIN(latency) as min_latency,
                MAX(latency) as max_latency,
                COUNT(*) as total_queries
            FROM traces 
            WHERE timestamp > ? AND status = 'success' AND latency > 0
        """, (cutoff,))
        
        latency_row = cursor.fetchone()
        latency_stats = {
            "avg": round(latency_row["avg_latency"] or 0, 2),
            "min": round(latency_row["min_latency"] or 0, 2),
            "max": round(latency_row["max_latency"] or 0, 2),
            "total": latency_row["total_queries"] or 0
        }
        
        # 4. Latency trend by period
        if days <= 1:
            cursor.execute("""
                SELECT 
                    strftime('%H', datetime(timestamp, 'unixepoch', 'localtime')) as period,
                    AVG(latency) as avg_latency
                FROM traces 
                WHERE timestamp > ? AND status = 'success' AND latency > 0
                GROUP BY period
                ORDER BY period
            """, (cutoff,))
        else:
            cursor.execute("""
                SELECT 
                    strftime('%Y-%m-%d', datetime(timestamp, 'unixepoch', 'localtime')) as period,
                    AVG(latency) as avg_latency
                FROM traces 
                WHERE timestamp > ? AND status = 'success' AND latency > 0
                GROUP BY period
                ORDER BY period
            """, (cutoff,))
        
        latency_trend = [{"period": row["period"], "latency": round(row["avg_latency"], 2)} for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            "query_timeline": query_timeline,
            "strategy_distribution": strategy_distribution,
            "latency_stats": latency_stats,
            "latency_trend": latency_trend
        }

