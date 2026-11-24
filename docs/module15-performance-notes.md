# Module 15 – Performance & Scalability Notes

## 1. N+1 Query Optimization

Endpoint: Admin applicant list by job.

- Problem: Accessing candidate details through lazy-loaded relationships caused additional SELECT queries.
- Solution: Used SQLAlchemy `selectinload(Application.candidate)`.
- Measurement: For 5 applications, SELECT queries decreased from 10 to 6.
- Result: 40% fewer SELECT queries.
- Added a regression test to verify efficient query execution.

## 2. Database Indexing

Added index through Alembic migration `498a98cde98d`:

- Index: `ix_applications_job_id_is_active`
- Columns: `(job_id, is_active)`
- Purpose: Support application filtering by job and active status.

EXPLAIN ANALYZE findings:
- Before: PostgreSQL used a Sequential Scan.
- After: PostgreSQL still used a Sequential Scan.
- Reason: The applications table contained only 20 rows.
- Conclusion: The index was created successfully, but measurable performance improvement could not be demonstrated with this small dataset.

Indexes improve suitable read queries but add storage and write overhead.

## 3. Load Testing with Locust

Test configuration:
- Concurrent users: 20
- Spawn rate: 2 users/second
- Duration: 2 minutes
- Endpoints: Login, job listing, job details, and my applications.

First recorded run:
- Total requests: 1,157
- Failures: 1
- Success rate: 99.91%
- Average response time: 11.21 ms
- Median response time: 9 ms
- 95th percentile: 17 ms

The single failure was reported as `Status: 0`, indicating no valid HTTP response. Application logs showed no corresponding application error. The cause was not conclusively identified.

## 4. Database Connection Pooling

Configured SQLAlchemy:
- `pool_size = 5`
- `max_overflow = 10`
- `pool_timeout = 30`
- `pool_recycle = 1800`

This permits up to 15 connections per application process. Multiple worker processes can increase the total connection count.

## 5. Statelessness and Horizontal Scaling

- PostgreSQL stores persistent application data.
- Redis stores shared job-list cache data and login rate-limit counters.
- JWT is used for authentication.
- No obvious module-level global dictionaries or lists were found in the inspected application files.

Because request-related shared data is stored in external services rather than process-local memory, multiple API instances can share the same application state.

## Conclusion

Module 15 work covered N+1 query optimization, database indexing, connection pooling, Locust load testing, and stateless application design. The query-count reduction was verified; the index was validated but its performance benefit requires a larger dataset.
