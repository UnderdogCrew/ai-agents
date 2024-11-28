from fastapi import FastAPI, Form
import openai
import os
from dotenv import load_dotenv
import json
import re
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from typing import List
import requests

try:
    from langchain_community.chat_models import ChatPerplexity
except ImportError:
    raise ImportError("`chat-perplexity` not installed.")

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Initialize OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

# Define the ICP request model
class ICPRequest(BaseModel):
    website: str# Define the ICP request model


class ICPContent(BaseModel):
    content: str


class OrgContent(BaseModel):
    organization_locations: List[str]
    organization_num_employees_ranges: List[str]
    q_organization_keyword_tags: List[str]


class ApolloApiContent(BaseModel):
    person_titles: List[str]
    contact_email_status: List[str]
    organization_ids: List[str]
    q_organization_domains: str


class EnrichmentApiContent(BaseModel):
    linkedin_urls: List[str]


# Define the ICP request model
class DiscoverRequest(BaseModel):
    icp_text: str

# Function to clean JSON output
def clean_json_output(raw_json):
    try:
        json_start = raw_json.find('[')
        json_end = raw_json.rfind(']') + 1
        if json_start == -1 or json_end == -1:
            return raw_json
        cleaned_json = raw_json[json_start:json_end]
        cleaned_json = re.sub(r',\s*}', '}', cleaned_json)
        cleaned_json = re.sub(r',\s*]', ']', cleaned_json)
        return cleaned_json
    except Exception as e:
        print(f"Error cleaning JSON: {str(e)}")
        return raw_json

@app.post("/generate_icp")
async def generate_icp(request: ICPRequest):
    website = request.website
    try:
        prompt = f"""
            Generate an Ideal Customer Profile (ICP) for the company {website}. The ICP should be comprehensive and structured, covering the following sections:

                Company Overview

                Brief description of {website}, including its core offerings such as mobile app development, web application development, SaaS solutions, and other related software services.
                Highlight the company’s mission, vision, and key value propositions.
                Demographic and Firmographic Characteristics

                Industry Sectors: Identify relevant industries (e.g., Technology Startups, E-commerce, Healthcare, Education, Finance and Fintech, Retail) that would benefit from {website}’s services.
                Company Size: Specify the ideal company sizes (e.g., Small to Medium Enterprises with 10-200 employees, Mid-sized to Large Enterprises with 200-1000+ employees).
                Geographical Location: Define primary and secondary markets (e.g., North America, Europe, Asia-Pacific, emerging markets).
                Revenue: Indicate the typical annual revenue range (e.g., $5 million to $500 million).
                Key Roles and Decision Makers

                List the primary decision-makers and influencers within target companies (e.g., CTOs, CIOs, CEOs, IT Managers, Product Managers, Entrepreneurs, Startup Founders).
                Technographic Characteristics

                Current Technology Stack: Describe the common technologies and platforms used by ideal customers (e.g., JavaScript, Python, React, Angular, AWS, Azure, Google Cloud).
                Software Needs: Outline the specific software needs (e.g., Custom Application Development, SaaS Solutions, Mobile App Development, Web Development).
                Adoption of New Technologies: Mention interest in emerging technologies (e.g., AI, ML, IoT, Blockchain).
                Pain Points

                Identify common challenges faced by ideal customers (e.g., scalability, customization, time-to-market, integration, user experience, security and compliance).
                Behavioral Traits

                Decision-Making Process: Describe how ideal customers make purchasing decisions (e.g., data-driven, seeking proven track records, preference for vendors offering support).
                Buying Motivations: Highlight what drives purchases (e.g., quality, reliability, cost-effectiveness, ROI, customer service).
                Customer Loyalty: Note preferences for long-term partnerships.
                Psychographic Characteristics

                Values: Identify core values of ideal customers (e.g., innovation, reliability, excellence in technology, commitment to customer success).
                Goals: Outline their primary objectives (e.g., enhancing operational efficiency, improving customer engagement, driving revenue growth through digital transformation).
                Communication Preferences

                Preferred Channels: Specify how ideal customers prefer to receive information (e.g., LinkedIn, industry conferences, webinars, technical blogs, online communities).
                Content Consumption: Detail the types of content they engage with (e.g., case studies, whitepapers, technical documentation, webinars, demo sessions, testimonials).
                Example Ideal Customers

                Provide specific examples of ideal customer types:
                Tech Startups: Early-stage companies developing innovative apps needing MVP development and scaling solutions.
                E-commerce Platforms: Online retailers seeking to develop mobile apps to enhance shopping experiences and increase sales.
                Healthcare Providers: Hospitals and clinics requiring secure patient management systems and telemedicine applications.
                Educational Institutions: Universities and schools aiming to implement e-learning platforms and student engagement tools.
                Financial Services Firms: Banks and fintech companies needing secure, user-friendly financial applications.
                Summary

                Concisely summarize the Ideal Customer Profile, emphasizing the key characteristics that make a company an ideal customer for {website}.
                Highlight the benefits {website} offers to these ideal customers and the value of forming long-term partnerships.
                Additional Instructions:

                Ensure the ICP is tailored specifically to {website}’s services and market positioning.
                Use clear headings and bullet points for readability.
                Provide actionable insights that can help {website} align its marketing, sales, and product development strategies with the identified ideal customers.
            """
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1500,
            n=1,
            stop=None
        )

        result = response.choices[0].message['content']
        return {"raw": result}

    except Exception as e:
        return {"error": f"Error generating ICP: {str(e)}"}



@app.post("/json-apollo")
async def json_apollo(request: ICPContent):
    content = request.content
    try:
        prompt = f"""
            {content}
            get me these details from the above context

            1. organization_locations
            2. organization_num_employees_ranges
            3. person_titles
            4. q_organization_keyword_tags
            
            return all values in array, and return only values without any explanation and return in JSON
            """
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1500,
            n=1,
            stop=None
        )

        result = response.choices[0].message['content']
        json_result = result.replace("json", "")
        json_result = json_result.replace("```", "")
        response_data = json.loads(json_result)
        return response_data

    except Exception as e:
        return {"error": f"Error generating ICP: {str(e)}"}\


