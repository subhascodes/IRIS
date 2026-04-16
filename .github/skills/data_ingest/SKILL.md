---
name: data_ingest
description: "Use when: loading and validating the insurance policy dataset for governance pipeline. Ensures dataset exists, is readable, contains required columns, and validates data types. Entry point for all agent workflows."
---

# Data Ingest Skill

## Purpose
Load, validate, and cache the insurance policy dataset. Ensures data integrity before risk simulation.

## Input Parameters
```json
{
  "dataset_path": "data/dataset.csv",
  "validate_only": false,
  "cache": true
}
```

## Process

1. **File Check**: Verify `dataset.csv` exists and is readable
2. **Schema Validation**: Confirm all required columns present
3. **Type Validation**: Ensure numeric columns are properly typed
4. **Row Integrity**: Check for null values and duplicates
5. **Caching**: Store in memory for reuse across pipeline steps

## Required Columns
- `policy_id` (string): unique identifier
- `customer_age` (float): age of policyholder
- `vehicle_age` (float): age of vehicle
- `annual_mileage` (float): annual driving miles
- `base_rate` (float): base premium before adjustments
- `current_premium` (float): current premium amount
- `risk_segment` (string): market segment
- `age_group` (string): age band

## Output
```json
{
  "status": "ok",
  "rows": 10000,
  "columns": ["policy_id", "customer_age", ...],
  "timestamp_loaded": "2026-04-14T15:30:00Z",
  "cache_reference": "cache-001-20260414"
}
```

## Error Codes
- `missing_file`: Dataset file not found
- `empty_dataset`: CSV is empty
- `missing_columns`: Required columns absent
- `type_error`: Column contains wrong data type
- `access_denied`: File permissions issue

## Performance
- Typical processing: 50ms - 500ms (depends on dataset size)
- Memory footprint: ~50MB for 10k policies
- Caching reduces subsequent calls to <5ms
