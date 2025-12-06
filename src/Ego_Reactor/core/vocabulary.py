"""
Dynamic Vocabulary Manager with Symbol Birth/Death.
"""

import time
from dataclasses import dataclass, field
from typing import Optional
from Ego_Reactor.core.symbols import Symbol


@dataclass
class SymbolRecord:
    """Tracks the lifecycle of a symbol."""
    symbol: Symbol
    birth_time: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    observation_count: int = 1
    confirming_nodes: set = field(default_factory=set)
    is_permanent: bool = False
    surprise_sum: float = 0.0

    @property
    def idle_time(self) -> float:
        return time.time() - self.last_seen

    def observe(self, node_id: str, surprise: float = 0.0) -> str:
        self.last_seen = time.time()
        self.observation_count += 1
        self.surprise_sum += surprise
        self.confirming_nodes.add(node_id)
        if len(self.confirming_nodes) >= 2 and not self.is_permanent:
            self.is_permanent = True
            return "promoted"
        return "observed"

    def should_die(self, max_idle: float = 3600.0) -> bool:
        if self.is_permanent:
            return self.idle_time > 86400
        if self.observation_count < 3:
            return self.idle_time > (max_idle / 4)
        return self.idle_time > max_idle


class VocabularyManager:
    """Manages dynamic vocabulary for a node or swarm."""

    def __init__(self, max_symbols: int = 200):
        self.max_symbols = max_symbols
        self.symbols: dict[str, SymbolRecord] = {}
        self.births = 0
        self.deaths = 0
        self.promotions = 0
        self._seed_vocabulary()

    def _seed_vocabulary(self):
        core = [
            ("door", "open"), ("door", "closed"),
            ("motion", "detected"), ("motion", "idle"),
            ("light", "high"), ("light", "low"), ("light", "off"),
            ("temperature", "hot"), ("temperature", "cold"),
        ]
        for domain, state in core:
            sym = Symbol(domain, state)
            self.symbols[str(sym)] = SymbolRecord(
                symbol=sym, is_permanent=True, observation_count=10
            )

    def observe(self, symbol: Symbol, node_id: str, surprise: float = 0.0):
        key = str(symbol)
        if key not in self.symbols:
            self.symbols[key] = SymbolRecord(symbol=symbol, confirming_nodes={node_id})
            self.births += 1
            return "born"
        action = self.symbols[key].observe(node_id, surprise)
        if action == "promoted":
            self.promotions += 1
        return action

    def gc(self) -> int:
        dead = [k for k, r in self.symbols.items() if r.should_die()]
        for k in dead:
            del self.symbols[k]
            self.deaths += 1
        return len(dead)

    def get_stats(self) -> dict:
        perm = sum(1 for r in self.symbols.values() if r.is_permanent)
        return {"total": len(self.symbols), "permanent": perm, 
                "births": self.births, "deaths": self.deaths}

    def __len__(self):
        return len(self.symbols)
