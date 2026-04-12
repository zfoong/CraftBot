---
name: user-profile-interview
description: Conduct a conversational interview to explore user's job and life goals in depth
user-invocable: false
action-sets:
  - file_operations
  - core
---

# User Profile Interview

Conduct a friendly, multi-round conversational interview to deeply understand the user's work, life goals, and how CraftBot can help them.

## Context

The user has already provided the following during setup (hard onboarding):
- Name, location, timezone
- Language preference
- Communication tone (casual/formal/friendly/professional)
- Proactivity level (low/medium/high)
- Approval settings
- Preferred notification platform

These are saved in `agent_file_system/USER.md`. **Do NOT re-ask these questions.**

## Objective

Extract and document:
- Job/role, responsibilities, and typical workday
- Life goals and aspirations (explored in depth over multiple rounds)
- Personality observations
- How CraftBot can specifically help them

## Interview Flow

### Phase 1: Greeting + Job/Role

First, read `agent_file_system/USER.md` to get the user's name and existing info.

> "Hi [name]! Now that setup is done, I'd love to learn more about you so I can truly be useful.
> 1. What do you do for work? Tell me about your role and responsibilities.
> 2. What does a typical day look like for you?"

Collect:
- **Job/Role**: Their profession, responsibilities
- **Work context**: Team size, industry, daily workflow

Acknowledge their answer warmly before moving on.

### Phase 2: Deep Life Goals Exploration (Multi-Round)

This is the most important phase. Engage in genuine back-and-forth.

**Round 1** — Open-ended:
> "What are your biggest life goals or aspirations right now — both professional and personal?"

**Round 2** — Follow up on each goal:
- What's your timeline for this?
- What's the biggest obstacle you're facing?
- What would success look like for you?

**Round 3** — Broaden:
> "Beyond what you've shared, is there anything else you're working toward or dreaming about? Even small things count."

**Round 4+** — Continue if the user is engaged:
- "What daily habits or routines would support these goals?"
- "Are there skills you want to develop?"
- "What would make your day-to-day life easier?"

If the user is brief or disengaged, wrap up gracefully — don't force it.
If the user refuses or has no goals, respect that and skip ahead.

Note any personality traits, preferences, or working style observations from the conversation.

### Phase 3: Teach CraftBot Usefulness

Based on everything learned, explain how CraftBot can specifically help:
- Map their goals to CraftBot's capabilities (automation, scheduling, research, web browsing, file management, notifications, task tracking, coding assistance, etc.)
- Give concrete examples tailored to their work and goals
- Be specific about what CraftBot can automate or handle for them
- Keep it concise — 3-5 bullet points maximum

### Phase 4: Proactive Task Suggestions

Suggest 1-3 specific, actionable tasks CraftBot can start on right away:
- Tasks that leverage CraftBot's automation capabilities
- Recurring tasks that save time in the long run
- Immediate tasks that can show impact in the short-term
- Bite-size tasks that are specialized — be specific with numbers or actionable items. DO NOT suggest generic tasks.
- Avoid giving multiple approaches in each suggested task — provide the BEST option to achieve the goal.
- Tasks that align with their work and personal aspirations

## After Interview

1. **Read current files**: Use `stream_read` to read `agent_file_system/USER.md`

2. **Update USER.md** with extracted information using `stream_edit`:
   - Identity section: Update **Job** field
   - Life Goals section: Update **Goals** and **Help Wanted** with detailed info gathered
   - Personality section: Write a paragraph summarizing personality observations
   - **Do NOT overwrite** pre-populated fields: Full Name, Preferred Name, Location, Timezone, Language, Preferred Tone, Preferred Messaging Platform, Prefer Proactive Assistance, Approval Required For

3. **Update AGENT.md** if user provided a name for the agent:
   - Update the "Agent Given Name" field

4. **Send usefulness explanation + task suggestions** in a single message

5. **End task immediately**: Use `task_end` right after suggesting tasks. Do NOT wait for confirmation or ask if information is accurate.

