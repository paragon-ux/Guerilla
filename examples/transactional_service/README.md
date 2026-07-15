# Transactional Revisioned Service

**Status:** Phase 9 synthetic example

This example is represented by
`guerilla.adapters.synthetic.TransactionalRevisionedServiceAdapter`. It models an
in-process system of record with atomic compare-and-set mutation, monotonic
external revisions, queryable action status, deterministic rejection, and native
idempotency.

It is not a real integration and does not access a network service.
