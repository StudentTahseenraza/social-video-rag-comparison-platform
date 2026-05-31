import asyncio
import json
from typing import Dict, Any, List, TypedDict, Annotated, Optional
from datetime import datetime
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END

# Fix: MemorySaver import - different in newer versions
try:
    from langgraph.checkpoint import MemorySaver
except ImportError:
    try:
        from langgraph.checkpoint.memory import MemorySaver
    except ImportError:
        # Fallback: create a simple memory saver
        class MemorySaver:
            def __init__(self):
                self.checkpoints = {}
            
            def save(self, config, state):
                thread_id = config.get("configurable", {}).get("thread_id", "default")
                self.checkpoints[thread_id] = state
            
            def load(self, config):
                thread_id = config.get("configurable", {}).get("thread_id", "default")
                return self.checkpoints.get(thread_id, {})

from app.services.vector_store import vector_store
from app.services.llm_service import llm_service
from app.utils.helpers import setup_logging

logger = setup_logging()

# Define state schema
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], lambda x, y: x + y]
    session_id: str
    video_a_id: str
    video_b_id: str
    retrieved_chunks: Optional[List[Dict[str, Any]]]
    current_question_type: Optional[str]
    analysis_steps: List[str]
    citations: List[Dict[str, Any]]

class VideoAnalyzerAgent:
    """LangGraph agent for complex video analysis and comparison"""
    
    def __init__(self):
        self.workflow = None
        self.app = None
        self.memory = MemorySaver()
        self.tools = self._create_tools()
        
    def _create_tools(self):
        """Create tools for the agent"""
        
        @tool
        async def calculate_engagement_rate(video_id: str, views: int, likes: int, comments: int) -> str:
            """Calculate engagement rate for a video"""
            if views and views > 0:
                engagement = ((likes or 0) + (comments or 0)) / views * 100
                return f"Engagement rate: {engagement:.2f}%"
            return "Engagement rate: Not enough data"
        
        @tool
        async def compare_metrics(metric_name: str, video_a_data: str, video_b_data: str) -> str:
            """Compare specific metrics between two videos"""
            return f"Comparing {metric_name}: Video A: {video_a_data}, Video B: {video_b_data}"
        
        @tool
        async def extract_hook(transcript: str, duration: int) -> str:
            """Extract the hook from first 5-10 seconds of transcript"""
            if not transcript:
                return "No transcript available to extract hook"
            words = transcript.split()[:50]
            hook = " ".join(words)
            return f"Hook (first 5-10 seconds): {hook}..."
        
        return [
            calculate_engagement_rate,
            compare_metrics,
            extract_hook
        ]
    
    def build_workflow(self):
        """Build the LangGraph workflow"""
        
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("agent", self._call_agent)
        workflow.add_node("retrieve", self._retrieve_context)
        workflow.add_node("analyze", self._analyze_comparison)
        workflow.add_node("format_response", self._format_response)
        
        workflow.set_entry_point("agent")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "retrieve": "retrieve",
                "analyze": "analyze",
                "end": END
            }
        )
        
        workflow.add_edge("retrieve", "agent")
        workflow.add_edge("analyze", "format_response")
        workflow.add_edge("format_response", END)
        
        # Compile with memory
        self.app = workflow.compile(checkpointer=self.memory)
        self.workflow = workflow
        
        logger.info("LangGraph agent workflow built successfully")
        return self.app
    
    async def _call_agent(self, state: AgentState) -> Dict[str, Any]:
        """Call the LLM agent to decide next action"""
        
        messages = state["messages"]
        last_message = messages[-1] if messages else None
        
        # Build system prompt
        system_prompt = self._build_agent_prompt(state)
        
        context = ""
        if state.get("retrieved_chunks"):
            context = "\n\nRetrieved Context:\n" + "\n".join([
                f"[{c['label']}]: {c['text'][:200]}..." 
                for c in state["retrieved_chunks"][:3]
            ])
        
        agent_prompt = f"""{system_prompt}

{context}

Current question: {last_message.content if last_message else "Analyze videos"}

Provide analysis based on the available context."""
        
        try:
            response = await llm_service.llm.ainvoke([HumanMessage(content=agent_prompt)])
            return {
                "messages": [response],
                "analysis_steps": state.get("analysis_steps", []) + ["Agent decision made"]
            }
        except Exception as e:
            logger.error(f"Agent call failed: {e}")
            return {
                "messages": [AIMessage(content="I'll analyze the videos based on available data.")],
                "analysis_steps": state.get("analysis_steps", []) + ["Fallback response"]
            }
    
    def _should_continue(self, state: AgentState) -> str:
        """Determine next step"""
        last_message = state["messages"][-1] if state["messages"] else None
        if not last_message:
            return "end"
        
        content = last_message.content.lower()
        
        if "retrieve" in content or "search" in content:
            return "retrieve"
        if "compare" in content or "analyze" in content or "why" in content:
            return "analyze"
        
        return "end"
    
    async def _retrieve_context(self, state: AgentState) -> Dict[str, Any]:
        """Retrieve relevant context from vector store"""
        
        last_message = state["messages"][-1]
        query = last_message.content if last_message else ""
        
        try:
            chunks = await vector_store.retrieve_relevant_chunks(
                query=query,
                session_id=state["session_id"],
                video_a_id=state["video_a_id"],
                video_b_id=state["video_b_id"],
                top_k=5
            )
            return {
                "retrieved_chunks": chunks,
                "analysis_steps": state.get("analysis_steps", []) + [f"Retrieved {len(chunks)} relevant chunks"]
            }
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return {"retrieved_chunks": [], "analysis_steps": state.get("analysis_steps", []) + ["Retrieval failed"]}
    
    async def _analyze_comparison(self, state: AgentState) -> Dict[str, Any]:
        """Perform deep analysis comparing videos"""
        
        chunks = state.get("retrieved_chunks", [])
        
        video_a_chunks = [c for c in chunks if c.get('label') == 'A']
        video_b_chunks = [c for c in chunks if c.get('label') == 'B']
        
        analysis_prompt = f"""
        Analyze and compare the two videos.
        
        Video A content: {self._format_chunks(video_a_chunks)}
        Video B content: {self._format_chunks(video_b_chunks)}
        
        Provide analysis covering engagement, content strategy, and key differences.
        """
        
        try:
            response = await llm_service.llm.ainvoke([HumanMessage(content=analysis_prompt)])
            return {
                "messages": [AIMessage(content=response.content)],
                "analysis_steps": state.get("analysis_steps", []) + ["Comparative analysis completed"]
            }
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return {
                "messages": [AIMessage(content="Analysis completed based on available video data.")],
                "analysis_steps": state.get("analysis_steps", []) + ["Fallback analysis"]
            }
    
    async def _format_response(self, state: AgentState) -> Dict[str, Any]:
        """Format final response with citations"""
        
        last_message = state["messages"][-1] if state["messages"] else None
        chunks = state.get("retrieved_chunks", [])
        
        citations = []
        for chunk in chunks[:3]:
            citations.append({
                "source": f"Video {chunk.get('label', 'Unknown')}",
                "text_preview": chunk.get('text', '')[:100],
                "relevance": chunk.get('relevance_score', 1.0)
            })
        
        return {
            "citations": citations,
            "analysis_steps": state.get("analysis_steps", []) + ["Response formatted"],
            "messages": [AIMessage(content=last_message.content if last_message else "Analysis complete")]
        }
    
    def _build_agent_prompt(self, state: AgentState) -> str:
        return f"""You are a Video Analysis Agent comparing Video A and Video B.

Session: {state['session_id']}

Always cite sources (Video A or Video B) and be specific with metrics."""
    
    def _format_chunks(self, chunks: List[Dict[str, Any]]) -> str:
        if not chunks:
            return "No content available"
        return "\n".join([f"- {c['text'][:150]}..." for c in chunks])
    
    async def process_question(
        self, 
        session_id: str, 
        question: str, 
        video_a_id: str, 
        video_b_id: str
    ):
        """Process a question through the agent workflow"""
        
        initial_state = AgentState(
            messages=[HumanMessage(content=question)],
            session_id=session_id,
            video_a_id=video_a_id,
            video_b_id=video_b_id,
            retrieved_chunks=None,
            current_question_type=None,
            analysis_steps=["Initialized"],
            citations=[]
        )
        
        config = {"configurable": {"thread_id": session_id}}
        
        try:
            final_state = None
            async for event in self.app.astream(initial_state, config):
                for node_name, node_state in event.items():
                    final_state = node_state
                    
                    if node_name == "format_response":
                        yield {
                            "type": "final",
                            "content": node_state["messages"][-1].content if node_state.get("messages") else "",
                            "citations": node_state.get("citations", []),
                            "steps": node_state.get("analysis_steps", [])
                        }
        except Exception as e:
            logger.error(f"Agent processing error: {str(e)}")
            yield {"type": "error", "error": str(e)}

video_analyzer_agent = VideoAnalyzerAgent()