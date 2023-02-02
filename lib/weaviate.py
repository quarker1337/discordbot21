from lib.utils import (
    logger,
)
from lib.constants import (
    WEAVICLIENT,
    ADMINUSER
)

client = WEAVICLIENT


# New Schema Create Function, this only needs to run once!
def createschema():
    # Check if Schema already exists, if so abort.


    # Creating Basic Schema that we need to save Example Conversations
    memory_class_obj = {
        "class": "Memorys",
        "description": "Example Conversations",
        "properties": [
            {
                "dataType": [
                    "string"
                ],
                "description": "Title of Memory",
                "name": "Title"
            },
            {
                "dataType": [
                    "string"
                ],
                "description": "Memory Content",
                "name": "Content"
            },
            {
                "dataType": [
                    "int"
                ],
                "description": "Word Count/Tokens",
                "name": "Tokens"
            }
        ]
    }

    example_class_obj = {
        "class": "Examples",
        "description": "Example Conversations",
        "properties": [
            {
                "dataType": [
                    "number"
                ],
                "description": "messageID",
                "name": "messageID"
            },
            {
                "dataType": [
                    "string"
                ],
                "description": "Example Conversation",
                "name": "Content"
            }
        ]

    }

    client.schema.create_class(example_class_obj)
    client.schema.create_class(memory_class_obj)

async def deletedb():
    client.schema.delete_all()

async def countobjects(classname):
    result = (
        client.query
        .aggregate(classname)
        .with_meta_count()
        .do()
    )
    return result

async def listobjects(classname):
    result = (
        client.query
        .get(classname, ['content', '_additional {id}'] )
        .with_limit(3)
        .do()
    )
    return result

async def listnearobjects(classname, searchterm):
    nearText = {
        "concepts": [searchterm],
        "distance": 0.7,
    }
    result = (
        client.query
        .get(classname, ['content', '_additional {id}'] )
        .with_near_text(nearText)
        .with_limit(5)
        .do()
    )
    print(result)
    return result

async def deleteobject(classname, objectid):
    result = client.data_object.delete(objectid, classname)
    return result
