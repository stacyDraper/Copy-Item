<!-- 08-json-contracts-proposal.md -->
<!-- Target: docs/08-json-contracts.md -->

## v1.1 Note — Demo (KnownTypes & MapRaw)
- **KnownTypes**: Treat `ListTypes` and `LibraryTypes` as arrays in canonical form. If a string is provided at runtime, normalize it to arrays in Stage 1.
- **Map vs MapRaw**: Keep `MapRaw` as the original string for diagnostics; `Map` holds the parsed JSON value used by later stages.
