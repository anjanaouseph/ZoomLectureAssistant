# 1. Get transcript
# 2. Clean transcript
# 3. Process with LLM
# 4. Extract structured data
# 5. Store results (Notion)
# 6. Send reminders (Gmail)

from ast import Store
from marshal import version
import os
from unittest import result
import requests
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI #Python code talk to Google’s AI model
from gmail import send_email_notification

# Load environment variables
load_dotenv()

# Set API keys from environment variables
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_PAGE_ID = os.getenv("NOTION_PAGE_ID") # The ID of the Notion page where the meeting notes will be stored
GMAIL_API_TOKEN = os.getenv("GMAIL_API_TOKEN") # Token for sending email reminders
BOT_ID = os.getenv("BOT_ID") # Unique identifier for the bot, used for authentication and tracking
#Identifies your Zoom bot (Attendee API)
ATTENDEE_API_TOKEN = os.getenv("ATTENDEE_API_TOKEN")
# Auth token for Zoom/Attendee API. Attendee (often called “Zoom attendee bot”) is a 
# service that automatically joins your Zoom meetings as a bot and does useful things like recording and transcribing.
# Lets you access transcript data securely

# Set environment variables explicitly for langchain
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
os.environ["NOTION_API_KEY"] = NOTION_API_KEY
#it sets environment variables inside your running Python program
#Some libraries don’t read your Python variables. They ONLY read from os.environ like langchain

# Initialize the Google Generative AI model
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.7)
#Gemini 1.5 Pro because it handles long-context inputs like lecture transcripts very well.

#model: Specifies which version of the Google Generative AI model to use. "gemini-1.5-pro" is a specific model variant that 
# may have certain capabilities or optimizations. 
#temperature: Controls the randomness of the model's output. A higher temperature (e.g., 0.7) makes the output more creative and diverse, 
# while a lower temperature (e.g., 0.2) makes it more focused and deterministic.        
#“I used a temperature of 0.7 to balance accuracy and flexibility, since lecture transcripts can be noisy and require 
# some interpretive understanding while still maintaining reliable outputs.”

# I chose a temperature of 0.7 to balance accuracy and flexibility. 
# Since lecture transcripts are often noisy and unstructured, 
# the model needs some randomness to interpret context correctly, but not so much that it generates inconsistent or incorrect outputs.
# Temperature controls how “random” or “creative” the AI is:
# Low → predictable, strict
# High → creative, flexible

# fetch transcript gets the lecture transcript from Zoom (Attendee API)
#retrieves lecture data from the Attendee API using authentication headers,
# BOT_ID is a unique identifier for a Zoom recording bot session (from the Attendee API).
# When you use the Attendee Zoom bot: 
# A bot joins your Zoom meeting It records audio generates transcript That session is saved with a unique ID → BOT_ID
def fetch_transcript(bot_id=BOT_ID, api_token=ATTENDEE_API_TOKEN): 
    url = f"https://app.attendee.dev/api/v1/bots/{bot_id}/transcript"
    headers = {
        'Authorization': f'Token {api_token}',
        'Content-Type': 'application/json'
    }
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else f"Error: {response.status_code}"

# This function shortens the transcript
def get_first_n_words(text, n=100):
    words = text.split() #Converts text → list of words
    return ' '.join(words[:n]) #Keeps only first 100 words (default)
#This function trims the transcript to a fixed size so it fits within LLM limits and improves processing efficiency.
#This preprocessing step is important because large transcripts can exceed token limits and reduce model efficiency.

#TODO:
#clean transcripts better (remove noise, speakers, filler words) -> to be explored later
#Chunking + targeted prompts

#sends my AI-generated lecture notes to Notion.
def append_to_notion_page(title, summary, key_points):

    # Authenticates with Notion
    # Tells Notion you're sending JSON data
    # Specifies API version

    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    #building the content blocks to add to the Notion page. Each block represents a different section of the lecture notes, 
    # such as the title, summary, and key points. The blocks are structured according to Notion's API requirements, 
    # allowing for proper formatting when added to the page.
    #Notion works using blocks, so you format everything like this.
#    A page = parent
#    Content inside it = children

    blocks = [
        {"object": "block", "type": "heading_1", "heading_1": {"rich_text": [{"type": "text", "text": {"content": title}}]}},
        {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Summary"}}]}},
        {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": summary}}]}},
        {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Key Points"}}]}},
        {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": key_points}}]}},
        {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}}]}}
    ]
    response = requests.patch(
        f"https://api.notion.com/v1/blocks/{NOTION_PAGE_ID}/children", #updating an existing Notion page
        headers=headers,
        json={"children": blocks}
    )
    return "Content successfully added to Notion page" if response.status_code == 200 else f"Error: {response.status_code} - {response.text}"

# an AI agent (summarizer)
# Define summarizer agent
summarizer = Agent(
    role="CS Lecture Summarizer", #Defines what the agent is
    goal="Create concise summaries of CS lectures", #What the agent is trying to achieve
    backstory="You are an expert in computer science education with deep knowledge of algorithms, data structures, programming languages, and software engineering principles. You excel at distilling complex technical concepts into clear, organized summaries.",
    #You are telling the AI how to think
    verbose=True,#Prints logs while running for debugging
    llm=llm #connects the agent to the Google Generative AI model we initialized earlier
)

