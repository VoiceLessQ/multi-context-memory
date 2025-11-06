"""
MCP Multi-Context Memory System
Copyright (c) 2024 VoiceLessQ
https://github.com/VoiceLessQ/multi-context-memory

This file is part of the MCP Multi-Context Memory System.
Licensed under the MIT License. See LICENSE file in the project root.

Project Fingerprint: 7a8f9b3c-mcpmem-voicelessq-2024
Original Author: VoiceLessQ
"""

"""
Text processing utilities for the enhanced MCP Multi-Context Memory System.
"""
import re
from typing import List, Optional
from collections import Counter


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    Extract keywords from text content.
    
    Args:
        text: Input text to extract keywords from
        max_keywords: Maximum number of keywords to return
        
    Returns:
        List of extracted keywords
    """
    if not text or not text.strip():
        return []
    
    # Convert to lowercase and remove special characters
    clean_text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text.lower())
    
    # Split into words
    words = clean_text.split()
    
    # Remove common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
        'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these',
        'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him',
        'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'
    }
    
    # Filter out stop words and short words
    filtered_words = [
        word for word in words 
        if word not in stop_words and len(word) > 2
    ]
    
    # Count word frequencies
    word_counts = Counter(filtered_words)
    
    # Return most common words as keywords
    return [word for word, _ in word_counts.most_common(max_keywords)]


def generate_summary(text: str, max_sentences: int = 3) -> str:
    """
    Generate a summary of text content using extractive summarization.
    
    Args:
        text: Input text to summarize
        max_sentences: Maximum number of sentences in summary
        
    Returns:
        Generated summary text
    """
    if not text or not text.strip():
        return ""
    
    # Split text into sentences
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if len(sentences) <= max_sentences:
        return text.strip()
    
    # Simple scoring based on sentence length and keyword frequency
    keywords = extract_keywords(text, 20)
    keyword_set = set(keywords)
    
    sentence_scores = []
    for sentence in sentences:
        # Score based on keywords and length
        words = set(re.findall(r'\w+', sentence.lower()))
        keyword_overlap = len(words.intersection(keyword_set))
        length_score = min(len(sentence.split()), 20) / 20  # Normalize to 0-1
        
        score = keyword_overlap + length_score
        sentence_scores.append((score, sentence))
    
    # Sort by score and take top sentences
    sentence_scores.sort(reverse=True)
    top_sentences = [sentence for _, sentence in sentence_scores[:max_sentences]]
    
    # Return sentences in original order
    summary_sentences = []
    for sentence in sentences:
        if sentence in top_sentences:
            summary_sentences.append(sentence)
            if len(summary_sentences) >= max_sentences:
                break
    
    return '. '.join(summary_sentences) + '.'


def clean_text(text: str) -> str:
    """
    Clean and normalize text content.
    
    Args:
        text: Input text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove control characters
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    
    return text.strip()


def tokenize_text(text: str) -> List[str]:
    """
    Tokenize text into words.
    
    Args:
        text: Input text to tokenize
        
    Returns:
        List of tokens
    """
    if not text:
        return []
    
    # Clean text first
    clean = clean_text(text)
    
    # Extract words (alphanumeric sequences)
    tokens = re.findall(r'\b\w+\b', clean.lower())
    
    return tokens


def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity between two texts using Jaccard similarity.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity score between 0 and 1
    """
    if not text1 or not text2:
        return 0.0
    
    # Tokenize both texts
    tokens1 = set(tokenize_text(text1))
    tokens2 = set(tokenize_text(text2))
    
    if not tokens1 or not tokens2:
        return 0.0
    
    # Calculate Jaccard similarity
    intersection = len(tokens1.intersection(tokens2))
    union = len(tokens1.union(tokens2))
    
    return intersection / union if union > 0 else 0.0


def truncate_text(text: str, max_length: int = 500, suffix: str = "...") -> str:
    """
    Truncate text to specified length.
    
    Args:
        text: Input text to truncate
        max_length: Maximum length of output text
        suffix: Suffix to add when text is truncated
        
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    # Try to truncate at word boundary
    truncated = text[:max_length - len(suffix)]
    last_space = truncated.rfind(' ')
    
    if last_space > max_length * 0.8:  # Only truncate at word if it's not too short
        truncated = truncated[:last_space]
    
    return truncated + suffix