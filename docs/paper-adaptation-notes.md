# Paper adaptation notes

Do not copy production thresholds blindly. The reference paper uses a much larger corpus; DSIC-2906 must audit empirical match-rate distributions and choose feasible `n_sample` values for its own index size.

Implementation fidelity checklist:
- same similarity metric across exact and approximate search;
- predicate-agnostic shared graph;
- verified TwoHop traversal;
- verified AdaptiveL frontier expansion and Algorithm-3 scaling;
- log all deviations from the anchor implementation;
- keep original AdaptiveL results even if RC-AdaptiveL is evaluated.
