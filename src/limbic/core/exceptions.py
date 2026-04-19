
class CognitiveException(Exception):
    """Base class for exceptions in the limbic system that require cognitive regression."""
    def __init__(self, message, component=None, severity="medium"):
        super().__init__(message)
        self.component = component
        self.severity = severity