# This defines what the agent should do
summarize_task = Task(
    description="PLACEHOLDER", #This will later contain:your transcript,instructions. You dynamically update it later in code. actual instructions + transcripts
    expected_output="A detailed summary of the lecture", #Tells the agent how the output should look
    agent=summarizer #which agent should perform this task (the summarizer) we just defined
)

task_extractor = Agent(
     role="Assignment & Key Point Extractor",
    goal="Extract key technical points and assignments from lecture",
    backstory="You are an assistant that identifies important concepts, deadlines, and tasks from lectures.",
    verbose=True,
    llm=llm
)

extract_task = Task(
    description="PLACEHOLDER",
    expected_output="A list of key technical points and assignments",
    agent=task_extractor
)

# Creating a Crew (team of AI agents) that will execute tasks.
lecture_crew = Crew(
    agents=[summarizer, task_extractor],
    tasks=[summarize_task, extract_task],
    process=Process.sequential,
    verbose=True
)

# agents=[summarizer] - This defines who is in the team. In this case, it's just the summarizer agent we created.
# tasks=[summarize_task] - This specifies what tasks the team will work on. Task = summarize lecture + extract key points.
# process=Process.sequential - This tells the crew to execute tasks one after the other in a specific order. One after the other. Here only one task.
# Execution flow:
# Step 1 → summarizer runs summarize_task
# Step 2 → extractor runs extract_task

# Zoom transcript
#    ↓
# AI agents
#    ↓
# Extract summary + assignments
#    ↓
# Store in Notion
#    ↓
# Send email

def main():
    print("Fetching transcript from Attendee API...")
    transcript_data = fetch_transcript()

    # Convert API response to text
    if isinstance(transcript_data, dict) and "transcript" in transcript_data: #Did API return valid data? does key transcript and is it a dict?
        transcript_entries = transcript_data.get("transcript", []) #Gets list of transcript chunks
        transcript_text = "\n\n".join( #Converts structured data → readable text
            f"{entry.get('speaker', 'Unknown')}: {entry.get('text', '')}" #formats each chunk as "Speaker: Text"
            for entry in transcript_entries
        )
    else:
        transcript_text = str(transcript_data) #If the API response is NOT in the expected format, convert whatever we got into a string.

    # Trim transcript (for now)
    trimmed_transcript = get_first_n_words(transcript_text, 100)#Keeps only first 100 words (helps avoid token limits)

    print("Transcript trimmed.")
    print(f"Sample:\n{trimmed_transcript[:200]}...\n")

    # -------------------------------
    # Update Tasks (Dynamic Input)
    # -------------------------------
    # Inject transcript into tasks

    # Task 1 (Summarizer)
    lecture_crew.tasks[0].description = f"""
    Transcript:
    \"\"\"{trimmed_transcript}\"\"\"

    Return ONLY:

    SUMMARY:
    <3–5 paragraph summary>
    """

    # Task 2: Extraction
    lecture_crew.tasks[1].description = f"""
    Transcript:
    \"\"\"{trimmed_transcript}\"\"\"

    Return ONLY:

    KEY POINTS:
    - point 1
    - point 2

    ASSIGNMENTS:
    - assignment 1
    """

    # -------------------------------
    # Run Crew
    # -------------------------------

    print("Running CrewAI pipeline...")
    result = lecture_crew.kickoff() #Run AI Agents on the tasks we defined. This will execute the summarization and extraction sequentially, and return the results.
    print("Processing completed!\n")

    # -------------------------------
    # Parse Output
    # -------------------------------

    summary = "No summary generated"
    key_points_clean = "No key points extracted"
    assignments = "No assignments found"

    if result:
        if "SUMMARY:" in result:
            summary = result.split("SUMMARY:")[1].split("KEY POINTS:")[0].strip()

        if "KEY POINTS:" in result:
            # First extract everything after KEY POINTS
            key_section = result.split("KEY POINTS:")[1]

            # If assignments exist → split further
            if "ASSIGNMENTS:" in key_section:
                key_points_clean = key_section.split("ASSIGNMENTS:")[0].strip()
                assignments = key_section.split("ASSIGNMENTS:")[1].strip()
            else:
                key_points_clean = key_section.strip() #strip() removes extra whitespace from the beginning and end of the string

    # -------------------------------
    # Store in Notion
    # -------------------------------

    title = "CS Lecture Summary - " + datetime.now().strftime("%Y-%m-%d")

    print("Adding content to Notion page...")
    notion_result = append_to_notion_page(title, summary, key_points_clean) #Sends results to Notion
    print(notion_result)

    # -------------------------------
    # Send Email Notification
    # -------------------------------

    if assignments != "No assignments found":
        print("Sending email notification...")

        email_subject = "New Lecture Summary & Assignments"

        email_result = send_email_notification(
            email_subject,
            summary,
            key_points_clean,
            assignments
        )

        print(email_result)
    else:
        print("No assignments found — skipping email.")

if __name__ == "__main__":
    main()

#Adding a 3rd Agent for extracting assignments
#More API calls → higher cost 💸
# Slightly slower
# More code complexity
# Overkill for small project