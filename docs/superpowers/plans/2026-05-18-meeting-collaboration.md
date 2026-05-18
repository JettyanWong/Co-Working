# Meeting Collaboration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone group and meeting coordination module that lets users create groups, invite group members to meetings, collect availability windows, compute current overlap, and publish a final read-only meeting decision.

**Architecture:** Add a small, independent meeting domain alongside the existing project domain. Keep group membership, meeting invites, join requests, availability slots, and final published results in separate tables so each concern has one clear owner. Reuse the existing Flask auth, access control, and Socket.IO setup, but do not couple this feature to projects.

**Tech Stack:** Flask, Flask-SQLAlchemy, Flask-Login, Flask-SocketIO, vanilla HTML/CSS/JS, SQLite/MySQL via the current app config.

---

### Task 1: Add meeting domain models and relationships

**Files:**
- Modify: `backend/app/models/__init__.py`
- Create: `backend/app/models/group.py`
- Create: `backend/app/models/meeting.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_meeting_models.py` with a basic import and schema expectation test that references `Group`, `GroupMember`, `Meeting`, `MeetingInvite`, `MeetingRequest`, `AvailabilitySlot`, and `MeetingFinal`.

```python
def test_meeting_models_importable():
    from app.models import Group, GroupMember, Meeting, MeetingInvite, MeetingRequest, AvailabilitySlot, MeetingFinal
    assert Group is not None
    assert Meeting is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_meeting_models.py -v`
Expected: FAIL because the new models are not defined yet.

- [ ] **Step 3: Write minimal implementation**

Add the models and export them from `backend/app/models/__init__.py`.

```python
from datetime import datetime
from app import db


class Group(db.Model):
    __tablename__ = 'groups'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GroupMember(db.Model):
    __tablename__ = 'group_members'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.Enum('owner', 'admin', 'member'), default='member')
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)


class Meeting(db.Model):
    __tablename__ = 'meetings'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    planned_date = db.Column(db.Date, nullable=True)
    planned_time_range = db.Column(db.String(50), nullable=True)
    status = db.Column(db.Enum('draft', 'inviting', 'collecting', 'calculating', 'finalized'), default='draft')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_meeting_models.py -v`
Expected: PASS after the models are exported.

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/__init__.py backend/app/models/group.py backend/app/models/meeting.py backend/tests/test_meeting_models.py
git commit -m "feat: add meeting domain models"
```

### Task 2: Add invite, request, availability, and final snapshot models

**Files:**
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/models/group.py`
- Modify: `backend/app/models/meeting.py`
- Create: `backend/tests/test_meeting_tables.py`

- [ ] **Step 1: Write the failing test**

Assert that the new tables expose the fields needed for invitations, join requests, availability, and final published data.

```python
def test_meeting_support_tables_have_required_fields():
    from app.models import MeetingInvite, MeetingRequest, AvailabilitySlot, MeetingFinal
    assert hasattr(MeetingInvite, '__tablename__')
    assert hasattr(MeetingFinal, '__tablename__')
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_meeting_tables.py -v`
Expected: FAIL because the support tables do not exist yet.

- [ ] **Step 3: Write minimal implementation**

Add these models with direct foreign keys to `meetings` and `users`.

```python
class MeetingInvite(db.Model):
    __tablename__ = 'meeting_invites'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meetings.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    invite_status = db.Column(db.Enum('pending', 'accepted', 'declined'), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MeetingRequest(db.Model):
    __tablename__ = 'meeting_requests'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meetings.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    request_status = db.Column(db.Enum('pending', 'approved', 'rejected'), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AvailabilitySlot(db.Model):
    __tablename__ = 'availability_slots'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meetings.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    available_date = db.Column(db.Date, nullable=False)
    time_range = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MeetingFinal(db.Model):
    __tablename__ = 'meeting_finals'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meetings.id'), nullable=False)
    final_creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    final_location = db.Column(db.String(200), nullable=False)
    final_date = db.Column(db.Date, nullable=False)
    final_time_range = db.Column(db.String(50), nullable=False)
    final_attendees_snapshot = db.Column(db.Text, nullable=False)
    published_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_meeting_tables.py -v`
