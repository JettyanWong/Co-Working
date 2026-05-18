# Social Collaboration And Visibility Operations Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a friend-based social layer, alias-aware people selection, team recruitment workflows, and team-scoped visibility rules without breaking the current Coworking project, task, document, and meeting flows.

**Architecture:** Build the new capability as an additive collaboration layer on top of the existing Flask app. Keep global friend visibility, team-local visibility, published invitation visibility, and picker logic separate so each rule can evolve independently. Reuse the current auth/session model, existing `group` and `meeting` work where safe, and introduce compatibility adapters instead of replacing live behavior in one pass.

**Tech Stack:** Flask, Flask-SQLAlchemy, Flask-Login, vanilla HTML/CSS/JS, existing industrial UI system, SQLite/MySQL through current app config.

---

## 1. Subagent Team Blueprint

Use **7 subagents**. This is the smallest team that still keeps responsibilities clean and avoids collisions.

### Subagent 1: `visibility-architect`

**Scope**
- Owns compatibility boundaries.
- Decides how new social models attach to existing `users`, `groups`, `meetings`, and task assignment logic.
- Guards against regressions in existing routes.

**Primary outputs**
- API contracts.
- compatibility matrix.
- migration notes.

**Files**
- Modify: `docs/superpowers/specs/2026-05-18-social-collaboration-visibility-design.md`
- Create: `docs/superpowers/plans/2026-05-18-social-collaboration-visibility-operations.md`
- Create if needed: `docs/superpowers/specs/2026-05-18-people-picker-contract.md`

**Must not own**
- direct UI implementation,
- database model coding,
- route coding.

### Subagent 2: `social-backend`

**Scope**
- Owns friend code, friend requests, friendships, and aliases.
- Owns contact discovery and relationship-state APIs.

**Primary outputs**
- social models,
- social routes,
- tests for friend flows.

**Files**
- Modify: `backend/app/models/user.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/routes/__init__.py`
- Modify: `backend/app/__init__.py` only if model import or migration wiring is required
- Create: `backend/app/models/social.py`
- Create: `backend/app/routes/social.py`
- Create: `backend/tests/test_social_routes.py`
- Create: `backend/tests/test_social_models.py`

**Must not own**
- team routes,
- meeting routes,
- frontend pages.

### Subagent 3: `team-backend`

**Scope**
- Owns team creation, membership, roles, public invitation publishing, join requests, and approval rules.
- Responsible for evolving current `group` capability into product-facing `team` behavior.

**Primary outputs**
- team APIs,
- published invitation APIs,
- role enforcement.

**Files**
- Modify: `backend/app/models/group.py`
- Modify: `backend/app/routes/groups.py`
- Create: `backend/app/models/team_invitation.py` or extend `group.py` if file count must stay lower
- Create: `backend/app/routes/team_invitations.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/routes/__init__.py`
- Create: `backend/tests/test_team_routes.py`

**Must not own**
- friend APIs,
- frontend picker rendering,
- task route changes.

### Subagent 4: `collaboration-backend`

**Scope**
- Owns meeting visibility tightening and task/team visibility integration.
- Ensures only invited or approved meeting participants can submit availability.
- Adds visibility-aware assignment helpers for tasks.

**Primary outputs**
- meeting permission fixes,
- task visibility helpers,
- shared selector backend logic.

**Files**
- Modify: `backend/app/routes/meetings.py`
- Modify: `backend/app/routes/tasks.py`
- Create: `backend/app/services/visibility.py`
- Modify: `backend/app/services/meeting_availability.py` if needed
- Create: `backend/tests/test_visibility_service.py`
- Create: `backend/tests/test_meeting_permissions.py`
- Create: `backend/tests/test_task_visibility.py`

**Must not own**
- contact UI,
- team management UI.

### Subagent 5: `contacts-frontend`

**Scope**
- Owns contact page, friend search, incoming/outgoing requests, alias editing, and reusable people-picker UI contract.

