from crewai import Agent
from langchain.llms import OpenAI

from tools.browser_tools import BrowserTools
from tools.calculator_tools import CalculatorTools
from tools.search_tools import SearchTools

import os

os.environ["OPENAI_API_KEY"] = "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"
os.environ['SERPER_API_KEY'] = "5e0b1d78ec1cfd2927171148591bcc5e3efe33b5"
os.environ['SEC_API_API_KEY'] = "1dc5c9bca79c315c191547b378aae847500c4685579f7bdbe71647fbfd11253f"
os.environ['BROWSERLESS_API_KEY'] = "QHHtkmyd7LoUPif3abd9c596e7fec944658c9a0e8e"
os.environ['OPENAI_MODEL_NAME'] = "gpt-4o-mini"


class TripAgents():

  def city_selection_agent(self):
    return Agent(
        role='City Selection Expert',
        goal='Select the best city based on weather, season, and prices',
        backstory='An expert in analyzing travel data to pick ideal destinations',
        tools=[
            SearchTools.search_internet,
            BrowserTools.scrape_and_summarize_website,
        ],
        verbose=True)

  def local_expert(self):
    return Agent(
        role='Local Expert at this city',
        goal='Provide the BEST insights about the selected city',
        backstory="""A knowledgeable local guide with extensive information
        about the city, it's attractions and customs""",
        tools=[
            SearchTools.search_internet,
            BrowserTools.scrape_and_summarize_website,
        ],
        verbose=True)

  def travel_concierge(self):
    return Agent(
        role='Amazing Travel Concierge',
        goal="""Create the most amazing travel itineraries with budget and 
        packing suggestions for the city""",
        backstory="""Specialist in travel planning and logistics with 
        decades of experience""",
        tools=[
            SearchTools.search_internet,
            BrowserTools.scrape_and_summarize_website,
            CalculatorTools.calculate,
        ],
        verbose=True)
