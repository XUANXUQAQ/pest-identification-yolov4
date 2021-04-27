class ResBody:
    def __init__(self, code, message, data):
        self.__code = code
        self.__message = message
        self.__result = data

    def get_code(self):
        return self.__code

    def get_message(self):
        return self.__message

    def get_result(self):
        return self.__result


def success(data=None):
    return toJSON(ResBody(20000, '成功', data))


def error(message):
    return toJSON(ResBody(40000, message, None))


def toJSON(res):
    return {
        'code': res.get_code(),
        'message': res.get_message(),
        'result': res.get_result()
    }