Expected: PASS after the tables are defined and exported.

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/__init__.py backend/app/models/group.py backend/app/models/meeting.py backend/tests/test_meeting_tables.py
git commit -m "feat: add meeting support tables"
```

### Task 3: Add group and meeting API routes

**Files:**
- Create: `backend/app/routes/groups.py`
- Create: `backend/app/routes/meetings.py`
- Modify: `backend/app/__init__.py`
- Create: `backend/tests/test_meeting_routes.py`

- [ ] **Step 1: Write the failing test**

Create route tests for:
- creating a group
- inviting a user to a group
- creating a meeting inside a group
- only allowing group members to invite or create meetings

```python
def test_group_creation_requires_login(client):
    res = client.post('/api/groups', json={'name': 'Alpha'})
    assert res.status_code == 401
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_meeting_routes.py -v`
Expected: FAIL because the endpoints do not exist yet.

- [ ] **Step 3: Write minimal implementation**

Add `/api/groups` and `/api/meetings` routes and register both blueprints in `backend/app/__init__.py`.

```python
@bp.route('/groups', methods=['POST'])
@login_required
def create_group():
    data = request.get_json() or {}
    name = data.get('name')
    if not name:
        return jsonify({'error': 'Group name is required'}), 400
    group = Group(name=name, description=data.get('description'), owner_id=current_user.id)
    db.session.add(group)
    db.session.flush()
    db.session.add(GroupMember(group_id=group.id, user_id=current_user.id, role='owner'))
    db.session.commit()
    return jsonify({'group': group.to_dict()}), 201
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_meeting_routes.py -v`
Expected: PASS after the blueprints and permission checks are wired up.

- [ ] **Step 5: Commit**

```bash
git add backend/app/__init__.py backend/app/routes/groups.py backend/app/routes/meetings.py backend/tests/test_meeting_routes.py
git commit -m "feat: add meeting group and meeting routes"
```

### Task 4: Implement availability intersection and meeting final publish flow

**Files:**
- Modify: `backend/app/routes/meetings.py`
- Create: `backend/app/services/meeting_availability.py`
- Create: `backend/tests/test_meeting_availability.py`

- [ ] **Step 1: Write the failing test**

Test that the intersection function only uses submitted users and returns the overlap for the current set of slots.

```python
def test_intersection_uses_only_submitted_slots():
    slots = [
        {'user_id': 1, 'available_date': '2026-05-20', 'time_range': '14:00-16:00'},
        {'user_id': 2, 'available_date': '2026-05-20', 'time_range': '15:00-17:00'},
    ]
    result = compute_current_overlap(slots)
    assert result == [{'available_date': '2026-05-20', 'time_range': '15:00-16:00'}]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_meeting_availability.py -v`
Expected: FAIL because the helper does not exist yet.

- [ ] **Step 3: Write minimal implementation**

Implement `compute_current_overlap()` in `backend/app/services/meeting_availability.py` and use it from meeting routes.

```python
from datetime import datetime


def _parse_time_range(time_range):
    start_str, end_str = time_range.split('-')
    return (
        datetime.strptime(start_str, '%H:%M').time(),
        datetime.strptime(end_str, '%H:%M').time(),
    )


def compute_current_overlap(slots):
    grouped = {}
    for slot in slots:
        grouped.setdefault(slot['available_date'], []).append(_parse_time_range(slot['time_range']))

    overlaps = []
    for available_date, ranges in grouped.items():
        latest_start = max(start for start, _ in ranges)
        earliest_end = min(end for _, end in ranges)
        if latest_start < earliest_end:
            overlaps.append({
                'available_date': available_date,
                'time_range': f"{latest_start.strftime('%H:%M')}-{earliest_end.strftime('%H:%M')}",
            })
    return overlaps
