# Knowledge Integration Guide for MCP Multi-Context Memory System

This guide explains how to add and manage knowledge in the MCP Multi-Context Memory System, designed to be scalable from the beginning.

## Overview

The system is designed to handle knowledge ingestion, organization, and retrieval at scale. It combines structured database storage with semantic capabilities to create a comprehensive knowledge management solution.

## Knowledge Ingestion Methods

### 1. Direct API Input

#### Basic Memory Creation
```python
import requests
import json

# Add a simple fact
response = requests.post("http://localhost:8000/api/memory/", json={
    "title": "Python is a high-level programming language",
    "content": "Python emphasizes code readability with its notable use of significant whitespace.",
    "context_id": 1,
    "access_level": "public",
    "memory_metadata": {
        "tags": ["programming", "python", "language"],
        "source": "Wikipedia",
        "confidence": 0.9,
        "importance": 7
    }
})
```

#### Complex Knowledge Entry
```python
# Add a complex concept with related information
concept_data = {
    "title": "Machine Learning",
    "content": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed.",
    "context_id": 2,
    "access_level": "public",
    "memory_metadata": {
        "tags": ["ai", "ml", "technology", "computer science"],
        "category": "concept",
        "difficulty": "intermediate",
        "prerequisites": ["programming", "mathematics"],
        "related_concepts": ["neural networks", "deep learning"],
        "source": "Stanford CS229",
        "confidence": 0.95,
        "importance": 10
    }
}

response = requests.post("http://localhost:8000/api/memory/", json=concept_data)
```

### 2. Batch Knowledge Import

#### From JSON/CSV Files
```python
import pandas as pd
import requests

# Import from CSV
df = pd.read_csv('knowledge_data.csv')

for _, row in df.iterrows():
    memory_data = {
        "title": row['title'],
        "content": row['content'],
        "context_id": row.get('context_id', 1),
        "access_level": row.get('access_level', 'public'),
        "memory_metadata": {
            "tags": row.get('tags', '').split(','),
            "source": row.get('source', 'Unknown'),
            "confidence": row.get('confidence', 0.8),
            "importance": row.get('importance', 5)
        }
    }
    
    requests.post("http://localhost:8000/api/memory/", json=memory_data)
```

#### From Structured Documents
```python
# Process and import from structured documents (PDF, DOCX, etc.)
def process_document(file_path, context_id):
    # Extract text from document
    text = extract_text_from_document(file_path)
    
    # Split into chunks with overlap
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    
    # Create memories for each chunk
    memories = []
    for i, chunk in enumerate(chunks):
        memory_data = {
            "title": f"Document Chunk {i+1}",
            "content": chunk,
            "context_id": context_id,
            "access_level": "private",
            "memory_metadata": {
                "tags": ["document", "chunk"],
                "source": file_path,
                "chunk_id": i,
                "total_chunks": len(chunks)
            }
        }
        
        response = requests.post("http://localhost:8000/api/memory/", json=memory_data)
        if response.status_code == 200:
            memories.append(response.json())
    
    return memories

# Create relationships between chunks
def link_document_chunks(memories):
    for i in range(len(memories) - 1):
        requests.post("http://localhost:8000/api/relation/", json={
            "name": "follows",
            "source_memory_id": memories[i]['id'],
            "target_memory_id": memories[i+1]['id'],
            "strength": 1.0,
            "relation_metadata": {
                "type": "sequence",
                "document_id": memories[i]['memory_metadata']['source']
            }
        })
```

### 3. Web Content Ingestion

#### Web Scraping with Knowledge Extraction
```python
import requests
from bs4 import BeautifulSoup
import re

def ingest_web_content(url, context_id):
    # Fetch web content
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extract main content
    content = extract_main_content(soup)
    
    # Extract key information
    title = soup.find('title').text if soup.find('title') else url
    keywords = extract_keywords(content)
    
    # Create memory
    memory_data = {
        "title": title,
        "content": content,
        "context_id": context_id,
        "access_level": "public",
        "memory_metadata": {
            "tags": keywords + ["web", "scraped"],
            "source": url,
            "scraped_date": datetime.now().isoformat(),
            "content_type": "web_page"
        }
    }
    
    return requests.post("http://localhost:8000/api/memory/", json=memory_data)

def extract_main_content(soup):
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    
    # Get text
    text = soup.get_text()
    
    # Clean whitespace
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = ' '.join(chunk for chunk in chunks if chunk)
    
    return text
```

