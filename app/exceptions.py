class OrderPersistingException(Exception):
    """Exception raised for errors in persisting the order to the database."""

    def __init__(self, message="An error occurred while persisting the order"):
        self.message = message
        super().__init__(self.message)


class OrderPlacementException(Exception):
    """Exception raised for errors during the order placement process."""

    def __init__(self, message="An error occurred while placing the order"):
        self.message = message
        super().__init__(self.message)
