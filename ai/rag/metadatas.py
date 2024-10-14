from langchain.chains.query_constructor.schema import AttributeInfo

NewsMetaData = [
    AttributeInfo(
        name="year", description="The year of the news created", type="integer"
    ),
    AttributeInfo(
        name="month",
        description="The month of the news created",
        type="integer",
    ),
    AttributeInfo(
        name="day", description="The day of the news created", type="integer"
    ),
    AttributeInfo(
        name="hour", description="The hour of the news created", type="integer"
    ),
    AttributeInfo(
        name="created_at", description="The timestamp of the news created", type="float"
    ),
]

PostMetaData = [
    AttributeInfo(name="source", description="id of post", type="integer"),
    AttributeInfo(
        name="created_at", description="ISO string of post created", type="string"
    ),
    AttributeInfo(name="user", description="id of post's user", type="integer"),
    AttributeInfo(name="parent", description="id of post's parent id", type="integer"),
    AttributeInfo(
        name="nickname", description="nickname of post's user", type="string"
    ),
]
