import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold, GenerationConfig
from core.tools import get_tool_registry, ToolResult
import os
from typing import Optional, List
import asyncio

import json
import hashlib
from core.config import current_settings
from core.prompt_manager import PromptManager

class GeminiClient:
    def __init__(self, project_id: str = None, location: str = "us-central1", model_name: str = None):
        self.project_id = project_id
        self.location = location
        self.model_name = model_name or current_settings.llm_model
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.cache_file = ".gemini_cache.json"
        self.cache = self._load_cache()
        self.prompt_manager = PromptManager()
        
        try:
            if not self.api_key:
                raise ValueError("GEMINI_API_KEY not found in environment variables")
                
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            self.is_mock = False
            print(f"Successfully initialized Gemini API with model: {self.model_name}")
        except Exception as e:
            print(f"Warning: Failed to initialize Gemini API ({e}). Using Mock Client.")
            self.is_mock = True

    # ... (omitted methods) ...

    async def generate_answer(self, query: str, context: str) -> str:
        """
        Generates a final answer based on the query and retrieved context.
        """
        # Truncate context to avoid hitting token limits (approx 8000 chars ~ 2000 tokens)
        MAX_CONTEXT_LEN = 8000
        if len(context) > MAX_CONTEXT_LEN:
            context = context[:MAX_CONTEXT_LEN] + "...(truncated)"

        prompt = self.prompt_manager.get_template("answer_generation").format(
            context=context,
            query=query
        )
        try:
            return await self.generate_content(prompt, temperature=current_settings.temperature)
        except Exception as e:
            print(f"Answer generation failed: {e}")
            return "Failed to generate answer."

    def _load_cache(self) -> dict:
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_cache(self):
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f)
        except Exception as e:
            print(f"Failed to save cache: {e}")

    def _get_cache_key(self, prompt: str, temperature: float) -> str:
        return hashlib.md5(f"{prompt}::{temperature}::{self.model_name}".encode()).hexdigest()

    def _init_vertex(self):
        # Deprecated: Vertex AI init
        pass

    async def generate_content(self, prompt: str, temperature: float = 0.0) -> str:
        if self.is_mock:
            await asyncio.sleep(1) # Simulate latency
            return "Mock response from Gemini"
            
        # Check Cache
        cache_key = self._get_cache_key(prompt, temperature)
        if cache_key in self.cache:
            print("Cache Hit! Returning cached response.")
            return self.cache[cache_key]

        try:
            config = GenerationConfig(temperature=temperature)
            response = await self.model.generate_content_async(
                prompt,
                generation_config=config
            )
            
            # Update Cache
            self.cache[cache_key] = response.text
            self._save_cache()
            
            return response.text
        except Exception as e:
            print(f"Error generating content: {e}. Raising exception for fallback.")
            raise e

    async def extract_graph_entities(self, text: str) -> str:
        # Try Real AI first if not mock
        if not self.is_mock:
            try:
                full_prompt = self.prompt_manager.get_template("graph_extraction").format(text=text)
                return await self.generate_content(full_prompt, temperature=0.1)
            except Exception as e:
                print(f"Real AI extraction failed: {e}. Falling back to Mock.")
                # Fall through to mock logic

        # Mock Logic (Fallback) - Dynamic Generation
        await asyncio.sleep(1)
        
        # Generate deterministic but unique nodes based on text content hash or length
        import hashlib
        text_hash = hashlib.md5(text.encode()).hexdigest()[:6]
        
        # Create a "Document" node and some "Entity" nodes based on words in the text
        # This ensures that different files create different nodes.
        
        doc_node_name = f"Doc_{text_hash}"
        
        # Extract some pseudo-entities (just capitalized words or long words)
        words = [w for w in text.split() if len(w) > 5 and w.isalnum()]
        entities = list(set(words))[:3] # Take top 3 unique "entities"
        
        cypher_queries = []
        cypher_queries.append(f"MERGE (d:Document {{name: '{doc_node_name}', hash: '{text_hash}'}})")
        
        for i, entity in enumerate(entities):
            entity_name = f"Entity_{entity}_{text_hash}"
            cypher_queries.append(f"MERGE (e{i}:Entity {{name: '{entity_name}', original_text: '{entity}'}})")
            cypher_queries.append(f"MERGE (d)-[:CONTAINS]->(e{i})")
            
        # If no entities found, just link to a generic topic
        if not entities:
            topic = "General_Knowledge"
            cypher_queries.append(f"MERGE (t:Topic {{name: '{topic}'}})")
            cypher_queries.append(f"MERGE (d)-[:RELATES_TO]->(t)")

        return "\n".join(cypher_queries)

    async def evaluate_rag_context(self, query: str, context: List[str], persona: str = "Novice") -> str:
        """
        Evaluates if the retrieved context is sufficient to answer the query, based on the persona.
        """
        context_str = "\n".join([f"- {item}" for item in context])
        
        persona_instructions = {
            "Novice": "You are a helpful teacher explaining to a beginner. Focus on clarity and simplicity.",
            "Intermediate": "You are a knowledgeable peer. Focus on accuracy and providing relevant details.",
            "Expert": "You are a domain expert. Focus on technical depth, precision, and comprehensive coverage."
        }
        
        instruction = persona_instructions.get(persona, persona_instructions["Novice"])
        
        full_prompt = self.prompt_manager.get_template("rag_evaluation").format(
            instruction=instruction,
            persona=persona,
            query=query,
            context_str=context_str
        )
        
        # Try Real AI first
        if not self.is_mock:
            try:
                return await self.generate_content(full_prompt, temperature=0.0)
            except Exception as e:
                print(f"Real AI evaluation failed: {e}. Falling back to Mock.")
                # Fall through to mock logic

        # Mock Logic (Fallback)
        await asyncio.sleep(1)
        if context and len(context) > 0:
            return '{"score": 0.9, "reasoning": "Context contains relevant info.", "missing_info": "None"}'
        else:
            return '{"score": 0.1, "reasoning": "No context retrieved.", "missing_info": "All info"}'

    async def extract_search_keywords(self, query: str) -> List[str]:
        """
        Extracts key entities/keywords from a natural language query for Graph search.
        """
        if self.is_mock:
            return query.split() # Fallback

        prompt = self.prompt_manager.get_template("keyword_extraction").format(query=query)
        
        try:
            response = await self.generate_content(prompt, temperature=0.0)
            keywords = [k.strip() for k in response.split(',')]
            return keywords
        except Exception as e:
            print(f"Keyword extraction failed: {e}")
            return query.split() # Fallback



    async def calculate_faithfulness(self, question: str, answer: str, context: List[str]) -> float:
        """
        Calculates Faithfulness: Is the answer derived from the context?
        """
        context_str = "\n".join(context)
        prompt = self.prompt_manager.get_template("metric_faithfulness").format(
            context_str=context_str,
            answer=answer
        )
        try:
            response = await self.generate_content(prompt, temperature=0.0)
            return float(response.strip())
        except:
            return 0.5

    async def calculate_answer_relevance(self, question: str, answer: str) -> float:
        """
        Calculates Answer Relevance: Is the answer relevant to the question?
        """
        prompt = self.prompt_manager.get_template("metric_relevance").format(
            question=question,
            answer=answer
        )
        try:
            response = await self.generate_content(prompt, temperature=0.0)
            return float(response.strip())
        except:
            return 0.5

    async def calculate_context_recall(self, question: str, context: List[str], ground_truth: str) -> float:
        """
        Calculates Context Recall: Is all relevant information from Ground Truth present in the Context?
        """
        if not ground_truth:
            return 0.0
            
        context_str = "\n".join(context)
        prompt = self.prompt_manager.get_template("metric_recall").format(
            ground_truth=ground_truth,
            context_str=context_str
        )
        try:
            response = await self.generate_content(prompt, temperature=0.0)
            return float(response.strip())
        except:
            return 0.5


