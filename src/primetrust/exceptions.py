class PrimeTrustError(Exception):
    def __init__(self, message, data):
        super(PrimeTrustError, self).__init__(message)
        self.data = data
