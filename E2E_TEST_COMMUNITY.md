# End-to-End Community System Test Guide

## Prerequisites
1. MySQL service running on `127.0.0.1:3306` (credentials in `save_mysql.py`)
2. Flask app running: `python agent.py`
3. Two browser tabs/windows open to `http://localhost:5000`
4. Set different `localStorage.id_nguoi_dung` values (e.g., `1` and `2`)

### Setting Up Test Users
In Browser 1 (User 1):
```javascript
localStorage.setItem('id_nguoi_dung', '1');
localStorage.setItem('ten_dang_nhap', 'User1');
```
In Browser 2 (User 2):
```javascript
localStorage.setItem('id_nguoi_dung', '2');
localStorage.setItem('ten_dang_nhap', 'User2');
```

---

## Test Scenarios

### 1. Community Posts & Reactions
**Objective:** Verify post creation, reaction buttons, and realtime reaction count updates.

**Steps:**
1. User 1 navigates to `/posts` (or `/community/posts`)
2. Fills "Hôm nay bạn muốn chia sẻ gì?" with: `"Hello community! First post."`
3. Clicks "Đăng bài" → verify post appears in feed
4. User 2 clicks "👍 Like" reaction → verify reaction count increments in real-time (should show "Reactions: 1")
5. User 1 clicks "❤️ Love" reaction → verify count increments to "Reactions: 2"

**Expected Results:**
- Post is visible to both users
- Reaction counts update without full page reload
- Click on "Comment" button reveals comment input
- Multiple reactions per user possible

**Backend Check:**
- POST `/api/community/post` creates entry in `posts` table
- POST `/api/community/post/{id}/reaction` records in `reactions` table
- Activity points awarded (1 point for reaction)

---

### 2. Comments & Comment Reactions
**Objective:** Test comment posting and interaction.

**Steps:**
1. User 2 clicks "Comment" on User 1's post
2. Types: `"Great post! Love it."` and clicks "Gửi"
3. Comment appears in the comment section
4. User 1 navigates back and clicks "Comment" again → verify comment is still visible

**Expected Results:**
- Comments persist and display author name + timestamp
- Comment count on post increments
- Each comment has author name and creation time

**Backend Check:**
- POST `/api/community/post/{id}/comment` creates `comments` entry
- GET `/api/community/post/{id}/comments` returns list

---

### 3. Sticker Reactions
**Objective:** Test inline sticker picker and sticker reactions.

**Steps:**
1. User 1 clicks "✨ Sticker" button on a post
2. Modal appears with sticker options (or "No stickers" if DB not seeded)
3. If stickers available: Click one → reaction count should increment
4. Verify sticker counts also increment reaction total

**Expected Results:**
- Modal pops up inline (not separate window)
- Stickers apply successfully
- Reaction count includes stickers

**Note:** If `/api/stickers` returns no stickers, DB seeding may be needed.

---

### 4. Private Messaging
**Objective:** Test direct messages between users.

