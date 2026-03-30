# -*- coding: utf-8 -*-
"""
Soft onboarding task creator.

Creates a task that conducts a conversational interview to build
the user profile and populate USER.md and AGENT.md.
"""

from typing import TYPE_CHECKING

from app.logger import logger

if TYPE_CHECKING:
    from app.task.task_manager import TaskManager


SOFT_ONBOARDING_TASK_INSTRUCTION = """
Conduct a friendly conversational interview to learn about the user.

Your goal is to gather information to personalize the agent experience efficiently.
Ask MULTIPLE related questions together to reduce back-and-forth turns.

INTERVIEW FLOW (4 batches):

1. Warm Introduction + Identity Questions
Start with a friendly greeting and ask the first batch using a numbered list:
   - What should I call you?
   - What do you do for work?
   - Where are you based?
   (Infer timezone from their location, keep this silent)

   Example opening:
    > "Hi there! I'm excited to be your new AI assistant. To personalize your experience, let me ask a few quick questions:
    > 1. What should I call you?
    > 2. What do you do for work?
    > 3. Where are you based?"

2. Preference Questions (Combined)
   - What language do you prefer me to communicate in?
   - Do you prefer casual or formal communication?
   - Should I proactively suggest things or wait for instructions?
   - What types of actions should I ask your approval for?

3. Messaging Platform
   - Which messaging platform should I use for notifications? (Telegram/WhatsApp/Discord/Slack/CraftBot Interface only)

4. Life Goals & Assistance
   - What are your life goals or aspirations?
   - What would you like me to help you with generally?

Refer to the "user-profile-interview" skill for questions and style.

IMPORTANT GUIDELINES:
- Ask related questions together using a numbered list format
- Be warm and conversational, not robotic
- Acknowledge their answers before the next batch
- Infer timezone from location (e.g., San Francisco = Pacific Time)
- The life goals question is most important, ask multiple questions if necessary or goal unclear. Guide them to answer this question. Skip if user has no life or goal.
- If user is annoyed by this interview or refuse to answer, just skip, and end task.

After gathering ALL information:
1. Tell the user to wait a moment while you update their preference
2. Read agent_file_system/USER.md
3. Update USER.md with the collected information using stream_edit (including Language in Communication Preferences and Life Goals section)
4. Suggest tasks based on life goals: Send a message suggesting 1-3 tasks that CraftBot can help with to improve their life and get closer to achieving their goals. Focus on:
   - Tasks that leverage CraftBot's automation capabilities
   - Recurring tasks that save time in the long run
   - Immediate tasks that can show impact in short-term
   - Bite-size tasks that is specialized, be specific with numbers or actionable items. DO NOT suggest generic task.
   - Avoid giving mutliple approaches in each suggested task, provide the BEST option to achieve goal.
   - Tasks that align with their work and personal aspirations
5. End the task immediately with task_end (do NOT wait for confirmation)

Start with: "Hi! I'm excited to be your AI assistant. To personalize your experience, let me ask a few quick questions:" then list the first batch.
"""


def create_soft_onboarding_task(task_manager: "TaskManager") -> str:
    """
    Create a soft onboarding interview task.

    This task uses the user-profile-interview skill to conduct
    a conversational Q&A interview and populate USER.md/AGENT.md.

    Args:
        task_manager: TaskManager instance to create the task

    Returns:
        Task ID of the created interview task
    """
    task_id = task_manager.create_task(
        task_name="User Profile Interview",
        task_instruction=SOFT_ONBOARDING_TASK_INSTRUCTION,
        mode="simple",
        action_sets=["file_operations", "core"],
        selected_skills=["user-profile-interview"]
    )

    logger.info(f"[ONBOARDING] Created soft onboarding task: {task_id}")
    return task_id
