class ChessError(Exception):
    """Base exception for ChessERP library"""
    pass

class AuthError(ChessError):
    """Authentication failed"""
    pass

class ApiError(ChessError):
    """API returned an error status"""
    def __init__(self, status_code: int, message: str, details: str = None):
        self.status_code = status_code
        self.message = message
        self.details = details
        super().__init__(f"Status {status_code}: {message} - {details}")
