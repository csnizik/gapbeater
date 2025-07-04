# GapBeater Project Context and Development Guidelines

This document serves as the definitive reference for all development decisions, ensuring strict alignment with the project's stated goals, strategic objectives, and technical principles.

## Core Mission
Optimize Gaps Solitaire through advanced chess engine algorithms, providing intelligent move recommendations via sophisticated game tree search and multi-phase strategic planning.

## Strategic Objectives

### Primary Goals
1. **Performance Excellence**: Achieve 50,000+ position evaluations per second
2. **Strategic Intelligence**: Implement two-phase optimization (blind → perfect information)
3. **Algorithmic Sophistication**: Adapt chess engine techniques for solitaire optimization
4. **User Experience**: Provide <2 second response times for move recommendations

### Core Game Understanding
- **4-row, 13-column board** with 52 cards (Aces removed, creating 4 gaps)
- **Sequential ordering goal**: Arrange each row as 2-3-4-5-6-7-8-9-10-J-Q-K by suit
- **Movement constraints**: Cards can only move to gaps where left neighbor is exactly one rank lower, same suit
- **Immutable sequences**: Correctly placed sequences starting with 2 cannot be moved
- **Reshuffle mechanics**: Maximum 3 reshuffles, preserving correct sequences

## Two-Phase Simulation Strategy

### Phase 1: Blind Strategy
- Analyze initial deal without knowledge of future reshuffles
- Find optimal moves for current position
- Collect reshuffle data as entered by user
- Provide real-time move recommendations

### Phase 2: Perfect Information Strategy  
- Re-analyze entire game with complete knowledge of all 4 phases
- Optimize strategy across all reshuffles simultaneously
- May recommend seemingly suboptimal early moves for superior late-game positions
- Employ retrograde analysis working backwards from winning positions

## Technical Architecture Principles

### Core Design Principles
- **DRY (Don't Repeat Yourself)**: Shared components and reusable abstractions
- **SOLID Design**: Single responsibility, open/closed, dependency inversion
- **Performance First**: Optimized for millions of position evaluations per second
- **Modular Architecture**: Easily extensible and testable components

### Key Algorithmic Approaches
- **Modified Minimax**: Adapted for single-player sequential decision making
- **Alpha-Beta Pruning**: Eliminate inferior move sequences early
- **Transposition Tables**: Cache position evaluations (Zobrist hashing)
- **Iterative Deepening**: Progressive improvement within time constraints
- **Late Move Reductions**: Search promising moves deeper
- **Futility Pruning**: Eliminate insignificant moves
- **Move Ordering**: Prioritize sequence-building and advantageous gap positions

### Performance Targets
- **Search Speed**: 50,000+ positions per second
- **Search Depth**: 15+ moves ahead in typical positions  
- **Response Time**: <2 seconds for move recommendations
- **Memory Usage**: <100MB for complete game analysis

## Development Standards

### Code Quality Requirements
- Test-driven development for core algorithms
- Performance benchmarking for optimization components
- Code review focusing on maintainability and efficiency
- Documentation of strategic insights and algorithm improvements

### Architectural Constraints
- All components must follow single responsibility principle
- Interfaces should be designed for extensibility (open/closed principle)
- Dependencies should be injected, not hardcoded
- Performance-critical code must be benchmarked
- Memory usage must be monitored and optimized

### Decision Framework
Every development decision must be evaluated against:
1. **Performance Impact**: Does this maintain our 50k+ positions/second target?
2. **Strategic Alignment**: Does this support the two-phase optimization strategy?
3. **Architectural Integrity**: Does this follow SOLID principles and modular design?
4. **Game Logic Accuracy**: Does this correctly implement Gaps Solitaire rules?
5. **Extensibility**: Does this support future algorithm enhancements?

## Prohibited Patterns
- Monolithic functions that violate single responsibility
- Hardcoded algorithms that cannot be swapped or extended
- Performance bottlenecks in critical paths
- Memory leaks or unbounded memory growth
- Game rule violations or shortcuts
- Breaking changes to established interfaces without clear migration path

## Required Implementation Phases

### Phase 1: Core Engine (Current Priority)
- [x] Basic game state management and input handling
- [ ] Efficient game state representation
- [ ] Legal move generation with game rule validation
- [ ] Position evaluation system with multi-factor scoring
- [ ] Basic minimax search with alpha-beta pruning

### Phase 2: Advanced Optimization
- [ ] Transposition tables with Zobrist hashing
- [ ] Advanced pruning techniques (LMR, futility pruning)
- [ ] Move ordering and history heuristics
- [ ] Performance monitoring and tuning tools

### Phase 3: Strategic Intelligence
- [ ] Multi-phase strategic planning implementation
- [ ] Retrograde analysis for optimal cross-phase strategy
- [ ] Machine learning integration for position evaluation
- [ ] Parallel processing and search optimization

### Phase 4: User Experience
- [ ] Enhanced visualization and analysis tools
- [ ] Strategy explanation and educational features
- [ ] Performance benchmarking and statistics
- [ ] Export and analysis of game sequences

This document must be consulted for every significant development decision to ensure unwavering adherence to the project's strategic vision and technical standards.