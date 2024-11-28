from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    allow_origin_regex=None,
    max_age=600,
)


# Define request model
class TripRequest(BaseModel):
    origin: str
    cities: list[str]
    date_range: str
    interests: str


class TripPlanner:
    def __init__(self, origin, cities, date_range, interests):
        self.cities = cities
        self.origin = origin
        self.interests = interests
        self.date_range = date_range
        self.llm = ChatOpenAI(
            temperature=0.7,
            model="gpt-4o-mini"
        )

    def run(self):
        try:
            # Create prompt template
            prompt = ChatPromptTemplate.from_messages([
                ("system", """Expand this guide into a full 7-day travel 
                itinerary with detailed per-day plans, including 
                weather forecasts, places to eat, packing suggestions, 
                and a budget breakdown.

                You MUST suggest actual places to visit, actual hotels 
                to stay and actual restaurants to go to.

                This itinerary should cover all aspects of the trip, 
                from arrival to departure, integrating the city guide
                information with practical travel logistics.

                Your final answer MUST be a complete expanded travel plan,
                formatted as markdown, encompassing a daily schedule,
                anticipated weather conditions, recommended clothing and
                items to pack, and a detailed budget, ensuring THE BEST
                TRIP EVER. Be specific and give it a reason why you picked
                each place, what makes them special! If you do your BEST WORK, I'll tip you $100!"""),
                ("user", """Please create a travel plan with the following details:
                Starting from: {origin}
                Cities to visit: {cities}
                Date range: {date_range}
                Interests and preferences: {interests}

                Complete expanded travel plan with daily schedule, weather conditions, packing suggestions, and budget breakdown
                """)
            ])

            # Create the chain
            chain = prompt | self.llm | StrOutputParser()

            # Execute the chain
            result = chain.invoke({
                "origin": self.origin,
                "cities": ", ".join(self.cities),
                "date_range": self.date_range,
                "interests": self.interests
            })

            return result

        except Exception as e:
            print(f"Error in TripPlanner: {str(e)}")
            return f"Error generating trip plan: {str(e)}"


# API endpoints
@app.get("/")
async def root():
    return {"message": "Welcome to Trip Planner API"}


@app.post("/generate-trip-plan")
async def generate_trip_plan(trip_request: TripRequest):
    try:
        if not all([trip_request.origin, trip_request.cities, trip_request.date_range, trip_request.interests]):
            raise HTTPException(status_code=400, detail="All fields are required")

        trip_planner = TripPlanner(
            trip_request.origin,
            trip_request.cities,
            trip_request.date_range,
            trip_request.interests
        )

        result = trip_planner.run()
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