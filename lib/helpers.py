from enum import Enum


class ObjectType(Enum):
    '''
    Represents any object on managebac (that the api will deal with)
    '''
    event = 0
    message = 1
    unknown = 2
    files = 3
    file_ = 4


def get_type_from_url(url):
    '''
    Guesses the object type from the url

    Returns:
        An :class:`ObjectType` emum
    '''
    if 'events' in url:
        return ObjectType.event

    if 'messages' in url:
        return ObjectType.message

    if 'cf.managebac.com' in url:
        return ObjectType.file_

    if 'assets' in url:
        return ObjectType.file

    return ObjectType.unknown
    
