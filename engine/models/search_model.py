from typing import List, Dict
from pydantic import BaseModel, Field

class SearchIn(BaseModel):
    query: str
    suggestions: List[str]


class Result(BaseModel):
    title: str = Field(..., description="The title of the most relevant result.")
    link: str = Field(..., description="The URL for this top result.")
    description: str = Field(..., description="A concise, two-line summary of the top result.")
    result_rank: int = Field(..., description="The rank of this result means how relevant the infomation.")
    quick_view: str = Field(..., description="Summary of the child page.")

# class TopResult(BaseModel):
#     title: str = Field(..., description="The title of the most relevant result.")
#     link: str = Field(..., description="The URL for this top result.")
#     image: str = Field(..., description="The URL for an image related to the top result.")
#     description: str = Field(..., description="A concise, two-line summary of the top result.")

class SearchOut(BaseModel):
    query: str = Field(..., description="This field should contain exactly the user's query.")
    assistant_answer: str = Field(..., description="This field should contain the assistant's answer to the user's query.")
    top_result: Result
    results: List[Result]
    extended_description: str = Field(..., description="This field should offer a more detailed and comprehensive explanation, summary, or background information related to the query, spanning approximately 10-11 lines.")