**Primary outputs**
- contacts page,
- alias-aware list components,
- shared picker helper.

**Files**
- Create: `frontend/static/contacts.html`
- Create: `frontend/static/js/contacts.js`
- Create: `frontend/static/js/people-picker.js`
- Modify: `frontend/static/css/industrial-ui.css`
- Modify: `frontend/static/index.html`
- Create if needed: `frontend/static/css/contacts.css`

**Must not own**
- team management page,
- backend code.

### Subagent 6: `teams-frontend`

**Scope**
- Owns team creation, team member management, published invitation management, join approval UI, and meeting page adaptation to new visibility rules.

**Primary outputs**
- teams page,
- published invitation UI,
- team-aware meeting selection flow.

**Files**
- Create: `frontend/static/teams.html`
- Create: `frontend/static/js/teams.js`
- Modify: `frontend/static/meetings.html`
- Modify: `frontend/static/js/meetings.js`
- Modify: `frontend/static/index.html`

**Must not own**
- contact page logic,
- backend visibility service.

### Subagent 7: `verification-and-rollout`

**Scope**
- Owns regression checks, smoke-test scripts, rollout notes, and non-destructive migration instructions.
- Confirms new work does not break current project flows.

**Primary outputs**
- verification checklist,
- smoke scripts,
- rollout notes.

**Files**
- Create: `backend/tests/test_regression_existing_routes.py`
- Create: `docs/superpowers/plans/2026-05-18-social-collaboration-rollout-checklist.md`
- Create if needed: `backend/scripts/smoke_social_collaboration.py`

**Must not own**
- feature behavior design,
- large code changes in feature files.

## 2. Execution Rules For The Subagent Team

- Each subagent gets a disjoint write set wherever possible.
- No subagent may edit the same file at the same time as another subagent.
- Every subagent must report:
  - status,
  - files changed,
  - tests run,
  - concerns.
- After a subagent finishes and its work is reviewed, kill it immediately.
- If a subagent needs a shared file already owned by another subagent, stop and reassign ownership rather than editing in parallel.

## 3. File Structure To Implement

This structure is designed to be additive and low-risk.

### Backend files to create

- `backend/app/models/social.py`
  Responsibility: friend code, friend request, friendship, alias data models.

- `backend/app/routes/social.py`
  Responsibility: search by friend code/username, send request, accept/reject request, list friends, update alias.

- `backend/app/models/team_invitation.py`
  Responsibility: published team invitations, selected-team scope rows, team join requests.

- `backend/app/routes/team_invitations.py`
  Responsibility: publish invitation, list visible invitations, apply to team, approve/reject join requests.

- `backend/app/services/visibility.py`
  Responsibility: central visibility and people-picker policy helpers.

- `backend/tests/test_social_models.py`
- `backend/tests/test_social_routes.py`
- `backend/tests/test_team_routes.py`
- `backend/tests/test_visibility_service.py`
- `backend/tests/test_meeting_permissions.py`
- `backend/tests/test_task_visibility.py`
- `backend/tests/test_regression_existing_routes.py`

### Backend files to modify

- `backend/app/models/user.py`
  Add immutable `friend_code`.

- `backend/app/models/__init__.py`
  Export new models only.

- `backend/app/routes/__init__.py`
  Export new blueprints only.

- `backend/app/__init__.py`
  Register additive blueprints and additive schema migration blocks only.

- `backend/app/models/group.py`
  Extend current group model into team role semantics without deleting existing behavior.

- `backend/app/routes/groups.py`
  Add missing creation/invitation/admin permissions while preserving existing working endpoints.

- `backend/app/routes/meetings.py`
  Tighten participant eligibility using the shared visibility policy.

- `backend/app/routes/tasks.py`
  Introduce visibility-aware assignee validation without breaking current project-member assignment behavior.

### Frontend files to create

- `frontend/static/contacts.html`
  Contacts page.

- `frontend/static/js/contacts.js`
  Friend search, request flows, alias editing.

