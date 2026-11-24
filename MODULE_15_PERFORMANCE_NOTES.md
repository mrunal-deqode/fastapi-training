# Module 15 — Performance & Scalability Notes

**Project:** Recruitment & Hiring Management API
**Branch:** `module-15-performance`
**Date:** 24 November 2026

## 1. N+1 Query Problem

**Problem:** The admin applicant-list endpoint accessed candidate details through a SQLAlchemy relationship, causing additional queries for candidate information.

**Solution:** Implemented `selectinload(Application.candidate)` to eagerly load candidate data.

| Measurement | Before | After |
|---|---:|---:|
| SELECT queries | 10 | 6 |
| Applications tested | 5 | 5 |

**Result:** 40% reduction in SELECT queries. Added a regression test to ensure the query count remains efficient.

## 2. PostgreSQL Indexing

**Problem:** The application-list query filters records using `job_id` and `is_active`.

**Solution:** Added the composite index:

`ix_applications_job_id_is_active`

**Validation:** Used `EXPLAIN (ANALYZE, BUFFERS)` before and after creating the index.

**Observation:** PostgreSQL continued choosing a Sequential Scan because the test table contained only 20 records. Therefore, a measurable query-performance improvement was not established. The index is intended to support this filtering pattern as the table grows.

## 3. Connection Pooling

Configured SQLAlchemy connection pooling:

- `pool_size = 5` (initial configuration)
- `max_overflow = 10`
- `pool_timeout = 30`
- `pool_recycle = 1800`

**Issue observed:** Under heavier concurrent load, PostgreSQL connection-pool exhaustion occurred.

The pool configuration was subsequently considered for increasing to 15 regular connections and 10 overflow connections. The impact of that change still requires verification.

## 4. Load Testing with Locust

Created a Locust script targeting:

- Candidate login
- Job listing
- Job details
- My applications

**Initial recorded test:**

| Metric | Result |
|---|---:|
| Total requests | 1,157 |
| Failed requests | 1 |
| Success rate | 99.91% |
| Average response time | 11.21 ms |
| 95th percentile | 17 ms |

A separate heavier test exposed intermittent failures and connection-pool exhaustion. Further testing is required before treating the API as validated for high concurrency.

## 5. Statelessness and Scalability

- PostgreSQL stores persistent application data.
- Redis is used for job-list caching and failed-login tracking.
- JWT authentication avoids relying on server-local login sessions.
- Shared state should remain in external services rather than process-local memory.

This design supports running multiple API instances behind a load balancer.

## Conclusion

The N+1 issue was fixed and verified with a 40% reduction in SELECT queries. A composite PostgreSQL index was added and evaluated, and Locust testing was introduced to measure API performance.

Further work is needed to validate connection-pool sizing and high-concurrency behavior with larger datasets.

**Module 15 outcome:** Core performance improvements implemented; high-load verification remains ongoing.