Quick test steps for calling/recording features

1. Start the Flask app (activate venv):

```powershell
& .\.venv\Scripts\Activate.ps1
python agent.py
```

2. Open the app in browser and login. Ensure `localStorage.id_nguoi_dung` is set to your user id.

3. Open `Voice` page. Use the floating call UI (bottom-right): enter callee user id and press `Call`.

4. Accept incoming call on callee browser. Speak; when done press `Hangup`.

5. After hangup, the client will upload recording to `/api/calls/upload_recording` and update `calls.recording_url`.

6. Open the voice history panel -> press `Tải cuộc gọi` to view calls and play recordings.

Notes:
- Ensure migrations have been run so `calls` table exists.
- If DB not available, upload will still save file under `static/audio/` but won't link to DB.
