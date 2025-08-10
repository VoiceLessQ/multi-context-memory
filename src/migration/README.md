# Migration System for Enhanced Memory System

This directory contains the migration system for the enhanced memory system.

## Components

### `migration_manager.py`
This file contains the `MigrationManager` class that manages the migration process from old format to new format.

### `run_migration.py`
This script runs the migration process.

## Features

- Batch processing of memories
- Compression of existing memories
- Lazy loading support
- Progress tracking
- Backup before migration
- Rollback on failure
- Detailed reporting
- Dry run mode

## Running the Migration

### Prerequisites
- Python 3.8+
- Required dependencies (see `requirements.txt`)
- Existing database with memories to migrate

### Running the Migration Script

1. Navigate to the project root directory
2. Run the migration script:

```bash
python src/migration/run_migration.py --db-url sqlite:///./data/memory.db --batch-size 100
```

### Options

- `--db-url`: Database URL (default: `sqlite:///./data/memory.db`)
- `--batch-size`: Batch size for migration (default: 100)
- `--dry-run`: Dry run mode (no actual migration)
- `--verbose`: Verbose logging

### Example Commands

```bash
# Dry run
python src/migration/run_migration.py --dry-run

# Actual migration with batch size of 50
python src/migration/run_migration.py --batch-size 50

# Migration with verbose logging
python src/migration/run_migration.py --verbose
```

## Migration Process

1. **Initialization**
   - Create migration record
   - Set up migration manager

2. **Pre-Migration**
   - Create backup
   - Get total count of memories

3. **Batch Processing**
   - Process memories in batches
   - Compress content
   - Enable lazy loading
   - Preserve relations
   - Track progress

4. **Post-Migration**
   - Generate report
   - Update migration status
   - Log statistics

## Migration Statistics

The migration system tracks the following statistics:

- Total memories
- Migrated memories
- Failed memories
- Success rate
- Compression ratio
- Lazy loading ratio
- Performance metrics

## Testing

### Running Migration Tests

1. Navigate to the project root directory
2. Run the migration test script:

```bash
python tests/test_migration.py
```

### Test Coverage

The test suite covers:
- Dry run mode
- Actual migration
- Batch processing
- Compression
- Lazy loading
- Relations preservation
- Progress tracking
- Reporting

## Troubleshooting

### Common Issues

1. **Migration Fails**
   - Check logs for errors
   - Verify database connection
   - Ensure sufficient disk space
   - Check permissions

2. **Performance Issues**
   - Reduce batch size
   - Optimize database queries
   - Increase system resources

3. **Data Integrity Issues**
   - Verify backup
   - Check migration report
   - Use rollback if necessary

### Rollback

If migration fails, the system will automatically rollback to the previous state using the backup.

## Migration Report

After migration, a detailed report is generated with the following information:

- Migration ID
- Total memories
- Migrated memories
- Failed memories
- Success rate
- Compression ratio
- Lazy loading ratio
- Performance metrics
- Elapsed time

## Best Practices

1. **Always Backup**
   - The system creates a backup before migration
   - Verify the backup is valid

2. **Test with Dry Run**
   - Use `--dry-run` to test the migration process
   - Verify the expected changes

3. **Monitor Progress**
   - Check the migration progress regularly
   - Monitor system resources

4. **Check Logs**
   - Review logs for any errors
   - Check for warnings

5. **Verify Results**
   - After migration, verify the data
   - Check compression and lazy loading

## Adding New Features

To add new features to the migration system:

1. Extend the `MigrationManager` class
2. Add new migration methods
3. Update the migration script
4. Add tests for new features
5. Update documentation

## Integration with Enhanced Memory System

The migration system integrates with the following components:

- Enhanced Memory Database
- Compression Manager
- Memory Monitor
- Backup Manager
- Rollback Manager