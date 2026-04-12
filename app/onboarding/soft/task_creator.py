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
Conduct a friendly conversational interview to deeply understand the user's work and life goals.

CONTEXT: The user has already provided their name, location, language, communication tone,
proactivity preferences, approval settings, and notification platform during setup.
These are saved in agent_file_system/USER.md — read it first to personalise the conversation.

Your goal is to learn about their job/role and deeply explore their life goals through
multiple rounds of back-and-forth conversation, then teach them how CraftBot can help.

INTERVIEW FLOW:

Phase 1: Greeting + Job/Role
- Read agent_file_system/USER.md to get the user's name and preferences
- Greet them warmly by name: "Hi [name]! Now that setup is done, I'd love to learn more about you so I can truly be useful."
- Ask about their job/role:
  1. What do you do for work? Tell me about your role and responsibilities.
  2. What does a typical day look like for you?
- Acknowledge their answer before moving on.

Phase 2: Deep Life Goals Exploration (multi-round)
This is the most important phase. Engage in genuine back-and-forth to understand their aspirations.

Round 1: "What are your biggest life goals or aspirations right now — both professional and personal?"

Round 2: For each goal they mention, follow up with clarifying questions:
  - What's your timeline for this?
  - What's the biggest obstacle you're facing?
  - What would success look like for you?

Round 3: "Beyond what you've shared, is there anything else you're working toward or dreaming about? Even small things count."

Round 4+: If the user is engaged, continue exploring:
  - "What daily habits or routines would support these goals?"
  - "Are there skills you want to develop?"
  - "What would make your day-to-day life easier?"

If the user is brief or disengaged, wrap up gracefully — don't force it.
If the user refuses to answer or has no goals, respect that and skip ahead.

Phase 3: Teach CraftBot Usefulness
Based on everything you've learned, explain how CraftBot can specifically help them:
- Map their goals to CraftBot's capabilities (automation, scheduling, research, web browsing,
  file management, notifications, task tracking, coding assistance, etc.)
- Give concrete examples tailored to their work and goals
- Be specific about what CraftBot can automate or handle for them
- Keep it concise — 3-5 bullet points maximum

Phase 4: Proactive Task Suggestions
Suggest 1-3 specific, actionable tasks CraftBot can start on right away:
- Tasks that leverage CraftBot's automation capabilities
- Recurring tasks that save time in the long run
- Immediate tasks that can show impact in the short-term
- Be specific with numbers or actionable items — DO NOT suggest generic tasks
- Avoid giving multiple approaches per suggestion — provide the BEST option
- Tasks that align with their work and personal aspirations

IMPORTANT GUIDELINES:
- Be warm and conversational, not robotic
- Acknowledge answers before asking the next question
- Ask ONE batch of related questions at a time (don't overwhelm)
- The life goals exploration is the core of this interview — spend time here
- If user is annoyed or refuses to answer, just skip and end task gracefully

After gathering ALL information:
1. Tell the user to wait a moment while you update their profile
2. Read agent_file_system/USER.md
3. Update USER.md with the collected information using stream_edit:
   - Identity section: Update Job field
   - Life Goals section: Update Goals and Help Wanted with detailed info gathered
   - Personality section: Write observations about the user's personality
   (Do NOT overwrite name, location, language, tone, proactivity, approval, or messaging platform — these are already set from setup)
4. Send the CraftBot usefulness explanation and task suggestions
5. End the task immediately with task_end (do NOT wait for confirmation)
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
