# GapBeater - Gaps Solitaire Optimizer

An intelligent simulator and strategy optimizer for Gaps (also known as Addiction) Solitaire that uses advanced game tree search algorithms adapted from chess engine optimization techniques.

## Table of Contents

- [Game Rules](#game-rules)
- [Strategic Approach](#strategic-approach)
- [Project Architecture](#project-architecture)
- [Installation & Usage](#installation--usage)
- [Development Roadmap](#development-roadmap)
- [Technical Implementation](#technical-implementation)

## Game Rules

### Initial Setup

- Standard 52-card deck arranged in 4 rows of 13 positions each
- All four Aces are removed, creating 4 gaps randomly distributed across the board
- Goal: Arrange cards in sequential order by suit (2, 3, 4, 5, 6, 7, 8, 9, 10, J, Q, K) in each row

### Movement Rules

- **Legal Moves**: A card can only be moved into a gap if the card immediately to the left of the gap is exactly one rank lower than the moving card and of the same suit
- **Examples**:
  - If there's a 5♥ to the left of a gap, only the 6♥ can fill that gap
  - If there's a 2♠ to the left of a gap, only the 3♠ can fill that gap
- **Unplayable Gaps**:
  - Gaps immediately to the right of a King (no card higher than King)
  - Gaps immediately to the right of another gap

### Special Rules

- **Starting Sequences**: The only way to start a sequence is by placing a 2 in the first position of any row. The first position in a row is the only position that doesn't require a lower card to its left.
- **Immutable Sequences**: Once a 2 is correctly placed in the first position, it and any subsequent correctly placed same-suit cards in sequence (2, 3, 4... of same suit) become locked and cannot be moved, even during reshuffles.
- **Maximum Moves**: At any given time, there are at most 4 legal moves available (one per gap)

### Reshuffle Mechanism

- When no legal moves remain, all cards except correctly placed sequences are collected
- Correctly placed cards remain immutable sequences and are not included in any reshuffles
- The reshuffled cards are randomly redistributed to the empty positions
- The 4 gaps are also shuffled and randomly placed among the redistributed cards
- **Reshuffle Limit**: Maximum of 3 reshuffles per game
- **Win Condition:** All 4 suits need to be arranged in rows, starting with the 2 and ending with the K; the last space in each row will be the gap. This is considered a win
- **End Condition**: If no legal moves exist after the 3rd reshuffle, the game ends

## Strategic Approach

The gapbeater app does not play the game, deal the cards or perform any randomization. It accepts input from the user, starting with the row positions in the initial deal of a game. With that information, it begins running simulations to find best possible moves. Assuming it does not achieve the win condition from the initial card positions, once the app has determined a best possible set of moves, it gives those to the player and allows the player to re-input the result of the first redeal (which doesn't affect any correctly placed sequences). The app continues this approach until either achieving a win condition or an end condition. After reaching either a win or non-winning end, the app then restarts the simulation, this time having foreknowledge of what each shuffle will look like. In its second phase, it can use this foreknowledge to improve upon its original strategy.

### Immediate Tactical Goals

1. **Create First Position Gaps**: Priority is opening gaps in the first column where 2s can be placed
2. **Avoid King Traps**: Minimize creating gaps immediately after Kings, as these become permanently unplayable
3. **Sequence Building**: Once a 2 is placed, focus on extending that sequence as far as possible
4. **Row Balance**: Maintain relatively even progress across all four rows to maximize reshuffle potential

### Multi-Phase Strategic Planning

GapBeater implements a unique two-pass optimization strategy:

#### First Simulation (Blind Strategy)

- Analyzes the initial deal without knowledge of future reshuffles
- Finds the best possible end position after simulating all moves
- Collects data on all three reshuffle layouts as they're entered by the user
- Provides move recommendations for each phase as they occur

#### Second Simulation (Perfect Information Strategy)

- Re-analyzes the entire game sequence with complete knowledge of all four phases
- Optimizes strategy across all reshuffles simultaneously
- May recommend seemingly suboptimal moves in early phases that set up superior positions in later phases
- Employs retrograde analysis to work backwards from winning positions

### Advanced Optimization Techniques

The simulator applies chess engine optimization methods adapted for solitaire:

- **Alpha-Beta Pruning**: Eliminates inferior move sequences early
- **Transposition Tables**: Caches position evaluations to avoid redundant calculations
- **Late Move Reductions**: Searches promising moves deeper while reducing depth for unlikely candidates
- **Futility Pruning**: Eliminates moves that cannot improve the position significantly
- **Move Ordering**: Prioritizes moves that create correct sequences or advantageous gap positions
- **Iterative Deepening**: Provides increasingly better solutions within time constraints

## Project Architecture

```md
gapbeater/
├── main.py                 # Entry point and game flow coordination
├── src/
│   ├── game.py            # GameManager - handles game state and user interaction
│   ├── input_handler.py   # User input collection and validation
│   ├── layout.py          # Board visualization and rendering
│   ├── validator.py       # Card input validation and normalization
│   └── simulator/         # (Planned) Advanced search and optimization components
│       ├── game_state.py  # Efficient board representation
│       ├── move_gen.py    # Legal move generation
│       ├── evaluator.py   # Position evaluation and scoring
│       ├── search.py      # Tree search algorithms
│       └── optimizer.py   # Multi-phase strategic planning
├── saves/                 # Saved game states in JSON format
└── tests/                 # Unit and integration tests
```

## Installation & Usage

### Prerequisites

- Python 3.8+
- No external dependencies required for basic functionality

### Running the Application

```bash
git clone <repository-url>
cd gapbeater
python main.py
```

### Basic Workflow

1. **Create New Game**: Enter cards as dealt (e.g., "4c" for 4 of Clubs, "x" for 10, "-" for gaps)
2. **Get Analysis**: Receive move recommendations from the simulator
3. **Execute Moves**: Follow recommendations and update the board
4. **Handle Reshuffles**: Enter new card positions after each reshuffle
5. **Multi-Phase Optimization**: After all reshuffles are known, get optimized strategy

### Input Format

- **Cards**: `rank + suit` (e.g., "2h", "xd", "ks", where "x" represents 10)
- **Ranks**: 2-9, x (10), j (Jack), q (Queen), k (King)
- **Suits**: c (Clubs), d (Diamonds), h (Hearts), s (Spades)
- **Gaps**: "-" or "g"
- **Save & Exit**: "z"

## Development Roadmap

### Phase 1: Core Engine (Current)

- [x] Basic game state management and input handling
- [ ] Game state representation and move generation
- [ ] Position evaluation system
- [ ] Basic minimax search with alpha-beta pruning

### Phase 2: Advanced Optimization

- [ ] Transposition tables and caching
- [ ] Advanced pruning techniques (LMR, futility pruning)
- [ ] Move ordering and history heuristics
- [ ] Performance monitoring and tuning tools

### Phase 3: Strategic Intelligence

- [ ] Multi-phase strategic planning
- [ ] Retrograde analysis for optimal cross-phase strategy
- [ ] Machine learning integration for position evaluation
- [ ] Parallel processing and search optimization

### Phase 4: User Experience

- [ ] Enhanced visualization and analysis tools
- [ ] Strategy explanation and educational features
- [ ] Performance benchmarking and statistics
- [ ] Export and analysis of game sequences

## Technical Implementation

### Core Principles

- **DRY (Don't Repeat Yourself)**: Shared components and reusable abstractions
- **SOLID Design**: Single responsibility, open/closed, dependency inversion
- **Performance First**: Optimized for millions of position evaluations per second
- **Modular Architecture**: Easily extensible and testable components

### Key Algorithms

- **Modified Minimax**: Adapted for single-player sequential decision making
- **Zobrist Hashing**: Efficient position caching and transposition tables
- **Iterative Deepening**: Anytime algorithm providing progressive improvement
- **Strategic Evaluation**: Multi-factor scoring considering immediate and long-term benefits

### Performance Targets

- **Search Speed**: 50,000+ positions per second
- **Search Depth**: 15+ moves ahead in typical positions
- **Response Time**: <2 seconds for move recommendations
- **Memory Usage**: <100MB for complete game analysis

## Contributing

This project follows iterative development with emphasis on:

- Test-driven development for core algorithms
- Performance benchmarking for optimization components
- Code review focusing on maintainability and efficiency
- Documentation of strategic insights and algorithm improvements
