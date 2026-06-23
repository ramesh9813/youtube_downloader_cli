from .console import read_input
from .parsing import is_exit_command


def choose_session_attempts(current):
    print(f"\nCurrent attempts: {current}")
    while True:
        selected = read_input(
            "Enter the number of attempts, or e to keep the current value: "
        )
        if is_exit_command(selected):
            return current
        if selected.isdigit() and int(selected) > 0:
            attempts = int(selected)
            print(
                f"Attempts changed to {attempts}. "
                "This will be used until you change it or exit."
            )
            return attempts
        print("Enter a whole number greater than 0.")
