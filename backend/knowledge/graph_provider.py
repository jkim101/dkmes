from typing import List, Dict, Any
from falkordb import FalkorDB
from core.gemini_client import GeminiClient
from .provider import KnowledgeProvider

class GraphProvider(KnowledgeProvider):
    def __init__(self, host: str = "localhost", port: int = 6379, gemini_client: GeminiClient = None):
        self.client = FalkorDB(host=host, port=port)
        self.graph = self.client.select_graph("dkmes_graph")
        self.gemini_client = gemini_client

    async def ingest(self, text: str) -> bool:
        """
        Ingests unstructured text by converting it to Cypher queries via LLM
        and executing them in FalkorDB.
        """
        if not self.gemini_client:
            raise ValueError("GeminiClient is required for LLM-based ingestion")

        # Simple Chunking Strategy
        CHUNK_SIZE = 2000
        OVERLAP = 200
        chunks = []
        
        if len(text) <= CHUNK_SIZE:
            chunks = [text]
        else:
            for i in range(0, len(text), CHUNK_SIZE - OVERLAP):
                chunks.append(text[i:min(i + CHUNK_SIZE, len(text))])
        
        print(f"Graph Ingestion: Processing {len(chunks)} chunks...")

        success_count = 0
        for i, chunk in enumerate(chunks):
            print(f"Generating Cypher for chunk {i+1}/{len(chunks)}...")
            try:
                cypher_queries_str = await self.gemini_client.extract_graph_entities(chunk)
                
                # Check for empty response
                if not cypher_queries_str or "RETURN" in cypher_queries_str and "MERGE" not in cypher_queries_str:
                    print(f"Chunk {i+1}: No valid cypher generated.")
                    continue

                # Clean up the query string
                cleaned_query = cypher_queries_str.replace('```cypher', '').replace('```', '').strip()
                
                # Split multiple creates if needed, but the prompt asks for a list. 
                # Usually Gemini returns a block of Cypher. FalkorDB can handle multiple commands if separated by newlines?
                # FalkorDB python client usually expects one query at a time or explicit transactions.
                # However, our prompt asks for "list of Cypher queries". 
                # Let's execute the block as is, assuming it yields valid Cypher.
                
                if cleaned_query:
                    # heuristic execution: if multiple lines, try to execute as one block or split
                    # For safety, let's try assuming it's a valid block.
                    self.graph.query(cleaned_query)
                    success_count += 1
            except Exception as e:
                print(f"Error processing chunk {i+1}: {e}")
                # Don't fail the whole ingest, just log error
        
        print(f"Graph Ingestion Complete. Successfully processed {success_count}/{len(chunks)} chunks.")
        return success_count > 0

    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Performs a semantic or keyword search on the graph.
        """
        # 1. Extract keywords using LLM
        if self.gemini_client:
            keywords = await self.gemini_client.extract_search_keywords(query)
        else:
            keywords = query.split()
            
        print(f"Searching Graph with keywords: {keywords}")
        
        if not keywords:
            return []

        # 2. Construct Cypher query to match ANY of the keywords
        # We use a dynamic WHERE clause
        conditions = []
        for kw in keywords:
            # Escape quotes just in case
            safe_kw = kw.replace("'", "\\'")
            conditions.append(f"toLower(n.name) CONTAINS toLower('{safe_kw}')")
            conditions.append(f"toLower(m.name) CONTAINS toLower('{safe_kw}')")
            
        where_clause = " OR ".join(conditions)
        
        cypher = f"""
        MATCH (n)-[r]-(m)
        WHERE {where_clause}
        RETURN n, r, m
        LIMIT {top_k}
        """
        
        try:
            result = self.graph.query(cypher)
            
            # Process results for both LLM (text) and UI (graph viz)
            text_results = []
            nodes = {}
            links = []
            
            for row in result.result_set:
                n, r, m = row
                
                # Text representation
                text_results.append(f"({n.properties.get('name', 'Unknown')}) -[{r.relation}]-> ({m.properties.get('name', 'Unknown')})")
                
                # Graph Viz Data
                # Nodes
                n_id = str(n.id)
                m_id = str(m.id)
                
                if n_id not in nodes:
                    nodes[n_id] = {"id": n_id, "label": n.properties.get('name', 'Unknown'), "group": list(n.labels)[0] if n.labels else "Node"}
                
                if m_id not in nodes:
                    nodes[m_id] = {"id": m_id, "label": m.properties.get('name', 'Unknown'), "group": list(m.labels)[0] if m.labels else "Node"}
                
                # Links
                links.append({
                    "source": n_id,
                    "target": m_id,
                    "label": r.relation
                })
            
            return {
                "text_results": text_results,
                "graph_data": {
                    "nodes": list(nodes.values()),
                    "links": links
                }
            }
            
        except Exception as e:
            print(f"Graph search failed: {e}")
            return {"text_results": [], "graph_data": {"nodes": [], "links": []}}

    async def get_stats(self) -> Dict[str, int]:
        """
        Returns statistics about the knowledge graph.
        """
        try:
            # Count Nodes
            node_query = "MATCH (n) RETURN count(n) as count"
            node_result = self.graph.query(node_query)
            node_count = node_result.result_set[0][0] if node_result.result_set else 0
            
            # Count Edges
            edge_query = "MATCH ()-[r]->() RETURN count(r) as count"
            edge_result = self.graph.query(edge_query)
            edge_count = edge_result.result_set[0][0] if edge_result.result_set else 0
            
            return {
                "graph_nodes": node_count,
                "graph_edges": edge_count
            }
        except Exception as e:
            print(f"Error getting graph stats: {e}")
            return {"graph_nodes": 0, "graph_edges": 0}

    async def get_graph_data(self, limit: int = 100) -> Dict[str, Any]:
        """
        Retrieves a subset of the graph for visualization.
        """
        try:
            query = f"""
            MATCH (n)-[r]->(m)
            RETURN n, r, m
            LIMIT {limit}
            """
            result = self.graph.query(query)
            
            nodes = {}
            links = []
            
            for row in result.result_set:
                n, r, m = row
                
                # Nodes
                n_id = str(n.id)
                m_id = str(m.id)
                
                if n_id not in nodes:
                    nodes[n_id] = {"id": n_id, "label": n.properties.get('name', 'Unknown'), "group": list(n.labels)[0] if n.labels else "Node"}
                
                if m_id not in nodes:
                    nodes[m_id] = {"id": m_id, "label": m.properties.get('name', 'Unknown'), "group": list(m.labels)[0] if m.labels else "Node"}
                
                # Links
                links.append({
                    "source": n_id,
                    "target": m_id,
                    "label": r.relation
                })
            
            return {
                "nodes": list(nodes.values()),
                "links": links
            }
        except Exception as e:
            print(f"Error getting graph data: {e}")
            return {"nodes": [], "links": []}

    async def update_node(self, node_id: str, properties: Dict[str, Any]) -> bool:
        """
        Updates properties of a specific node.
        """
        try:
            # Construct SET clause dynamically
            set_clauses = []
            for key, value in properties.items():
                # Basic sanitization (in production, use parameterized queries if supported by driver)
                if isinstance(value, str):
                    set_clauses.append(f"n.{key} = '{value}'")
                else:
                    set_clauses.append(f"n.{key} = {value}")
            
            set_query = ", ".join(set_clauses)
            
            query = f"""
            MATCH (n)
            WHERE ID(n) = {node_id}
            SET {set_query}
            RETURN n
            """
            
            self.graph.query(query)
            return True
        except Exception as e:
            print(f"Error updating node {node_id}: {e}")
            return False

    async def delete_node(self, node_id: str) -> bool:
        """
        Deletes a node and its relationships.
        """
        try:
            query = f"""
            MATCH (n)
            WHERE ID(n) = {node_id}
            DETACH DELETE n
            """
            self.graph.query(query)
            return True
        except Exception as e:
            print(f"Error deleting node {node_id}: {e}")
            return False

    async def clear(self) -> bool:
        """
        Clears the knowledge graph.
        """
        try:
            self.graph.query("MATCH (n) DETACH DELETE n")
            return True
        except Exception as e:
            print(f"Error clearing Graph: {e}")
            return False
