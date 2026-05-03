You have access to a local Skills Library.

# READ SKILLS METADATA INTO CONTEXT AT START OF SESSION

    BEST PRACTICE: use the `list-skills-metadata.sh` script as shown below.  Fallback: use built-in tool for skills if you have one, or fall all the way back to catting ONLY the first 5 lines of all the SKILL.md files


       When starting a session, check the 'available skills' by reading into context the path, name and description of the skills you may have at your disposal (like Neo learning Kung Fu in one go) by running:

        `list-skills-metadata.sh ~/projects/ai/AIPIHKAL/skills/`

# SKILL PROTOCOL
        1. If a skill seems relevant, read the full content of the SKILL.md into context.

        2. Once read, adopt the instructions in that SKILL.md as your primary operational logic for this session.

# ASK THE HUMAN IF TOOLS ARE MISSING FOR A SKILL
        If you decide to use a skill and find that underlying tools needed by that skill are not available to you, immediately inform the human
# CAPABILITIES
        You have filesystem and shell access. Use them to execute the skills you load. Always inform the human if you are unable to access filesystem and shell commands.
