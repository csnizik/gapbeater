"""
Development Guidelines for GapBeater

This file provides specific implementation guidelines for developers working
on GapBeater to ensure all code changes strictly adhere to the project's
strategic objectives and technical principles as documented in PROJECT_CONTEXT.md.

## Code Review Checklist

Before submitting any code changes, verify:

### Performance Requirements
- [ ] Does this maintain 50,000+ position evaluations per second?
- [ ] Are response times under 2 seconds for move recommendations?
- [ ] Is memory usage optimized (<100MB for complete analysis)?
- [ ] Have you benchmarked performance-critical changes?

### Architectural Alignment
- [ ] Does this follow SOLID design principles?
- [ ] Is the single responsibility principle maintained?
- [ ] Are dependencies properly injected rather than hardcoded?
- [ ] Is the code modular and easily testable?

### Game Logic Accuracy
- [ ] Does this correctly implement Gaps Solitaire rules?
- [ ] Are immutable sequences properly preserved during reshuffles?
- [ ] Is move generation following legal move constraints?
- [ ] Does evaluation consider all strategic factors?

### Strategic Implementation
- [ ] Does this support the two-phase optimization strategy?
- [ ] Can this component work with both blind and perfect information modes?
- [ ] Is retrograde analysis capability preserved?
- [ ] Are multi-phase considerations maintained?

## Implementation Patterns

### Component Creation
Always use factory functions for component creation:
```python
# Good
move_generator = create_move_generator()
evaluator = create_evaluator(custom_weights)
search_engine = create_search_engine(move_generator, evaluator)

# Avoid direct instantiation when dependencies are involved
```

### Error Handling
Follow defensive programming principles:
```python
# Validate inputs early
if not (0 <= row < GameState.ROWS and 0 <= col < GameState.COLS):
    raise ValueError(f"Invalid position: row={row}, col={col}")

# Handle edge cases explicitly
if not legal_moves:
    return SearchResult(best_move=None, score=evaluation.total_score, ...)
```

### Performance Optimization
- Use type hints for better performance and clarity
- Implement efficient algorithms (prefer O(log n) over O(n) when possible)
- Cache expensive computations when appropriate
- Use dataclasses for immutable data structures

### Testing Requirements
- All new components must have unit tests
- Performance-critical code must have benchmarks
- Integration tests for multi-component features
- Test both success and failure scenarios

## Forbidden Patterns

### Do NOT implement these anti-patterns:
- Monolithic classes that violate single responsibility
- Hardcoded algorithms without abstraction
- Direct file I/O in core algorithms (use dependency injection)
- Performance bottlenecks in search critical paths
- Breaking changes to established interfaces without migration
- Game rule violations or incorrect implementations

## Strategic Considerations

When implementing new features, always consider:

1. **Two-Phase Strategy Impact**: How does this feature work in both blind strategy and perfect information modes?

2. **Cross-Phase Optimization**: Could this feature benefit from information sharing between game phases?

3. **Algorithm Extensibility**: Can this component be enhanced with machine learning or parallel processing later?

4. **Performance Scaling**: How does this perform with deeper search depths or larger transposition tables?

## Code Quality Standards

### Required Standards
- Type hints on all public methods
- Docstrings following Google/NumPy style
- Clear variable and method names
- No magic numbers (use named constants)
- Comprehensive error handling

### Code Organization
- Keep modules focused on single responsibilities
- Group related functionality in packages
- Use clear naming conventions
- Maintain consistent code style

## Algorithm Implementation

### Search Algorithms
When implementing search improvements:
- Maintain the alpha-beta pruning framework
- Ensure transposition table compatibility
- Support iterative deepening
- Consider move ordering impact

### Evaluation Functions
When modifying position evaluation:
- Maintain the multi-factor approach
- Ensure weights can be customized
- Support both tactical and strategic considerations
- Test against known good/bad positions

### Move Generation
When updating move generation:
- Verify all Gaps Solitaire rules are followed
- Ensure immutable sequence handling
- Optimize for search algorithm requirements
- Maintain correctness over speed

## Future Enhancement Areas

Areas planned for future development:
1. Machine learning integration for position evaluation
2. Parallel processing for search optimization
3. Enhanced visualization and analysis tools
4. Performance monitoring and auto-tuning
5. Advanced pruning techniques (LMR, futility pruning)

All implementations should be designed with these future enhancements in mind.

## Getting Help

When in doubt about implementation decisions:
1. Consult PROJECT_CONTEXT.md for strategic alignment
2. Review existing component implementations for patterns
3. Check test cases for expected behavior
4. Consider performance implications before optimization

Remember: The goal is not just working code, but code that advances the strategic objectives of creating the most sophisticated Gaps Solitaire optimizer possible.