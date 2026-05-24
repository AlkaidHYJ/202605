from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class AiModelCreate(BaseModel):
    model_name: str = Field(..., min_length=1, max_length=128)
    model_type: str = Field(..., min_length=1, max_length=32)
    base_url: str = Field(..., min_length=5, max_length=512)
    api_key: str = Field(..., min_length=1, max_length=512)
    model_id: str = Field(..., min_length=1, max_length=128)
    is_default: int = 0
    status: int = 1


class AiModelUpdate(BaseModel):
    model_name: str | None = Field(None, min_length=1, max_length=128)
    model_type: str | None = Field(None, min_length=1, max_length=32)
    base_url: str | None = Field(None, min_length=5, max_length=512)
    api_key: str | None = Field(None, min_length=1, max_length=512)
    model_id: str | None = Field(None, min_length=1, max_length=128)
    is_default: int | None = None
    status: int | None = None


class AiModelOut(BaseModel):
    id: int
    model_name: str
    model_type: str
    base_url: str
    model_id: str
    is_default: int
    status: int

    class Config:
        from_attributes = True


class AiModelTestRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)


class AiSkillCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    skill_name: str = Field(..., min_length=1, max_length=128)
    skill_type: int = Field(1, description="1 function 2 skill")
    description: str | None = None
    schema_json_text: str | None = Field(None, alias="schema_json")
    model_id: int | None = None
    status: int = 1


class AiSkillUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    skill_name: str | None = Field(None, min_length=1, max_length=128)
    skill_type: int | None = None
    description: str | None = None
    schema_json_text: str | None = Field(None, alias="schema_json")
    model_id: int | None = None
    status: int | None = None


class AiSkillOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: int
    skill_name: str
    skill_type: int
    description: str | None
    schema_json_text: str | None = Field(None, alias="schema_json")
    model_id: int | None
    status: int


class AiSkillAutoGenerateRequest(BaseModel):
    model_id: int
    skill_name: str = Field(..., min_length=1, max_length=128)
    skill_type: int = Field(1, description="1 function 2 skill")
    description_hint: str | None = None


class AiSkillAutoGenerateOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    description: str
    schema_json_text: str = Field(..., alias="schema_json")
    function_code: str | None = None
    skill_md: str | None = None


class DigitalAgentCreate(BaseModel):
    agent_name: str = Field(..., min_length=1, max_length=128)
    persona: str | None = None
    model_id: str | None = None
    skill_ids: list[int] = []
    status: int = 0


class DigitalAgentUpdate(BaseModel):
    agent_name: str | None = Field(None, min_length=1, max_length=128)
    persona: str | None = None
    model_id: str | None = None
    skill_ids: list[int] | None = None
    status: int | None = None


class DigitalAgentOut(BaseModel):
    id: int
    agent_name: str
    persona: str | None
    model_id: str | None
    skill_ids: str | None
    status: int

    class Config:
        from_attributes = True


class DigitalAgentPromptGenerateRequest(BaseModel):
    skill_ids: list[int] = []
    base_prompt: str | None = None
