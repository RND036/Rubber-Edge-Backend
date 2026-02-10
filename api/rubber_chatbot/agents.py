import os
import json
from typing import Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv
from django.core.cache import cache

from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferWindowMemory
from langchain.agents import create_tool_calling_agent, AgentExecutor

load_dotenv()


def _condense_results(results: list) -> str:
    """Condense search results to reduce token usage"""
    if not results:
        return json.dumps({"message": "No results found"})
    
    condensed = []
    for r in results[:3]:  # Max 3 results
        condensed.append({
            "title": r.get("title", "")[:80],
            "content": r.get("content", "")[:200],
            "url": r.get("url", "")
        })
    
    # Get Tavily's answer if available
    answer = results[0].get("answer", "") if results else ""
    
    return json.dumps({
        "answer": answer[:300] if answer else "",
        "sources": condensed
    }, separators=(',', ':'))  # Compact JSON


@tool("rubber_general_search")
def rubber_general_search(query: str) -> str:
    """Search Sri Lankan rubber cultivation, processing, markets, RRISL info, and general rubber farming questions."""
    try:
        tavily = TavilySearchResults(
            max_results=3,
            include_answer=True,
            include_domains=[
                "rrisl.gov.lk", "gov.lk", "anrpc.org", "srilankabusiness.com",
                "ncpcsrilanka.org", "tradingeconomics.com", "dailynews.lk",
                "sundaytimes.lk", "ft.lk"
            ], 
            tavily_api_key=os.getenv("TAVILY_API_KEY")
        )
        results = tavily.invoke({"query": f"Sri Lanka rubber {query}"})
        return _condense_results(results)
    except Exception as e:
        return f"Search error: {str(e)}"


@tool("rubber_disease_search")
def rubber_disease_search(query: str) -> str:
    """Search rubber diseases, pests, and plant health issues from RRISL and government agricultural sources."""
    try:
        tavily = TavilySearchResults(
            max_results=3,
            include_answer=True,
            include_domains=[
                "rrisl.gov.lk", "gov.lk", "ncpcsrilanka.org", "doa.gov.lk",
                "agrariandept.gov.lk"
            ], 
            tavily_api_key=os.getenv("TAVILY_API_KEY")
        )
        results = tavily.invoke({"query": f"Sri Lanka rubber disease pest RRISL {query}"})
        return _condense_results(results)
    except Exception as e:
        return f"Disease search error: {str(e)}"


@tool("rubber_medicine_location_search")
def rubber_medicine_location_search(query: str) -> str:
    """Find locations and dealers for rubber agrochemicals, fungicides, pesticides, and farming inputs in Sri Lanka."""
    try:
        tavily = TavilySearchResults(
            max_results=4,
            include_answer=True,
            include_domains=[
                "agrariandept.gov.lk", "doa.gov.lk", "yellowpages.lk", 
                "gov.lk", "rrisl.gov.lk", "finder.lk", "yamu.lk"
            ], 
            tavily_api_key=os.getenv("TAVILY_API_KEY")
        )
        
        location_query = f"Sri Lanka rubber agrochemical fungicide pesticide dealer shop location {query}"
        results = tavily.invoke({"query": location_query})
        return _condense_results(results)
    except Exception as e:
        return f"Medicine location search error: {str(e)}"


@tool("rubber_price_search")
def rubber_price_search(query: str) -> str:
    """Search current rubber prices, market rates, RSS prices, latex prices, and rubber market trends in Sri Lanka.
    Use this when users ask about 'price', 'rate', 'how much', 'market', 'RSS', 'latex price'."""
    try:
        tavily = TavilySearchResults(
            max_results=3,
            include_answer=True,
            include_domains=[
                "tradingeconomics.com", "ft.lk", "dailynews.lk", 
                "sundaytimes.lk", "cbsl.gov.lk", "rrisl.gov.lk",
                "investing.com", "srilankabusiness.com"
            ], 
            tavily_api_key=os.getenv("TAVILY_API_KEY")
        )
        
        price_query = f"Sri Lanka rubber price rate RSS latex market today latest {query}"
        results = tavily.invoke({"query": price_query})
        
        # ✅ FIXED: Return simple string instead of complex JSON to prevent agent loops
        if results and results[0].get("answer"):
            answer = results[0]["answer"][:400]  # Limit to 400 chars
            return f"Latest rubber prices: {answer}\n\nSources: {', '.join([r.get('url', '') for r in results[:2]])}"
        else:
            prices = []
            for r in results[:3]:
                if r.get("content"):
                    prices.append(r["content"][:150])
            return f"Current rubber prices (summary):\n" + "\n".join(prices[:3]) or "Could not find current prices. Check RRISL website."
            
    except Exception as e:
        return f"Price search error: {str(e)}"


