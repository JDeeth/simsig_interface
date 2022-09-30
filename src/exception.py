class SimSigException(Exception):
    """Base class for simsig_interface exceptions"""


class InvalidLogin(SimSigException):
    """Attempted to connect to payware sim with invalid user credentials"""
