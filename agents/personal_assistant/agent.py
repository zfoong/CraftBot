# -*- coding: utf-8 -*-
"""
PersonalAssistantAgent
========

"""

from __future__ import annotations

import importlib.util
from importlib import import_module
from pathlib import Path

import yaml

from core.agent_base import AgentBase
from core.logger import logger


class PersonalAssistantAgent(AgentBase):
    # Factory for Docker entrypoint / tests
    @classmethod
    def from_bundle(cls, bundle_dir: str | Path) -> "PersonalAssistantAgent":
        bundle_path = Path(bundle_dir).resolve()
        cfg = yaml.safe_load((bundle_path / "config.yaml").read_text())
        return cls(cfg, bundle_path)

    def __init__(self, cfg: dict, bundle_path: Path):
        self._bundle_path = Path(bundle_path)
        self._cfg = cfg
        
        super().__init__(
            data_dir=cfg.get("data_dir", "core/data"),
            chroma_path=str(self._bundle_path / cfg.get("rag_dir", "rag_docs")),
            llm_provider=cfg.get("llm_provider", "byteplus"),
        )

    # -------- AgentBase hooks ----------------------------------------- #

    def _generate_role_info_prompt(self) -> str:
        return (
            "You are an intelligent personal assistant for professionals and executives."
        )

if __name__ == "__main__":  
    import asyncio

    bundle_dir = Path(__file__).parent  
    agent = PersonalAssistantAgent.from_bundle(bundle_dir)
    asyncio.run(agent.run())