### 4. API Integration

#### From External Knowledge Sources
```python
# Integrate with Wikipedia API
def import_wikipedia_articles(topic, limit=10):
    base_url = "https://en.wikipedia.org/api/rest_v1/page/summary/"
    
    # Search for articles (you'd need a search API endpoint)
    # This is a simplified example
    articles = search_wikipedia(topic, limit)
    
    for article in articles:
        response = requests.get(base_url + article['pageid'])
        if response.status_code == 200:
            data = response.json()
            
            memory_data = {
                "title": data['title'],
                "content": data['extract'],
                "context_id": 3,  # Wikipedia context
                "access_level": "public",
                "memory_metadata": {
                    "tags": ["wikipedia", topic] + data.get('categories', []),
                    "source": f"https://en.wikipedia.org/wiki/{data['title'].replace(' ', '_')}",
                    "wikipedia_id": data['pageid'],
                    "last_updated": data.get('timestamp'),
                    "importance": 8
                }
            }
            
            requests.post("http://localhost:8000/api/memory/", json=memory_data)
```

## Knowledge Organization Strategies

### 1. Hierarchical Context Structure

```python
# Create a hierarchical context system
contexts = [
    {
        "name": "Technology",
        "description": "All technology-related knowledge",
        "parent_context_id": None,
        "context_metadata": {
            "category": "domain",
            "scope": "broad"
        }
    },
    {
        "name": "Computer Science",
        "description": "Computer science fundamentals",
        "parent_context_id": 1,  # Technology
        "context_metadata": {
            "category": "subdomain",
            "scope": "medium"
        }
    },
    {
        "name": "Artificial Intelligence",
        "description": "AI and machine learning",
        "parent_context_id": 2,  # Computer Science
        "context_metadata": {
            "category": "specialization",
            "scope": "narrow"
        }
    }
]

for context in contexts:
    requests.post("http://localhost:8000/api/context/", json=context)
```

### 2. Knowledge Taxonomy

```python
# Define knowledge categories and tags
knowledge_taxonomy = {
    "programming": {
        "languages": ["python", "javascript", "java", "c++"],
        "concepts": ["algorithms", "data structures", "paradigms"],
        "tools": ["git", "docker", "vscode"]
    },
    "science": {
        "physics": ["quantum", "relativity", "mechanics"],
        "biology": ["genetics", "ecology", "evolution"],
        "chemistry": ["organic", "inorganic", "physical"]
    },
    "business": {
        "management": ["strategy", "operations", "leadership"],
        "finance": ["accounting", "investment", "economics"],
        "marketing": ["digital", "brand", "content"]
    }
}

# Apply taxonomy during ingestion
def apply_taxonomy(memory_data, taxonomy):
    content = memory_data['content'].lower()
    tags = memory_data['memory_metadata'].get('tags', [])
    
    for category, subcategories in taxonomy.items():
        for subcategory, keywords in subcategories.items():
            for keyword in keywords:
                if keyword in content:
                    tags.append(category)
                    tags.append(subcategory)
                    break
    
    memory_data['memory_metadata']['tags'] = list(set(tags))
    return memory_data
```

### 3. Relationship Mapping