SYSTEM_PROMPT = """You are Rubby AI - A specialized Sri Lankan Rubber Farming Expert Assistant 🌿🇱🇰

EXPERTISE SCOPE:
• Rubber (Hevea brasiliensis) cultivation techniques
• Disease and pest identification & management
• Agrochemical recommendations and dealer locations
• Rubber prices, market trends, and economics
• RRISL (Rubber Research Institute of Sri Lanka) guidelines
• Processing, tapping, and best practices

🚀 IMPORTANT PRICE PROTOCOL (to prevent agent loops):
1. When users ask about prices, rates, or market info:
   - Use rubber_price_search tool EXACTLY ONCE
   - Extract key prices (RSS1, RSS2, RSS3, RSS4, RSS5, Latex Crepe, etc.)
   - Answer IMMEDIATELY after getting results
   - DO NOT call the tool multiple times
2. Always say: "Prices fluctuate daily. Check with local buyers for current rates."

DISEASE & TREATMENT PROTOCOL:
1. Identify the disease/pest clearly
2. Recommend cultural/sanitation methods FIRST
3. Suggest resistant clones when applicable
4. Provide GENERAL chemical categories only
5. ALWAYS include: "⚠️ This is educational information only. Please consult RRISL or your local agricultural officer."

LOCATION & MEDICINE PROTOCOL:
1. Use rubber_medicine_location_search tool ONCE for location queries
2. Always remind: "Verify dealer licensing with local Agrarian Service Center"

RESPONSE GUIDELINES:
• Be conversational and friendly (use "Ayubowan!" for greetings)
• Provide practical, actionable advice for Sri Lankan context
• Keep responses concise (under 300 words)
• Use local units (perches, liters, kg)
• Reference Sri Lankan districts when relevant

NON-RUBBER QUERIES:
"I specialize only in Sri Lankan rubber farming. For other topics, consult relevant experts."

CRITICAL DISCLAIMER:
ALWAYS end with:
"⚠️ Rubby AI can make mistakes. Always verify with RRISL, agricultural officers, or trusted experts."

Current Date & Time: {current_datetime}
"""


class RubberAgent:
    def __init__(self):
        self.llm = ChatGroq(
            model="openai/gpt-oss-120b",  
            temperature=0.3,  # Lowered for more consistent behavior
            groq_api_key=os.getenv("GROQ_API_KEY")
        )
        
        self.tools = [
            rubber_general_search, 
            rubber_disease_search, 
            rubber_medicine_location_search,
            rubber_price_search
        ]
    
    def query(self, message: str, session_id: str) -> Dict[str, Any]:
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", SYSTEM_PROMPT.format(
                    current_datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )),
                MessagesPlaceholder("chat_history"), 
                ("user", "{input}"), 
                MessagesPlaceholder("agent_scratchpad")
            ])
            
            # Window memory - keeps only last 3 exchanges
            memory_key = f"rubber_memory_{session_id}"
            memory = ConversationBufferWindowMemory(
                memory_key="chat_history", 
                return_messages=True,
                k=3,  # 3 exchanges (6 messages)
                max_token_limit=800
            )
            
            cached = cache.get(memory_key)
            if cached:
                memory.chat_memory.messages = cached[-6:]  # Last 6 messages max
            
            # ✅ FIXED: Increased iterations + early stopping
            agent = create_tool_calling_agent(self.llm, self.tools, prompt)
            executor = AgentExecutor(
                agent=agent, 
                tools=self.tools, 
                memory=memory, 
                verbose=False,
                max_iterations=12,  # ✅ INCREASED from 3 to 12
                max_execution_time=35,  # Increased timeout
                handle_parsing_errors=True,
                early_stopping_method="generate"  # ✅ Force final answer instead of error
            )
            
            # Execute query
            result = executor.invoke({"input": message})
            
            # Cache updated memory (limit size)
            cache.set(memory_key, memory.chat_memory.messages[-6:], 3600)
            
            # Extract tool usage
            tools_used = []
            intermediate_steps = result.get("intermediate_steps", [])
            if intermediate_steps:
                tools_used = [step[0].tool for step in intermediate_steps if hasattr(step[0], 'tool')]
            
            # Format response
            response_text = result.get("output", "I apologize, but I need more information to help you properly.")
            
            # Ensure disclaimer
            if "⚠️ Rubby AI can make mistakes" not in response_text:
                response_text += "\n\n⚠️ Rubby AI can make mistakes. Always verify with RRISL, agricultural officers, or trusted experts."
            
            return {
                "response": response_text,
                "session_id": session_id,
                "tools_used": tools_used,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_str = str(e).lower()
            
            # Handle 413 Payload Too Large
            if any(x in error_str for x in ["413", "payload too large", "request too large"]):
                self.clear_session(session_id)
                return {
                    "response": (
                        "⚠️ Conversation history was too long. I've cleared it.\n\n"
                        "Please ask your question again for fresh results.\n\n"
                        "💡 Tip: Ask specific questions for best performance."
                    ),
                    "session_id": session_id,
                    "tools_used": [],
                    "timestamp": datetime.now().isoformat(),
                    "error": True,
                    "error_type": "payload_too_large"
                }
            
            # Max iterations handled by early_stopping_method="generate"
            error_response = (
                f"Sorry, I had trouble processing that. Please try rephrasing or ask a simpler question.\n\n"
                f"Error: {str(e)[:100]}\n\n"
                "⚠️ Rubby AI can make mistakes. Always verify with RRISL experts."
            )
            return {
                "response": error_response,
                "session_id": session_id,
                "tools_used": [],
                "timestamp": datetime.now().isoformat(),
                "error": True,
                "error_type": type(e).__name__
            }
    
    def clear_session(self, session_id: str) -> bool:
        """Clear conversation memory for a session"""
        try:
            memory_key = f"rubber_memory_{session_id}"
            cache.delete(memory_key)
            return True
        except Exception:
            return False


# Global agent instance
agent = RubberAgent()


def query_rubber_agent(message: str, session_id: str = "default") -> Dict:
    """Main entry point for querying the Rubber AI agent"""
    return agent.query(message, session_id)


def clear_rubber_session(session_id: str = "default") -> bool:
    """Clear conversation history for a session"""
    return agent.clear_session(session_id)
