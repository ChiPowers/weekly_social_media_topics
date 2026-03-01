# agent/budget.py


class BudgetExceededError(Exception):
    """Raised when an API call would exceed the configured per-run budget."""
    pass


class BudgetTracker:
    """
    Tracks API calls made during a single pipeline run.
    Call budget.charge(n) BEFORE making any API call.
    Raises BudgetExceededError if the call would exceed the limit.
    """

    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.used = 0

    def charge(self, n: int = 1) -> None:
        """
        Declare intent to make n API calls.
        Raises BudgetExceededError BEFORE the call is made if it would exceed the budget.
        Increments the counter only after the check passes.
        """
        if self.used + n > self.limit:
            raise BudgetExceededError(
                f"API call budget exceeded: would use {self.used + n} calls "
                f"but limit is {self.limit}. Halting cleanly."
            )
        self.used += n

    @property
    def remaining(self) -> int:
        """API calls remaining before budget is exhausted."""
        return self.limit - self.used
