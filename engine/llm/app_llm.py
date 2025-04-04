from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
import os, json
from typing import List
from google import genai
from pydantic import BaseModel
from langchain.prompts import PromptTemplate


load_dotenv()


class LLMResponse:

    @staticmethod
    async def open_ai(
        prompt: str,
        input_variables_payload: dict,
        output_is_list: bool = True,
        response_model: BaseModel = None,
    ):
        class TempClass(BaseModel):
            list_response: List[response_model]

        llm = AzureChatOpenAI(
            api_version="2024-08-01-preview",
            deployment_name="gpt-4o-0806",
            temperature=0.0,
            streaming=True,
            client=None,  # Ensure this is correctly set or omitted if not needed
        )
        prompt = PromptTemplate(
            template=prompt,
            input_variables=list(input_variables_payload.keys()),
        )
        if response_model == None:
            chain = prompt | llm
            response = await chain.ainvoke(input_variables_payload)
            return response.content

        if output_is_list:
            llm = llm.with_structured_output(TempClass)
        else:
            llm = llm.with_structured_output(response_model)
            
        chain = prompt | llm
        response = await chain.ainvoke(input_variables_payload)

        if output_is_list:
            response = response.list_response
        return response

    @staticmethod
    async def google_llm(
        respose_model: BaseModel,
        prompt: str,
        input_variables_dict: dict,
        output_is_list: bool = True,
        model_name: str = "gemini-2.0-flash",
    ):
        GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
        prompt = prompt.format(**input_variables_dict)
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = await client.aio.models.generate_content(
            model=model_name,
            # "gemini-2.0-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": list[respose_model],
            },
        )
        if not output_is_list:
            return respose_model(**json.loads(response.text))
        return [respose_model(**i) for i in json.loads(response.text)]
