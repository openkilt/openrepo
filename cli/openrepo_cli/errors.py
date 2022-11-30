
class OpenRepoApiException(Exception):
    def __init__(self, msg, error_content=''):
        self.error_content = error_content
        return super().__init__(msg)

class ORNon200ResponseException(OpenRepoApiException):
    def __init__(self, msg, response_code, error_content=''):
        self.response_code = response_code
        return super().__init__(msg, error_content=error_content)

class ORUnauthorizedException(OpenRepoApiException):
    pass

class ORConnectionException(OpenRepoApiException):
    pass

class ORInvalidRequestException(OpenRepoApiException):
    pass