```

Add publish/update endpoints that persist a `MeetingFinal` snapshot and allow the creator to overwrite it before or after publish.

```python
@bp.route('/meetings/<int:meeting_id>/final', methods=['PUT'])
@login_required
def upsert_final_meeting(meeting_id):
    meeting = Meeting.query.get_or_404(meeting_id)
    if meeting.creator_id != current_user.id:
        return jsonify({'error': 'Only meeting creator can edit final details'}), 403

    data = request.get_json() or {}
    final = MeetingFinal.query.filter_by(meeting_id=meeting_id).first()
    if not final:
        final = MeetingFinal(meeting_id=meeting_id, final_creator_id=current_user.id)
        db.session.add(final)

    final.final_location = data.get('final_location', meeting.location)
    final.final_date = data.get('final_date', meeting.planned_date)
    final.final_time_range = data.get('final_time_range', meeting.planned_time_range)
    final.final_attendees_snapshot = json.dumps(data.get('final_attendees_snapshot', []))
    meeting.status = 'finalized'
    db.session.commit()
    return jsonify({'final': final.to_dict()})
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_meeting_availability.py -v`
Expected: PASS after the overlap helper and publish flow are wired up.

- [ ] **Step 5: Commit**

```bash
git add backend/app/routes/meetings.py backend/app/services/meeting_availability.py backend/tests/test_meeting_availability.py
git commit -m "feat: add meeting availability overlap"
```

### Task 5: Add meeting UI entry and pages

**Files:**
- Modify: `frontend/static/index.html`
- Modify: `frontend/static/js/app.js`
- Create: `frontend/static/meetings.html`
- Create: `frontend/static/js/meetings.js`

- [ ] **Step 1: Write the failing test**

Use a browser/manual check plan if there is no automated UI harness yet:
- opening `index.html` should show a `会议` nav entry
- opening `meetings.html` should show the meeting dashboard sections

- [ ] **Step 2: Run test to verify it fails**

Open the app in the browser and verify the navigation item is missing.

- [ ] **Step 3: Write minimal implementation**

Add a `会议` nav item to `frontend/static/index.html`, wire it to a new meeting page, and implement the dashboard sections for groups, meeting creation, availability, and final results.

```html
<a href="/static/meetings.html" class="nav-item" id="navMeetings">会议</a>
```

- [ ] **Step 4: Run test to verify it passes**

Open the browser and confirm the new entry and the new page render without console errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/static/index.html frontend/static/js/app.js frontend/static/meetings.html frontend/static/js/meetings.js
git commit -m "feat: add meeting ui entry"
```

### Task 6: Add read-only final meeting display and polish

**Files:**
- Modify: `frontend/static/meetings.html`
- Modify: `frontend/static/js/meetings.js`
- Modify: `backend/app/routes/meetings.py`
- Create: `backend/tests/test_meeting_final_readonly.py`

- [ ] **Step 1: Write the failing test**

Assert that once a meeting is finalized, non-creators cannot edit the final snapshot.

```python
def test_final_snapshot_is_creator_only_editable(client, auth_user):
    res = client.put('/api/meetings/1/final', json={'final_location': 'Room 1'})
    assert res.status_code in (401, 403)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_meeting_final_readonly.py -v`
Expected: FAIL until the permission guard exists.

- [ ] **Step 3: Write minimal implementation**

Add creator-only guards on final snapshot edits and make the UI show read-only state for everyone else.

```python
if final and final.final_creator_id != current_user.id:
    return jsonify({'error': 'Final meeting details are read-only'}), 403
```

```javascript
const canEditFinal = meeting.final_creator_id === currentUser.id;
document.getElementById('finalSaveBtn').disabled = !canEditFinal;
document.getElementById('finalFields').classList.toggle('is-readonly', !canEditFinal);
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_meeting_final_readonly.py -v`
Expected: PASS after the permission checks and UI state are in place.

- [ ] **Step 5: Commit**

```bash
git add backend/app/routes/meetings.py frontend/static/meetings.html frontend/static/js/meetings.js backend/tests/test_meeting_final_readonly.py
git commit -m "feat: lock final meeting snapshot"
```

## Verification Checklist

- All new models are exported from `backend/app/models/__init__.py`.
- The meeting blueprints are registered in `backend/app/__init__.py`.
- The availability overlap helper only uses submitted slots.
- The final meeting snapshot is stored separately from live invite/request/availability rows.
- The navigation entry for `会议` is visible in the main app.
- Non-creators cannot edit final published meeting data.

## Notes for the implementer

- Keep the meeting module standalone; do not attach it to project tables.
- Prefer small files with one responsibility each.
- If a route needs to know whether a user belongs to a group or meeting, check the new group membership tables first.
- If the overlap algorithm becomes more complex, keep it in `backend/app/services/meeting_availability.py` instead of embedding it in the route handlers.
