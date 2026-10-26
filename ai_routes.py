from pydantic import BaseModel, ConfigDict, Field
from fastapi import APIRouter,HTTPException

import llm_service
from task_candidate import TaskCandidate


class TaskCandidateRequest(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra='forbid',

    )

    text: str = Field(
        min_length=1,
        max_length=2000,
    )


ai_router = APIRouter(
    prefix="/ai",
    tags=["ai"],

)


@ai_router.post(
    "/task-candidate",
    response_model=TaskCandidate,
)
async def generate_task_candidate(
        request: TaskCandidateRequest
) -> TaskCandidate:

    try:
        candidate =await llm_service.generate_candidate(request.text)
    except RuntimeError as error:
        raise HTTPException(
            status_code=502,
            detail="候选任务生成失败，请稍后重试",

        ) from error

    return candidate
