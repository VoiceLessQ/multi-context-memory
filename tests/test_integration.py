"""
Integration test script for the enhanced MCP Multi-Context Memory System.
This script validates the integration of all new systems and components.
"""
import asyncio
import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from database.enhanced_memory_db import EnhancedMemoryDB
from database.models import Memory, Context, Relation
from utils.compression import CompressionManager
from monitoring.performance_monitor import PerformanceMonitor
from backup.backup_manager import BackupManager
from rollback.rollback_manager import RollbackManager
from api.main import app
from fastapi.testclient import TestClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntegrationTestSuite:
    """Integration test suite for the enhanced MCP Multi-Context Memory System."""
    
    def __init__(self):
        self.test_results: Dict[str, Dict[str, Any]] = {}
        self.db_url = "sqlite:///./test_memory.db"
        self.backup_dir = "./test_backups/"
        self.test_data_dir = "./test_data/"
        
        # Initialize test components
        self.db = EnhancedMemoryDB(self.db_url)
        self.compression_manager = CompressionManager()
        self.performance_monitor = PerformanceMonitor()
        self.backup_manager = BackupManager(self.backup_dir)
        self.rollback_manager = RollbackManager(self.db_url, self.backup_dir)
        self.client = TestClient(app)
        
        # Create test directories
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(self.test_data_dir, exist_ok=True)
    
    async def setup_test_environment(self):
        """Set up the test environment."""
        logger.info("Setting up test environment...")
        
        # Initialize database
        await self.db.initialize()
        
        # Create test context
        test_context = Context(
            name="test_context",
            description="Test context for integration tests"
        )
        await self.db.create_context(test_context)
        
        # Create test memories
        test_memories = [
            Memory(
                content="Test memory 1",
                context_id=1,
                metadata={"type": "test", "priority": "high"}
            ),
            Memory(
                content="Test memory 2 with longer content to test compression capabilities",
                context_id=1,
                metadata={"type": "test", "priority": "medium"}
            ),
            Memory(
                content="Test memory 3",
                context_id=1,
                metadata={"type": "test", "priority": "low"}
            )
        ]
        
        for memory in test_memories:
            await self.db.create_memory(memory)
        
        # Create test relations
        test_relations = [
            Relation(
                from_id=1,
                to_id=2,
                relation_type="related_to",
                metadata={"strength": 0.8}
            ),
            Relation(
                from_id=2,
                to_id=3,
                relation_type="similar_to",
                metadata={"strength": 0.6}
            )
        ]
        
        for relation in test_relations:
            await self.db.create_relation(relation)
        
        logger.info("Test environment setup complete")
    
    async def run_compression_tests(self):
        """Test compression functionality."""
        logger.info("Running compression tests...")
        
        test_results = {
            "name": "Compression Tests",
            "tests": [],
            "passed": 0,
            "failed": 0
        }
        
        # Test compression enable/disable
        try:
            # Enable compression
            await self.db.set_compression_enabled(True)
            assert await self.db.get_compression_enabled() == True
            test_results["tests"].append({
                "name": "Enable Compression",
                "status": "PASSED",
                "details": "Compression successfully enabled"
            })
            test_results["passed"] += 1
            
            # Disable compression
            await self.db.set_compression_enabled(False)
            assert await self.db.get_compression_enabled() == False
            test_results["tests"].append({
                "name": "Disable Compression",
                "status": "PASSED",
                "details": "Compression successfully disabled"
            })
            test_results["passed"] += 1
            
        except Exception as e:
            test_results["tests"].append({
                "name": "Compression Enable/Disable",
                "status": "FAILED",
                "details": str(e)
            })
            test_results["failed"] += 1
        
        # Test compression with data
        try:
            # Create memory with compression enabled
            await self.db.set_compression_enabled(True)
            test_memory = Memory(
                content="This is a test memory with compression enabled",
                context_id=1,
                metadata={"type": "compression_test"}
            )
            await self.db.create_memory(test_memory)
            
            # Retrieve memory and verify content
            retrieved_memory = await self.db.get_memory(test_memory.id)
            assert retrieved_memory.content == test_memory.content
            test_results["tests"].append({
                "name": "Compression with Data",
                "status": "PASSED",
                "details": "Memory content preserved with compression"
            })
            test_results["passed"] += 1
            
        except Exception as e:
            test_results["tests"].append({
                "name": "Compression with Data",
                "status": "FAILED",
                "details": str(e)
            })
            test_results["failed"] += 1
        
        self.test_results["compression"] = test_results
        logger.info(f"Compression tests completed: {test_results['passed']} passed, {test_results['failed']} failed")
    
    async def run_performance_tests(self):
        """Test performance monitoring."""
        logger.info("Running performance tests...")
        
        test_results = {
            "name": "Performance Tests",
            "tests": [],
            "passed": 0,
            "failed": 0
        }
        
        # Test performance monitoring
        try:
            # Start monitoring
            self.performance_monitor.start_monitoring()
            
            # Perform some operations to generate metrics
            for i in range(10):
                memory = Memory(
                    content=f"Performance test memory {i}",
                    context_id=1,
                    metadata={"type": "performance_test"}
                )
                await self.db.create_memory(memory)
            
            # Get performance metrics
            metrics = self.performance_monitor.get_metrics()
            assert "memory_operations" in metrics
            assert "average_response_time" in metrics
            assert "throughput" in metrics
            
            test_results["tests"].append({
                "name": "Performance Monitoring",
                "status": "PASSED",
                "details": "Performance metrics collected successfully"
            })
            test_results["passed"] += 1
            
            # Stop monitoring
            self.performance_monitor.stop_monitoring()
            
        except Exception as e:
            test_results["tests"].append({
                "name": "Performance Monitoring",
                "status": "FAILED",
                "details": str(e)
            })
            test_results["failed"] += 1
        
        # Test threshold alerts
        try:
            # Set a low threshold for testing
            self.performance_monitor.set_threshold("memory_operations", 5)
            
            # Perform operations to trigger threshold
            for i in range(10):
                memory = Memory(
                    content=f"Threshold test memory {i}",
                    context_id=1,
                    metadata={"type": "threshold_test"}
                )
                await self.db.create_memory(memory)
            
            # Check if alert was triggered
            alerts = self.performance_monitor.get_alerts()
            assert len(alerts) > 0
            
            test_results["tests"].append({
                "name": "Threshold Alerts",
                "status": "PASSED",
                "details": "Performance alerts triggered successfully"
            })
            test_results["passed"] += 1
            
        except Exception as e:
            test_results["tests"].append({
                "name": "Threshold Alerts",
                "status": "FAILED",
                "details": str(e)
            })
            test_results["failed"] += 1
        
        self.test_results["performance"] = test_results
        logger.info(f"Performance tests completed: {test_results['passed']} passed, {test_results['failed']} failed")
    
    async def run_backup_tests(self):
        """Test backup functionality."""
        logger.info("Running backup tests...")
        
        test_results = {
            "name": "Backup Tests",
            "tests": [],
            "passed": 0,
            "failed": 0
        }
        
        # Test backup creation
        try:
            backup_path = await self.backup_manager.create_backup(self.db_url)
            assert os.path.exists(backup_path)
            
            test_results["tests"].append({
                "name": "Backup Creation",
                "status": "PASSED",
                "details": f"Backup created successfully at {backup_path}"
            })
            test_results["passed"] += 1
            
        except Exception as e:
            test_results["tests"].append({
                "name": "Backup Creation",
                "status": "FAILED",
                "details": str(e)
            })
            test_results["failed"] += 1
        
        # Test backup restoration
        try:
            # Create a new database for restoration test
            restore_db_url = "sqlite:///./test_restored_memory.db"
            restore_db = EnhancedMemoryDB(restore_db_url)
            await restore_db.initialize()
            
            # Restore from backup
            await self.backup_manager.restore_backup(backup_path, restore_db_url)
            
            # Verify data integrity
            restored_memories = await restore_db.get_memories()
            assert len(restored_memories) > 0
            
            test_results["tests"].append({
                "name": "Backup Restoration",
                "status": "PASSED",
                "details": "Backup restored successfully with data integrity"
            })
            test_results["passed"] += 1
            
        except Exception as e:
            test_results["tests"].append({
                "name": "Backup Restoration",
                "status": "FAILED",
                "details": str(e)
            })
            test_results["failed"] += 1
        
        self.test_results["backup"] = test_results
        logger.info(f"Backup tests completed: {test_results['passed']} passed, {test_results['failed']} failed")
    
    async def run_rollback_tests(self):
        """Test rollback functionality."""
        logger.info("Running rollback tests...")
        
        test_results = {
            "name": "Rollback Tests",
            "tests": [],
            "passed": 0,
            "failed": 0
        }
        
        # Test checkpoint creation
        try:
            checkpoint_id = await self.rollback_manager.create_checkpoint("Test checkpoint")
            assert checkpoint_id is not None
            
            test_results["tests"].append({
                "name": "Checkpoint Creation",
                "status": "PASSED",
                "details": f"Checkpoint created successfully with ID: {checkpoint_id}"
            })
            test_results["passed"] += 1
            
        except Exception as e:
            test_results["tests"].append({
                "name": "Checkpoint Creation",
                "status": "FAILED",
                "details": str(e)
            })
            test_results["failed"] += 1
        
        # Test rollback
        try:
            # Create some data
            for i in range(5):
                memory = Memory(
                    content=f"Rollback test memory {i}",
                    context_id=1,
                    metadata={"type": "rollback_test"}
                )
                await self.db.create_memory(memory)
            
            # Perform rollback
            await self.rollback_manager.rollback_to_checkpoint(checkpoint_id)
            
            # Verify rollback
            memories_after_rollback = await self.db.get_memories()
            # Should only have the original 3 memories
            assert len(memories_after_rollback) == 3
            
            test_results["tests"].append({
                "name": "Rollback Operation",
                "status": "PASSED",
                "details": "Rollback completed successfully"
            })
            test_results["passed"] += 1
            
        except Exception as e:
            test_results["tests"].append({
                "name": "Rollback Operation",
                "status": "FAILED",
                "details": str(e)
            })
            test_results["failed"] += 1
        
        self.test_results["rollback"] = test_results
        logger.info(f"Rollback tests completed: {test_results['passed']} passed, {test_results['failed']} failed")
    
    async def run_api_tests(self):
        """Test API endpoints."""
        logger.info("Running API tests...")
        
        test_results = {
            "name": "API Tests",
            "tests": [],
            "passed": 0,
            "failed": 0
        }
        
        # Test memory endpoints
        try:
            # Create memory
            memory_data = {
                "content": "API test memory",
                "context_id": 1,
                "metadata": {"type": "api_test"}
            }
            response = self.client.post("/memories", json=memory_data)
            assert response.status_code == 200
            assert response.json()["content"] == memory_data["content"]
            
            test_results["tests"].append({
                "name": "Create Memory",
                "status": "PASSED",
                "details": "Memory created successfully via API"
            })
            test_results["passed"] += 1
            
            # Get memory
            memory_id = response.json()["id"]
            response = self.client.get(f"/memories/{memory_id}")
            assert response.status_code == 200
            assert response.json()["id"] == memory_id
            
            test_results["tests"].append({
                "name": "Get Memory",
                "status": "PASSED",
                "details": "Memory retrieved successfully via API"
            })
            test_results["passed"] += 1
            
            # Update memory
            update_data = {"content": "Updated API test memory"}
            response = self.client.put(f"/memories/{memory_id}", json=update_data)
            assert response.status_code == 200
            assert response.json()["content"] == update_data["content"]
            
            test_results["tests"].append({
                "name": "Update Memory",
                "status": "PASSED",
                "details": "Memory updated successfully via API"
            })
            test_results["passed"] += 1
            
            # Delete memory
            response = self.client.delete(f"/memories/{memory_id}")
            assert response.status_code == 200
            
            test_results["tests"].append({
                "name": "Delete Memory",
                "status": "PASSED",
                "details": "Memory deleted successfully via API"
            })
            test_results["passed"] += 1
            
        except Exception as e:
            test_results["tests"].append({
                "name": "Memory CRUD Operations",
                "status": "FAILED",
                "details": str(e)
            })
            test_results["failed"] += 1
        
        # Test context endpoints
        try:
            # Create context
            context_data = {
                "name": "API test context",
                "description": "Test context for API testing"
            }
            response = self.client.post("/contexts", json=context_data)
            assert response.status_code == 200
            assert response.json()["name"] == context_data["name"]
            
            test_results["tests"].append({
                "name": "Create Context",
                "status": "PASSED",
                "details": "Context created successfully via API"
            })
            test_results["passed"] += 1
            
            # Get contexts
            response = self.client.get("/contexts")
            assert response.status_code == 200
            assert len(response.json()) > 0
            
            test_results["tests"].append({
                "name": "Get Contexts",
                "status": "PASSED",
                "details": "Contexts retrieved successfully via API"
            })
            test_results["passed"] += 1
            
        except Exception as e:
            test_results["tests"].append({
                "name": "Context Operations",
                "status": "FAILED",
                "details": str(e)
            })
            test_results["failed"] += 1
        
        # Test relation endpoints
        try:
            # Create relation
            relation_data = {
                "from_id": 1,
                "to_id": 2,
                "relation_type": "api_test_relation",
                "metadata": {"strength": 0.7}
            }
            response = self.client.post("/relations", json=relation_data)
            assert response.status_code == 200
            assert response.json()["relation_type"] == relation_data["relation_type"]
            
            test_results["tests"].append({
                "name": "Create Relation",
                "status": "PASSED",
                "details": "Relation created successfully via API"
            })
            test_results["passed"] += 1
            
            # Get relations
            response = self.client.get("/relations")
            assert response.status_code == 200
            assert len(response.json()) > 0
            
            test_results["tests"].append({
                "name": "Get Relations",
                "status": "PASSED",
                "details": "Relations retrieved successfully via API"
            })
            test_results["passed"] += 1
            
        except Exception as e:
            test_results["tests"].append({
                "name": "Relation Operations",
                "status": "FAILED",
                "details": str(e)
            })
            test_results["failed"] += 1
        
        self.test_results["api"] = test_results
        logger.info(f"API tests completed: {test_results['passed']} passed, {test_results['failed']} failed")
    
    async def run_system_integration_tests(self):
        """Test system integration."""
        logger.info("Running system integration tests...")
        
        test_results = {
            "name": "System Integration Tests",
            "tests": [],
            "passed": 0,
            "failed": 0
        }
        
        # Test compression with backup
        try:
            # Enable compression
            await self.db.set_compression_enabled(True)
            
            # Create some data
            for i in range(5):
                memory = Memory(
                    content=f"Integration test memory {i}",
                    context_id=1,
                    metadata={"type": "integration_test"}
                )
                await self.db.create_memory(memory)
            
            # Create backup
            backup_path = await self.backup_manager.create_backup(self.db_url)
            
            # Verify backup size is smaller due to compression
            db_size = os.path.getsize(self.db_url.replace("sqlite:///", ""))
            backup_size = os.path.getsize(backup_path)
            
            # Backup should be smaller than original database
            assert backup_size < db_size
            
            test_results["tests"].append({
                "name": "Compression with Backup",
                "status": "PASSED",
                "details": "Backup size reduced with compression"
            })
            test_results["passed"] += 1
            
        except Exception as e:
            test_results["tests"].append({
                "name": "Compression with Backup",
                "status": "FAILED",
                "details": str(e)
            })
            test_results["failed"] += 1
        
        # Test performance monitoring with rollback
        try:
            # Start monitoring
            self.performance_monitor.start_monitoring()
            
            # Create some data
            for i in range(10):
                memory = Memory(
                    content=f"Performance rollback test memory {i}",
                    context_id=1,
                    metadata={"type": "performance_rollback_test"}
                )
                await self.db.create_memory(memory)
            
            # Create checkpoint
            checkpoint_id = await self.rollback_manager.create_checkpoint("Performance test checkpoint")
            
            # Get performance metrics
            metrics = self.performance_monitor.get_metrics()
            assert "memory_operations" in metrics
            assert metrics["memory_operations"] >= 10
            
            # Perform rollback
            await self.rollback_manager.rollback_to_checkpoint(checkpoint_id)
            
            # Verify metrics after rollback
            metrics_after = self.performance_monitor.get_metrics()
            # Metrics should reflect the rollback
            assert metrics_after["memory_operations"] < metrics["memory_operations"]
            
            test_results["tests"].append({
                "name": "Performance with Rollback",
                "status": "PASSED",
                "details": "Performance metrics tracked correctly with rollback"
            })
            test_results["passed"] += 1
            
        except Exception as e:
            test_results["tests"].append({
                "name": "Performance with Rollback",
                "status": "FAILED",
                "details": str(e)
            })
            test_results["failed"] += 1
        
        # Test API with backup and rollback
        try:
            # Create data via API
            memory_data = {
                "content": "API backup rollback test memory",
                "context_id": 1,
                "metadata": {"type": "api_backup_rollback_test"}
            }
            response = self.client.post("/memories", json=memory_data)
            assert response.status_code == 200
            
            memory_id = response.json()["id"]
            
            # Create backup
            backup_path = await self.backup_manager.create_backup(self.db_url)
            
            # Create checkpoint
            checkpoint_id = await self.rollback_manager.create_checkpoint("API test checkpoint")
            
            # Update memory via API
            update_data = {"content": "Updated API backup rollback test memory"}
            response = self.client.put(f"/memories/{memory_id}", json=update_data)
            assert response.status_code == 200
            
            # Perform rollback
            await self.rollback_manager.rollback_to_checkpoint(checkpoint_id)
            
            # Verify memory was rolled back
            response = self.client.get(f"/memories/{memory_id}")
            assert response.status_code == 200
            assert response.json()["content"] == memory_data["content"]
            
            test_results["tests"].append({
                "name": "API with Backup and Rollback",
                "status": "PASSED",
                "details": "API operations work correctly with backup and rollback"
            })
            test_results["passed"] += 1
            
        except Exception as e:
            test_results["tests"].append({
                "name": "API with Backup and Rollback",
                "status": "FAILED",
                "details": str(e)
            })
            test_results["failed"] += 1
        
        self.test_results["system_integration"] = test_results
        logger.info(f"System integration tests completed: {test_results['passed']} passed, {test_results['failed']} failed")
    
    async def run_all_tests(self):
        """Run all integration tests."""
        logger.info("Starting integration test suite...")
        
        # Setup test environment
        await self.setup_test_environment()
        
        # Run individual test suites
        await self.run_compression_tests()
        await self.run_performance_tests()
        await self.run_backup_tests()
        await self.run_rollback_tests()
        await self.run_api_tests()
        await self.run_system_integration_tests()
        
        # Generate test report
        await self.generate_test_report()
        
        logger.info("Integration test suite completed")
    
    async def generate_test_report(self):
        """Generate a comprehensive test report."""
        logger.info("Generating test report...")
        
        report = {
            "test_suite": "MCP Multi-Context Memory System Integration Tests",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_results": self.test_results
        }
        
        # Calculate totals
        for category, results in self.test_results.items():
            report["total_tests"] += len(results["tests"])
            report["passed_tests"] += results["passed"]
            report["failed_tests"] += results["failed"]
        
        # Save report
        report_path = os.path.join(self.test_data_dir, "integration_test_report.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Test report saved to {report_path}")
        
        # Print summary
        print("\n" + "="*50)
        print("INTEGRATION TEST SUMMARY")
        print("="*50)
        print(f"Total Tests: {report['total_tests']}")
        print(f"Passed: {report['passed_tests']}")
        print(f"Failed: {report['failed_tests']}")
        print(f"Success Rate: {(report['passed_tests']/report['total_tests']*100):.2f}%")
        print("="*50)
        
        # Print failed tests
        if report['failed_tests'] > 0:
            print("\nFAILED TESTS:")
            for category, results in self.test_results.items():
                for test in results["tests"]:
                    if test["status"] == "FAILED":
                        print(f"- {category}.{test['name']}: {test['details']}")
    
    async def cleanup_test_environment(self):
        """Clean up the test environment."""
        logger.info("Cleaning up test environment...")
        
        # Remove test database files
        for db_file in ["./test_memory.db", "./test_restored_memory.db"]:
            if os.path.exists(db_file):
                os.remove(db_file)
        
        # Remove test backup directory
        if os.path.exists(self.backup_dir):
            for file in os.listdir(self.backup_dir):
                os.remove(os.path.join(self.backup_dir, file))
            os.rmdir(self.backup_dir)
        
        # Remove test data directory
        if os.path.exists(self.test_data_dir):
            for file in os.listdir(self.test_data_dir):
                os.remove(os.path.join(self.test_data_dir, file))
            os.rmdir(self.test_data_dir)
        
        logger.info("Test environment cleaned up")

async def main():
    """Main function to run the integration test suite."""
    test_suite = IntegrationTestSuite()
    
    try:
        await test_suite.run_all_tests()
    finally:
        await test_suite.cleanup_test_environment()

if __name__ == "__main__":
    asyncio.run(main())