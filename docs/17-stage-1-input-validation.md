<!-- 17-stage-1-input-validation-proposal.md -->
<!-- Target: docs/17-stage-1-input-validation.md -->

### v1.1 Note — Demo (QuickMatch & Filter)
- **QuickMatch** requires both `Column` and `Value`; if either is missing, omit both.
- **operation=update** requires a match strategy (QuickMatch or `settings.match`) in Stage 1.
- **Filter.Type** accepted: `odata`, `caml xml`, `caml text`; normalize to lowercase during normalize step.
