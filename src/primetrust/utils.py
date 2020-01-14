from functools import wraps


def require_connection(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if getattr(self, '_auth_token', None) is None:
            raise RuntimeError(f'Tried accessing Prime API before calling \'connect\'.')
        return func(self, *args, **kwargs)

    return wrapper
