import streamlit as st
from pydantic import BaseModel, ValidationError
import openai
from dotenv import load_dotenv
import os
import json
import pandas as pd
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load environment variables
load_dotenv()

# Configuration settings
API_TITLE = os.getenv("API_TITLE", "ICP Generator")
API_VERSION = os.getenv("API_VERSION", "1.0")
DEBUG_MODE = os.getenv("DEBUG_MODE", "False") == "True"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# Define the ICP request model
class ICPRequest(BaseModel):
    website: str


# Function to clean JSON output
def clean_json_output(raw_json):
    """
    Attempts to clean the JSON string by removing unwanted text.
    This is a basic example and may need to be tailored based on actual output.
    """
    try:
        # Remove any text before the first '[' and after the last ']'
        json_start = raw_json.find('[')
        json_end = raw_json.rfind(']') + 1
        if json_start == -1 or json_end == -1:
            # If not found, return as-is
            return raw_json
        cleaned_json = raw_json[json_start:json_end]

        # Remove trailing commas and other common issues
        cleaned_json = re.sub(r',\s*}', '}', cleaned_json)
        cleaned_json = re.sub(r',\s*]', ']', cleaned_json)

        return cleaned_json
    except Exception as e:
        print(f"Error cleaning JSON: {str(e)}")
        return raw_json  # Return as-is if cleaning fails


# Function to extract JSON from response using regex
def extract_json_from_response(raw_response):
    """
    Extracts JSON array from raw response using regular expressions.
    """
    try:
        # Use regex to find JSON array
        match = re.search(r'\[.*\]', raw_response, re.DOTALL)
        if match:
            json_str = match.group(0)
            return json_str
        else:
            return ""
    except Exception as e:
        print(f"Error extracting JSON: {str(e)}")
        return ""


# Define the ICPPlanner class using OpenAI's API directly
class ICPPlanner:
    def __init__(self, website, api_key):
        self.website = website
        self.api_key = api_key
        openai.api_key = self.api_key

    def run(self):
        try:
            prompt = f"""
            Generate an Ideal Customer Profile (ICP) for the company {self.website}. The ICP should be comprehensive and structured, covering the following sections:

                Company Overview

                Brief description of {self.website}, including its core offerings such as mobile app development, web application development, SaaS solutions, and other related software services.
                Highlight the company’s mission, vision, and key value propositions.
                Demographic and Firmographic Characteristics

                Industry Sectors: Identify relevant industries (e.g., Technology Startups, E-commerce, Healthcare, Education, Finance and Fintech, Retail) that would benefit from {self.website}’s services.
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

                Concisely summarize the Ideal Customer Profile, emphasizing the key characteristics that make a company an ideal customer for {self.website}.
                Highlight the benefits {self.website} offers to these ideal customers and the value of forming long-term partnerships.
                Additional Instructions:

                Ensure the ICP is tailored specifically to {self.website}’s services and market positioning.
                Use clear headings and bullet points for readability.
                Provide actionable insights that can help {self.website} align its marketing, sales, and product development strategies with the identified ideal customers.
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

            return {"raw": result, "parsed": self.parse_icp(result)}

        except Exception as e:
            print(f"Error in ICPPlanner.run: {str(e)}")
            return {"raw": "", "parsed": f"Error generating ICP: {str(e)}"}

    def parse_icp(self, raw_response):
        """
        Parses the raw ICP response.
        """
        try:
            # Assuming the ICP is in Markdown or plain text, return as-is
            return raw_response
        except Exception as e:
            print(f"Error parsing ICP: {str(e)}")
            return f"Error parsing ICP: {str(e)}"


# Define the ProspectsPlanner class using OpenAI's API directly
class ProspectsPlanner:
    def __init__(self, icp_text, api_key):
        self.icp_text = icp_text
        self.api_key = api_key
        openai.api_key = self.api_key

    def run(self):
        try:
            prompt = f"""
            **Generate a list of potential LinkedIn prospects based on the following Ideal Customer Profile (ICP) and format it into a table with the columns: Name, LinkedIn Profile URL, Title, Company, and Location.**
            
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
                    "LinkedIn Profile URL": "linkedin.com/in/johndoe",
                    "Title": "CTO",
                    "Location": "San Francisco, USA"
                }},
                {{
                    "Name": "John Hard",
                    "Company": "E-Commerce Solutions Ltd.",
                    "LinkedIn Profile URL": "linkedin.com/in/janesmith",
                    "Title": "CIO",
                    "Location": "London, UK"
                }}
                // Continue until 10 prospects without using comments
            ]
            ```

            **IMPORTANT**: Only output the JSON array enclosed within the ```json``` code block. Do not include any additional text, explanations, or comments. Ensure that there are exactly 10 prospect entries without any trailing commas or syntax errors.

            Ideal Customer Profile:
            {self.icp_text}
            """

            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=2000,
                n=1,
                stop=None
            )

            result = response.choices[0].message['content']

            return {"raw": result, "parsed": self.parse_json(result)}

        except Exception as e:
            print(f"Error in ProspectsPlanner.run: {str(e)}")
            return {"raw": "", "parsed": f"Error generating prospects: {str(e)}"}

    def parse_json(self, raw_json):
        """
        Parses the raw JSON response from the language model.
        """
        try:
            # Extract JSON content from the code block
            json_start = raw_json.find('```json')
            if json_start != -1:
                json_start = raw_json.find('[', json_start)
                json_end = raw_json.rfind(']')
                cleaned_json = raw_json[json_start:json_end + 1]
            else:
                cleaned_json = raw_json

            # Remove any trailing comments or text after the JSON array
            cleaned_json = re.split(r'\n\s*//', cleaned_json)[0]

            # Parse the JSON
            prospects = json.loads(cleaned_json)

            # Validate that we have exactly 10 prospects
            if not isinstance(prospects, list) or len(prospects) != 10:
                return "Error: Expected a list of 10 prospects."

            # Further validation of each prospect's fields
            required_fields = {"Name", "LinkedIn Profile URL", "Location", "Title", "Company"}
            for prospect in prospects:
                if not isinstance(prospect, dict):
                    return "Error: Each prospect should be a JSON object."
                if not required_fields.issubset(prospect.keys()):
                    return f"Error: Missing fields in prospect: {prospect}"

            return prospects

        except json.JSONDecodeError as jde:
            print(f"JSON Decode Error in ProspectsPlanner.parse_json: {str(jde)}")
            return f"Error parsing prospects JSON: {str(jde)}"
        except Exception as e:
            print(f"Error in ProspectsPlanner.parse_json: {str(e)}")
            return f"Error parsing prospects JSON: {str(e)}"


