"""
Tests for project context initialization and alignment.

These tests validate that the project context module correctly captures
and enforces the strategic objectives and technical principles from README.md.
"""

import unittest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from context import ProjectContext, PerformanceTargets, CorePrinciples, StrategicPhase


class TestProjectContext(unittest.TestCase):
    """Test project context understanding and principle enforcement"""
    
    def test_core_mission_defined(self):
        """Verify core mission is correctly captured"""
        expected_mission = "Optimizing Gaps Solitaire through advanced chess engine algorithms"
        self.assertEqual(ProjectContext.MISSION, expected_mission)
    
    def test_performance_targets_meet_requirements(self):
        """Verify performance targets match README specifications"""
        perf = ProjectContext.PERFORMANCE
        
        # From README: 50,000+ positions per second
        self.assertGreaterEqual(perf.search_speed_positions_per_second, 50_000)
        
        # From README: 15+ moves ahead in typical positions
        self.assertGreaterEqual(perf.max_search_depth_moves, 15)
        
        # From README: <2 seconds for move recommendations
        self.assertLessEqual(perf.max_response_time_seconds, 2.0)
        
        # From README: <100MB for complete game analysis
        self.assertLessEqual(perf.max_memory_usage_mb, 100)
    
    def test_core_principles_captured(self):
        """Verify all core principles from README are captured"""
        principles = ProjectContext.PRINCIPLES
        
        # Verify DRY principle
        self.assertIn("Don't Repeat Yourself", principles.dry_principle)
        self.assertIn("reusable abstractions", principles.dry_principle)
        
        # Verify SOLID design
        self.assertIn("Single responsibility", principles.solid_design)
        self.assertIn("dependency inversion", principles.solid_design)
        
        # Verify performance-first approach
        self.assertIn("millions of position evaluations", principles.performance_first)
        
        # Verify modular architecture
        self.assertIn("extensible and testable", principles.modular_architecture)
    
    def test_two_phase_strategy_captured(self):
        """Verify two-phase optimization strategy is correctly understood"""
        phases = ProjectContext.STRATEGIC_PHASES
        
        self.assertEqual(len(phases), 2)
        
        # First phase (Blind Strategy)
        first_phase = phases[0]
        self.assertIn("Blind Strategy", first_phase.name)
        self.assertIn("without knowledge of future reshuffles", first_phase.description)
        self.assertIn("Collects data on all three reshuffle layouts", str(first_phase.characteristics))
        
        # Second phase (Perfect Information Strategy)
        second_phase = phases[1]
        self.assertIn("Perfect Information Strategy", second_phase.name)
        self.assertIn("complete knowledge of all phases", second_phase.description)
        self.assertIn("retrograde analysis", str(second_phase.characteristics))
    
    def test_chess_engine_techniques_captured(self):
        """Verify chess engine optimization techniques are documented"""
        techniques = ProjectContext.OPTIMIZATION_TECHNIQUES
        
        # Verify key techniques from README
        required_techniques = [
            "alpha_beta_pruning",
            "transposition_tables", 
            "late_move_reductions",
            "futility_pruning",
            "move_ordering",
            "iterative_deepening"
        ]
        
        for technique in required_techniques:
            self.assertIn(technique, techniques)
            self.assertTrue(len(techniques[technique]) > 0)
    
    def test_tactical_goals_defined(self):
        """Verify immediate tactical goals are captured"""
        goals = ProjectContext.TACTICAL_GOALS
        
        self.assertGreaterEqual(len(goals), 4)
        
        # Check for key tactical concepts
        goals_text = " ".join(goals).lower()
        self.assertIn("first position gaps", goals_text)
        self.assertIn("king traps", goals_text)
        self.assertIn("sequence building", goals_text)
        self.assertIn("row balance", goals_text)
    
    def test_implementation_alignment_validation(self):
        """Test that implementation alignment validation works correctly"""
        
        # Valid implementation descriptions
        valid_descriptions = [
            "This modular performance-optimized component follows DRY principles",
            "SOLID design with single responsibility for high-performance search",
            "Modular architecture enables extensible optimization techniques"
        ]
        
        for description in valid_descriptions:
            self.assertTrue(
                ProjectContext.validate_implementation_alignment(description),
                f"Should accept aligned implementation: {description}"
            )
        
        # Invalid implementation description
        invalid_description = "Legacy monolithic approach with global variables"
        self.assertFalse(
            ProjectContext.validate_implementation_alignment(invalid_description),
            "Should reject non-aligned implementation"
        )
    
    def test_strategic_guidance_comprehensive(self):
        """Verify strategic guidance covers all key areas"""
        guidance = ProjectContext.get_strategic_guidance()
        
        required_areas = ["architecture", "performance", "strategy", "algorithms", "testing", "principles"]
        
        for area in required_areas:
            self.assertIn(area, guidance)
            self.assertTrue(len(guidance[area]) > 0)
        
        # Verify specific guidance content
        self.assertIn("simulator/", guidance["architecture"])
        self.assertIn("50,000", guidance["performance"])
        self.assertIn("two-phase", guidance["strategy"])
        self.assertIn("alpha-beta", guidance["algorithms"])
        self.assertIn("test-driven", guidance["testing"])
        self.assertIn("SOLID", guidance["principles"])


class TestContextIntegration(unittest.TestCase):
    """Test integration of context with existing codebase"""
    
    def test_context_importable(self):
        """Verify context module can be imported without errors"""
        try:
            from context import ProjectContext
            self.assertTrue(hasattr(ProjectContext, 'MISSION'))
            self.assertTrue(hasattr(ProjectContext, 'PERFORMANCE'))
            self.assertTrue(hasattr(ProjectContext, 'PRINCIPLES'))
        except ImportError as e:
            self.fail(f"Context module should be importable: {e}")
    
    def test_performance_targets_are_frozen(self):
        """Verify performance targets are immutable"""
        perf = ProjectContext.PERFORMANCE
        
        with self.assertRaises(Exception):
            # Should not be able to modify frozen dataclass
            perf.search_speed_positions_per_second = 1000
    
    def test_principles_are_frozen(self):
        """Verify core principles are immutable"""
        principles = ProjectContext.PRINCIPLES
        
        with self.assertRaises(Exception):
            # Should not be able to modify frozen dataclass
            principles.dry_principle = "Something else"


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)