- `frontend/static/js/people-picker.js`
  Shared alias-aware picker used by tasks, teams, and meetings.

- `frontend/static/teams.html`
  Team management and public invitation page.

- `frontend/static/js/teams.js`
  Team creation, member management, public invitation publishing, request approvals.

### Frontend files to modify

- `frontend/static/index.html`
  Add navigation entries for `联系人` and `Teams`.

- `frontend/static/js/app.js`
  Add open-page helpers only if needed.

- `frontend/static/meetings.html`
  Replace raw “group” wording with product-facing “team” wording where safe, and add participant gating messaging.

- `frontend/static/js/meetings.js`
  Consume team-scoped visibility and alias-aware attendee display.

- `frontend/static/css/industrial-ui.css`
  Shared styling for contact badges, friend code, alias chips, picker rows, invitation scope badges.

## 4. File-By-File Implementation Contract

Each file below includes the required inputs, outputs, behavior, and recommended tools.

### `backend/app/models/social.py`

**Input**
- SQLAlchemy `db`
- existing `User` table

**Output**
- `FriendRequest`
- `Friendship`
- `FriendAlias`

**Behavior**
- enforce unique pending request per user pair,
- enforce symmetric friendship pair normalization,
- enforce alias ownership on friend pairs only.

**Tools**
- Flask-SQLAlchemy
- existing model export pattern

### `backend/app/routes/social.py`

**Input**
- session-authenticated `current_user`
- JSON payloads for search, request, accept, reject, alias update

**Output**
- JSON APIs:
  - `GET /api/social/search`
  - `GET /api/social/friends`
  - `GET /api/social/requests`
  - `POST /api/social/requests`
  - `POST /api/social/requests/<id>/accept`
  - `POST /api/social/requests/<id>/reject`
  - `PUT /api/social/friends/<target_user_id>/alias`

**Behavior**
- search by `friend_code` or username,
- return minimal identity plus relationship state,
- never expose full user profile payloads in search results,
- alias update affects only viewer-owned display.

**Tools**
- Flask Blueprint
- Flask-Login
- shared visibility serializer helpers

### `backend/app/models/team_invitation.py`

**Input**
- `Team`/`Group` identity
- publisher user id

**Output**
- `TeamInvitation`
- `TeamInvitationScope`
- `TeamJoinRequest`

**Behavior**
- support visibility scope values `public`, `friends`, `selected_teams`,
- allow multiple `selected_teams` rows,
- preserve audit history for approvals.

**Tools**
- Flask-SQLAlchemy

### `backend/app/routes/team_invitations.py`

**Input**
- authenticated user
- team invitation payloads

**Output**
- JSON APIs:
  - `POST /api/team-invitations`
  - `GET /api/team-invitations`
  - `GET /api/team-invitations/<id>`
  - `POST /api/team-invitations/<id>/apply`
  - `POST /api/team-invitations/<id>/requests/<request_id>/approve`
  - `POST /api/team-invitations/<id>/requests/<request_id>/reject`

**Behavior**
- only `owner` or `admin` can publish invitations,
- visibility filter must respect `public`, `friends`, and `selected_teams`,
- only `owner` or `admin` can approve/reject join requests.

**Tools**
- Flask Blueprint
- visibility service helpers

### `backend/app/services/visibility.py`

**Input**
- current user id,
- target user id,
- optional team id,
- optional invitation scope,
- friend/team relationship queries.

**Output**
- pure helper functions:
  - `are_friends(user_a_id, user_b_id)`
  - `share_team(user_a_id, user_b_id, team_id=None)`
  - `relationship_state(viewer_id, target_user_id)`
  - `visible_people_for_team(viewer_id, team_id)`
  - `visible_team_invitations(viewer_id)`
  - `can_submit_meeting_availability(user_id, meeting_id)`
  - `can_assign_task(viewer_id, assignee_id, context)`

**Behavior**
- centralize all visibility rules,
- prevent route-level duplication,
- make team-local visibility independent from friendship.

