# ChatGPT Custom GPT

1. Create a GPT and paste `adapters/universal-system-prompt.md` (the part below the line) into **Instructions**.
2. Under **Knowledge**, upload every file in `skills/motion2code/references/` and the templates in
   `skills/motion2code/templates/` (rename `.html` to `.txt` if the uploader rejects them).
3. With **Code Interpreter** enabled, also upload `skills/motion2code/scripts/` as a zip. `palette.py` runs on
   uploaded frames with Python alone; the other scripts need ffmpeg and a browser, which the sandbox may lack.
4. Send frames of the video with each request (a contact sheet and frames every 0.25 s).
