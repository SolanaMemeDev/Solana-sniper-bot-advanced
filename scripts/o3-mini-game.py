import curses
import random
import time
import platform
from termcolor import colored

# For Windows, use winsound to beep
if platform.system() == "Windows":
    import winsound

def play_sound():
    """
    Play a simple beep sound.
    On Windows, uses winsound.Beep; otherwise uses curses.beep.
    """
    if platform.system() == "Windows":
        winsound.Beep(440, 150)
    else:
        curses.beep()  # On some systems this may not be very “fun”, but it's terminal sound!

def main():
    # Display a colorful welcome screen using termcolor
    print(colored("==========================================", "magenta"))
    print(colored("  Welcome to the Terminal Snake Game!", "green", attrs=["bold"]))
    print(colored("  Enjoy retro colors and fun beep sounds.", "cyan"))
    print(colored("  (PS: There are a couple of bugs in the code for testing!)", "yellow"))
    print(colored("==========================================", "magenta"))
    print(colored("Press Enter to begin...", "yellow"))
    input()  # Wait for user input before starting

    # Use curses.wrapper to set up and clean up the terminal properly.
    curses.wrapper(game_loop)

def game_loop(stdscr):
    # --- Initialize curses settings ---
    curses.curs_set(0)          # Hide the cursor
    stdscr.nodelay(1)           # Do not block for user input
    stdscr.timeout(100)         # Refresh every 100ms

    # Initialize color pairs for use with curses
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Snake body color
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)    # Food color
    # (BUG INTENTIONAL:) We will later call curses.color_pair(3) for the snake's head, but we never initialize pair 3.

    sh, sw = stdscr.getmaxyx()  # Screen height and width

    # --- Initialize snake starting position ---
    snake_x = sw // 4
    snake_y = sh // 2
    snake = [
        [snake_y, snake_x],
        [snake_y, snake_x - 1],
        [snake_y, snake_x - 2]
    ]

    # --- Place the first food item ---
    food = [sh // 2, sw // 2]
    stdscr.addch(food[0], food[1], curses.ACS_PI, curses.color_pair(2))

    key = curses.KEY_RIGHT  # Start by moving right
    score = 0

    # --- Main Game Loop ---
    while True:
        next_key = stdscr.getch()
        if next_key != -1:
            key = next_key

        # Calculate new head position based on input
        head = snake[0].copy()
        if key == curses.KEY_DOWN:
            head[0] += 1
        elif key == curses.KEY_UP:
            head[0] -= 1
        elif key == curses.KEY_LEFT:
            head[1] -= 1
        elif key == curses.KEY_RIGHT:
            head[1] += 1

        snake.insert(0, head)

        # --- Collision with boundaries ---
        # (BUG INTENTIONAL:) This boundary check uses sh and sw directly,
        # which means the snake dies if it touches row 0 or column 0 or exactly sh or sw.
        if head[0] in [0, sh] or head[1] in [0, sw]:
            play_sound()
            msg = "Game Over! Score: " + str(score)
            stdscr.addstr(sh // 2, sw // 2 - len(msg) // 2, msg)
            stdscr.refresh()
            time.sleep(2)
            break

        # --- Collision with self ---
        if head in snake[1:]:
            play_sound()
            msg = "Game Over! Score: " + str(score)
            stdscr.addstr(sh // 2, sw // 2 - len(msg) // 2, msg)
            stdscr.refresh()
            time.sleep(2)
            break

        # --- Check if snake eats the food ---
        if head == food:
            score += 1
            play_sound()
            # (BUG INTENTIONAL:) New food is placed randomly without checking if it spawns on the snake's body.
            food = [random.randint(1, sh - 2), random.randint(1, sw - 2)]
            stdscr.addch(food[0], food[1], curses.ACS_PI, curses.color_pair(2))
        else:
            # Remove the snake's tail (clear the last segment)
            tail = snake.pop()
            stdscr.addch(tail[0], tail[1], ' ')

        # --- Draw the snake's head ---
        # (BUG INTENTIONAL:) Using color_pair(3) even though it was never initialized.
        stdscr.addch(snake[0][0], snake[0][1], curses.ACS_CKBOARD, curses.color_pair(3))

        stdscr.refresh()

if __name__ == "__main__":
    main()
