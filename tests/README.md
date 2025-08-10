# Test Suite for Enhanced Memory System

This directory contains test scripts for the enhanced memory system.

## Test Scripts

### `test_new_data.py`
This script tests the enhanced memory system with new data only. It verifies that:
- Memory creation works with compression
- Memory search works with lazy loading
- Memory retrieval works with lazy loading
- Memory monitoring collects correct metrics
- Dashboard generation works
- Performance meets expectations

### `test_config.py`
This file contains configuration settings for the test suite.

### `run_test_new_data.py`
This script runs the test suite for new data.

## Running Tests

### Prerequisites
- Python 3.8+
- Required dependencies (see `requirements.txt`)

### Running the Test Suite

1. Navigate to the project root directory
2. Run the test runner script:

```bash
python tests/run_test_new_data.py
```

### Running Individual Tests

You can also run individual test functions directly:

```bash
python -m tests.test_new_data
```

## Test Configuration

The test configuration is defined in `test_config.py`. You can modify:
- Database URL
- Test data directory
- Backup directory
- Log directory
- Test user settings
- Context settings
- Compression settings
- Lazy loading settings
- Performance monitoring settings
- Test cleanup settings

## Test Data

The test suite generates test data including:
- Small memories
- Medium memories
- Large memories
- Very large memories

## Test Coverage

The test suite covers:
- Memory creation with compression
- Memory search with lazy loading
- Memory retrieval with lazy loading
- Memory monitoring
- Dashboard generation
- Performance testing
- Data cleanup

## Test Output

Test output is logged to:
- Console
- `logs/test_new_data.log`

## Test Results

After running the tests, you should see output similar to:

```
INFO:__main__:Starting test with new data...
INFO:__main__:Testing memory creation with compression...
INFO:__main__:Created memory 1 in 0.0012 seconds
INFO:__main__:Memory size: 45 bytes
INFO:__main__:Compressed: True
...
INFO:__main__:All tests completed successfully!
```

## Troubleshooting

If you encounter issues:
1. Ensure all dependencies are installed
2. Check that the database directory is writable
3. Verify that the log directory exists
4. Check that the test configuration is correct

## Adding New Tests

To add new tests:
1. Create a new test function in `test_new_data.py`
2. Add the test to the `main()` function
3. Update the test configuration if needed
4. Update this README file

## Test Environment

The test suite creates a separate test environment to avoid affecting the production database.