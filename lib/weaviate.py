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
    web_summarys_class_obj = {
        "class": "WebExtract",
        "description": "Website Text Extractions",
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
                "description": "Raw Content that got extracted",
                "name": "raw",
                "moduleConfig": {
                    "text2vec-transformers": {
                        "vectorizePropertyName": "false",
                        "skip": "true"
                        }
                }
            },
            {
                "dataType": [
                    "string"
                ],
                "description": "Fact List",
                "name": "facts"
            }
        ]

    }
    server_class_obj = {
        "class": "Server",
        "description": "Discord Servers",
        "properties": [
            {
                "dataType": [
                    "number"
                ],
                "description": "Discord Unique ID of the Channel",
                "name": "ServerID"
            },
            {
                "dataType": [
                    "string"
                ],
                "description": "Servername in Discord",
                "name": "server_name"
            }
        ]

    }
    channel_class_obj = {
        "class": "Channel",
        "description": "Discord Channels",
        "properties": [
            {
                "dataType": [
                    "number"
                ],
                "description": "Discord Unique ID of the Channel",
                "name": "ChannelID"
            },
            {
                "dataType": [
                    "string"
                ],
                "description": "Channelname in Discord",
                "name": "channel_name"
            }
        ]

    }
    users_class_obj = {
        "class": "User",
        "description": "Authors of Discord Messages",
        "properties": [
            {
                "dataType": [
                    "number"
                ],
                "description": "Discord Unique ID of the User",
                "name": "UserID"
            },
            {
                "dataType": [
                    "string"
                ],
                "description": "The Username of the User",
                "name": "Username"
            },
            {
                "dataType": [
                    "string"
                ],
                "description": "The nick of the User",
                "name": "Nick"
            }
        ]
    }

    messages_class_obj = {
        "class": "Messages",
        "description": "Discord Messages",
                       "properties": [
        {
            "dataType": [
                "number"
            ],
            "description": "Discord Unique ID of the Message",
            "name": "MessageID"
        },
        {
            "dataType": [
                "string"
            ],
            "description": "The Message content",
            "name": "Content"
        }
    ]
}
    client.schema.create_class(example_class_obj)
    client.schema.create_class(server_class_obj)
    client.schema.create_class(channel_class_obj)
    client.schema.create_class(users_class_obj)
    client.schema.create_class(messages_class_obj)
    client.schema.create_class(web_summarys_class_obj)
    client.schema.create_class(memory_class_obj)
# Create Cross-References

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
