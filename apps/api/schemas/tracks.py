from pydantic import BaseModel


class ResolveRequest(BaseModel):
    url: str
