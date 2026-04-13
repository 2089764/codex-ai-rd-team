.PHONY: help rd rd-echo test sync-profiles

OBJ ?=
RUNTIME_DIR ?= ./runtime
AGENT_CLIENT ?= auto

help:
	@echo "可用命令:"
	@echo "  make rd OBJ=\"修复登录500 bug\"         # 默认 auto（优先 codex，回退 echo）"
	@echo "  make rd-echo OBJ=\"修复登录500 bug\"    # 强制 echo（离线演示）"
	@echo "  make test                                # 运行测试"
	@echo "  make sync-profiles                       # 同步 A1 tech profiles"

rd:
	@if [ -z "$(strip $(OBJ))" ]; then \
		echo '请提供 OBJ，例如: make rd OBJ="修复登录500 bug"'; \
		exit 2; \
	fi
	@python3 -m orchestrator.cli orchestrate \
		--objective "$(OBJ)" \
		--agent-client "$(AGENT_CLIENT)" \
		--runtime-dir "$(RUNTIME_DIR)"

rd-echo:
	@if [ -z "$(strip $(OBJ))" ]; then \
		echo '请提供 OBJ，例如: make rd-echo OBJ="修复登录500 bug"'; \
		exit 2; \
	fi
	@python3 -m orchestrator.cli orchestrate \
		--objective "$(OBJ)" \
		--agent-client echo \
		--runtime-dir "$(RUNTIME_DIR)"

test:
	@python3 -m unittest discover -s tests -v

sync-profiles:
	@python3 scripts/sync_tech_profiles.py
