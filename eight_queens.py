"""
Eight Queens Solver
Places 8 queens on a chessboard so no queen threatens another,
and displays the solution graphically using matplotlib.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches


def solve_queens(n=8):
    """Find one solution to the N-Queens problem using backtracking.

    Returns a list of length n where result[col] = row of the queen in that column.
    """
    cols = []  # cols[i] = row assigned to queen in column i

    def is_safe(row, col):
        for c, r in enumerate(cols):
            if r == row or abs(r - row) == abs(c - col):
                return False
        return True

    def backtrack(col):
        if col == n:
            return True
        for row in range(n):
            if is_safe(row, col):
                cols.append(row)
                if backtrack(col + 1):
                    return True
                cols.pop()
        return False

    backtrack(0)
    return cols


def draw_board(queens):
    """Draw the chessboard with queens using matplotlib."""
    n = len(queens)

    fig, ax = plt.subplots(figsize=(8, 8))
    fig.suptitle("Eight Queens Solution", fontsize=18, fontweight="bold")

    # Draw squares
    for row in range(n):
        for col in range(n):
            color = "#F0D9B5" if (row + col) % 2 == 0 else "#B58863"
            square = patches.Rectangle((col, row), 1, 1, facecolor=color)
            ax.add_patch(square)

    # Draw queens
    for col, row in enumerate(queens):
        ax.text(
            col + 0.5,
            row + 0.5,
            "\u265B",
            fontsize=36,
            ha="center",
            va="center",
            color="#222222",
        )

    # Labels
    ax.set_xlim(0, n)
    ax.set_ylim(0, n)
    ax.set_xticks([i + 0.5 for i in range(n)])
    ax.set_xticklabels(list("abcdefgh"), fontsize=14)
    ax.set_yticks([i + 0.5 for i in range(n)])
    ax.set_yticklabels([str(i + 1) for i in range(n)], fontsize=14)
    ax.tick_params(length=0)
    ax.set_aspect("equal")

    # Remove the outer frame
    for spine in ax.spines.values():
        spine.set_visible(False)

    plt.tight_layout()
    plt.savefig("eight_queens.png", dpi=150, bbox_inches="tight")
    print("Board saved to eight_queens.png")
    plt.show()


def main():
    queens = solve_queens(8)
    print("Solution found!")
    print(f"Queen positions (column -> row): {queens}")
    print()

    # Print a text representation as well
    n = len(queens)
    print("    " + "   ".join(list("abcdefgh")))
    print("  ┌" + "───┬" * (n - 1) + "───┐")
    for row in range(n - 1, -1, -1):
        row_str = f"{row + 1} │"
        for col in range(n):
            if queens[col] == row:
                row_str += " ♛ │"
            else:
                row_str += "   │"
        print(row_str)
        if row > 0:
            print("  ├" + "───┼" * (n - 1) + "───┤")
    print("  └" + "───┴" * (n - 1) + "───┘")
    print()

    draw_board(queens)


if __name__ == "__main__":
    main()
