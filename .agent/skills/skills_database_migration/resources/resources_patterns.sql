-- Standard SQL Migration Patterns

### Adding Column (Zero Downtime)
ALTER TABLE table_name ADD COLUMN column_name data_type;
UPDATE table_name SET column_name = default_value WHERE column_name IS NULL;
ALTER TABLE table_name ALTER COLUMN column_name SET NOT NULL;

### Renaming Column (3-Phase)
-- 1. Add new column
-- 2. Dual-write
-- 3. Drop old