**Tools**
- plain Python service helpers
- SQLAlchemy queries only

### `backend/app/models/user.py`

**Input**
- current user model

**Output**
- immutable `friend_code` field
- helper serializer includes `friend_code` in appropriate response shapes only

**Behavior**
- auto-generate on create,
- unique and indexed,
- never editable via ordinary user update.

**Tools**
- SQLAlchemy column + helper

### `backend/app/models/group.py`

**Input**
- existing group/team implementation

**Output**
- product-safe team semantics

**Behavior**
- maintain backward-compatible current fields,
- enforce `owner/admin/member`,
- support invitation-based membership and published-application-based membership,
- preserve existing meeting foreign keys.

**Tools**
- SQLAlchemy relationships

### `backend/app/routes/groups.py`

**Input**
- authenticated user
- team create/update/member payloads

**Output**
- keep existing working endpoints,
- extend them to support proper UI creation and membership flows

**Behavior**
- `POST /api/groups` must remain supported,
- only `owner/admin` can add members or process elevated membership actions,
- list endpoints should only show teams the current user can actually see.

**Tools**
- Flask Blueprint
- visibility service

### `backend/app/routes/meetings.py`

**Input**
- existing team meeting flows

**Output**
- stricter participant gating

**Behavior**
- invited or approved users can submit availability,
- merely sharing a team is not enough if meeting invite restrictions exist,
- alias-friendly serialized attendee shapes if viewer context is available.

**Tools**
- existing meeting routes
- visibility service

### `backend/app/routes/tasks.py`

**Input**
- current task creation/update payloads

**Output**
- additive visibility-aware assignee checks

**Behavior**
- preserve project-member assignment for project tasks,
- add optional team-scoped assignment path where applicable,
- never fall back to unrestricted global user selection.

**Tools**
- existing task route structure
- visibility service

### `frontend/static/js/people-picker.js`

**Input**
- API search results
- relationship state
- alias data

**Output**
- reusable picker renderer and selection helper

**Behavior**
- show alias as primary label when available,
- show username and friend code in hover/detail,
- support team-scoped and friend-scoped data sources,
- never load directly from unrestricted `/api/users`.

**Tools**
- vanilla JS module pattern
- existing industrial UI classes

### `frontend/static/contacts.html`

**Input**
- current logged-in user

**Output**
- contact management page

**Behavior**
- search by username or friend code,
- display incoming/outgoing friend requests,
- show friend list,
- allow editing alias,
- keep desktop/mobile readable.

**Tools**
- existing card/table/form patterns
- `industrial-ui.css`

### `frontend/static/js/contacts.js`

**Input**
- social API responses

**Output**
- page state management and event handlers

**Behavior**
- debounce search,
- submit friend requests,
- accept/reject requests,
- edit alias,
- re-render lists after each mutation.

**Tools**
- fetch
- shared status helpers

### `frontend/static/teams.html`

**Input**
- current user, visible teams, visible published invitations

**Output**
- team management page

**Behavior**
- create team,
- manage members,
- publish invitation with scope selection,
- allow selecting multiple target teams,
- review join requests.

**Tools**
- existing industrial layout

### `frontend/static/js/teams.js`

**Input**
- groups/team APIs
- team invitation APIs
- people-picker module

**Output**
- team creation and recruitment logic

**Behavior**
- create team with owner auto-membership,
- invite direct friends to private team,
- publish public/friends/selected-teams invitation,
- approve/reject join requests,
- display team-local visibility state clearly.

**Tools**
- fetch
- `people-picker.js`

### `frontend/static/js/meetings.js`

**Input**
- team-scoped meeting APIs
- people-picker module

**Output**
- alias-aware meeting UI

**Behavior**
- attendee display uses alias when available,
- only invited/approved users can submit availability,
- request-join UI only appears for eligible team members,
- preserve current meeting page behavior where unaffected.

**Tools**
- fetch
- existing polling pattern

## 5. Implementation Sequence

This order minimizes conflicts with current code.