**Steps:**
1. User 1 navigates to `/messages`
2. Fills recipient field with `2` (User 2's ID)
3. Types: `"Hi User2, let's chat privately!"` and sends
4. User 2 navigates to `/messages`
5. Should see User 1's message in inbox
6. User 2 replies: `"Hi User1!"`
7. Both users refresh and verify message history persists

**Expected Results:**
- Messages appear in both inboxes
- Sender/receiver labels are correct
- Timestamps displayed
- History persists across refreshes
- Activity points awarded for each message sent

**Backend Check:**
- Socket.IO event `send_message` (private) emits `private_message_{receiver_id}`
- REST POST `/api/send_message` records in `messages` table

---

### 5. Group Chat
**Objective:** Test group messaging and membership.

**Steps:**
1. Admin creates a group via `/api/community/group` (e.g., "Test Group")
2. User 1 joins group → clicks "Join Group" or navigates to `/groups/{group_id}`
3. User 2 joins same group
4. User 1 sends: `"Hello everyone in the group!"`
5. User 2 receives the message in group chat
6. Both users see activity points increment

**Expected Results:**
- Both users see same group messages
- Recipient count accurate
- Group-specific message routing works
- Leave group option removes user from recipient list

**Backend Check:**
- Socket.IO room `group_{group_id}` emits `group_message`
- POST `/api/community/group` creates group entry
- Activity points awarded for group message send

---

### 6. Reports & Admin Actions
**Objective:** Test reporting spam/inappropriate content and admin moderation.

**Steps:**
1. User 1 creates a post with suspicious content: `"Buy cheap meds now!!!"`
2. User 2 clicks "Report" on the post
3. Fills reason: `"Spam"`
4. Admin navigates to `/admin/moderation`
5. Sees the report in "Reports" section
6. Clicks "View" to preview the reported content
7. Clicks "Ban Owner" → bans User 1 at level 1 (30 minutes)
8. Verify ban record appears in "Ban history" section
9. Audit log shows the admin action

**Expected Results:**
- Report appears immediately in admin panel
- Ban record shows correct level and duration
- Audit log records: `admin_action → user → ban_level_1`
- User 1 is now restricted (cannot post/message for 30 min)

**Backend Check:**
- POST `/api/report` creates `reports` entry
- POST `/api/admin/ban` calls `apply_ban()` → escalates infraction
- POST `/api/admin/reports/{id}/resolve` marks report resolved
- `/api/admin/audit_log` returns recent admin actions

---

### 7. Ban Escalation
**Objective:** Test automatic ban level escalation on repeated infractions.

**Steps:**
1. User 1 (or new test user `3`) repeatedly sends identical messages (5+ times in 5 min)
2. System auto-triggers infraction: `"repeated_messages"` → ban level 1 (30 min)
3. User sends more repeated content → infraction count +1
4. Auto-escalate to level 2 (1 hour) when weight threshold met
5. Admin panel shows escalated ban record
6. Verify duration increases: Level 2 = 1 hour, Level 3 = 1 week, etc.

**Expected Results:**
- Infraction recorded each time
- Ban automatically escalates per level mapping (in `save_mysql.py`):
  - Level 1: 30 minutes
  - Level 2: 1 hour
  - Level 3: 1 week
  - Level 4: 1 month
  - Level 5: 1 year
  - Level 6: permanent
- Audit log reflects each escalation
- User cannot take actions during ban

**Backend Check:**
- Spam heuristics in `handle_socket_send_message` detect repeated messages
- `record_infraction()` increments weight
- `auto_escalate_bans()` checks threshold and applies next level
- Ban duration per `apply_ban()` logic

---

### 8. Activity Points & Streaks
**Objective:** Verify activity tracking and streak rewards.

**Steps:**
1. User 1 joins a community (1 point)
2. User 1 sends a private message (1 point)
3. User 1 sends a group message (1 point)
4. User 1 makes a reaction (1 point)
5. User 1 posts a comment (1 point, if tracked)
6. Check `/profile/{id}` or activity endpoint to see cumulative points
7. Verify streak counter increments daily

**Expected Results:**
- Activity points recorded in `activity_points` table
- Total points display on user profile or leaderboard
- Streak counter increments if user active on consecutive days
- Rewards may unlock at milestones (100 pts, 500 pts, etc.)

**Backend Check:**
- POST endpoints call `award_streak_points()` after actions
- GET `/api/user/{id}/activity_points` returns sum of points
- Streak logic in `save_mysql.py` handles daily reset check

---

### 9. Voice Call & Recording
**Objective:** Test WebRTC call flow and recording upload.

**Steps:**
1. User 1 navigates to `/voice`
2. Enters User 2's ID and clicks "Start Call"
3. User 2 gets incoming call notification/modal
4. User 2 clicks "Accept" → WebRTC negotiation begins
5. Audio/video flows (or notification in dev tools)
6. User 1 talks for 10-15 seconds
7. User 1 clicks "Hangup"
8. Browser uploads recording to server
9. Admin navigates to `/calls` or call history page
10. Sees the recorded call listed with download/playback option

**Expected Results:**
- Call appears in call history after completion
- Recording file saved in `static/audio/{call_id}.wav` or similar
- Playback possible via `<audio>` element
- Call metadata (start_time, end_time, duration, recording_url) persists in DB
- Activity points awarded for call attempt/completion

**Backend Check:**
- Socket.IO handlers `handle_webrtc_offer`, `handle_webrtc_answer`, `handle_webrtc_ice_candidate`
- POST `/api/calls/start` records call metadata
- POST `/api/calls/upload_recording` saves file and updates `calls.recording_url`
- GET `/api/calls` returns call history

---

### 10. Unban & Bulk Unban
**Objective:** Test admin unban functionality.

**Steps:**
1. User 3 is banned (from previous test)
2. Admin navigates to `/admin/moderation`
3. Enters User 3's ID and clicks "Unban" → user immediately unbanned
4. Alternatively, fills "Bulk Unban" field with: `"3,4,5"` and clicks "Unban Bulk"
5. All three users now unbanned
6. Verify ban records show `active=0` or removed status
7. Audit log records each unban action

**Expected Results:**
- Unban effective immediately
- User can post/message/call after unban
- Audit log shows unban action with admin_id + timestamp
- Bulk unban processes multiple users simultaneously

**Backend Check:**
- POST `/api/admin/unban` sets `bans.active=0` for user
- POST `/api/admin/bulk_ban` or loop unban for each user_id
- Audit log entry created

---

### 11. Admin Moderation Dashboard Polish
**Objective:** Verify admin UI enhancements.

**Steps:**
1. Admin opens `/admin/moderation`
2. Verify "Audit Log" section displays recent actions
3. Use search field to filter reports (e.g., search "Spam")
4. Click "Refresh audit log" button → new actions appear
5. Verify moderation modal still displays content and action buttons

**Expected Results:**
- Audit log shows action type, target type, target ID, timestamp, details
- Search filters reports in real-time (no page reload)
- UI remains responsive

---

## Quick Smoke Test (5 minutes)
If time is limited, run this checklist:
- [ ] Create & view a post (Posts)
- [ ] Add a reaction (Reactions)
- [ ] Send a private message (Messaging)
- [ ] Report content (Reports)
- [ ] Ban a user (Admin Actions)
- [ ] Unban a user (Unban)
- [ ] Check Audit Log updates

---

## Troubleshooting

**Issue:** Migrations failed due to MySQL not running
- **Solution:** Start MySQL service, then run `python migrations/run_migrations.py up`

**Issue:** Posts not appearing in feed
- **Solution:** 
  - Verify `posts` table exists: `SHOW TABLES;` in MySQL
  - Check browser console for JS errors
  - Ensure `id_nguoi_dung` is set correctly in localStorage

**Issue:** WebRTC not connecting
- **Solution:**
  - Check `/voice` template loads without errors
  - Verify Socket.IO server running (look for `socketio` handler logs in `agent.py`)
  - Check browser WebRTC console (F12 > Console)

**Issue:** Ban not escalating
- **Solution:**
  - Verify `infractions` and `bans` tables created
  - Check `record_infraction()` being called (debug logs in `agent.py`)
  - Confirm weight threshold in `auto_escalate_bans()` logic

**Issue:** Activity points not recording
- **Solution:**
  - Check `activity_points` table exists
  - Verify `award_streak_points()` called after actions
  - Check database for inserted records

---

## Test Data Seeding (Optional)
If you want pre-populated test data:

```sql
-- Insert test users
INSERT INTO nguoi_dung (id_nguoi_dung, ten_dang_nhap, email) VALUES 
(1, 'User1', 'user1@test.com'),
(2, 'User2', 'user2@test.com'),
(3, 'User3', 'user3@test.com');

-- Insert stickers
INSERT INTO stickers (name, url) VALUES 
('Smile', '/static/stickers/smile.png'),
('Love', '/static/stickers/love.png');

-- Insert test community
INSERT INTO communities (name, description) VALUES 
('Test Community', 'For testing community features');
```

---

## Performance & Load Testing
Once basic features work, consider:
- Load test with 10+ concurrent users posting/messaging
- Verify Socket.IO room management doesn't leak memory
- Check call recording upload doesn't block server
- Monitor DB connection pool usage during high activity

---

## Success Criteria
All tests pass when:
1. Posts & reactions update in real-time
2. Comments appear immediately
3. Private/group messages deliver to correct recipients
4. Reports appear in admin panel
5. Bans auto-escalate and restrict user actions
6. Unbans take effect immediately
7. Calls record and upload successfully
8. Audit log tracks all admin actions
9. Activity points accumulate correctly
10. No SQL errors in logs
