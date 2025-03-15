"""
Vector Store for User Profiles

This module provides a vector store implementation for storing and retrieving user profiles.
It uses ChromaDB as the underlying vector database and OpenAI embeddings for vectorization.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Union
import chromadb
from chromadb.config import Settings
from langchain_openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.schema import Document

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UserProfileStore:
    """
    Vector store for user profiles.
    
    This class provides methods for storing and retrieving user profiles using a vector database.
    It uses ChromaDB as the underlying vector database and OpenAI embeddings for vectorization.
    
    Attributes:
        embeddings (OpenAIEmbeddings): The embeddings model
        db_directory (str): The directory where the vector database is stored
        vector_store (Chroma): The vector store instance
    """
    
    def __init__(self, db_directory: str = "user_profiles_db"):
        """
        Initialize the UserProfileStore.
        
        Args:
            db_directory (str, optional): The directory where the vector database is stored.
                Defaults to "user_profiles_db".
        """
        self.embeddings = OpenAIEmbeddings()
        self.db_directory = db_directory
        
        # Create the directory if it doesn't exist
        os.makedirs(db_directory, exist_ok=True)
        
        # Initialize the vector store
        self.vector_store = Chroma(
            collection_name="user_profiles",
            embedding_function=self.embeddings,
            persist_directory=db_directory
        )
        
        logger.info(f"UserProfileStore initialized with database directory: {db_directory}")
    
    def add_or_update_user(
        self,
        user_id: Union[str, int],
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        profile_text: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add or update a user profile in the vector store.
        
        Args:
            user_id (Union[str, int]): The user ID
            username (Optional[str], optional): The username. Defaults to None.
            first_name (Optional[str], optional): The first name. Defaults to None.
            last_name (Optional[str], optional): The last name. Defaults to None.
            profile_text (Optional[str], optional): Additional profile text. Defaults to None.
            metadata (Optional[Dict[str, Any]], optional): Additional metadata. Defaults to None.
        """
        # Convert user_id to string
        user_id = str(user_id)
        
        # Create the profile text
        profile_parts = []
        
        if first_name:
            profile_parts.append(f"First name: {first_name}")
        
        if last_name:
            profile_parts.append(f"Last name: {last_name}")
        
        if username:
            profile_parts.append(f"Username: {username}")
        
        if profile_text:
            profile_parts.append(profile_text)
        
        full_profile_text = "\n".join(profile_parts)
        
        # Create the metadata
        full_metadata = {
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
        }
        
        if metadata:
            full_metadata.update(metadata)
        
        # Create the document
        document = Document(
            page_content=full_profile_text,
            metadata=full_metadata
        )
        
        # Check if the user already exists
        existing_docs = self.vector_store.get(where={"user_id": user_id})
        
        if existing_docs["ids"]:
            # Update the existing document
            self.vector_store.delete(where={"user_id": user_id})
        
        # Add the document
        self.vector_store.add_documents([document])
        
        logger.info(f"User profile added/updated for user_id: {user_id}")
    
    def add_user_information(
        self,
        user_id: Union[str, int],
        information: str,
        category: Optional[str] = None
    ) -> None:
        """
        Add information to a user profile.
        
        Args:
            user_id (Union[str, int]): The user ID
            information (str): The information to add
            category (Optional[str], optional): The category of the information.
                Defaults to None.
        """
        # Convert user_id to string
        user_id = str(user_id)
        
        # Get the existing profile
        existing_docs = self.vector_store.get(where={"user_id": user_id})
        
        if not existing_docs["ids"]:
            # Create a new profile if it doesn't exist
            self.add_or_update_user(user_id, profile_text=information)
            return
        
        # Get the existing profile text and metadata
        existing_text = existing_docs["documents"][0]
        existing_metadata = existing_docs["metadatas"][0]
        
        # Add the new information
        if category:
            new_info = f"{category}: {information}"
        else:
            new_info = information
        
        # Update the profile text
        updated_text = f"{existing_text}\n{new_info}"
        
        # Update the metadata
        if category:
            if "categories" not in existing_metadata:
                existing_metadata["categories"] = {}
            
            if category not in existing_metadata["categories"]:
                existing_metadata["categories"][category] = []
            
            existing_metadata["categories"][category].append(information)
        
        # Update the profile
        self.vector_store.delete(where={"user_id": user_id})
        
        # Create the document
        document = Document(
            page_content=updated_text,
            metadata=existing_metadata
        )
        
        # Add the document
        self.vector_store.add_documents([document])
        
        logger.info(f"Information added to user profile for user_id: {user_id}")
    
    def get_user_profile(self, user_id: Union[str, int]) -> Optional[Dict[str, Any]]:
        """
        Get a user profile from the vector store.
        
        Args:
            user_id (Union[str, int]): The user ID
        
        Returns:
            Optional[Dict[str, Any]]: The user profile, or None if not found
        """
        # Convert user_id to string
        user_id = str(user_id)
        
        # Get the profile
        results = self.vector_store.get(where={"user_id": user_id})
        
        if not results["ids"]:
            return None
        
        # Return the profile
        return {
            "user_id": user_id,
            "profile_text": results["documents"][0],
            "metadata": results["metadatas"][0]
        }
    
    def search_similar_profiles(
        self,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for user profiles similar to the query.
        
        Args:
            query (str): The query text
            limit (int, optional): The maximum number of results to return.
                Defaults to 5.
        
        Returns:
            List[Dict[str, Any]]: List of user profiles
        """
        # Search for similar profiles
        results = self.vector_store.similarity_search_with_score(query, k=limit)
        
        # Format the results
        profiles = []
        for doc, score in results:
            profiles.append({
                "user_id": doc.metadata.get("user_id"),
                "profile_text": doc.page_content,
                "metadata": doc.metadata,
                "similarity_score": score
            })
        
        return profiles
    
    def extract_user_interests(self, user_id: Union[str, int]) -> Dict[str, List[str]]:
        """
        Extract user interests from the profile.
        
        Args:
            user_id (Union[str, int]): The user ID
        
        Returns:
            Dict[str, List[str]]: Dictionary of interests by category
        """
        profile = self.get_user_profile(user_id)
        
        if not profile:
            return {}
        
        # Extract interests from the metadata
        metadata = profile["metadata"]
        
        if "categories" not in metadata:
            return {}
        
        return metadata["categories"] 