### Phase A: Social foundation

- [ ] Add `friend_code` to users with additive migration logic.
- [ ] Add `social.py` models.
- [ ] Add social routes.
- [ ] Add tests for friend requests, accept/reject, alias editing.
- [ ] Verify current login and admin flows still work.

### Phase B: Shared visibility policy

- [ ] Create `backend/app/services/visibility.py`.
- [ ] Move relationship and candidate checks into this service.
- [ ] Add unit tests for friend visibility, shared-team visibility, and published-invitation visibility.

### Phase C: Team recruitment and permissions

- [ ] Extend current group routes into product-facing team behavior.
- [ ] Add published invitation data model and routes.
- [ ] Add approval flows for `owner/admin`.
- [ ] Add backend regression tests for current group and meeting endpoints.

### Phase D: Contacts and picker UI

- [ ] Add `contacts.html` and `contacts.js`.
- [ ] Add `people-picker.js`.
- [ ] Wire alias-first rendering and hover details.
- [ ] Confirm no page still loads candidates directly from unrestricted user APIs.

### Phase E: Team UI

- [ ] Add `teams.html` and `teams.js`.
- [ ] Add navigation entries.
- [ ] Add team create/manage/publish/apply/approve screens.

### Phase F: Meeting and task integration

- [ ] Tighten meeting participant gating.
- [ ] Update meeting UI for alias-aware display.
- [ ] Add team/friend-scoped assignee selection rules to tasks.
- [ ] Verify task detail flow still works.

### Phase G: Rollout and regression

- [ ] Run smoke checks for:
  - login,
  - project list,
  - project task CRUD,
  - document editor,
  - file view,
  - contact request,
  - team creation,
  - meeting availability submit.
- [ ] Record rollout notes.

## 6. Commands And Tools Per Stage

Use these as the default toolbox.

### Exploration

- `rg`
- `sed -n`
- `git diff --stat`
- `git status --short`

### Backend verification

- `python -B -m pytest ...` when pytest is available
- small smoke scripts using project venv when pytest is unavailable
- `python -c "import ast, pathlib; ..."` for syntax parse

### Frontend verification

- `node --check frontend/static/js/<file>.js`
- in-app browser for page smoke checks

### Git discipline

- frequent small commits,
- no destructive resets,
- never stage `.DS_Store`, `instance/`, or local DB noise.

## 7. Compatibility Guardrails

These rules are mandatory.

- Do not delete or rename existing routes that current pages still call.
- Keep `group` backend endpoints working while product wording gradually shifts to `team`.
- Do not change current login, user approval, or password-reset behavior.
- Do not replace current task assignment rules with team rules everywhere in one pass.
- Do not let any picker or invitation flow query the full user table directly for rich selection.
- Do not require friendship for users who already share a team.
- Do not let shared team membership automatically create friendship.
- Do not allow `member` role to approve team join requests.

## 8. Definition Of Done

The work is done only when all of the following are true:

- a user can find another user by friend code or username,
- a user can send and receive friend requests,
- accepted friends appear in contacts,
- a user can save a private alias for a friend,
- alias-first rendering works in every implemented picker,
- a user can create a team from the UI,
- `owner` and `admin` can approve join requests,
- team invitations support `public`, `friends`, and `selected_teams` scopes,
- selected-team scope supports multi-select,
- non-friend teammates can still see each other inside the team context,
- meeting participation is constrained by invite/approval logic,
- no existing project/task/document/file flows are broken.

## 9. Recommended Commit Boundaries

- `feat: add social relationship models and routes`
- `feat: add visibility policy service`
- `feat: add team invitation and join approval flows`
- `feat: add contacts page and alias-aware picker`
- `feat: add teams management page`
- `feat: tighten meeting and task visibility rules`
- `test: add collaboration visibility regression coverage`

## 10. Immediate Next Step

Create the subagent team using the exact 7-role split above, then execute **Phase A** first. Do not start meetings or task refactors before the social foundation and visibility service are in place.
