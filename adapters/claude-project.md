# Claude (claude.ai Projects)

Prefer the skill: zip the `skills/motion2code/` folder and upload it under **Settings > Capabilities > Skills**.
Claude then loads `SKILL.md` and the references on demand, and can run the scripts in its code environment when
ffmpeg and Playwright are available there.

Without skills, use a Project:

1. Paste `adapters/universal-system-prompt.md` (the part below the line) into the project instructions.
2. Add to project knowledge: every file in `skills/motion2code/references/` and the three files in
   `skills/motion2code/templates/`.
3. Upload frames of your video (a contact sheet and frames every 0.25 s) with your request, since chat tools
   cannot play video.

For Claude Code, install the plugin or copy the skill folder (see the repository README).
