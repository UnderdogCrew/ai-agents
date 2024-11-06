import streamlit as st
from crewai import Crew
from textwrap import dedent
from trip_agents import TripAgents
from trip_tasks import TripTasks
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TripCrew:
    def __init__(self, origin, cities, date_range, interests):
        self.cities = cities
        self.origin = origin
        self.interests = interests
        self.date_range = date_range

    def run(self):
        agents = TripAgents()
        tasks = TripTasks()

        city_selector_agent = agents.city_selection_agent()
        local_expert_agent = agents.local_expert()
        travel_concierge_agent = agents.travel_concierge()

        identify_task = tasks.identify_task(
            city_selector_agent,
            self.origin,
            self.cities,
            self.interests,
            self.date_range
        )
        gather_task = tasks.gather_task(
            local_expert_agent,
            self.origin,
            self.interests,
            self.date_range
        )
        plan_task = tasks.plan_task(
            travel_concierge_agent, 
            self.origin,
            self.interests,
            self.date_range
        )

        crew = Crew(
            agents=[
                city_selector_agent, local_expert_agent, travel_concierge_agent
            ],
            tasks=[identify_task, gather_task, plan_task],
            verbose=True
        )

        result = crew.kickoff()
        return result

# Streamlit UI
st.title("Trip Planner Crew")

st.write("## Welcome to Trip Planner Crew")
st.write("Please provide the following details to plan your trip:")

# User inputs
location = st.text_input("From where will you be traveling?")
cities = st.text_input("What cities are you interested in visiting? (comma-separated)")
date_range = st.text_input("What is your preferred date range for the trip?")
interests = st.text_area("What are some of your interests and hobbies?")

# Run trip planner
if st.button("Generate Trip Plan"):
    if location and cities and date_range and interests:
        trip_crew = TripCrew(location, cities.split(','), date_range, interests)

        # Display a spinner while the trip plan is being generated
        with st.spinner("Generating your trip plan..."):
            result = trip_crew.run()

        st.write("## Here is your Trip Plan")
        st.write(result)
    else:
        st.warning("Please fill out all fields to generate a trip plan.")