# ============================================================================
# Agentic AI: Function Calling Support
# ============================================================================

from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class ToolCall:
    """Represents a tool call made by the agent."""
    name: str
    arguments: Dict[str, Any]
    result: Any = None
    execution_time_ms: float = 0.0


@dataclass  
class AgentResponse:
    """Response from an agentic conversation turn."""
    answer: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    thinking: str = ""  # Chain of thought reasoning
    reasoning_trace: str = ""  # Summary of tools used and decisions made
    

class AgenticGeminiClient(GeminiClient):
    """
    Extended Gemini client with Agentic capabilities.
    Supports tool calling, planning, and multi-step reasoning.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_tool_iterations = 8  # Prevent infinite loops
    
    async def generate_with_tools(
        self, 
        query: str, 
        context: str = "",
        tool_registry = None
    ) -> AgentResponse:
        """
        Generate a response with autonomous tool calling.
        
        The agent can decide to call tools to gather more information
        before generating the final answer.
        """
        from core.tools import get_tool_registry, ToolRegistry
        
        registry = tool_registry or get_tool_registry()
        tools_schema = registry.get_gemini_tools_schema()
        
        tool_calls = []
        iteration = 0
        accumulated_context = context
        
        # System prompt for agentic behavior
        # System prompt for agentic behavior
        system_prompt = self.prompt_manager.get_template("agent_system")
        
        tools_description = "\n".join([
            f"- {t['name']}: {t['description']}" 
            for t in tools_schema
        ])
        
        while iteration < self.max_tool_iterations:
            iteration += 1
            
            # Build prompt
            prompt = system_prompt.format(
                tools_description=tools_description,
                context=accumulated_context or "No additional context available."
            )
            prompt += f"\n\nUser Question: {query}\n\nYour Response:"
            
            try:
                response = await self.generate_content(prompt, temperature=0.2)
            except Exception as e:
                return AgentResponse(
                    answer=f"Error generating response: {e}",
                    tool_calls=tool_calls
                )
            
            # Check if response is a tool call
            if self._is_tool_call(response):
                tool_call_info = self._parse_tool_call(response)
                if tool_call_info:
                    tool_name = tool_call_info.get("tool")
                    tool_args = tool_call_info.get("arguments", {})
                    
                    # Execute the tool
                    result = await registry.execute_tool(tool_name, **tool_args)
                    
                    tool_call = ToolCall(
                        name=tool_name,
                        arguments=tool_args,
                        result=result.data if result.success else result.error,
                        execution_time_ms=result.execution_time_ms
                    )
                    tool_calls.append(tool_call)
                    
                    # Add tool result to context for next iteration
                    accumulated_context += f"\n\n[Tool: {tool_name}] Result:\n{result.data if result.success else result.error}"
                    continue
            
            # Generate reasoning trace from tool calls
            reasoning_trace = ""
            if tool_calls:
                trace_parts = []
                for tc in tool_calls:
                    trace_parts.append(f"→ {tc.name}({', '.join(f'{k}={v}' for k,v in tc.arguments.items())})")
                reasoning_trace = "Reasoning: " + " ".join(trace_parts)
            
            # Not a tool call - this is the final answer
            return AgentResponse(
                answer=response,
                tool_calls=tool_calls,
                reasoning_trace=reasoning_trace
            )
        
        if len(accumulated_context) > 20000:
            accumulated_context = accumulated_context[-20000:] + "..."

        # Max iterations reached - generate summary
        trace_parts = [f"→ {tc.name}" for tc in tool_calls]
        reasoning_trace = "Reasoning (incomplete): " + " ".join(trace_parts) if trace_parts else ""
        
        # Try to synthesize an answer even if incomplete
        synthesized_answer = await self.generate_content(
            f"Synthesize immediate answer from context below for question: {query}\n\nContext:\n{accumulated_context[:5000]}", 
            temperature=0.2
        )
        
        return AgentResponse(
            answer=synthesized_answer,
            tool_calls=tool_calls,
            reasoning_trace=reasoning_trace
        )
    
    def _is_tool_call(self, response: str) -> bool:
        """Check if the response is a tool call request."""
        response = response.strip()
        # Handle markdown blocks first
        if "```" in response:
             if "```json" in response:
                 content = response.split("```json")[1].split("```")[0].strip()
                 if content.startswith("{") and '"tool":' in content:
                     return True
             # Try generic code block
             content = response.split("```")[1].split("```")[0].strip()
             if content.startswith("{") and '"tool":' in content:
                 return True

        if response.startswith("{") and '"tool":' in response:
            return True
        return False
    
    def _parse_tool_call(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse a tool call from the response."""
        import json
        try:
            # Clean up the response
            response = response.strip()
            # Handle markdown code blocks
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            data = json.loads(response)
            if "tool" in data:
                return data
        except json.JSONDecodeError:
            pass
        return None

