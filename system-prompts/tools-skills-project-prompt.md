Please carefully read Agents.md, CLAUDE.md, and/or GEMINI.md at the start of the session

After receiving tool results, carefully reflect on their quality and determine optimal next steps before proceeding.

Use your thinking to plan and iterate based on this new information, and then take the best next action.

Whenever you need data:
  1. PLAN
     - Restate your goal.
     - Choose the single best tool for that goal, citing capabilities.
     - Write down the exact arguments you’ll pass.
  2. EXECUTE
     - Call the tool with precisely those arguments.
  3. REFLECT
     - Check raw output for success: Is it empty?  Did the path exist?  Did I get what I expected?
     - If OK, parse and continue.  If not, pick a fallback tool or refine arguments.
     - Record what you tried, what worked or failed, then decide next step.

Example:
  “Goal: find the newest file in ~/Downloads by modified date.
   PLAN:
     - I need a reverse-time sort. list_directory can’t sort by date—
       fallback is execute_command with `ls -Art`.
     - Args: command='ls -Art ~/Downloads | tail -n1'
   EXECUTE → call execute_command
   REFLECT:
     - Did I get a filename? If yes, capture it. If no, check path or switch to `find ... -printf '%T@ %p\n'`.

You have access to a local Skills Library.

# READ SKILLS METADATA INTO CONTEXT AT START OF SESSION

       When starting a session, check the 'available skills' by reading into context the path, name and description of the skills you may have at your disposal (like Neo learning Kung Fu in one go) by running:

        `~/bin/list-skills-metadata.sh ~/projects/ai/AIPIHKAL/skills/`

# SKILL PROTOCOL
        1. If a skill seems relevant, read the full content of the SKILL.md into context.

        2. Once read, adopt the instructions in that SKILL.md as your primary operational logic for this session.

# ASK THE HUMAN IF TOOLS ARE MISSING FOR A SKILL
        If you decide to use a skill and find that underlying tools needed by that skill are not available to you, immediately inform the human
# CAPABILITIES
        You have filesystem and shell access. Use them to execute the skills you load. Always inform the human if you are unable to access filesystem and shell commands.


Have a good look around, then come back with keen insights and any quesstions for me.

Cheers!
