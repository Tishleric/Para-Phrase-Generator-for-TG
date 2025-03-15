# src/agents/football_agent.py
# Football score detection and processing agent
"""
This module defines the FootballAgent class, which is responsible for
detecting football score references in messages and providing match context.
"""

import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from ..sdk_imports import function_tool, WebSearchTool
from .base_agent import BaseAgent
from ..config import get_agent_model

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FootballAgent(BaseAgent):
    """
    Football score detection and processing agent with web search capabilities.
    
    This agent is responsible for detecting references to football scores, 
    live commentary, and player mentions in messages, enriching them with
    context from web searches, and providing detailed summaries.
    
    Attributes:
        name (str): The name of the agent
        agent (Agent): The OpenAI Agent instance
    """
    
    def __init__(self):
        """
        Initialize a FootballAgent instance with web search capabilities.
        """
        instructions = """
        You are a specialized agent for processing football (soccer) references in messages.
        
        Your tasks are:
        1. Detect different types of football references in chat messages:
           - Explicit match scores (e.g., "Barcelona 3-1 Real Madrid")
           - Team mentions (e.g., "Liverpool is playing well today")
           - Player excitement (e.g., "ENZOOOOO" or "HAALAND SCORES AGAIN!")
           - Live commentary phrases (e.g., "what a goal!", "red card!", "great save!")
           - General match discussion (e.g., "watching the game", "halftime now")
        
        2. Use web search strategically to find the most relevant context:
           - For identified teams, search for their most recent or ongoing matches
           - For player mentions, search for their recent in-game actions
           - For live commentary, determine which match is likely being discussed
           - Prioritize results from the last 24 hours as messages likely refer to recent events
        
        3. Provide rich, relevant context in your summaries:
           - Current score and match status for ongoing games
           - Recent goals or key events that explain excited reactions
           - League/tournament context (standings, importance of the match)
           - Only include information directly relevant to the chat messages
        
        Always format your summaries concisely so they can be easily integrated
        into the overall conversation summary.
        """
        
        # Define function tools
        tools = [
            self._extract_football_references,
            self._analyze_match_information,
            self._detect_live_commentary,
            self._extract_teams_and_players,
            WebSearchTool()  # Add web search capability
        ]
        
        super().__init__(
            name="Football Score Agent",
            instructions=instructions,
            model=get_agent_model("football"),
            tools=tools
        )
        
        # Initialize common football teams dictionary for faster lookups
        self.teams_dict = {
            # English Premier League
            "arsenal": "Arsenal FC", "chelsea": "Chelsea FC", "liverpool": "Liverpool FC",
            "manchester united": "Manchester United", "man utd": "Manchester United", "man u": "Manchester United",
            "manchester city": "Manchester City", "man city": "Manchester City", 
            "tottenham": "Tottenham Hotspur", "spurs": "Tottenham Hotspur",
            "newcastle": "Newcastle United", "wolves": "Wolverhampton Wanderers",
            "villa": "Aston Villa", "aston villa": "Aston Villa",
            "everton": "Everton FC", "leeds": "Leeds United",
            "brighton": "Brighton & Hove Albion", "leicester": "Leicester City",
            "west ham": "West Ham United", "brentford": "Brentford FC",
            
            # Spanish La Liga
            "barcelona": "FC Barcelona", "barca": "FC Barcelona", 
            "real madrid": "Real Madrid", "madrid": "Real Madrid",
            "atletico": "Atlético Madrid", "atleti": "Atlético Madrid",
            "sevilla": "Sevilla FC", "valencia": "Valencia CF",
            
            # Italian Serie A
            "juventus": "Juventus FC", "juve": "Juventus FC",
            "milan": "AC Milan", "inter": "Inter Milan",
            "napoli": "SSC Napoli", "roma": "AS Roma",
            
            # German Bundesliga
            "bayern": "Bayern Munich", "dortmund": "Borussia Dortmund", "bvb": "Borussia Dortmund",
            "leipzig": "RB Leipzig", "leverkusen": "Bayer Leverkusen",
            
            # French Ligue 1
            "psg": "Paris Saint-Germain", "paris": "Paris Saint-Germain",
            "marseille": "Olympique Marseille", "lyon": "Olympique Lyonnais"
        }
        
        # Initialize common player name dictionary
        self.players_dict = {
            # Popular players for quick matching
            "messi": "Lionel Messi", "leo": "Lionel Messi",
            "ronaldo": "Cristiano Ronaldo", "cr7": "Cristiano Ronaldo",
            "mbappe": "Kylian Mbappé", "kylian": "Kylian Mbappé",
            "haaland": "Erling Haaland", "erling": "Erling Haaland",
            "salah": "Mohamed Salah", "mo salah": "Mohamed Salah",
            "benzema": "Karim Benzema", "karim": "Karim Benzema",
            "de bruyne": "Kevin De Bruyne", "kdb": "Kevin De Bruyne",
            "neymar": "Neymar Jr", "ney": "Neymar Jr",
            "lewandowski": "Robert Lewandowski", "lewy": "Robert Lewandowski",
            "kane": "Harry Kane", "son": "Son Heung-min",
            "enzo": "Enzo Fernández", "fernandez": "Enzo Fernández",
            "vinicius": "Vinícius Júnior", "vini": "Vinícius Júnior"
        }
        
        logger.info("Initialized Football Score Agent with web search capabilities")
    
    @function_tool
    def _extract_football_references(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract football match references from text.
        
        Args:
            text (str): Text to extract football references from
            
        Returns:
            List[Dict[str, Any]]: List of extracted match references
        """
        if not text:
            return []
        
        references = []
        
        # Pattern for score-like references (e.g., "2-1", "3:2")
        score_pattern = r'\b(\d{1,2})[\-\:](\d{1,2})\b'
        score_matches = re.finditer(score_pattern, text)
        
        # Pattern for team names followed by scores
        team_score_pattern = r'([A-Za-z\s]+)\s+(\d{1,2})[\-\:](\d{1,2})\s+([A-Za-z\s]+)'
        team_score_matches = re.finditer(team_score_pattern, text)
        
        # Process score-only matches
        for match in score_matches:
            score_home = match.group(1)
            score_away = match.group(2)
            
            # Check if this is already part of a team-score match
            is_part_of_team_match = False
            for team_match in re.finditer(team_score_pattern, text):
                if match.start() >= team_match.start() and match.end() <= team_match.end():
                    is_part_of_team_match = True
                    break
            
            if not is_part_of_team_match:
                references.append({
                    "type": "score_only",
                    "score_home": int(score_home),
                    "score_away": int(score_away),
                    "match_string": match.group(0),
                    "span": (match.start(), match.end())
                })
        
        # Process team-score matches
        for match in team_score_matches:
            team_home = match.group(1).strip()
            score_home = match.group(2)
            score_away = match.group(3)
            team_away = match.group(4).strip()
            
            references.append({
                "type": "team_score",
                "team_home": team_home,
                "score_home": int(score_home),
                "score_away": int(score_away),
                "team_away": team_away,
                "match_string": match.group(0),
                "span": (match.start(), match.end())
            })
        
        # Look for team names in our dictionary
        for alias, full_name in self.teams_dict.items():
            # Create a pattern that matches the team name as a whole word
            pattern = r'\b' + re.escape(alias) + r'\b'
            for match in re.finditer(pattern, text.lower()):
                # Check if this team name is already part of another reference
                is_part_of_other_ref = False
                for ref in references:
                    span = ref["span"]
                    if match.start() >= span[0] and match.end() <= span[1]:
                        is_part_of_other_ref = True
                        break
                
                if not is_part_of_other_ref:
                    references.append({
                        "type": "team_only",
                        "team": full_name,
                        "original_text": text[match.start():match.end()],
                        "span": (match.start(), match.end())
                    })
        
        return references
    
    @function_tool
    def _detect_live_commentary(self, text: str) -> Dict[str, Any]:
        """
        Detect patterns of live football commentary in messages.
        
        Args:
            text (str): Text to analyze for live commentary
            
        Returns:
            Dict[str, Any]: Analysis of live commentary indicators
        """
        text_lower = text.lower()
        
        # Common phrases in live football commentary
        goal_phrases = [
            "goal", "scores", "what a goal", "what a shot", "what a finish",
            "amazing goal", "beautiful goal", "great finish", "in the net",
            "back of the net", "golazo", "scored", "header", "volley"
        ]
        
        card_phrases = [
            "red card", "yellow card", "sent off", "booking", "carded",
            "suspended", "ejected", "dismissed", "straight red", "second yellow"
        ]
        
        save_phrases = [
            "save", "great save", "what a save", "keeper", "goalkeeper",
            "denied", "stopped", "blocked", "parried", "deflected"
        ]
        
        miss_phrases = [
            "missed", "miss", "off target", "wide", "over the bar",
            "hit the post", "hit the bar", "crossbar", "woodwork"
        ]
        
        game_status_phrases = [
            "kickoff", "kick off", "halftime", "half time", "full time",
            "injury time", "extra time", "overtime", "penalties",
            "starting lineup", "substitution", "sub", "bench", "var",
            "review", "free kick", "penalty", "corner", "offside",
            "match day", "gameday", "watching the game", "watching the match"
        ]
        
        # Check for phrases
        commentary_types = {
            "goal": any(phrase in text_lower for phrase in goal_phrases),
            "card": any(phrase in text_lower for phrase in card_phrases),
            "save": any(phrase in text_lower for phrase in save_phrases),
            "miss": any(phrase in text_lower for phrase in miss_phrases),
            "status": any(phrase in text_lower for phrase in game_status_phrases)
        }
        
        # Look for all-caps excitement (common in live commentary)
        # A message with 30% or more characters in uppercase indicates excitement
        if len(text) > 0:
            uppercase_ratio = sum(1 for c in text if c.isupper()) / len(text)
            excitement_level = "high" if uppercase_ratio > 0.5 else "medium" if uppercase_ratio > 0.3 else "low"
        else:
            excitement_level = "none"
            
        # Check for match minutes (e.g., "45'", "90+3'")
        minute_pattern = r'(\d{1,3})(?:\+\d{1,2})?\''
        minute_matches = re.findall(minute_pattern, text)
        has_match_minutes = len(minute_matches) > 0
        
        detected_commentary = any(commentary_types.values()) or excitement_level in ["high", "medium"] or has_match_minutes
        
        return {
            "is_live_commentary": detected_commentary,
            "commentary_types": commentary_types,
            "excitement_level": excitement_level,
            "has_match_minutes": has_match_minutes,
            "match_minutes": minute_matches if has_match_minutes else []
        }
    
    @function_tool
    def _extract_teams_and_players(self, text: str) -> Dict[str, Any]:
        """
        Extract mentions of teams and players, including excited references.
        
        Args:
            text (str): Text to analyze for team and player mentions
            
        Returns:
            Dict[str, Any]: Extracted team and player references
        """
        # First, extract standard team mentions using the teams dictionary
        teams = []
        for alias, full_name in self.teams_dict.items():
            pattern = r'\b' + re.escape(alias) + r'\b'
            if re.search(pattern, text.lower()):
                teams.append({
                    "alias": alias,
                    "full_name": full_name,
                    "confidence": "high"
                })
        
        # Extract standard player mentions using the players dictionary
        players = []
        for alias, full_name in self.players_dict.items():
            pattern = r'\b' + re.escape(alias) + r'\b'
            if re.search(pattern, text.lower()):
                players.append({
                    "alias": alias,
                    "full_name": full_name,
                    "original_text": alias,
                    "confidence": "high"
                })
        
        # Look for excited player mentions (usually all caps with repeated characters)
        excited_pattern = r'([A-Z]{2,}[A-Z]+)'
        excited_matches = re.findall(excited_pattern, text)
        
        for match in excited_matches:
            # Skip if too short
            if len(match) < 3:
                continue
                
            # Normalize the name (remove repeated characters)
            normalized = re.sub(r'(.)\1+', r'\1', match).lower()
            
            # Check if this normalized name matches a known player
            matched_player = None
            for alias, full_name in self.players_dict.items():
                # Check if the normalized excited text matches a player alias
                if alias in normalized or normalized in alias:
                    matched_player = {
                        "alias": alias,
                        "full_name": full_name,
                        "original_text": match,
                        "normalized": normalized,
                        "confidence": "medium"
                    }
                    break
            
            # If no match found but it looks like a name, add it as unknown player
            if matched_player is None and len(normalized) >= 3:
                matched_player = {
                    "alias": normalized,
                    "full_name": None,  # Unknown full name
                    "original_text": match,
                    "normalized": normalized,
                    "confidence": "low"
                }
            
            if matched_player is not None:
                # Check if we already have this player in the list
                if not any(p["alias"] == matched_player["alias"] for p in players):
                    players.append(matched_player)
        
        return {
            "teams": teams,
            "players": players,
            "has_teams": len(teams) > 0,
            "has_players": len(players) > 0
        }
    
    @function_tool
    def _analyze_match_information(self, match_reference: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze football match information from a reference.
        
        Args:
            match_reference (Dict[str, Any]): Football match reference
            
        Returns:
            Dict[str, Any]: Analysis of the match information
        """
        ref_type = match_reference["type"]
        
        if ref_type == "team_score":
            team_home = match_reference["team_home"]
            team_away = match_reference["team_away"]
            score_home = match_reference["score_home"]
            score_away = match_reference["score_away"]
            
            # Try to standardize team names for better search results
            team_home_std = None
            team_away_std = None
            
            # Look for standardized team names from our dictionary
            for alias, full_name in self.teams_dict.items():
                if alias.lower() in team_home.lower() or team_home.lower() in alias:
                    team_home_std = full_name
                if alias.lower() in team_away.lower() or team_away.lower() in alias:
                    team_away_std = full_name
                    
            # Use standardized names if found, otherwise use original
            team_home_final = team_home_std or team_home
            team_away_final = team_away_std or team_away
            
            # Determine the winner
            if score_home > score_away:
                result = f"{team_home_final} won"
            elif score_home < score_away:
                result = f"{team_away_final} won"
            else:
                result = "Draw"
            
            # Create search query suggestions for better web search
            current_date = datetime.now().strftime("%B %d, %Y")
            search_queries = [
                f"{team_home_final} vs {team_away_final} {score_home}-{score_away} {current_date}",
                f"{team_home_final} {team_away_final} {score_home}-{score_away} match result",
                f"{team_home_final} {team_away_final} recent match score"
            ]
            
            return {
                "match_type": "identified",
                "team_home": team_home_final,
                "team_away": team_away_final,
                "score_home": score_home,
                "score_away": score_away,
                "result": result,
                "confidence": "high",
                "search_queries": search_queries
            }
        
        elif ref_type == "score_only":
            score_home = match_reference["score_home"]
            score_away = match_reference["score_away"]
            
            # For score-only references, we need to rely on other context
            today = datetime.now().strftime("%B %d, %Y")
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%B %d, %Y")
            
            search_queries = [
                f"football match {score_home}-{score_away} {today}",
                f"soccer result {score_home}-{score_away} {yesterday}",
                f"recent football match ending {score_home}-{score_away}"
            ]
            
            return {
                "match_type": "partial",
                "score_home": score_home,
                "score_away": score_away,
                "result": "Unknown teams",
                "confidence": "low",
                "search_queries": search_queries
            }
        
        elif ref_type == "team_only":
            team = match_reference["team"]
            
            # Create search query suggestions
            today = datetime.now().strftime("%B %d, %Y")
            search_queries = [
                f"{team} match today {today}",
                f"{team} latest football result",
                f"{team} recent match score",
                f"{team} next match"
            ]
            
            return {
                "match_type": "team_mention",
                "team": team,
                "recent_form": "Unknown",
                "confidence": "medium",
                "search_queries": search_queries
            }
        
        return {
            "match_type": "unknown",
            "confidence": "none",
            "search_queries": []
        }
    
    def _enhance_with_user_preferences(self, user_id: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance football analysis with user preferences.
        
        Args:
            user_id (str): The user ID to get preferences for
            analysis (Dict[str, Any]): The current analysis
            
        Returns:
            Dict[str, Any]: Enhanced analysis with user preferences
        """
        try:
            # Initialize a vector store client
            from langchain_community.vectorstores import FAISS
            from langchain_community.embeddings import OpenAIEmbeddings
            from langchain.schema import Document
            import os
            import json
            
            # Make a copy of the original analysis
            enhanced = analysis.copy()
            
            # Vector store path
            vector_store_dir = os.path.join(os.getcwd(), "data", "vector_stores", "user_preferences")
            
            # If the directory doesn't exist, create it
            os.makedirs(vector_store_dir, exist_ok=True)
            
            # User-specific vector store path
            user_vs_path = os.path.join(vector_store_dir, f"user_{user_id}")
            
            # Initialize embeddings model
            embeddings = OpenAIEmbeddings()
            
            # Check if we have existing preferences
            if os.path.exists(user_vs_path):
                try:
                    # Load the existing vector store
                    vector_store = FAISS.load_local(user_vs_path, embeddings)
                    logger.info(f"Loaded vector store for user {user_id}")
                    
                    # Create a query from the match details
                    teams = []
                    if "home_team" in analysis and "away_team" in analysis:
                        teams = [analysis["home_team"], analysis["away_team"]]
                    
                    league = analysis.get("league", "")
                    
                    # Construct query
                    query = f"Football match {' vs '.join(teams)}"
                    if league:
                        query += f" in {league}"
                    
                    # Add any major events
                    if "key_events" in analysis:
                        events = analysis["key_events"]
                        if isinstance(events, list) and events:
                            query += f" with events: {', '.join(events[:3])}"
                    
                    # Query the vector store
                    docs = vector_store.similarity_search(query, k=3)
                    
                    if docs:
                        # Extract preferences from the documents
                        preferences = []
                        for doc in docs:
                            try:
                                pref_data = json.loads(doc.page_content)
                                preferences.append(pref_data)
                            except json.JSONDecodeError:
                                # If not JSON, just use the text
                                preferences.append({"text": doc.page_content})
                        
                        # Add preferences to the enhanced analysis
                        enhanced["user_preferences"] = preferences
                        
                        # Apply preferences to the analysis
                        favorite_team = None
                        for pref in preferences:
                            if "favorite_team" in pref:
                                favorite_team = pref["favorite_team"]
                                break
                        
                        # If we found a favorite team, highlight that team's stats
                        if favorite_team:
                            if "home_team" in analysis and analysis["home_team"] == favorite_team:
                                enhanced["is_favorite_team_home"] = True
                            elif "away_team" in analysis and analysis["away_team"] == favorite_team:
                                enhanced["is_favorite_team_away"] = True
                            
                            # Add a note about the favorite team
                            enhanced["favorite_team_note"] = f"This match features {favorite_team}, one of your favorite teams."
                except Exception as e:
                    logger.error(f"Error loading vector store: {str(e)}")
            
            # Simulate saving a new preference (in a real system, this would be
            # based on user feedback after viewing the match details)
            self._save_user_preference(user_id, analysis)
            
            return enhanced
            
        except ImportError as e:
            logger.warning(f"Vector store dependencies not available: {str(e)}")
            # Return the original analysis with a note
            analysis["user_preferences_error"] = "Vector store integration not available"
            return analysis
        except Exception as e:
            logger.error(f"Error enhancing with user preferences: {str(e)}")
            # Return the original analysis with the error
            analysis["user_preferences_error"] = str(e)
            return analysis
    
    def _save_user_preference(self, user_id: str, analysis: Dict[str, Any]) -> None:
        """
        Save a user preference to the vector store.
        
        Args:
            user_id (str): The user ID to save preferences for
            analysis (Dict[str, Any]): The analysis data to extract preferences from
        """
        try:
            # Import vector store libraries
            from langchain_community.vectorstores import FAISS
            from langchain_community.embeddings import OpenAIEmbeddings
            from langchain.schema import Document
            import os
            import json
            import time
            
            # Vector store path
            vector_store_dir = os.path.join(os.getcwd(), "data", "vector_stores", "user_preferences")
            
            # If the directory doesn't exist, create it
            os.makedirs(vector_store_dir, exist_ok=True)
            
            # User-specific vector store path
            user_vs_path = os.path.join(vector_store_dir, f"user_{user_id}")
            
            # Initialize embeddings model
            embeddings = OpenAIEmbeddings()
            
            # Extract teams
            home_team = analysis.get("home_team", "")
            away_team = analysis.get("away_team", "")
            league = analysis.get("league", "")
            score = analysis.get("score", "")
            
            # Create a preference document
            # In a real system, this would be based on actual user interaction
            # For this implementation, we'll just use the viewed match as a preference
            preference = {
                "timestamp": time.time(),
                "match": f"{home_team} vs {away_team}",
                "league": league,
                "score": score,
                "viewed": True
            }
            
            # Simulate favorite team (in reality would come from user settings)
            # Here we'll just use the home team as an example
            if home_team:
                preference["favorite_team"] = home_team
            
            # Prepare the document
            doc = Document(
                page_content=json.dumps(preference),
                metadata={
                    "user_id": user_id,
                    "timestamp": preference["timestamp"],
                    "type": "football_preference"
                }
            )
            
            # Check if vector store exists
            if os.path.exists(user_vs_path):
                try:
                    # Load existing store
                    vector_store = FAISS.load_local(user_vs_path, embeddings)
                    
                    # Add the new document
                    vector_store.add_documents([doc])
                    
                    # Save the updated store
                    vector_store.save_local(user_vs_path)
                    logger.info(f"Updated vector store with new preference for user {user_id}")
                except Exception as e:
                    logger.error(f"Error updating vector store: {str(e)}")
            else:
                try:
                    # Create a new vector store
                    vector_store = FAISS.from_documents([doc], embeddings)
                    
                    # Save the vector store
                    vector_store.save_local(user_vs_path)
                    logger.info(f"Created new vector store for user {user_id}")
                except Exception as e:
                    logger.error(f"Error creating vector store: {str(e)}")
        
        except ImportError as e:
            logger.warning(f"Vector store dependencies not available: {str(e)}")
        except Exception as e:
            logger.error(f"Error saving user preference: {str(e)}")
    
    def process_football_references(self, messages: List[Dict[str, Any]]) -> Optional[str]:
        """
        Process football references found in messages with web search enhancement.
        
        Args:
            messages (List[Dict[str, Any]]): List of message dictionaries
            
        Returns:
            Optional[str]: Summary of football content, or None if no references found
        """
        # Extract all text from messages
        all_text = " ".join([msg.get("text", "") for msg in messages if msg.get("text")])
        
        # Extract football references
        football_references = self._extract_football_references(all_text)
        
        # Check for live commentary
        commentary_analysis = self._detect_live_commentary(all_text)
        
        # Extract teams and players
        entities_analysis = self._extract_teams_and_players(all_text)
        
        # Determine if we have any football content to analyze
        has_content = (len(football_references) > 0 or 
                      commentary_analysis["is_live_commentary"] or 
                      entities_analysis["has_teams"] or 
                      entities_analysis["has_players"])
        
        if not has_content:
            logger.info("No football references found in messages")
            return None
        
        # Analyze each reference
        match_analyses = [self._analyze_match_information(ref) for ref in football_references]
        
        # Format input for the agent
        references_text = ""
        search_queries = []
        
        # Add match references
        if match_analyses:
            references_text += "Match References:\n"
            for analysis in match_analyses:
                match_type = analysis["match_type"]
                
                if match_type == "identified":
                    references_text += f"- {analysis['team_home']} {analysis['score_home']}-{analysis['score_away']} {analysis['team_away']} ({analysis['result']})\n"
                elif match_type == "partial":
                    references_text += f"- Unknown match with score {analysis['score_home']}-{analysis['score_away']}\n"
                elif match_type == "team_mention":
                    references_text += f"- Reference to {analysis['team']}\n"
                
                # Add search queries
                if "search_queries" in analysis:
                    search_queries.extend(analysis["search_queries"])
        
        # Add live commentary indicators
        if commentary_analysis["is_live_commentary"]:
            references_text += "\nLive Commentary Indicators:\n"
            
            for commentary_type, present in commentary_analysis["commentary_types"].items():
                if present:
                    references_text += f"- {commentary_type.capitalize()} commentary detected\n"
            
            if commentary_analysis["excitement_level"] in ["high", "medium"]:
                references_text += f"- High excitement level detected\n"
                
            if commentary_analysis["has_match_minutes"]:
                minutes = ", ".join(commentary_analysis["match_minutes"])
                references_text += f"- Match minute references: {minutes}\n"
                
                # Add search queries for match minutes
                today = datetime.now().strftime("%B %d, %Y")
                for minute in commentary_analysis["match_minutes"]:
                    if entities_analysis["has_teams"]:
                        team = entities_analysis["teams"][0]["full_name"]
                        search_queries.append(f"{team} match {minute}' minute {today}")
        
        # Add team mentions
        if entities_analysis["has_teams"]:
            references_text += "\nTeam Mentions:\n"
            for team in entities_analysis["teams"]:
                references_text += f"- {team['full_name']}\n"
                
                # Add search queries
                if not any(team['full_name'] in query for query in search_queries):
                    today = datetime.now().strftime("%B %d, %Y")
                    search_queries.append(f"{team['full_name']} match today {today}")
                    search_queries.append(f"{team['full_name']} latest result")
        
        # Add player mentions
        if entities_analysis["has_players"]:
            references_text += "\nPlayer Mentions:\n"
            for player in entities_analysis["players"]:
                if player["original_text"] == player["alias"]:
                    references_text += f"- {player['full_name'] or player['alias']}\n"
                else:
                    references_text += f"- {player['original_text']} (likely {player['full_name'] or player['alias']})\n"
                
                # Add search queries for players
                if player["full_name"]:
                    search_queries.append(f"{player['full_name']} recent performance")
                    search_queries.append(f"{player['full_name']} goal today")
                    
                    # If we have a team, combine player and team for better results
                    if entities_analysis["has_teams"]:
                        team = entities_analysis["teams"][0]["full_name"]
                        search_queries.append(f"{player['full_name']} {team} recent match")
        
        # Limit search queries to top 3 most specific ones to avoid noise
        search_queries = search_queries[:3]
        
        # Prepare the input for the agent to use with web search
        input_text = f"""
        I need to summarize football (soccer) content from a group chat. 
        
        Here are the references I found:
        
        {references_text}
        
        Please use web search to find additional context about these football references.
        Focus your searches on these specific queries to minimize noise:
        {", ".join(search_queries)}
        
        When providing the summary:
        1. Focus on in-game activity happening today or very recently (within the last 24 hours)
        2. For player mentions with high excitement (like "ENZOOOOO"), look for recent goals or key moments
        3. Provide match context (competition, stage, importance) if relevant
        4. Be concise but informative - the summary will be included in a larger chat summary
        5. Assume the mentions are about live or very recent matches unless evidence suggests otherwise
        
        If the web search doesn't yield relevant results, just summarize what's known from the references.
        """
        
        # Process with the agent (will use web search due to the instructions)
        response = self.process(input_text)
        return response 