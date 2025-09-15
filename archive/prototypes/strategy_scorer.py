"""
strategy_scorer.py
Tracks success rates of different strategies for performance optimization
"""

import json
from pathlib import Path
from datetime import datetime

class StrategyScorer:
    def __init__(self, stats_file="strategy_stats.json"):
        self.stats_file = Path(stats_file)
        self.stats = self._load_stats()
    
    def _load_stats(self):
        """Load existing stats or create new structure"""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            "domains": {},
            "global_stats": {
                "total_attempts": 0,
                "total_successes": 0,
                "strategy_performance": {}
            }
        }
    
    def record_result(self, domain, intent_name, strategy_name, success=True):
        """Record the result of a strategy attempt"""
        # Initialize domain if not exists
        if domain not in self.stats["domains"]:
            self.stats["domains"][domain] = {}
        
        if intent_name not in self.stats["domains"][domain]:
            self.stats["domains"][domain][intent_name] = {
                "attempts": 0,
                "successes": 0,
                "strategies": {}
            }
        
        # Update domain stats
        domain_stats = self.stats["domains"][domain][intent_name]
        domain_stats["attempts"] += 1
        if success:
            domain_stats["successes"] += 1
        
        # Update strategy stats
        if strategy_name not in domain_stats["strategies"]:
            domain_stats["strategies"][strategy_name] = {
                "attempts": 0,
                "successes": 0
            }
        
        strategy_stats = domain_stats["strategies"][strategy_name]
        strategy_stats["attempts"] += 1
        if success:
            strategy_stats["successes"] += 1
        
        # Update global stats
        global_stats = self.stats["global_stats"]
        global_stats["total_attempts"] += 1
        if success:
            global_stats["total_successes"] += 1
        
        if strategy_name not in global_stats["strategy_performance"]:
            global_stats["strategy_performance"][strategy_name] = {
                "attempts": 0,
                "successes": 0
            }
        
        global_strategy = global_stats["strategy_performance"][strategy_name]
        global_strategy["attempts"] += 1
        if success:
            global_strategy["successes"] += 1
        
        # Save updated stats
        self._save_stats()
    
    def _save_stats(self):
        """Save stats to file"""
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save strategy stats: {e}")
    
    def get_best_strategy(self, domain, intent_name):
        """Get the best performing strategy for a domain/intent"""
        if domain not in self.stats["domains"]:
            return None
        
        if intent_name not in self.stats["domains"][domain]:
            return None
        
        strategies = self.stats["domains"][domain][intent_name]["strategies"]
        best_strategy = None
        best_rate = 0
        
        for strategy_name, stats in strategies.items():
            if stats["attempts"] >= 2:  # Need at least 2 attempts for reliability
                success_rate = stats["successes"] / stats["attempts"]
                if success_rate > best_rate:
                    best_rate = success_rate
                    best_strategy = strategy_name
        
        return best_strategy
    
    def print_stats(self):
        """Print current statistics"""
        global_stats = self.stats["global_stats"]
        total_rate = 0
        if global_stats["total_attempts"] > 0:
            total_rate = global_stats["total_successes"] / global_stats["total_attempts"]
        
        print(f"📊 Strategy Performance Stats:")
        print(f"   Total Success Rate: {total_rate:.2%} ({global_stats['total_successes']}/{global_stats['total_attempts']})")
        print(f"   Domains Tracked: {len(self.stats['domains'])}")
