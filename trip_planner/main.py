from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from crewai import Crew
from trip_agents import TripAgents
from trip_tasks import TripTasks
from dotenv import load_dotenv
from config import Settings, get_settings

# Load environment variables
load_dotenv()

# Initialize FastAPI app
settings = get_settings()
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    debug=settings.DEBUG_MODE
)

# Define request model
class TripRequest(BaseModel):
    origin: str
    cities: list[str]
    date_range: str
    interests: str

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

# API endpoints
@app.get("/")
async def root():
    return {"message": "Welcome to Trip Planner API"}

@app.post("/generate-trip-plan")
async def generate_trip_plan(trip_request: TripRequest):
    try:
        if not all([trip_request.origin, trip_request.cities, trip_request.date_range, trip_request.interests]):
            raise HTTPException(status_code=400, detail="All fields are required")
        
        trip_crew = TripCrew(
            trip_request.origin,
            trip_request.cities,
            trip_request.date_range,
            trip_request.interests
        )
        
        result = trip_crew.run()
        return {"trip_plan": result}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/settings")
async def get_api_settings(settings: Settings = Depends(get_settings)):
    return {
        "title": settings.API_TITLE,
        "version": settings.API_VERSION
    }

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "main:app", 
        host=settings.API_HOST, 
        port=settings.API_PORT,
        reload=settings.DEBUG_MODE
    )
