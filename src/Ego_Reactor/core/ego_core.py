"""
EgoCore - The predictive engine at the heart of each node.

EgoCore maintains a simple but powerful model: it tracks symbol
transition probabilities (what typically follows what) and uses
this to predict upcoming events. Surprise = prediction error.

This is inspired by predictive coding in neuroscience - the brain
constantly predicts sensory input and only "notices" (propagates)
prediction errors.

The key insight: most of the world is boring and predictable.
Door opens, door closes. Motion detected, motion stops. 
EgoCore learns these patterns and stops wasting energy on them.
"""

from dataclasses import dataclass, field
from typing import Optional
from collections import defaultdict
import math

from Ego_Reactor.core.symbols import Symbol, Event, EventType


@dataclass
class Prediction:
    """A prediction about what symbol comes next."""
    symbol: Symbol
    probability: float      # 0.0 to 1.0
    confidence: float       # How sure we are about this prediction
    expected_time: float    # When we expect it (relative seconds)


class EgoCore:
    """
    Predictive core that learns symbol patterns and computes surprise.
    
    Architecture:
    - Layer 0 (implicit): Raw sensor novelty detection
    - Layer 1: Symbol transition model (this class)
    - Layer 2: Meta-predictor for precision weighting (coming soon)
    
    The transition model is a simple first-order Markov chain with
    exponential decay for temporal patterns.
    """
    
    def __init__(self, node_id: str, learning_rate: float = 0.1):
        self.node_id = node_id
        self.learning_rate = learning_rate
        
        # Transition counts: transitions[from_symbol][to_symbol] = count
        # Using defaultdict for automatic initialization
        self.transitions: dict[str, dict[str, float]] = defaultdict(
            lambda: defaultdict(float)
        )
        
        # Symbol timing: avg time between observations
        # timing[symbol] = (mean_interval, observation_count)
        self.timing: dict[str, tuple[float, int]] = {}
        
        # Last observed symbol and timestamp (for transition learning)
        self.last_symbol: Optional[Symbol] = None
        self.last_time: float = 0.0
        
        # Current predictions (what we expect to see)
        self.predictions: dict[str, Prediction] = {}
        
        # Precision weight (Layer 2) - adjusted dynamically
        # Higher = more sensitive, Lower = more filtering
        self.epsilon: float = 0.3  # Surprise threshold
        self.base_epsilon: float = 0.3
        
        # Stats for debugging/visualization
        self.total_events: int = 0
        self.suppressed_events: int = 0  # Events below epsilon (not propagated)
    
    def observe(self, event: Event) -> Event:
        """
        Process an incoming event, update model, compute surprise.
        
        This is the main entry point. It:
        1. Computes surprise by comparing against predictions
        2. Updates the transition model
        3. Generates new predictions
        4. Returns the event with surprise attached
        
        Args:
            event: The incoming event (surprise may be 0 initially)
            
        Returns:
            The same event with computed surprise value
        """
        self.total_events += 1
        symbol = event.symbol
        symbol_key = str(symbol)
        current_time = event.timestamp
        
        # --- Compute Surprise ---
        surprise = self._compute_surprise(symbol, current_time)
        
        # --- Update Transition Model ---
        if self.last_symbol is not None:
            last_key = str(self.last_symbol)
            # Increment transition count with decay
            self.transitions[last_key][symbol_key] += 1.0
            
            # Normalize (soft normalization via decay)
            total = sum(self.transitions[last_key].values())
            for k in self.transitions[last_key]:
                self.transitions[last_key][k] /= (1 + self.learning_rate)
            self.transitions[last_key][symbol_key] = (
                self.transitions[last_key][symbol_key] * (1 + self.learning_rate)
            )
        
        # --- Update Timing Model ---
        if symbol_key in self.timing:
            mean_interval, count = self.timing[symbol_key]
            if self.last_time > 0:
                new_interval = current_time - self.last_time
                # Running average
                new_mean = (mean_interval * count + new_interval) / (count + 1)
                self.timing[symbol_key] = (new_mean, count + 1)
        else:
            self.timing[symbol_key] = (1.0, 1)  # Initial estimate
        
        # --- Update State ---
        self.last_symbol = symbol
        self.last_time = current_time
        
        # --- Generate New Predictions ---
        self._update_predictions(symbol, current_time)
        
        # --- Track Suppression Stats ---
        if surprise < self.epsilon:
            self.suppressed_events += 1
        
        # Return event with computed surprise
        return Event(
            symbol=event.symbol,
            timestamp=event.timestamp,
            event_type=event.event_type,
            surprise=surprise,
            confidence=event.confidence,
            source_node=self.node_id,
            hops=event.hops
        )
    
    def _compute_surprise(self, symbol: Symbol, current_time: float) -> float:
        """
        Compute surprise as inverse of prediction probability.
        
        Surprise formula: -log(P(symbol)) normalized to [0, 1]
        If we predicted this symbol with high probability, low surprise.
        If unexpected, high surprise.
        """
        symbol_key = str(symbol)
        
        # Check if we predicted this symbol
        if symbol_key in self.predictions:
            pred = self.predictions[symbol_key]
            # Surprise is inverse of probability
            # Using -log(p) clamped and normalized
            if pred.probability > 0.01:
                raw_surprise = -math.log(pred.probability)
                # Normalize: -log(1.0) = 0, -log(0.01) ≈ 4.6
                surprise = min(1.0, raw_surprise / 4.6)
            else:
                surprise = 1.0  # Very unexpected
        else:
            # No prediction at all = moderately surprising
            # (not 1.0 because absence of prediction isn't as bad as wrong prediction)
            surprise = 0.7
        
        # Boost surprise if timing is off
        if self.last_symbol is not None:
            last_key = str(self.last_symbol)
            if last_key in self.timing:
                expected_interval, _ = self.timing[last_key]
                actual_interval = current_time - self.last_time
                if expected_interval > 0:
                    timing_ratio = abs(actual_interval - expected_interval) / expected_interval
                    timing_surprise = min(0.3, timing_ratio * 0.1)  # Cap timing boost
                    surprise = min(1.0, surprise + timing_surprise)
        
        return surprise
    
    def _update_predictions(self, symbol: Symbol, current_time: float):
        """Generate predictions for what comes next."""
        self.predictions.clear()
        symbol_key = str(symbol)
        
        if symbol_key in self.transitions:
            # Get transition probabilities
            trans = self.transitions[symbol_key]
            total = sum(trans.values())
            
            if total > 0:
                for next_sym, count in trans.items():
                    prob = count / total
                    if prob > 0.05:  # Only track meaningful predictions
                        # Estimate timing
                        expected_time = 1.0
                        if next_sym in self.timing:
                            expected_time, _ = self.timing[next_sym]
                        
                        self.predictions[next_sym] = Prediction(
                            symbol=Symbol(*next_sym.split(":")),
                            probability=prob,
                            confidence=min(1.0, total / 10),  # More data = more confident
                            expected_time=expected_time
                        )
    
    def check_negative_events(self, current_time: float) -> list[Event]:
        """
        Check for expected-but-missing events (negative evidence).
        
        This is Grok's suggestion #3 - noticing absences.
        If we predicted something with high confidence but it didn't
        happen within 2x the expected interval, emit a negative event.
        
        Returns:
            List of negative events (may be empty)
        """
        negative_events = []
        
        for sym_key, pred in list(self.predictions.items()):
            if pred.confidence > 0.7 and pred.probability > 0.6:
                # High-confidence prediction
                time_since_last = current_time - self.last_time
                deadline = pred.expected_time * 2.0
                
                if time_since_last > deadline:
                    # Expected but missing!
                    neg_event = Event(
                        symbol=pred.symbol,
                        event_type=EventType.NEGATIVE,
                        surprise=0.5,  # Moderate surprise for absence
                        confidence=pred.confidence,
                        source_node=self.node_id
                    )
                    negative_events.append(neg_event)
                    # Remove from predictions to avoid repeat firing
                    del self.predictions[sym_key]
        
        return negative_events
    
    def adjust_precision(self, recent_surprise_rate: float):
        """
        Layer 2: Adjust epsilon based on meta-prediction of activity.
        
        If recent surprise rate is high, lower epsilon (be more sensitive).
        If things have been calm, raise epsilon (filter more aggressively).
        
        This is the "precision weighting" from predictive coding.
        """
        if recent_surprise_rate > 0.5:
            # Lots of surprises - lower threshold to catch more
            self.epsilon = max(0.1, self.base_epsilon * 0.7)
        elif recent_surprise_rate < 0.1:
            # Very calm - raise threshold to save energy
            self.epsilon = min(0.6, self.base_epsilon * 1.5)
        else:
            # Normal - return to baseline
            self.epsilon = self.base_epsilon
    
    def get_stats(self) -> dict:
        """Return statistics for monitoring."""
        suppression_rate = (
            self.suppressed_events / self.total_events 
            if self.total_events > 0 else 0.0
        )
        return {
            "node_id": self.node_id,
            "total_events": self.total_events,
            "suppressed_events": self.suppressed_events,
            "suppression_rate": f"{suppression_rate:.1%}",
            "epsilon": f"{self.epsilon:.2f}",
            "vocabulary_size": len(set(
                k for trans in self.transitions.values() for k in trans.keys()
            )),
            "active_predictions": len(self.predictions),
        }