## USER.md Template Reference

```markdown
## Identity
- **Full Name:** [Pre-populated from setup]
- **Preferred Name:** [Pre-populated from setup]
- **Email:** [If provided]
- **Location:** [Pre-populated from setup]
- **Timezone:** [Pre-populated from setup]
- **Job:** [Collected during this interview]
- **Other:** [Additional info like age, interests]

## Communication Preferences
- **Language:** [Pre-populated from setup]
- **Preferred Tone:** [Pre-populated from setup]
- **Response Style:** [brief/detailed/balanced — infer from conversation]
- **Preferred Messaging Platform:** [Pre-populated from setup]

## Agent Interaction
- **Prefer Proactive Assistance:** [Pre-populated from setup]
- **Approval Required For:** [Pre-populated from setup]

## Life Goals
- **Goals:** [Detailed goals from multi-round exploration]
- **Help Wanted:** [What they want CraftBot to help with]

## Personality
[Paragraph describing personality observations from conversation]
```

## Conversation Guidelines

- Be warm and conversational, not robotic or interrogative
- Ask ONE batch of related questions at a time — don't overwhelm
- Acknowledge their answers before moving to the next question
- If they seem uncomfortable with a question, offer to skip it
- Adapt your follow-up questions based on their answers
- The life goals exploration is the core — spend time here, ask follow-ups
- If user is annoyed by this interview or refuses to answer, just skip and end task
- Keep the conversation natural — it should feel like a friendly chat, not a form

## Allowed Actions

`send_message`, `stream_read`, `stream_edit`, `task_update_todos`, `task_end`

## FORBIDDEN Actions

Do NOT use: `run_shell`, `run_python`, `write_file`, `create_file`, `web_search`

## Example Interaction

**Agent**: "Hi Alex! Now that setup is done, I'd love to learn more about you so I can truly be useful.
1. What do you do for work? Tell me about your role and responsibilities.
2. What does a typical day look like for you?"

**User**: "I'm a software engineer at a startup. Mostly backend work — APIs, databases, deployments. Typical day is standup, coding, code reviews, and debugging production issues."

**Agent**: "Sounds like a busy day! Backend work at a startup means you're probably wearing a lot of hats. Now for the big question — what are your biggest life goals or aspirations right now, both professional and personal?"

**User**: "I want to build my own startup eventually. Also trying to get better at product management and save money."

**Agent**: "Those are great goals! Let me dig a bit deeper:
1. For building your own startup — do you have a specific idea in mind, or are you still exploring? What's your timeline?
2. For product management — are you looking at formal courses, or more hands-on learning?
3. For saving — do you have a specific target or milestone you're working toward?"

**User**: "I have a few ideas but nothing concrete yet. Maybe 2-3 years. For PM, I want hands-on experience. Saving target is $50K."

**Agent**: "That's a solid plan. Beyond these three goals, is there anything else you're working toward? Even small daily improvements count."

**User**: "I want to build better habits — reading more, exercising regularly."

**Agent**: "Great picture of where you're headed! Here's how I can specifically help you:

- **Startup research**: I can research markets, competitors, and business models for your startup ideas and deliver summaries
- **PM learning**: I can curate daily PM articles, case studies, and podcast episodes tailored to hands-on learning
- **Savings tracking**: I can set up automated weekly check-ins on your savings progress toward $50K
- **Habit building**: I can create daily reminders and track streaks for reading and exercise

Based on all this, here are some tasks I can start on right now:

1. **Weekly startup idea research** — Every Monday, I'll research one of your startup ideas: market size, competitors, and potential customers, and deliver a 1-page summary
2. **Daily PM digest** — Curate 3 top product management articles each morning focused on practical, hands-on PM skills
3. **Savings milestone tracker** — Set up a bi-weekly check-in where we review your progress toward $50K and identify areas to optimize"

[Agent ends task immediately after this message]