@app.post("/apollo-api-orgs")
async def generate_apollo_api_orgs(request: OrgContent):
    organization_locations = request.organization_locations
    organization_num_employees_ranges = request.organization_num_employees_ranges
    q_organization_keyword_tags = request.q_organization_keyword_tags
    try:
        url = "https://icp-builder.lyzr.tools/api/apollo-api-orgs"

        payload = json.dumps({
            "organization_locations": organization_locations,
            "organization_num_employees_ranges": organization_num_employees_ranges,
            "q_organization_keyword_tags": q_organization_keyword_tags,
            "per_page": 100,
            "page": 1
        })
        headers = {
            'accept': '*/*',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8,gu;q=0.7',
            'content-type': 'application/json',
            'cookie': '_ga=GA1.1.140139446.1732073866; ext_name=ojplmecpdpgccookcobabopnaifgidhf; _ga_Y1BS164MXE=GS1.1.1732721900.2.0.1732721909.0.0.0; sb-jkagupfysoootgbodrmh-auth-token.0=base64-eyJhY2Nlc3NfdG9rZW4iOiJleUpoYkdjaU9pSklVekkxTmlJc0ltdHBaQ0k2SW10T04wMWFiWEptYXk5R1JtZFFiM1FpTENKMGVYQWlPaUpLVjFRaWZRLmV5SnBjM01pT2lKb2RIUndjem92TDJwcllXZDFjR1o1YzI5dmIzUm5ZbTlrY20xb0xuTjFjR0ZpWVhObExtTnZMMkYxZEdndmRqRWlMQ0p6ZFdJaU9pSTFZalUxWkRZeE5TMDNOemczTFRRNU5qVXRZVEZqTlMwNVlXSXpaREU0WTJZMU5tWWlMQ0poZFdRaU9pSmhkWFJvWlc1MGFXTmhkR1ZrSWl3aVpYaHdJam94TnpNeU56azRPVEUyTENKcFlYUWlPakUzTXpJM09UVXpNVFlzSW1WdFlXbHNJam9pYm1sc2NHRjBaV3cyTWtCbmJXRnBiQzVqYjIwaUxDSndhRzl1WlNJNklpSXNJbUZ3Y0Y5dFpYUmhaR0YwWVNJNmV5SndjbTkyYVdSbGNpSTZJbWR2YjJkc1pTSXNJbkJ5YjNacFpHVnljeUk2V3lKbmIyOW5iR1VpWFgwc0luVnpaWEpmYldWMFlXUmhkR0VpT25zaVlYWmhkR0Z5WDNWeWJDSTZJbWgwZEhCek9pOHZiR2d6TG1kdmIyZHNaWFZ6WlhKamIyNTBaVzUwTG1OdmJTOWhMMEZEWnpodlkwbzVTMU53ZUhCWE5IQkRSalZwWmtKd09XRmxMV1p1Y0RFMmR5MVhjREJuYUZaQ1ZsWkVWMHgwU21WNVozbEtVazh0UFhNNU5pMWpJaXdpWlcxaGFXd2lPaUp1YVd4d1lYUmxiRFl5UUdkdFlXbHNMbU52YlNJc0ltVnRZV2xzWDNabGNtbG1hV1ZrSWpwMGNuVmxMQ0ptZFd4c1gyNWhiV1VpT2lKT2FXd2djR0YwWld3aUxDSnBjM01pT2lKb2RIUndjem92TDJGalkyOTFiblJ6TG1kdmIyZHNaUzVqYjIwaUxDSnVZVzFsSWpvaVRtbHNJSEJoZEdWc0lpd2ljR2h2Ym1WZmRtVnlhV1pwWldRaU9tWmhiSE5sTENKd2FXTjBkWEpsSWpvaWFIUjBjSE02THk5c2FETXVaMjl2WjJ4bGRYTmxjbU52Ym5SbGJuUXVZMjl0TDJFdlFVTm5PRzlqU2psTFUzQjRjRmMwY0VOR05XbG1RbkE1WVdVdFptNXdNVFozTFZkd01HZG9Wa0pXVmtSWFRIUktaWGxuZVVwU1R5MDljemsyTFdNaUxDSndjbTkyYVdSbGNsOXBaQ0k2SWpFd056a3dNek01TmpNM05EVTNORGd6Tmpnek9DSXNJbk4xWWlJNklqRXdOemt3TXpNNU5qTTNORFUzTkRnek5qZ3pPQ0o5TENKeWIyeGxJam9pWVhWMGFHVnVkR2xqWVhSbFpDSXNJbUZoYkNJNkltRmhiREVpTENKaGJYSWlPbHQ3SW0xbGRHaHZaQ0k2SW05aGRYUm9JaXdpZEdsdFpYTjBZVzF3SWpveE56TXlOemsxTXpFMmZWMHNJbk5sYzNOcGIyNWZhV1FpT2lJNU1qQXlPRFExTmkweE1ETXlMVFJrTXpjdE9UZ3pNUzA1TTJRek5HRTRaVGMwTmpJaUxDSnBjMTloYm05dWVXMXZkWE1pT21aaGJITmxmUS5saldkenhHa3NfY0szRFk3Q2lLRl9SaE0td0FuQkRYVzFMY3VQX2dNcnl3IiwidG9rZW5fdHlwZSI6ImJlYXJlciIsImV4cGlyZXNfaW4iOjM2MDAsImV4cGlyZXNfYXQiOjE3MzI3OTg5MTYsInJlZnJlc2hfdG9rZW4iOiJJLXhMcFNLSnV6V3pGOVhHRFJzdEdnIiwidXNlciI6eyJpZCI6IjViNTVkNjE1LTc3ODctNDk2NS1hMWM1LTlhYjNkMThjZjU2ZiIsImF1ZCI6ImF1dGhlbnRpY2F0ZWQiLCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImVtYWlsIjoibmlscGF0ZWw2MkBnbWFpbC5jb20iLCJlbWFpbF9jb25maXJtZWRfYXQiOiIyMDI0LTExLTI4VDEyOjAxOjU2LjAyMDI2MVoiLCJwaG9uZSI6IiIsImNvbmZpcm1lZF9hdCI6IjIwMjQtMTEtMjhUMTI6MDE6NTYuMDIwMjYxWiIsImxhc3Rfc2lnbl9pbl9hdCI6IjIwMjQtMTEtMjhUMTI6MDE6NTYuNDY5MzU2OTdaIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZ29vZ2xlIiwicHJvdmlkZXJzIjpbImdvb2dsZSJdfSwidXNlcl9tZXRhZGF0YSI6eyJhdmF0YXJfdXJsIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EvQUNnOG9jSjlLU3B4cFc0cENGNWlmQnA5YWUtZm5wMTZ3LVdwMGdoVkJWVkRXTHRKZXlneUpSTy09czk2LWMiLCJlbWFpbCI6Im5pbHBhdGVsNjJAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZ1bGxfbmFtZSI6Ik5pbCBwYXRlbCIsImlzcyI6Imh0dHBzOi8vYWNjb3VudHMuZ29vZ2xlLmNvbSIsIm5hbWUiOiJOaWwgcGF0ZWwiLCJwaG9uZV92ZXJpZmllZCI6ZmFsc2UsInBpY3R1cmUiOiJodHRwczovL2xoMy5nb29nbGV1c2VyY29udGVudC5jb20vYS9BQ2c4b2NKOUtTcHhwVzRwQ0Y1aWZCcDlhZS1mbnAxNnctV3AwZ2hWQlZWRFdMdEpleWd5SlJPLT1zOTYtYyIsInByb3ZpZGVyX2lkIjoiMTA3OTAzMzk2Mzc0NTc0ODM2ODM4Iiwic3ViIjoiMTA3OTAzMzk2Mzc0NTc0ODM2ODM4In0sImlkZW50aXRpZXMiOlt7ImlkZW50aXR5X2lkIjoiMGJjZDdiNzMtMzQ0ZC00M2FlLWJhZjEtNGM0YTE1NWEwMGNmIiwiaWQiOiIxMDc5MDMzOTYzNzQ1NzQ4MzY4MzgiLCJ1c2VyX2lkIjoiNWI1NWQ2MTUtNzc4Ny00OTY1LWExYzUtOWFiM2QxOGNmNTZmIiwia; sb-jkagupfysoootgbodrmh-auth-token.1=WRlbnRpdHlfZGF0YSI6eyJhdmF0YXJfdXJsIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EvQUNnOG9jSjlLU3B4cFc0cENGNWlmQnA5YWUtZm5wMTZ3LVdwMGdoVkJWVkRXTHRKZXlneUpSTy09czk2LWMiLCJlbWFpbCI6Im5pbHBhdGVsNjJAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZ1bGxfbmFtZSI6Ik5pbCBwYXRlbCIsImlzcyI6Imh0dHBzOi8vYWNjb3VudHMuZ29vZ2xlLmNvbSIsIm5hbWUiOiJOaWwgcGF0ZWwiLCJwaG9uZV92ZXJpZmllZCI6ZmFsc2UsInBpY3R1cmUiOiJodHRwczovL2xoMy5nb29nbGV1c2VyY29udGVudC5jb20vYS9BQ2c4b2NKOUtTcHhwVzRwQ0Y1aWZCcDlhZS1mbnAxNnctV3AwZ2hWQlZWRFdMdEpleWd5SlJPLT1zOTYtYyIsInByb3ZpZGVyX2lkIjoiMTA3OTAzMzk2Mzc0NTc0ODM2ODM4Iiwic3ViIjoiMTA3OTAzMzk2Mzc0NTc0ODM2ODM4In0sInByb3ZpZGVyIjoiZ29vZ2xlIiwibGFzdF9zaWduX2luX2F0IjoiMjAyNC0xMS0yOFQxMjowMTo1Ni4wMTQzMjVaIiwiY3JlYXRlZF9hdCI6IjIwMjQtMTEtMjhUMTI6MDE6NTYuMDE0Mzg0WiIsInVwZGF0ZWRfYXQiOiIyMDI0LTExLTI4VDEyOjAxOjU2LjAxNDM4NFoiLCJlbWFpbCI6Im5pbHBhdGVsNjJAZ21haWwuY29tIn1dLCJjcmVhdGVkX2F0IjoiMjAyNC0xMS0yOFQxMjowMTo1NS45OTgyODFaIiwidXBkYXRlZF9hdCI6IjIwMjQtMTEtMjhUMTI6MDE6NTYuNDcxODkxWiIsImlzX2Fub255bW91cyI6ZmFsc2V9LCJwcm92aWRlcl90b2tlbiI6InlhMjkuYTBBZURDbFpEby1GMjB0QlJyRFhycTFkbUpYempyNmEtVE15VlFRYi1YQU1CWXRhZ1gzRFpzR21kQmVPMHpNYjNqRzRYVjNtS2VXUndIU3Yzb3d4Uy1xMm1ISERZRnAtYUZIb2tYa0VoV3VUaGViZW9RQjZaRWZCV04tSEo2ZFJXYVY4S3FNeDduc0xEQnAxdmJrblpFbnlxRkJWbzhaenBpTjBBZnlFVDVhQ2dZS0FRa1NBUk1TRlFIR1gyTWlobkNNY2R4NmxVdVJvaTNLZFBqYjZBMDE3NSIsInByb3ZpZGVyX3JlZnJlc2hfdG9rZW4iOiIxLy8wNWNrWHF1dkUyTmZrQ2dZSUFSQUFHQVVTTndGLUw5SXJMbTduRUhPaV9USmFjS2hidE45eUFhMjlxeldNUGhFYml6VTEzTFJkUThPQkJQSkdsUHhHYk9yTXlBMHRsVW9JZFJNIn0; mp_e7880c30aeb146194855dc28a37bd3bb_mixpanel=%7B%22distinct_id%22%3A%20%22%24device%3A19347a6068e850-0be6188605689b-1e525636-1aeaa0-19347a6068e850%22%2C%22%24device_id%22%3A%20%2219347a6068e850-0be6188605689b-1e525636-1aeaa0-19347a6068e850%22%2C%22%24initial_referrer%22%3A%20%22https%3A%2F%2Fwww.lyzr.ai%2F%22%2C%22%24initial_referring_domain%22%3A%20%22www.lyzr.ai%22%2C%22__mps%22%3A%20%7B%7D%2C%22__mpso%22%3A%20%7B%22%24initial_referrer%22%3A%20%22https%3A%2F%2Fwww.lyzr.ai%2F%22%2C%22%24initial_referring_domain%22%3A%20%22www.lyzr.ai%22%7D%2C%22__mpus%22%3A%20%7B%7D%2C%22__mpa%22%3A%20%7B%7D%2C%22__mpu%22%3A%20%7B%7D%2C%22__mpr%22%3A%20%5B%5D%2C%22__mpap%22%3A%20%5B%5D%2C%22app%22%3A%20%22ICP%20Builder%22%2C%22%24search_engine%22%3A%20%22google%22%7D',
            'origin': 'https://icp-builder.lyzr.tools',
            'priority': 'u=1, i',
            'referer': 'https://icp-builder.lyzr.tools/',
            'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Error generating ICP"}

    except Exception as e:
        return {"error": f"Error generating ICP: {str(e)}"}\


@app.post("/apollo-api")
async def generate_apollo_api(request: ApolloApiContent):
    person_titles = request.person_titles
    contact_email_status = request.contact_email_status
    organization_ids = request.organization_ids
    q_organization_domains = request.q_organization_domains
    try:
        url = "https://icp-builder.lyzr.tools/api/apollo-api"

        payload = json.dumps({
            "person_titles": person_titles,
            "contact_email_status": contact_email_status,
            "organization_ids": organization_ids,
            "q_organization_domains": q_organization_domains
        })
        headers = {
            'accept': '*/*',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8,gu;q=0.7',
            'content-type': 'application/json',
            'cookie': '_ga=GA1.1.140139446.1732073866; ext_name=ojplmecpdpgccookcobabopnaifgidhf; _ga_Y1BS164MXE=GS1.1.1732721900.2.0.1732721909.0.0.0; sb-jkagupfysoootgbodrmh-auth-token.0=base64-eyJhY2Nlc3NfdG9rZW4iOiJleUpoYkdjaU9pSklVekkxTmlJc0ltdHBaQ0k2SW10T04wMWFiWEptYXk5R1JtZFFiM1FpTENKMGVYQWlPaUpLVjFRaWZRLmV5SnBjM01pT2lKb2RIUndjem92TDJwcllXZDFjR1o1YzI5dmIzUm5ZbTlrY20xb0xuTjFjR0ZpWVhObExtTnZMMkYxZEdndmRqRWlMQ0p6ZFdJaU9pSTFZalUxWkRZeE5TMDNOemczTFRRNU5qVXRZVEZqTlMwNVlXSXpaREU0WTJZMU5tWWlMQ0poZFdRaU9pSmhkWFJvWlc1MGFXTmhkR1ZrSWl3aVpYaHdJam94TnpNeU56azRPVEUyTENKcFlYUWlPakUzTXpJM09UVXpNVFlzSW1WdFlXbHNJam9pYm1sc2NHRjBaV3cyTWtCbmJXRnBiQzVqYjIwaUxDSndhRzl1WlNJNklpSXNJbUZ3Y0Y5dFpYUmhaR0YwWVNJNmV5SndjbTkyYVdSbGNpSTZJbWR2YjJkc1pTSXNJbkJ5YjNacFpHVnljeUk2V3lKbmIyOW5iR1VpWFgwc0luVnpaWEpmYldWMFlXUmhkR0VpT25zaVlYWmhkR0Z5WDNWeWJDSTZJbWgwZEhCek9pOHZiR2d6TG1kdmIyZHNaWFZ6WlhKamIyNTBaVzUwTG1OdmJTOWhMMEZEWnpodlkwbzVTMU53ZUhCWE5IQkRSalZwWmtKd09XRmxMV1p1Y0RFMmR5MVhjREJuYUZaQ1ZsWkVWMHgwU21WNVozbEtVazh0UFhNNU5pMWpJaXdpWlcxaGFXd2lPaUp1YVd4d1lYUmxiRFl5UUdkdFlXbHNMbU52YlNJc0ltVnRZV2xzWDNabGNtbG1hV1ZrSWpwMGNuVmxMQ0ptZFd4c1gyNWhiV1VpT2lKT2FXd2djR0YwWld3aUxDSnBjM01pT2lKb2RIUndjem92TDJGalkyOTFiblJ6TG1kdmIyZHNaUzVqYjIwaUxDSnVZVzFsSWpvaVRtbHNJSEJoZEdWc0lpd2ljR2h2Ym1WZmRtVnlhV1pwWldRaU9tWmhiSE5sTENKd2FXTjBkWEpsSWpvaWFIUjBjSE02THk5c2FETXVaMjl2WjJ4bGRYTmxjbU52Ym5SbGJuUXVZMjl0TDJFdlFVTm5PRzlqU2psTFUzQjRjRmMwY0VOR05XbG1RbkE1WVdVdFptNXdNVFozTFZkd01HZG9Wa0pXVmtSWFRIUktaWGxuZVVwU1R5MDljemsyTFdNaUxDSndjbTkyYVdSbGNsOXBaQ0k2SWpFd056a3dNek01TmpNM05EVTNORGd6Tmpnek9DSXNJbk4xWWlJNklqRXdOemt3TXpNNU5qTTNORFUzTkRnek5qZ3pPQ0o5TENKeWIyeGxJam9pWVhWMGFHVnVkR2xqWVhSbFpDSXNJbUZoYkNJNkltRmhiREVpTENKaGJYSWlPbHQ3SW0xbGRHaHZaQ0k2SW05aGRYUm9JaXdpZEdsdFpYTjBZVzF3SWpveE56TXlOemsxTXpFMmZWMHNJbk5sYzNOcGIyNWZhV1FpT2lJNU1qQXlPRFExTmkweE1ETXlMVFJrTXpjdE9UZ3pNUzA1TTJRek5HRTRaVGMwTmpJaUxDSnBjMTloYm05dWVXMXZkWE1pT21aaGJITmxmUS5saldkenhHa3NfY0szRFk3Q2lLRl9SaE0td0FuQkRYVzFMY3VQX2dNcnl3IiwidG9rZW5fdHlwZSI6ImJlYXJlciIsImV4cGlyZXNfaW4iOjM2MDAsImV4cGlyZXNfYXQiOjE3MzI3OTg5MTYsInJlZnJlc2hfdG9rZW4iOiJJLXhMcFNLSnV6V3pGOVhHRFJzdEdnIiwidXNlciI6eyJpZCI6IjViNTVkNjE1LTc3ODctNDk2NS1hMWM1LTlhYjNkMThjZjU2ZiIsImF1ZCI6ImF1dGhlbnRpY2F0ZWQiLCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImVtYWlsIjoibmlscGF0ZWw2MkBnbWFpbC5jb20iLCJlbWFpbF9jb25maXJtZWRfYXQiOiIyMDI0LTExLTI4VDEyOjAxOjU2LjAyMDI2MVoiLCJwaG9uZSI6IiIsImNvbmZpcm1lZF9hdCI6IjIwMjQtMTEtMjhUMTI6MDE6NTYuMDIwMjYxWiIsImxhc3Rfc2lnbl9pbl9hdCI6IjIwMjQtMTEtMjhUMTI6MDE6NTYuNDY5MzU2OTdaIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZ29vZ2xlIiwicHJvdmlkZXJzIjpbImdvb2dsZSJdfSwidXNlcl9tZXRhZGF0YSI6eyJhdmF0YXJfdXJsIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EvQUNnOG9jSjlLU3B4cFc0cENGNWlmQnA5YWUtZm5wMTZ3LVdwMGdoVkJWVkRXTHRKZXlneUpSTy09czk2LWMiLCJlbWFpbCI6Im5pbHBhdGVsNjJAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZ1bGxfbmFtZSI6Ik5pbCBwYXRlbCIsImlzcyI6Imh0dHBzOi8vYWNjb3VudHMuZ29vZ2xlLmNvbSIsIm5hbWUiOiJOaWwgcGF0ZWwiLCJwaG9uZV92ZXJpZmllZCI6ZmFsc2UsInBpY3R1cmUiOiJodHRwczovL2xoMy5nb29nbGV1c2VyY29udGVudC5jb20vYS9BQ2c4b2NKOUtTcHhwVzRwQ0Y1aWZCcDlhZS1mbnAxNnctV3AwZ2hWQlZWRFdMdEpleWd5SlJPLT1zOTYtYyIsInByb3ZpZGVyX2lkIjoiMTA3OTAzMzk2Mzc0NTc0ODM2ODM4Iiwic3ViIjoiMTA3OTAzMzk2Mzc0NTc0ODM2ODM4In0sImlkZW50aXRpZXMiOlt7ImlkZW50aXR5X2lkIjoiMGJjZDdiNzMtMzQ0ZC00M2FlLWJhZjEtNGM0YTE1NWEwMGNmIiwiaWQiOiIxMDc5MDMzOTYzNzQ1NzQ4MzY4MzgiLCJ1c2VyX2lkIjoiNWI1NWQ2MTUtNzc4Ny00OTY1LWExYzUtOWFiM2QxOGNmNTZmIiwia; sb-jkagupfysoootgbodrmh-auth-token.1=WRlbnRpdHlfZGF0YSI6eyJhdmF0YXJfdXJsIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EvQUNnOG9jSjlLU3B4cFc0cENGNWlmQnA5YWUtZm5wMTZ3LVdwMGdoVkJWVkRXTHRKZXlneUpSTy09czk2LWMiLCJlbWFpbCI6Im5pbHBhdGVsNjJAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZ1bGxfbmFtZSI6Ik5pbCBwYXRlbCIsImlzcyI6Imh0dHBzOi8vYWNjb3VudHMuZ29vZ2xlLmNvbSIsIm5hbWUiOiJOaWwgcGF0ZWwiLCJwaG9uZV92ZXJpZmllZCI6ZmFsc2UsInBpY3R1cmUiOiJodHRwczovL2xoMy5nb29nbGV1c2VyY29udGVudC5jb20vYS9BQ2c4b2NKOUtTcHhwVzRwQ0Y1aWZCcDlhZS1mbnAxNnctV3AwZ2hWQlZWRFdMdEpleWd5SlJPLT1zOTYtYyIsInByb3ZpZGVyX2lkIjoiMTA3OTAzMzk2Mzc0NTc0ODM2ODM4Iiwic3ViIjoiMTA3OTAzMzk2Mzc0NTc0ODM2ODM4In0sInByb3ZpZGVyIjoiZ29vZ2xlIiwibGFzdF9zaWduX2luX2F0IjoiMjAyNC0xMS0yOFQxMjowMTo1Ni4wMTQzMjVaIiwiY3JlYXRlZF9hdCI6IjIwMjQtMTEtMjhUMTI6MDE6NTYuMDE0Mzg0WiIsInVwZGF0ZWRfYXQiOiIyMDI0LTExLTI4VDEyOjAxOjU2LjAxNDM4NFoiLCJlbWFpbCI6Im5pbHBhdGVsNjJAZ21haWwuY29tIn1dLCJjcmVhdGVkX2F0IjoiMjAyNC0xMS0yOFQxMjowMTo1NS45OTgyODFaIiwidXBkYXRlZF9hdCI6IjIwMjQtMTEtMjhUMTI6MDE6NTYuNDcxODkxWiIsImlzX2Fub255bW91cyI6ZmFsc2V9LCJwcm92aWRlcl90b2tlbiI6InlhMjkuYTBBZURDbFpEby1GMjB0QlJyRFhycTFkbUpYempyNmEtVE15VlFRYi1YQU1CWXRhZ1gzRFpzR21kQmVPMHpNYjNqRzRYVjNtS2VXUndIU3Yzb3d4Uy1xMm1ISERZRnAtYUZIb2tYa0VoV3VUaGViZW9RQjZaRWZCV04tSEo2ZFJXYVY4S3FNeDduc0xEQnAxdmJrblpFbnlxRkJWbzhaenBpTjBBZnlFVDVhQ2dZS0FRa1NBUk1TRlFIR1gyTWlobkNNY2R4NmxVdVJvaTNLZFBqYjZBMDE3NSIsInByb3ZpZGVyX3JlZnJlc2hfdG9rZW4iOiIxLy8wNWNrWHF1dkUyTmZrQ2dZSUFSQUFHQVVTTndGLUw5SXJMbTduRUhPaV9USmFjS2hidE45eUFhMjlxeldNUGhFYml6VTEzTFJkUThPQkJQSkdsUHhHYk9yTXlBMHRsVW9JZFJNIn0; mp_e7880c30aeb146194855dc28a37bd3bb_mixpanel=%7B%22distinct_id%22%3A%20%22%24device%3A19347a6068e850-0be6188605689b-1e525636-1aeaa0-19347a6068e850%22%2C%22%24device_id%22%3A%20%2219347a6068e850-0be6188605689b-1e525636-1aeaa0-19347a6068e850%22%2C%22%24initial_referrer%22%3A%20%22https%3A%2F%2Fwww.lyzr.ai%2F%22%2C%22%24initial_referring_domain%22%3A%20%22www.lyzr.ai%22%2C%22__mps%22%3A%20%7B%7D%2C%22__mpso%22%3A%20%7B%22%24initial_referrer%22%3A%20%22https%3A%2F%2Fwww.lyzr.ai%2F%22%2C%22%24initial_referring_domain%22%3A%20%22www.lyzr.ai%22%7D%2C%22__mpus%22%3A%20%7B%7D%2C%22__mpa%22%3A%20%7B%7D%2C%22__mpu%22%3A%20%7B%7D%2C%22__mpr%22%3A%20%5B%5D%2C%22__mpap%22%3A%20%5B%5D%2C%22app%22%3A%20%22ICP%20Builder%22%2C%22%24search_engine%22%3A%20%22google%22%7D',
            'origin': 'https://icp-builder.lyzr.tools',
            'priority': 'u=1, i',
            'referer': 'https://icp-builder.lyzr.tools/',
            'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Error generating ICP"}

    except Exception as e:
        return {"error": f"Error generating ICP: {str(e)}"}\


@app.post("/enrichment-api")
async def generate_enrichment_api(request: EnrichmentApiContent):
    linkedin_urls = request.linkedin_urls
    try:
        url = "https://icp-builder.lyzr.tools/api/enrichment-api"

        payload = json.dumps(
            {
                "linkedin_urls": linkedin_urls
            }
        )
        headers = {
            'accept': '*/*',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8,gu;q=0.7',
            'content-type': 'application/json',
            'cookie': '_ga=GA1.1.140139446.1732073866; ext_name=ojplmecpdpgccookcobabopnaifgidhf; _ga_Y1BS164MXE=GS1.1.1732721900.2.0.1732721909.0.0.0; sb-jkagupfysoootgbodrmh-auth-token.0=base64-eyJhY2Nlc3NfdG9rZW4iOiJleUpoYkdjaU9pSklVekkxTmlJc0ltdHBaQ0k2SW10T04wMWFiWEptYXk5R1JtZFFiM1FpTENKMGVYQWlPaUpLVjFRaWZRLmV5SnBjM01pT2lKb2RIUndjem92TDJwcllXZDFjR1o1YzI5dmIzUm5ZbTlrY20xb0xuTjFjR0ZpWVhObExtTnZMMkYxZEdndmRqRWlMQ0p6ZFdJaU9pSTFZalUxWkRZeE5TMDNOemczTFRRNU5qVXRZVEZqTlMwNVlXSXpaREU0WTJZMU5tWWlMQ0poZFdRaU9pSmhkWFJvWlc1MGFXTmhkR1ZrSWl3aVpYaHdJam94TnpNeU56azRPVEUyTENKcFlYUWlPakUzTXpJM09UVXpNVFlzSW1WdFlXbHNJam9pYm1sc2NHRjBaV3cyTWtCbmJXRnBiQzVqYjIwaUxDSndhRzl1WlNJNklpSXNJbUZ3Y0Y5dFpYUmhaR0YwWVNJNmV5SndjbTkyYVdSbGNpSTZJbWR2YjJkc1pTSXNJbkJ5YjNacFpHVnljeUk2V3lKbmIyOW5iR1VpWFgwc0luVnpaWEpmYldWMFlXUmhkR0VpT25zaVlYWmhkR0Z5WDNWeWJDSTZJbWgwZEhCek9pOHZiR2d6TG1kdmIyZHNaWFZ6WlhKamIyNTBaVzUwTG1OdmJTOWhMMEZEWnpodlkwbzVTMU53ZUhCWE5IQkRSalZwWmtKd09XRmxMV1p1Y0RFMmR5MVhjREJuYUZaQ1ZsWkVWMHgwU21WNVozbEtVazh0UFhNNU5pMWpJaXdpWlcxaGFXd2lPaUp1YVd4d1lYUmxiRFl5UUdkdFlXbHNMbU52YlNJc0ltVnRZV2xzWDNabGNtbG1hV1ZrSWpwMGNuVmxMQ0ptZFd4c1gyNWhiV1VpT2lKT2FXd2djR0YwWld3aUxDSnBjM01pT2lKb2RIUndjem92TDJGalkyOTFiblJ6TG1kdmIyZHNaUzVqYjIwaUxDSnVZVzFsSWpvaVRtbHNJSEJoZEdWc0lpd2ljR2h2Ym1WZmRtVnlhV1pwWldRaU9tWmhiSE5sTENKd2FXTjBkWEpsSWpvaWFIUjBjSE02THk5c2FETXVaMjl2WjJ4bGRYTmxjbU52Ym5SbGJuUXVZMjl0TDJFdlFVTm5PRzlqU2psTFUzQjRjRmMwY0VOR05XbG1RbkE1WVdVdFptNXdNVFozTFZkd01HZG9Wa0pXVmtSWFRIUktaWGxuZVVwU1R5MDljemsyTFdNaUxDSndjbTkyYVdSbGNsOXBaQ0k2SWpFd056a3dNek01TmpNM05EVTNORGd6Tmpnek9DSXNJbk4xWWlJNklqRXdOemt3TXpNNU5qTTNORFUzTkRnek5qZ3pPQ0o5TENKeWIyeGxJam9pWVhWMGFHVnVkR2xqWVhSbFpDSXNJbUZoYkNJNkltRmhiREVpTENKaGJYSWlPbHQ3SW0xbGRHaHZaQ0k2SW05aGRYUm9JaXdpZEdsdFpYTjBZVzF3SWpveE56TXlOemsxTXpFMmZWMHNJbk5sYzNOcGIyNWZhV1FpT2lJNU1qQXlPRFExTmkweE1ETXlMVFJrTXpjdE9UZ3pNUzA1TTJRek5HRTRaVGMwTmpJaUxDSnBjMTloYm05dWVXMXZkWE1pT21aaGJITmxmUS5saldkenhHa3NfY0szRFk3Q2lLRl9SaE0td0FuQkRYVzFMY3VQX2dNcnl3IiwidG9rZW5fdHlwZSI6ImJlYXJlciIsImV4cGlyZXNfaW4iOjM2MDAsImV4cGlyZXNfYXQiOjE3MzI3OTg5MTYsInJlZnJlc2hfdG9rZW4iOiJJLXhMcFNLSnV6V3pGOVhHRFJzdEdnIiwidXNlciI6eyJpZCI6IjViNTVkNjE1LTc3ODctNDk2NS1hMWM1LTlhYjNkMThjZjU2ZiIsImF1ZCI6ImF1dGhlbnRpY2F0ZWQiLCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImVtYWlsIjoibmlscGF0ZWw2MkBnbWFpbC5jb20iLCJlbWFpbF9jb25maXJtZWRfYXQiOiIyMDI0LTExLTI4VDEyOjAxOjU2LjAyMDI2MVoiLCJwaG9uZSI6IiIsImNvbmZpcm1lZF9hdCI6IjIwMjQtMTEtMjhUMTI6MDE6NTYuMDIwMjYxWiIsImxhc3Rfc2lnbl9pbl9hdCI6IjIwMjQtMTEtMjhUMTI6MDE6NTYuNDY5MzU2OTdaIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZ29vZ2xlIiwicHJvdmlkZXJzIjpbImdvb2dsZSJdfSwidXNlcl9tZXRhZGF0YSI6eyJhdmF0YXJfdXJsIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EvQUNnOG9jSjlLU3B4cFc0cENGNWlmQnA5YWUtZm5wMTZ3LVdwMGdoVkJWVkRXTHRKZXlneUpSTy09czk2LWMiLCJlbWFpbCI6Im5pbHBhdGVsNjJAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZ1bGxfbmFtZSI6Ik5pbCBwYXRlbCIsImlzcyI6Imh0dHBzOi8vYWNjb3VudHMuZ29vZ2xlLmNvbSIsIm5hbWUiOiJOaWwgcGF0ZWwiLCJwaG9uZV92ZXJpZmllZCI6ZmFsc2UsInBpY3R1cmUiOiJodHRwczovL2xoMy5nb29nbGV1c2VyY29udGVudC5jb20vYS9BQ2c4b2NKOUtTcHhwVzRwQ0Y1aWZCcDlhZS1mbnAxNnctV3AwZ2hWQlZWRFdMdEpleWd5SlJPLT1zOTYtYyIsInByb3ZpZGVyX2lkIjoiMTA3OTAzMzk2Mzc0NTc0ODM2ODM4Iiwic3ViIjoiMTA3OTAzMzk2Mzc0NTc0ODM2ODM4In0sImlkZW50aXRpZXMiOlt7ImlkZW50aXR5X2lkIjoiMGJjZDdiNzMtMzQ0ZC00M2FlLWJhZjEtNGM0YTE1NWEwMGNmIiwiaWQiOiIxMDc5MDMzOTYzNzQ1NzQ4MzY4MzgiLCJ1c2VyX2lkIjoiNWI1NWQ2MTUtNzc4Ny00OTY1LWExYzUtOWFiM2QxOGNmNTZmIiwia; sb-jkagupfysoootgbodrmh-auth-token.1=WRlbnRpdHlfZGF0YSI6eyJhdmF0YXJfdXJsIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EvQUNnOG9jSjlLU3B4cFc0cENGNWlmQnA5YWUtZm5wMTZ3LVdwMGdoVkJWVkRXTHRKZXlneUpSTy09czk2LWMiLCJlbWFpbCI6Im5pbHBhdGVsNjJAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZ1bGxfbmFtZSI6Ik5pbCBwYXRlbCIsImlzcyI6Imh0dHBzOi8vYWNjb3VudHMuZ29vZ2xlLmNvbSIsIm5hbWUiOiJOaWwgcGF0ZWwiLCJwaG9uZV92ZXJpZmllZCI6ZmFsc2UsInBpY3R1cmUiOiJodHRwczovL2xoMy5nb29nbGV1c2VyY29udGVudC5jb20vYS9BQ2c4b2NKOUtTcHhwVzRwQ0Y1aWZCcDlhZS1mbnAxNnctV3AwZ2hWQlZWRFdMdEpleWd5SlJPLT1zOTYtYyIsInByb3ZpZGVyX2lkIjoiMTA3OTAzMzk2Mzc0NTc0ODM2ODM4Iiwic3ViIjoiMTA3OTAzMzk2Mzc0NTc0ODM2ODM4In0sInByb3ZpZGVyIjoiZ29vZ2xlIiwibGFzdF9zaWduX2luX2F0IjoiMjAyNC0xMS0yOFQxMjowMTo1Ni4wMTQzMjVaIiwiY3JlYXRlZF9hdCI6IjIwMjQtMTEtMjhUMTI6MDE6NTYuMDE0Mzg0WiIsInVwZGF0ZWRfYXQiOiIyMDI0LTExLTI4VDEyOjAxOjU2LjAxNDM4NFoiLCJlbWFpbCI6Im5pbHBhdGVsNjJAZ21haWwuY29tIn1dLCJjcmVhdGVkX2F0IjoiMjAyNC0xMS0yOFQxMjowMTo1NS45OTgyODFaIiwidXBkYXRlZF9hdCI6IjIwMjQtMTEtMjhUMTI6MDE6NTYuNDcxODkxWiIsImlzX2Fub255bW91cyI6ZmFsc2V9LCJwcm92aWRlcl90b2tlbiI6InlhMjkuYTBBZURDbFpEby1GMjB0QlJyRFhycTFkbUpYempyNmEtVE15VlFRYi1YQU1CWXRhZ1gzRFpzR21kQmVPMHpNYjNqRzRYVjNtS2VXUndIU3Yzb3d4Uy1xMm1ISERZRnAtYUZIb2tYa0VoV3VUaGViZW9RQjZaRWZCV04tSEo2ZFJXYVY4S3FNeDduc0xEQnAxdmJrblpFbnlxRkJWbzhaenBpTjBBZnlFVDVhQ2dZS0FRa1NBUk1TRlFIR1gyTWlobkNNY2R4NmxVdVJvaTNLZFBqYjZBMDE3NSIsInByb3ZpZGVyX3JlZnJlc2hfdG9rZW4iOiIxLy8wNWNrWHF1dkUyTmZrQ2dZSUFSQUFHQVVTTndGLUw5SXJMbTduRUhPaV9USmFjS2hidE45eUFhMjlxeldNUGhFYml6VTEzTFJkUThPQkJQSkdsUHhHYk9yTXlBMHRsVW9JZFJNIn0; mp_e7880c30aeb146194855dc28a37bd3bb_mixpanel=%7B%22distinct_id%22%3A%20%22%24device%3A19347a6068e850-0be6188605689b-1e525636-1aeaa0-19347a6068e850%22%2C%22%24device_id%22%3A%20%2219347a6068e850-0be6188605689b-1e525636-1aeaa0-19347a6068e850%22%2C%22%24initial_referrer%22%3A%20%22https%3A%2F%2Fwww.lyzr.ai%2F%22%2C%22%24initial_referring_domain%22%3A%20%22www.lyzr.ai%22%2C%22__mps%22%3A%20%7B%7D%2C%22__mpso%22%3A%20%7B%22%24initial_referrer%22%3A%20%22https%3A%2F%2Fwww.lyzr.ai%2F%22%2C%22%24initial_referring_domain%22%3A%20%22www.lyzr.ai%22%7D%2C%22__mpus%22%3A%20%7B%7D%2C%22__mpa%22%3A%20%7B%7D%2C%22__mpu%22%3A%20%7B%7D%2C%22__mpr%22%3A%20%5B%5D%2C%22__mpap%22%3A%20%5B%5D%2C%22app%22%3A%20%22ICP%20Builder%22%2C%22%24search_engine%22%3A%20%22google%22%7D',
            'origin': 'https://icp-builder.lyzr.tools',
            'priority': 'u=1, i',
            'referer': 'https://icp-builder.lyzr.tools/',
            'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Error generating ICP"}

    except Exception as e:
        return {"error": f"Error generating ICP: {str(e)}"}



@app.post("/generate_prospects")
async def generate_prospects(request: DiscoverRequest):
    icp_text = request.icp_text
    # try:
    prompt = """
            
            **You have to use linkedIn for Generate a list of potential LinkedIn prospects based on the following Ideal Customer Profile (ICP) and format it into a table with the columns: Name, LinkedIn Profile URL, Email, Title, Company, and Location.**
            
            ### **Ideal Customer Profile (ICP):**
            1. **Target Roles:**
               - Chief Technology Officer (CTO)
               - Chief Information Officer (CIO)
               - IT Manager/Director
               - Product Manager
               - Head of Product Development
            
            2. **Industries:**
               - Technology Startups
               - E-commerce
               - Healthcare
               - Finance and Fintech
               - Education Technology
               - Retail
            
            3. **Company Size:**
               - Small to Medium Enterprises (10-200 employees)
               - Mid-sized to Large Enterprises (200-1000+ employees)
            
            4. **Geographic Locations:**
               - Primary Markets: North America, Europe, Asia-Pacific
               - Secondary Markets: Emerging markets like India, Southeast Asia, Latin America
            
            5. **Pain Points to Address:**
               - Scalability of software
               - Customization requirements
               - Time-to-market needs
               - Integration with existing systems
               - Enhancing user experience (UX)
            
            ### **Format Requirements:**
            - Use the table below for formatting:
              | Name              | Email                  | LinkedIn Profile URL                           | Title                          | Company                   | Location            |
              |-------------------|------------------------|------------------------------------------------|--------------------------------|---------------------------|---------------------|
              | Example Name      | example@email.com      | [linkedin.com/in/example](https://linkedin.com/in/example) | Example Title                  | Example Company           | Example Location    |
            
            ### **Additional Instructions:**
            - Ensure the LinkedIn Profile URL is accurate and links directly to the prospect's LinkedIn page.
            - If emails are not available, leave the email column blank.
            - Focus on high-value prospects that align with the ICP.
            - Ensure diverse representation across target industries and geographic regions.
            
            ---
            
            **This prompt can be used with LinkedIn Sales Navigator or other prospecting tools to generate a detailed and actionable list of potential leads.**

            The output should be a JSON array where each element is an object with the specified fields. Ensure the JSON is properly formatted.

            Example Output:
            ```json
            [
                {{
                    "Name": "John Doe",
                    "Company": "Tech Innovators Inc.",
                    "Email": "",
                    "LinkedIn Profile URL": "linkedin.com/in/johndoe",
                    "Title": "CTO",
                    "Location": "San Francisco, USA"
                }},
                {{
                    "Name": "John Hard",
                    "Company": "E-Commerce Solutions Ltd.",
                    "Email": "",
                    "LinkedIn Profile URL": "linkedin.com/in/janesmith",
                    "Title": "CIO",
                    "Location": "London, UK"
                }}
                // Continue until 10 prospects without using comments
            ]
            ```

            **IMPORTANT**: Only output the JSON array enclosed within the ```json``` code block. Do not include any additional text, explanations, or comments. Ensure that there are exactly 10 prospect entries without any trailing commas or syntax errors.

            Ideal Customer Profile:
            {icp_text}
        """
    # response = openai.ChatCompletion.create(
    #     model="gpt-4o-mini",
    #     messages=[
    #         {"role": "system", "content": "You are a helpful assistant."},
    #         {"role": "user", "content": prompt}
    #     ],
    #     temperature=0.2,
    #     max_tokens=2000,
    #     n=1,
    #     stop=None
    # )
    human = "{icp_text}"
    system_prompt = ChatPromptTemplate.from_messages([("system", prompt), ("human", human)])
    llm = ChatPerplexity(
        temperature=0,
        pplx_api_key=PERPLEXITY_API_KEY,
        streaming=False,
        model="llama-3.1-sonar-small-128k-online"
    )

    # result = response.choices[0].message['content']
    # result = response["text"]
    # prospects_json = clean_json_output(result)
    chain = system_prompt | llm
    response = chain.invoke({"icp_text": icp_text})
    response_json = response.content
    response_json = response_json.replace("json", "")
    response_json = response_json.replace("```", "")
    prospects_json = clean_json_output(response_json)
    print(prospects_json)
    prospects = json.loads(prospects_json)

    # Validate that we have exactly 10 prospects
    if not isinstance(prospects, list) or len(prospects) != 10:
        return {"error": "Expected a list of 10 prospects."}

    return {"prospects": prospects}

    # except Exception as e:
    #     return {"error": f"Error generating prospects: {str(e)}"}
