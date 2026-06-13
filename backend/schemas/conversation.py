from pydantic import BaseModel, ConfigDict, Field


class ConversationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_name: str
    title: str
    created_at: str
    updated_at: str


class ChatMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    role: str
    content: str
    intent: str | None = None
    selected_tool: str | None = None
    created_at: str


class ChatFeedbackRequest(BaseModel):
    message_id: int
    rating: int = Field(ge=-1, le=1)
    comment: str | None = Field(default=None, max_length=500)


class ChatFeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    message_id: int
    query: str | None = None
    response: str | None = None
    rating: int
    comment: str | None = None
    created_at: str
