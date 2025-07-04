"""
Project Context and Strategic Principles

This module encapsulates the core mission, strategic objectives, and technical principles
of the GapBeater project to ensure all development activities maintain strict alignment
with documented goals and architectural constraints.
"""

from typing import Dict, List, NamedTuple
from dataclasses import dataclass


@dataclass(frozen=True)
class PerformanceTargets:
    """Performance constraints and targets as defined in project documentation"""
    search_speed_positions_per_second: int = 50_000
    max_search_depth_moves: int = 15
    max_response_time_seconds: float = 2.0
    max_memory_usage_mb: int = 100


@dataclass(frozen=True)
class CorePrinciples:
    """Fundamental technical principles that must guide all implementation decisions"""
    dry_principle: str = "Don't Repeat Yourself - Shared components and reusable abstractions"
    solid_design: str = "Single responsibility, open/closed, dependency inversion"
    performance_first: str = "Optimized for millions of position evaluations per second"
    modular_architecture: str = "Easily extensible and testable components"


class StrategicPhase(NamedTuple):
    """Represents a phase in the two-pass optimization strategy"""
    name: str
    description: str
    characteristics: List[str]


class ProjectContext:
    """
    Centralized repository of project context, strategic objectives, and technical constraints.
    
    This class serves as the single source of truth for ensuring all development decisions
    align with the project's documented goals and principles.
    """
    
    # Core Mission
    MISSION = "Optimizing Gaps Solitaire through advanced chess engine algorithms"
    
    # Performance Targets
    PERFORMANCE = PerformanceTargets()
    
    # Technical Principles
    PRINCIPLES = CorePrinciples()
    
    # Two-Phase Strategic Planning
    STRATEGIC_PHASES = [
        StrategicPhase(
            name="First Simulation (Blind Strategy)",
            description="Analyzes initial deal without knowledge of future reshuffles",
            characteristics=[
                "Finds best possible end position after simulating all moves",
                "Collects data on all three reshuffle layouts as entered by user",
                "Provides move recommendations for each phase as they occur"
            ]
        ),
        StrategicPhase(
            name="Second Simulation (Perfect Information Strategy)",
            description="Re-analyzes entire game sequence with complete knowledge of all phases",
            characteristics=[
                "Optimizes strategy across all reshuffles simultaneously",
                "May recommend suboptimal early moves for superior later positions",
                "Employs retrograde analysis working backwards from winning positions"
            ]
        )
    ]
    
    # Chess Engine Optimization Techniques
    OPTIMIZATION_TECHNIQUES = {
        "alpha_beta_pruning": "Eliminates inferior move sequences early",
        "transposition_tables": "Caches position evaluations to avoid redundant calculations",
        "late_move_reductions": "Searches promising moves deeper while reducing depth for unlikely candidates",
        "futility_pruning": "Eliminates moves that cannot improve the position significantly",
        "move_ordering": "Prioritizes moves that create correct sequences or advantageous gap positions",
        "iterative_deepening": "Provides increasingly better solutions within time constraints"
    }
    
    # Immediate Tactical Goals
    TACTICAL_GOALS = [
        "Create First Position Gaps: Priority is opening gaps in first column where 2s can be placed",
        "Avoid King Traps: Minimize creating gaps immediately after Kings (permanently unplayable)",
        "Sequence Building: Once a 2 is placed, focus on extending that sequence as far as possible",
        "Row Balance: Maintain relatively even progress across all four rows to maximize reshuffle potential"
    ]
    
    @classmethod
    def validate_implementation_alignment(cls, implementation_description: str) -> bool:
        """
        Validates whether a proposed implementation aligns with project principles.
        
        Args:
            implementation_description: Description of the proposed implementation
            
        Returns:
            bool: True if implementation aligns with documented principles
            
        Note:
            This method should be used to reject any implementation that contradicts
            stated architectural goals or violates core principles.
        """
        # Basic validation criteria - can be extended as needed
        required_alignments = [
            "performance" in implementation_description.lower(),
            "modular" in implementation_description.lower() or "module" in implementation_description.lower(),
            any(principle.lower() in implementation_description.lower() 
                for principle in ["dry", "solid", "single responsibility"])
        ]
        
        return any(required_alignments)
    
    @classmethod
    def get_strategic_guidance(cls) -> Dict[str, str]:
        """
        Provides strategic guidance for development decisions based on project context.
        
        Returns:
            Dict containing key guidance principles for development
        """
        return {
            "architecture": "Follow planned simulator/ module structure with game_state, move_gen, evaluator, search, optimizer",
            "performance": f"Target {cls.PERFORMANCE.search_speed_positions_per_second:,} positions/second with <{cls.PERFORMANCE.max_response_time_seconds}s response time",
            "strategy": "Implement two-phase optimization: blind first pass, then perfect information strategy",
            "algorithms": "Adapt chess engine techniques (alpha-beta, transposition tables, iterative deepening)",
            "testing": "Use test-driven development for core algorithms with performance benchmarking",
            "principles": "Maintain DRY, SOLID design with modular, extensible components"
        }