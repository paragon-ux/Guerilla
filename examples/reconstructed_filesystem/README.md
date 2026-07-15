# Reconstructed Filesystem

**Status:** Phase 9 synthetic example

This example is represented by
`guerilla.adapters.synthetic.ReconstructedFilesystemAdapter`. It models state
reconstructed from files under a declared temporary root, content-hash external
revisions, rename and deletion observations, partial multi-file failure, no
native rollback, and adapter-emulated idempotency.

It must be used only with temporary test roots during Phase 9.
