# ZoomLectureAssistant

The system uses an attendee bot to join Zoom meetings and generate transcripts. These transcripts are processed using an LLM to extract structured information like summaries and key points. The results are stored in Notion using their API, and if assignments are detected, the system sends automated email notifications using Gmail OAuth. This creates a fully automated pipeline from meeting to actionable notes.

I initially used a multi-agent architecture using CrewAI to separate responsibilities like summarization and extraction. This improves modularity and makes it easier to scale the system. However, for efficiency, this could also be simplified to a single LLM call for this use case.

Agents become more useful when the system requires multi-step reasoning, different roles, or interaction with external tools. For example, if I extend this system to include scheduling reminders or generating quizzes, a multi-agent setup would be more appropriate.

A single LLM call would be simpler and more efficient for this use case. However, I used agents to demonstrate modular design and separation of concerns. This makes the system easier to extend and maintain as complexity grows.

Agents Use Cases in future:

Case 1 — Multi-step pipeline
Transcript → Clean → Summarize → Extract → Format

Different agents for each step

Case 2 — Different reasoning styles
Teacher agent → explains simply
Expert agent → explains technically
Quiz agent → generates questions
Case 3 — Tool usage (VERY strong answer)
Extractor → finds assignments
Calendar agent → schedules deadlines
Email agent → sends reminders

Agents interact with tools

Case 4 — Large data / chunking
Long lecture → split → summarize → combine
