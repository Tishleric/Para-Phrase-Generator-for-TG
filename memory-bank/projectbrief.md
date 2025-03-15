# Project Brief - Para-Phrase Generator

Below is the project brief that reflects the multi-agent architecture based on the OpenAI Agents release. It incorporates the best practices from the OpenAI Agents Python documentation and the OpenAI API quickstart for tool extension.

## Overview

This project is a Telegram bot designed to help group chat participants quickly catch up on conversations by summarizing recent messages. The bot leverages the OpenAI Agents framework to split responsibilities among multiple specialized agents. The main command (`/last X`) is routed to a delegation agent that inspects the conversation context and dynamically assigns subtasks to dedicated agents (for tone-specific summarization, Twitter link summarization, image analysis, football score lookup, etc.). Each of these agents can access enriched data—including vectorized profiles of group chat members—to generate more personalized and context-aware summaries.

## Current Functionality Recap

- **Message Storage & Command Handling:**  
  - Listens to all incoming messages and stores them (up to a defined limit).
  - Commands include `/last X` for summarization and `/tone TONE` for setting the tone (options: stoic, chaotic, pubbie, deaf).

- **Summarization Engine:**  
  - Uses Anthropic's Claude 3.7 Sonnet (via a custom wrapper) to generate summaries based on tone-specific instructions.
  - Formats messages with basic handling for replies and images.

- **Configuration & Deployment:**  
  - Environment variables (via a `.env` file) secure API tokens.
  - Dependencies are defined in `requirements.txt`.

## Multi-Agent Architecture

### Multi-Agent Delegation Flow

1. **Delegation Agent (Orchestrator):**  
   - **Role:** Receives the `/last X` command and acts as the entry point.  
   - **Function:** Analyzes the message history and context, then delegates subtasks to the appropriate specialized agents based on content cues (e.g., tone selection, embedded Twitter links, images, football scores).

2. **Tone-Specific Summary Agents:**  
   - **Role:** Produce summaries in the selected tone (stoic, chaotic, pubbie, deaf).  
   - **Enhancement:** Each summary agent is preloaded with vectorized data on group chat members, enabling personalized references (e.g., favourite sports teams or character traits).

3. **Specialized Sub-Agents for Content-Specific Tasks:**
   - **Twitter Link Bot:**  
     - **Task:** Detects and processes Twitter URLs found in the conversation.  
     - **Workflow:** Retrieves tweet content, summarizes it, and returns a concise summary to the tone-specific agent.
   - **Photo Summarizer Bot:**  
     - **Task:** Handles image messages using OCR/image recognition tools.  
     - **Workflow:** Analyzes visual content and returns a textual description for inclusion in the overall summary.
   - **Football Score Bot:**  
     - **Task:** Detects references to football scores.  
     - **Workflow:** Either queries a free sports API or uses an agent search method to provide current or past game context. The result is passed back for integration into the summary.

4. **Context Enrichment:**  
   - **Short-Term Context Extraction:**  
     - Before processing, the delegation agent examines a short window of preceding messages to gain additional context (particularly useful for shorter `/last X` requests).
   - **Persistent Vector Database:**  
     - A vector store is maintained to capture profiles and historical data about frequent chat members, enabling richer, context-aware summaries.

### Key Benefits of This Approach

- **Modularity & Scalability:**  
  Each specialized agent can be developed, tested, and scaled independently.
- **Enhanced Personalization:**  
  Access to vectorized user data allows summaries to reference personalities and recurring themes in a natural way.
- **Dynamic Delegation:**  
  By using the agents framework, the system can dynamically call out to the correct sub-agent based on real-time content, resulting in more accurate and detailed summaries.
- **Future-Proofing:**  
  The architecture is built to easily integrate additional agents (e.g., for other content types or emerging APIs).

## Implementation Plan

### **Phase 1: Research & Environment Setup**
- **Objective:** Prepare the development environment for integrating OpenAI Agents.
- **Steps:**
  1. **Review Documentation:**  
     - Thoroughly study the OpenAI Agents Python documentation and the tool-extension guide to understand API usage, agent creation, and tool integration.
  2. **Prototype Agent Framework:**  
     - Set up a sandbox project that demonstrates basic agent creation and delegation.
  3. **Integrate with Existing Codebase:**  
     - Refactor the current `/last` command flow to pass the request to a preliminary delegation agent.

### **Phase 2: Develop the Delegation Agent**
- **Objective:** Create an agent responsible for analyzing conversation context and delegating tasks.
- **Steps:**
  1. **Define Agent Responsibilities:**  
     - Write a clear specification for the delegation agent's inputs (message history, tone setting) and outputs (delegated responses).
  2. **Implement Dynamic Delegation Logic:**  
     - Develop code that inspects message content and decides which specialized agent(s) to call.
  3. **Integrate Vector Database Access:**  
     - Ensure the delegation agent can query the vector store to retrieve user profiles as needed.

### **Phase 3: Implement Specialized Content Agents**
- **Objective:** Build agents for handling specific content types and tone-specific summaries.
- **Steps:**
  1. **Tone-Specific Summary Agents:**
     - Split the current summarization logic into separate agents, each preloaded with tone-specific instructions.
     - Modify the agents to incorporate vectorized user data to add personality references.
  2. **Twitter Link Bot:**  
     - Develop logic to detect Twitter URLs and call an external summarization API (or use agent capabilities) to fetch tweet summaries.
  3. **Football Score Bot:**  
     - Implement a method to detect football score references.  
     - Integrate with a free sports API or utilize agent search functionality to retrieve game context.
  4. **Photo Summarizer Bot:**  
     - Integrate an image recognition library (e.g., Tesseract or a cloud-based solution) and wrap it in an agent that returns descriptive text.

### **Phase 4: End-to-End Integration & Testing**
- **Objective:** Combine the delegation agent, tone-specific agents, and specialized sub-agents into a unified flow.
- **Steps:**
  1. **Integrate Agent Communication:**  
     - Implement message passing between agents according to the delegation logic.
  2. **Conduct Real-World Testing:**  
     - Test the complete system in a group chat environment, ensuring that context hand-offs work seamlessly.
  3. **Refine Error Handling & Edge Cases:**  
     - Enhance error detection for failed agent calls and ensure fallback mechanisms are in place.

### **Phase 5: Documentation & Future Enhancements**
- **Objective:** Document the new architecture and plan for future agent additions.
- **Steps:**
  1. **Update Project Documentation:**  
     - Revise the project brief and developer documentation to reflect the new multi-agent design.
  2. **Plan for Additional Agents:**  
     - Identify other content types or features (e.g., additional social media platforms) that may benefit from dedicated agents.
  3. **Monitor Agent Performance:**  
     - Set up logging and performance metrics to monitor how well agents are delegating and summarizing.

## Conclusion

By restructuring the bot to use a multi-agent approach based on OpenAI's Agents framework, the project gains a modular, scalable architecture capable of handling complex, context-aware summarization. The delegation agent coordinates between tone-specific summary agents and specialized content processors, while leveraging a vector database for enriched user context. This approach not only enhances the bot's summarization accuracy but also paves the way for further feature expansion in future iterations. 