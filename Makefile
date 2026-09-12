PYTHON ?= python3

.PHONY: audit corpus embed queries filters groundtruth index dev freeze single compound resource stability ablation report test

audit:
	bash scripts/00_audit_corpus.sh
corpus:
	bash scripts/01_build_corpus.sh
embed:
	bash scripts/02_embed.sh
queries:
	bash scripts/03_build_queries.sh
filters:
	bash scripts/04_build_filters.sh
groundtruth:
	bash scripts/05_groundtruth.sh
index:
	bash scripts/06_build_index.sh
dev:
	bash scripts/07_dev_benchmark.sh
freeze:
	bash scripts/08_freeze_params.sh
single:
	bash scripts/09_main_single_filters.sh
compound:
	bash scripts/10_main_compound_filters.sh
resource:
	bash scripts/11_resource_benchmark.sh
stability:
	bash scripts/12_stability.sh
ablation:
	bash scripts/13_ablation.sh
report:
	bash scripts/14_report.sh

test:
	$(PYTHON) -m pytest