# Initialize Streamlit Session State
if 'icp_result' not in st.session_state:
    st.session_state.icp_result = None
if 'prospects_result' not in st.session_state:
    st.session_state.prospects_result = None


# Function to send email
def send_email(recipient, subject, body):
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")

    # Create the email
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        # Set up the server
        with smtplib.SMTP('smtp.gmail.com', 587) as server:  # Use your SMTP server
            server.starttls()  # Secure the connection
            server.login(sender_email, sender_password)  # Log in to your email account
            server.send_message(msg)  # Send the email
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False


# Streamlit App
def main():
    st.set_page_config(page_title=API_TITLE, page_icon="💼", layout="wide")
    st.title(f"{API_TITLE} v{API_VERSION}")
    st.write("Generate an Ideal Customer Profile (ICP) for your company and discover potential prospects.")

    # Input form
    with st.form("icp_form"):
        website = st.text_input("Enter your company's website:", value="",
                                help="Provide the website URL of your company.")
        submit_button = st.form_submit_button(label="Generate ICP")

    if submit_button:
        if not website.strip():
            st.error("Please enter a valid website URL.")
        else:
            with st.spinner("Generating ICP..."):
                try:
                    # Validate input using Pydantic
                    icp_request = ICPRequest(website=website.strip())

                    # Initialize and run ICPPlanner
                    planner = ICPPlanner(icp_request.website, OPENAI_API_KEY)
                    icp_result = planner.run()

                    # Check if ICP generation was successful
                    if isinstance(icp_result['parsed'], str) and icp_result['parsed'].startswith("Error"):
                        st.error(icp_result['parsed'])
                        st.session_state.icp_result = None
                    else:
                        # Update session state
                        st.session_state.icp_result = icp_result['parsed']
                        st.session_state.prospects_result = None  # Reset prospects

                        # Display the ICP
                        st.success("ICP Generated Successfully!")
                        st.markdown("### Ideal Customer Profile")
                        st.write(icp_result['parsed'])

                except ValidationError as ve:
                    st.error(f"Input validation error: {ve}")
                    st.session_state.icp_result = None
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                    st.session_state.icp_result = None

    # Display the "Discovered Prospects" button only if ICP is generated
    if st.session_state.icp_result and not (
            isinstance(st.session_state.icp_result, str) and st.session_state.icp_result.startswith("Error")):
        if st.button("Discovered Prospects"):
            with st.spinner("Generating Discovered Prospects..."):
                try:
                    # Initialize and run ProspectsPlanner
                    prospects_planner = ProspectsPlanner(st.session_state.icp_result, OPENAI_API_KEY)
                    prospects_result = prospects_planner.run()

                    # Check if Prospects generation was successful
                    if isinstance(prospects_result['parsed'], str) and prospects_result['parsed'].startswith("Error"):
                        st.error(prospects_result['parsed'])
                        st.session_state.prospects_result = None
                    else:
                        # Update session state
                        st.session_state.prospects_result = prospects_result['parsed']

                        # Convert prospects to DataFrame
                        prospects_df = pd.DataFrame(prospects_result['parsed'])

                        # Display the result
                        st.success("Discovered Prospects Generated Successfully!")
                        st.markdown("### Discovered Prospects")
                        st.dataframe(prospects_df)

                        # Optional: Add a download button for the prospects
                        csv = prospects_df.to_csv(index=False)
                        st.download_button(
                            label="Download Prospects as CSV",
                            data=csv,
                            file_name='prospects.csv',
                            mime='text/csv',
                        )

                        # Send Email Button
                        if st.button("Send Email"):
                            recipient = st.text_input("Enter recipient's email:")
                            subject = "Discovered Prospects"
                            body = prospects_df.to_string(index=False)  # Convert DataFrame to string for email body

                            if recipient:
                                if send_email(recipient, subject, body):
                                    st.success("Email sent successfully!")
                                else:
                                    st.error("Failed to send email.")
                            else:
                                st.error("Please enter a valid email address.")

                except Exception as e:
                    st.error(f"An error occurred while generating prospects: {str(e)}")
                    st.session_state.prospects_result = None

    # Optional: Display API settings
    with st.expander("API Settings"):
        st.write({
            "Title": API_TITLE,
            "Version": API_VERSION,
            "Debug Mode": DEBUG_MODE
        })


if __name__ == "__main__":
    # Check if API key is set
    if not OPENAI_API_KEY:
        st.error("OpenAI API Key not found. Please set it in the .env file.")
    else:
        main()