```python
# Create knowledge relationships
def establish_knowledge_relationships(memory_id, related_memories):
    for related_id, relationship_type, strength in related_memories:
        requests.post("http://localhost:8000/api/relation/", json={
            "name": relationship_type,
            "source_memory_id": memory_id,
            "target_memory_id": related_id,
            "strength": strength,
            "relation_metadata": {
                "type": "conceptual",
                "discovered_by": "rule_based"
            }
        })

# Example: Prerequisite relationships
def create_prerequisite_graph(concept_memories):
    for concept in concept_memories:
        prerequisites = concept['memory_metadata'].get('prerequisites', [])
        
        for prereq_name in prerequisites:
            # Find prerequisite memory
            prereq_response = requests.post("http://localhost:8000/api/memory/search", json={
                "query": prereq_name,
                "use_semantic": False,
                "limit": 1
            })
            
            if prereq_response.status_code == 200:
                prereq_results = prereq_response.json()
                if prereq_results:
                    prereq_id = prereq_results[0]['id']
                    
                    requests.post("http://localhost:8000/api/relation/", json={
                        "name": "requires",
                        "source_memory_id": concept['id'],
                        "target_memory_id": prereq_id,
                        "strength": 0.9,
                        "relation_metadata": {
                            "type": "prerequisite",
                            "description": f"{concept['title']} requires {prereq_name}"
                        }
                    })
```

## Scalable Knowledge Management

### 1. Chunking Strategy

```python
# Advanced text chunking for large documents
def intelligent_chunking(text, max_chunk_size=500, overlap=50):
    # Split into paragraphs first
    paragraphs = text.split('\n\n')
    
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) + 2 <= max_chunk_size:
            if current_chunk:
                current_chunk += "\n\n"
            current_chunk += paragraph
        else:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = paragraph
            else:
                # Paragraph is too long, split it
                sub_chunks = split_long_text(paragraph, max_chunk_size)
                chunks.extend(sub_chunks)
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

def split_long_text(text, max_size):
    sentences = text.split('. ')
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 2 <= max_size:
            if current_chunk:
                current_chunk += ". "
            current_chunk += sentence
        else:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = sentence
            else:
                # Sentence is too long, split by words
                words = sentence.split(' ')
                temp_chunk = ""
                for word in words:
                    if len(temp_chunk) + len(word) + 1 <= max_size:
                        if temp_chunk:
                            temp_chunk += " "
                        temp_chunk += word
                    else:
                        if temp_chunk:
                            chunks.append(temp_chunk)
                        temp_chunk = word
                if temp_chunk:
                    chunks.append(temp_chunk)
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks
```

### 2. Duplicate Detection and Merging

```python
# Detect and merge duplicate or similar memories
def detect_duplicates(new_memory, threshold=0.85):
    # Search for similar memories
    search_response = requests.post("http://localhost:8000/api/memory/search", json={
        "query": new_memory['content'],
        "use_semantic": True,
        "limit": 5
    })
    
    if search_response.status_code == 200:
        similar_memories = search_response.json()
        
        for memory in similar_memories:
            similarity_score = calculate_similarity(new_memory['content'], memory['content'])
            
            if similarity_score >= threshold:
                # Merge memories
                merge_memories(new_memory['id'], memory['id'])
                return memory['id']
    
    return None

def merge_memories(main_id, duplicate_id):
    # Get both memories
    main_response = requests.get(f"http://localhost:8000/api/memory/{main_id}")
    duplicate_response = requests.get(f"http://localhost:8000/api/memory/{duplicate_id}")
    
    if main_response.status_code == 200 and duplicate_response.status_code == 200:
        main_memory = main_response.json()
        duplicate_memory = duplicate_response.json()
        
        # Merge metadata
        merged_metadata = merge_metadata(
            main_memory['memory_metadata'],
            duplicate_memory['memory_metadata']
        )
        
        # Update main memory
        update_data = {
            "memory_metadata": merged_metadata,
            "content": f"{main_memory['content']}\n\nRelated: {duplicate_memory['content']}"
        }
        
        requests.put(f"http://localhost:8000/api/memory/{main_id}", json=update_data)
        
        # Mark duplicate as merged
        requests.put(f"http://localhost:8000/api/memory/{duplicate_id}", json={
            "memory_metadata": {
                **duplicate_memory['memory_metadata'],
                "merged_into": main_id,
                "status": "merged"
            }
        })
        
        # Redirect relationships
        redirect_relationships(duplicate_id, main_id)
```

