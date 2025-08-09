"""
Data validation module for the enhanced MCP Multi-Context Memory System.
Provides tools for validating data integrity during migration.
"""
import json
import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime
from pathlib import Path
import re

from ..database.enhanced_memory_db import EnhancedMemoryDB
from ..config.settings import get_settings
from ..config.logging import get_logger

logger = get_logger(__name__)

class DataValidator:
    """
    Validator for data integrity during migration.
    """
    
    def __init__(self, db: EnhancedMemoryDB):
        """
        Initialize validator.
        
        Args:
            db: EnhancedMemoryDB instance
        """
        self.db = db
        self.settings = get_settings()
        
        # Validation rules
        self.rules = {
            "memory": {
                "required_fields": ["id", "title", "content", "owner_id"],
                "string_fields": ["title", "content", "access_level"],
                "numeric_fields": ["id", "owner_id", "context_id"],
                "boolean_fields": ["is_active"],
                "enum_fields": {
                    "access_level": ["public", "user", "privileged", "admin"]
                },
                "max_lengths": {
                    "title": 200,
                    "content": 1000000  # 1MB
                }
            },
            "context": {
                "required_fields": ["id", "name", "owner_id"],
                "string_fields": ["name", "description", "access_level"],
                "numeric_fields": ["id", "owner_id"],
                "boolean_fields": ["is_active"],
                "enum_fields": {
                    "access_level": ["public", "user", "privileged", "admin"]
                },
                "max_lengths": {
                    "name": 100,
                    "description": 1000
                }
            },
            "relation": {
                "required_fields": ["id", "name", "owner_id"],
                "string_fields": ["name"],
                "numeric_fields": ["id", "owner_id", "source_context_id", "target_memory_id", 
                                 "source_memory_id", "target_context_id", "strength"],
                "boolean_fields": ["is_active"],
                "max_lengths": {
                    "name": 100
                },
                "numeric_ranges": {
                    "strength": [0.0, 1.0]
                }
            }
        }
    
    def validate_memory(self, memory_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate memory data.
        
        Args:
            memory_data: Memory data to validate
            
        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []
        
        # Check required fields
        for field in self.rules["memory"]["required_fields"]:
            if field not in memory_data:
                errors.append(f"Missing required field: {field}")
        
        # Check string fields
        for field in self.rules["memory"]["string_fields"]:
            if field in memory_data and not isinstance(memory_data[field], str):
                errors.append(f"Field {field} must be a string")
        
        # Check numeric fields
        for field in self.rules["memory"]["numeric_fields"]:
            if field in memory_data and not isinstance(memory_data[field], (int, float)):
                errors.append(f"Field {field} must be a number")
        
        # Check boolean fields
        for field in self.rules["memory"]["boolean_fields"]:
            if field in memory_data and not isinstance(memory_data[field], bool):
                errors.append(f"Field {field} must be a boolean")
        
        # Check enum fields
        for field, valid_values in self.rules["memory"]["enum_fields"].items():
            if field in memory_data and memory_data[field] not in valid_values:
                errors.append(f"Field {field} must be one of: {valid_values}")
        
        # Check max lengths
        for field, max_length in self.rules["memory"]["max_lengths"].items():
            if field in memory_data and isinstance(memory_data[field], str):
                if len(memory_data[field]) > max_length:
                    errors.append(f"Field {field} exceeds maximum length of {max_length}")
        
        # Check content format
        if "content" in memory_data and isinstance(memory_data["content"], str):
            # Check for potential security issues
            if "<script>" in memory_data["content"].lower():
                errors.append("Content contains potentially dangerous script tags")
            
            # Check for excessive whitespace
            if len(memory_data["content"].strip()) == 0:
                errors.append("Content cannot be empty or whitespace")
        
        # Check metadata format
        if "metadata" in memory_data and memory_data["metadata"] is not None:
            if not isinstance(memory_data["metadata"], dict):
                errors.append("Metadata must be a dictionary")
            else:
                # Check for sensitive data in metadata
                sensitive_keys = ["password", "token", "secret", "key"]
                for key in memory_data["metadata"].keys():
                    if any(sensitive in key.lower() for sensitive in sensitive_keys):
                        errors.append(f"Metadata contains potentially sensitive key: {key}")
        
        return len(errors) == 0, errors
    
    def validate_context(self, context_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate context data.
        
        Args:
            context_data: Context data to validate
            
        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []
        
        # Check required fields
        for field in self.rules["context"]["required_fields"]:
            if field not in context_data:
                errors.append(f"Missing required field: {field}")
        
        # Check string fields
        for field in self.rules["context"]["string_fields"]:
            if field in context_data and not isinstance(context_data[field], str):
                errors.append(f"Field {field} must be a string")
        
        # Check numeric fields
        for field in self.rules["context"]["numeric_fields"]:
            if field in context_data and not isinstance(context_data[field], (int, float)):
                errors.append(f"Field {field} must be a number")
        
        # Check boolean fields
        for field in self.rules["context"]["boolean_fields"]:
            if field in context_data and not isinstance(context_data[field], bool):
                errors.append(f"Field {field} must be a boolean")
        
        # Check enum fields
        for field, valid_values in self.rules["context"]["enum_fields"].items():
            if field in context_data and context_data[field] not in valid_values:
                errors.append(f"Field {field} must be one of: {valid_values}")
        
        # Check max lengths
        for field, max_length in self.rules["context"]["max_lengths"].items():
            if field in context_data and isinstance(context_data[field], str):
                if len(context_data[field]) > max_length:
                    errors.append(f"Field {field} exceeds maximum length of {max_length}")
        
        # Check metadata format
        if "metadata" in context_data and context_data["metadata"] is not None:
            if not isinstance(context_data["metadata"], dict):
                errors.append("Metadata must be a dictionary")
        
        return len(errors) == 0, errors
    
    def validate_relation(self, relation_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate relation data.
        
        Args:
            relation_data: Relation data to validate
            
        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []
        
        # Check required fields
        for field in self.rules["relation"]["required_fields"]:
            if field not in relation_data:
                errors.append(f"Missing required field: {field}")
        
        # Check string fields
        for field in self.rules["relation"]["string_fields"]:
            if field in relation_data and not isinstance(relation_data[field], str):
                errors.append(f"Field {field} must be a string")
        
        # Check numeric fields
        for field in self.rules["relation"]["numeric_fields"]:
            if field in relation_data and not isinstance(relation_data[field], (int, float)):
                errors.append(f"Field {field} must be a number")
        
        # Check boolean fields
        for field in self.rules["relation"]["boolean_fields"]:
            if field in relation_data and not isinstance(relation_data[field], bool):
                errors.append(f"Field {field} must be a boolean")
        
        # Check max lengths
        for field, max_length in self.rules["relation"]["max_lengths"].items():
            if field in relation_data and isinstance(relation_data[field], str):
                if len(relation_data[field]) > max_length:
                    errors.append(f"Field {field} exceeds maximum length of {max_length}")
        
        # Check numeric ranges
        for field, (min_val, max_val) in self.rules["relation"]["numeric_ranges"].items():
            if field in relation_data:
                value = relation_data[field]
                if not (min_val <= value <= max_val):
                    errors.append(f"Field {field} must be between {min_val} and {max_val}")
        
        # Check metadata format
        if "metadata" in relation_data and relation_data["metadata"] is not None:
            if not isinstance(relation_data["metadata"], dict):
                errors.append("Metadata must be a dictionary")
        
        return len(errors) == 0, errors
    
    def validate_jsonl_file(self, file_path: Path, entity_type: str) -> Dict[str, Any]:
        """
        Validate a JSONL file.
        
        Args:
            file_path: Path to JSONL file
            entity_type: Type of entity (memory, context, relation)
            
        Returns:
            Validation results
        """
        results = {
            "file_path": str(file_path),
            "entity_type": entity_type,
            "total_records": 0,
            "valid_records": 0,
            "invalid_records": 0,
            "errors": [],
            "sample_errors": []
        }
        
        if not file_path.exists():
            results["errors"].append("File not found")
            return results
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    results["total_records"] += 1
                    
                    try:
                        data = json.loads(line.strip())
                        
                        # Validate based on entity type
                        if entity_type == "memory":
                            is_valid, errors = self.validate_memory(data)
                        elif entity_type == "context":
                            is_valid, errors = self.validate_context(data)
                        elif entity_type == "relation":
                            is_valid, errors = self.validate_relation(data)
                        else:
                            is_valid = False
                            errors = [f"Unknown entity type: {entity_type}"]
                        
                        if is_valid:
                            results["valid_records"] += 1
                        else:
                            results["invalid_records"] += 1
                            results["errors"].extend([f"Line {line_num}: {error}" for error in errors])
                            
                            # Keep sample errors
                            if len(results["sample_errors"]) < 5:
                                results["sample_errors"].append({
                                    "line": line_num,
                                    "errors": errors
                                })
                    
                    except json.JSONDecodeError as e:
                        results["invalid_records"] += 1
                        error_msg = f"Line {line_num}: Invalid JSON - {str(e)}"
                        results["errors"].append(error_msg)
                        
                        if len(results["sample_errors"]) < 5:
                            results["sample_errors"].append({
                                "line": line_num,
                                "errors": [error_msg]
                            })
        
        except Exception as e:
            results["errors"].append(f"Error reading file: {str(e)}")
        
        return results
    
    def validate_database_integrity(self) -> Dict[str, Any]:
        """
        Validate database integrity.
        
        Returns:
            Validation results
        """
        results = {
            "users": {"total": 0, "valid": 0, "errors": []},
            "contexts": {"total": 0, "valid": 0, "errors": []},
            "memories": {"total": 0, "valid": 0, "errors": []},
            "relations": {"total": 0, "valid": 0, "errors": []},
            "cross_references": {"valid": 0, "errors": []}
        }
        
        try:
            with self.db.get_db() as db:
                from ..database.models import User, Context, Memory, Relation
                
                # Validate users
                users = db.query(User).all()
                results["users"]["total"] = len(users)
                for user in users:
                    if not user.username or not user.email:
                        results["users"]["errors"].append(f"User {user.id} has missing username or email")
                    else:
                        results["users"]["valid"] += 1
                
                # Validate contexts
                contexts = db.query(Context).filter(Context.is_active == True).all()
                results["contexts"]["total"] = len(contexts)
                for context in contexts:
                    if not context.name:
                        results["contexts"]["errors"].append(f"Context {context.id} has missing name")
                    elif not context.owner_id:
                        results["contexts"]["errors"].append(f"Context {context.id} has missing owner_id")
                    else:
                        results["contexts"]["valid"] += 1
                
                # Validate memories
                memories = db.query(Memory).filter(Memory.is_active == True).all()
                results["memories"]["total"] = len(memories)
                for memory in memories:
                    if not memory.title or not memory.content:
                        results["memories"]["errors"].append(f"Memory {memory.id} has missing title or content")
                    elif not memory.owner_id:
                        results["memories"]["errors"].append(f"Memory {memory.id} has missing owner_id")
                    else:
                        results["memories"]["valid"] += 1
                
                # Validate relations
                relations = db.query(Relation).filter(Relation.is_active == True).all()
                results["relations"]["total"] = len(relations)
                for relation in relations:
                    if not relation.name:
                        results["relations"]["errors"].append(f"Relation {relation.id} has missing name")
                    elif not relation.owner_id:
                        results["relations"]["errors"].append(f"Relation {relation.id} has missing owner_id")
                    else:
                        results["relations"]["valid"] += 1
                
                # Validate cross-references
                # Check context references in memories
                for memory in memories:
                    if memory.context_id:
                        context_exists = db.query(Context).filter(
                            Context.id == memory.context_id,
                            Context.is_active == True
                        ).first()
                        if not context_exists:
                            results["cross_references"]["errors"].append(
                                f"Memory {memory.id} references non-existent context {memory.context_id}"
                            )
                        else:
                            results["cross_references"]["valid"] += 1
                
                # Check memory references in relations
                for relation in relations:
                    if relation.source_memory_id:
                        memory_exists = db.query(Memory).filter(
                            Memory.id == relation.source_memory_id,
                            Memory.is_active == True
                        ).first()
                        if not memory_exists:
                            results["cross_references"]["errors"].append(
                                f"Relation {relation.id} references non-existent source memory {relation.source_memory_id}"
                            )
                        else:
                            results["cross_references"]["valid"] += 1
                    
                    if relation.target_memory_id:
                        memory_exists = db.query(Memory).filter(
                            Memory.id == relation.target_memory_id,
                            Memory.is_active == True
                        ).first()
                        if not memory_exists:
                            results["cross_references"]["errors"].append(
                                f"Relation {relation.id} references non-existent target memory {relation.target_memory_id}"
                            )
                        else:
                            results["cross_references"]["valid"] += 1
        
        except Exception as e:
            logger.error(f"Error validating database integrity: {str(e)}")
            results["error"] = str(e)
        
        return results
    
    def generate_validation_report(self, jsonl_path: str) -> Dict[str, Any]:
        """
        Generate a comprehensive validation report.
        
        Args:
            jsonl_path: Path to JSONL data directory
            
        Returns:
            Validation report
        """
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "jsonl_path": jsonl_path,
            "file_validations": [],
            "database_validation": None,
            "summary": {}
        }
        
        jsonl_dir = Path(jsonl_path)
        
        # Validate JSONL files
        for entity_type in ["contexts", "memories", "relations"]:
            file_path = jsonl_dir / f"{entity_type}.jsonl"
            if file_path.exists():
                validation_result = self.validate_jsonl_file(file_path, entity_type[:-1])  # Remove 's'
                report["file_validations"].append(validation_result)
        
        # Validate database integrity
        report["database_validation"] = self.validate_database_integrity()
        
        # Generate summary
        total_files = len(report["file_validations"])
        valid_files = sum(1 for v in report["file_validations"] if v["invalid_records"] == 0)
        
        total_records = sum(v["total_records"] for v in report["file_validations"])
        valid_records = sum(v["valid_records"] for v in report["file_validations"])
        
        report["summary"] = {
            "total_files": total_files,
            "valid_files": valid_files,
            "file_success_rate": (valid_files / total_files * 100) if total_files > 0 else 0,
            "total_records": total_records,
            "valid_records": valid_records,
            "record_success_rate": (valid_records / total_records * 100) if total_records > 0 else 0
        }
        
        return report

def run_validation(jsonl_path: str = None, database_url: str = None):
    """
    Run data validation.
    
    Args:
        jsonl_path: Path to JSONL data directory
        database_url: Database URL
    """
    settings = get_settings()
    
    # Use provided paths or defaults
    jsonl_path = jsonl_path or settings.jsonl_data_path
    database_url = database_url or settings.database_url
    
    # Initialize validator
    db = EnhancedMemoryDB(database_url=database_url)
    validator = DataValidator(db)
    
    try:
        # Generate validation report
        report = validator.generate_validation_report(jsonl_path)
        logger.info(f"Validation completed: {report['summary']}")
        
        return report
    
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        raise
    
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate data integrity")
    parser.add_argument("--jsonl-path", help="Path to JSONL data directory")
    parser.add_argument("--database-url", help="Database URL")
    
    args = parser.parse_args()
    
    # Run validation
    run_validation(args.jsonl_path, args.database_url)