import json
from typing import Optional
from typing_extensions import Literal
import openai
from dotenv import load_dotenv
import os
from pydantic import BaseModel

class Response(BaseModel):
    is_yes_no_question: bool
    reasoning: Optional[str]
    answer: Optional[Literal["yes","no"]]

PROMPT = """
You are a helpful assistant that can answer questions about the world. 
You are given a question and a dictionary of countries. Some countries will be red, and some will be blue. The remaining countries will be gray.
A user is going to ask you a yes/no question about these countries. You must answer the question with yes or no, or, if the question is not a yes/no question, you must answer with null.

If asked about the number of countries satisfying a condition, you should think step-by-step in your reasoning. Go through each of the relevant countries and determine if they satisfy the condition.

There are two teams: red and blue. Countries are either red or blue, or gray if they don't belong to either team. The opposite to red is blue, and the opposite to blue is red. 

The red countries are:
{red_countries}

The blue countries are:
{blue_countries}

The gray countries are:
{gray_countries}

The user's color is {user_color}. If the user asks about "their countries", they are referring to the countries belonging to their color. If it is unclear if the user is asking about their color countries or some other color, assume they are asking about their color countries.

The question is:
{question}
"""



# Load the API key from the .env file
load_dotenv()

# Initialize the OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ask_question_to_ai(question: str, countries_with_colors: dict, user_color: str) -> str:

    red_countries = [country for country, color in countries_with_colors.items() if color == "red"]
    blue_countries = [country for country, color in countries_with_colors.items() if color == "blue"]
    gray_countries = [country for country, color in countries_with_colors.items() if color == "gray"]

    prompt = PROMPT.format(question=question, red_countries=red_countries, blue_countries=blue_countries, gray_countries=gray_countries, user_color=user_color)

    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format=Response
    )
    response = json.loads(response.choices[0].message.content)
    print(f"response: {response}")
    return response['answer']