### 3. Knowledge Graph Construction

```python
# Build and maintain knowledge graphs
class KnowledgeGraphBuilder:
    def __init__(self):
        self.graph = {}
    
    def add_memory(self, memory):
        self.graph[memory['id']] = {
            'title': memory['title'],
            'content': memory['content'],
            'tags': memory['memory_metadata'].get('tags', []),
            'relations': []
        }
    
    def add_relation(self, source_id, target_id, relation_type, strength):
        if source_id in self.graph and target_id in self.graph:
            self.graph[source_id]['relations'].append({
                'target': target_id,
                'type': relation_type,
                'strength': strength
            })
    
    def find_path(self, start_id, end_id, max_depth=3):
        # Simple pathfinding algorithm
        visited = set()
        queue = [(start_id, [start_id])]
        
        while queue:
            current_id, path = queue.pop(0)
            
            if current_id == end_id:
                return path
            
            if len(path) > max_depth:
                continue
            
            if current_id in visited:
                continue
            
            visited.add(current_id)
            
            for relation in self.graph.get(current_id, {}).get('relations', []):
                if relation['target'] not in visited:
                    queue.append((relation['target'], path + [relation['target']]))
        
        return None
    
    def find_related_concepts(self, concept_id, relation_types=None, max_results=5):
        if relation_types is None:
            relation_types = ['related_to', 'similar_to', 'expands_on']
        
        related = set()
        
        # Direct relations
        for relation in self.graph.get(concept_id, {}).get('relations', []):
            if relation['type'] in relation_types:
                related.add(relation['target'])
        
        # Relations of relations (2-hop)
        for related_id in list(related):
            for relation in self.graph.get(related_id, {}).get('relations', []):
                if relation['type'] in relation_types:
                    related.add(relation['target'])
        
        return list(related)[:max_results]
```

## Knowledge Retrieval and Enhancement

### 1. Semantic Search Enhancement

```python
# Advanced semantic search with filters
def enhanced_search(query, context_ids=None, tags=None, date_range=None, 
                   min_confidence=None, use_semantic=True, limit=10):
    search_params = {
        "query": query,
        "use_semantic": use_semantic,
        "limit": limit
    }
    
    # Add filters
    if context_ids:
        search_params["context_ids"] = context_ids
    
    if tags:
        search_params["tags"] = tags
    
    if date_range:
        search_params["date_range"] = date_range
    
    if min_confidence:
        search_params["min_confidence"] = min_confidence
    
    response = requests.post("http://localhost:8000/api/memory/search", json=search_params)
    
    if response.status_code == 200:
        results = response.json()
        
        # Enhance results with related knowledge
        enhanced_results = []
        for memory in results:
            related = get_related_memories(memory['id'])
            memory['related_memories'] = related
            enhanced_results.append(memory)
        
        return enhanced_results
    
    return []

def get_related_memories(memory_id, limit=5):
    response = requests.get(f"http://localhost:8000/api/memory/{memory_id}/relations")
    
    if response.status_code == 200:
        relations = response.json()
        related_ids = [r['target_memory_id'] for r in relations]
        
        # Get full memory details
        related_memories = []
        for mem_id in related_ids[:limit]:
            mem_response = requests.get(f"http://localhost:8000/api/memory/{mem_id}")
            if mem_response.status_code == 200:
                related_memories.append(mem_response.json())
        
        return related_memories
    
    return []
```

### 2. Knowledge Summarization

```python
# Generate summaries of related memories
def summarize_knowledge(topic, context_ids=None, max_memories=10):
    # Find relevant memories
    search_response = requests.post("http://localhost:8000/api/memory/search", json={
        "query": topic,
        "use_semantic": True,
        "context_ids": context_ids,
        "limit": max_memories
    })
    
    if search_response.status_code == 200:
        memories = search_response.json()
        
        # Extract key points
        key_points = []
        for memory in memories:
            key_points.append({
                "title": memory['title'],
                "content": memory['content'],
                "importance": memory['memory_metadata'].get('importance', 5)
            })
        
        # Sort by importance
        key_points.sort(key=lambda x: x['importance'], reverse=True)
        
        # Generate summary
        summary = f"Summary of knowledge about '{topic}':\n\n"
        
        for point in key_points[:5]:  # Top 5 points
            summary += f"- {point['title']}: {point['content'][:200]}...\n"
        
        # Add related concepts
        related_concepts = find_related_concepts(memories[0]['id'])
        if related_concepts:
            summary += f"\nRelated concepts: {', '.join(related_concepts)}"
        
        return summary
    
    return "No relevant knowledge found."
```

### 3. Knowledge Validation and Updates

```python
# Periodic knowledge validation
def validate_knowledge():
    # Get all memories marked as needing validation
    search_response = requests.post("http://localhost:8000/api/memory/search", json={
        "query": "validation_needed",
        "use_semantic": False,
        "limit": 100
    })
    
    if search_response.status_code == 200:
        memories = search_response.json()
        
        for memory in memories:
            # Validate memory content
            is_valid, validation_message = validate_memory_content(memory)
            
            # Update memory status
            update_data = {
                "memory_metadata": {
                    **memory['memory_metadata'],
                    "validation_status": "validated" if is_valid else "invalid",
                    "validation_message": validation_message,
                    "last_validated": datetime.now().isoformat()
                }
            }
            
            requests.put(f"http://localhost:8000/api/memory/{memory['id']}", json=update_data)

def validate_memory_content(memory):
    # Implement validation logic
    # Check for outdated information, contradictions, etc.
    
    content = memory['content'].lower()
    
    # Example: Check for outdated technologies
    outdated_terms = ["deprecated", "obsolete", "outdated"]
    for term in outdated_terms:
        if term in content:
            return False, f"Contains {term} technology"
    
    # Check for contradictions with other memories
    contradictions = find_contradictions(memory)
    if contradictions:
        return False, f"Contradicts {len(contradictions)} other memories"
    
    return True, "Validated successfully"

def find_contradictions(memory):
    # Search for potentially contradictory information
    search_response = requests.post("http://localhost:8000/api/memory/search", json={
        "query": memory['content'],
        "use_semantic": True,
        "limit": 10
    })
    
    contradictions = []
    
    if search_response.status_code == 200:
        similar_memories = search_response.json()
        
        for similar in similar_memories:
            if memory['id'] != similar['id']:
                # Check for contradictions (simplified)
                if check_contradiction(memory['content'], similar['content']):
                    contradictions.append(similar['id'])
    
    return contradictions
```

## Implementation Roadmap

### Phase 1: Basic Knowledge Ingestion
- [ ] Implement core memory creation API
- [ ] Add basic text chunking
- [ ] Create simple relationship mapping
- [ ] Set up basic search functionality

### Phase 2: Advanced Organization
- [ ] Implement hierarchical contexts
- [ ] Add knowledge taxonomy system
- [ ] Create automated tagging
- [ ] Develop duplicate detection

### Phase 3: Scalable Features
- [ ] Implement intelligent chunking
- [ ] Add knowledge graph capabilities
- [ ] Create semantic search enhancements
- [ ] Develop summarization features

### Phase 4: Advanced Analytics
- [ ] Add knowledge validation
- [ ] Implement usage analytics
- [ ] Create recommendation system
- [ ] Add visualization tools

## Best Practices

### 1. Data Quality
- Always validate incoming knowledge
- Maintain source attribution
- Regularly update and prune knowledge
- Use confidence scores appropriately

### 2. Performance
- Implement proper indexing
- Use asynchronous processing for batch operations
- Cache frequently accessed knowledge
- Monitor system performance

### 3. Security
- Implement proper access controls
- Sanitize all inputs
- Audit knowledge changes
- Protect sensitive information

### 4. Maintainability
- Document knowledge schemas
- Version control for knowledge bases
- Regular backups
- Monitor system health

This guide provides a comprehensive approach to knowledge integration in the MCP Multi-Context Memory System, designed to scale from simple ingestion to complex knowledge management.