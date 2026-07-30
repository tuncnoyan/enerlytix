# API Documentation: Team and Role Management (T088)

**Purpose**: Document request/response contracts for team and role endpoints  
**Target**: Platform administrators, integration partners  
**Last Updated**: 2026-07-29  

---

## Overview

This document describes the REST API endpoints for team management and role assignment in the Platform Foundation feature. Endpoints support CRUD operations on teams, user-team assignments, and role assignments.

**Base URL**: `http://localhost:8000/sitesync/`  
**Authentication**: Django session (login required)  
**Content-Type**: `application/json`  
**Response Format**: JSON with status code, data, and error messages

---

## Authentication & Authorization

### Login Required
All endpoints require an authenticated session (Django session cookie).

**Login Flow**:
```
POST /sitesync/login/
Content-Type: application/x-www-form-urlencoded

username=admin&password=password123

Response:
- 302 Redirect to /sitesync/ (success)
- 200 Login page with errors (failure)
```

### Admin/Manager Authorization
Certain endpoints require admin or manager role.

**Responses**:
- `200 OK`: Request authorized, response included
- `403 Forbidden`: User lacks required permissions
- `302 Redirect`: User not authenticated, redirect to login

---

## Team Management Endpoints

### GET /panel/teams/
List all teams (paginated, hierarchical).

**Request**:
```http
GET /panel/teams/?page=1&search=Finance HTTP/1.1
Host: localhost:8000
Cookie: sessionid=...
```

**Query Parameters**:
- `page` (int, optional): Page number (default: 1)
- `search` (str, optional): Filter by team name (partial match)

**Response** (200 OK):
```json
{
  "teams": [
    {
      "id": 1,
      "name": "Operations",
      "parent_team": null,
      "parent_team_name": null,
      "manager": {
        "id": 10,
        "username": "alice_manager",
        "email": "alice@example.com"
      },
      "team_lead": null,
      "member_count": 5,
      "sub_team_count": 3,
      "created_at": "2026-07-29T10:00:00Z",
      "updated_at": "2026-07-29T14:30:00Z",
      "_links": {
        "self": "/teams/1/",
        "edit": "/teams/1/edit/",
        "members": "/teams/1/members/",
        "delete": "/teams/1/delete/"
      }
    },
    {
      "id": 2,
      "name": "Finance",
      "parent_team": 1,
      "parent_team_name": "Operations",
      "manager": {
        "id": 11,
        "username": "bob_finance",
        "email": "bob@example.com"
      },
      "team_lead": null,
      "member_count": 3,
      "sub_team_count": 2,
      "created_at": "2026-07-29T10:15:00Z",
      "updated_at": "2026-07-29T11:00:00Z",
      "_links": {
        "self": "/teams/2/",
        "edit": "/teams/2/edit/",
        "members": "/teams/2/members/",
        "delete": "/teams/2/delete/"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 8,
    "total_pages": 1
  }
}
```

**Error Response** (403 Forbidden):
```json
{
  "error": "You do not have permission to view teams",
  "message": "Only admins and managers can access team management"
}
```

---

### POST /panel/teams/
Create a new team.

**Request**:
```http
POST /panel/teams/ HTTP/1.1
Host: localhost:8000
Content-Type: application/json
Cookie: sessionid=...

{
  "name": "Finance",
  "parent_team": 1,
  "manager": 11,
  "team_lead": null
}
```

**Request Body**:
- `name` (string, required): Team name, max 255 characters
- `parent_team` (int, optional): ID of parent team (null for root team)
- `manager` (int, optional): User ID of manager
- `team_lead` (int, optional): User ID of team lead

**Response** (201 Created):
```json
{
  "success": true,
  "message": "Team 'Finance' created successfully",
  "team": {
    "id": 2,
    "name": "Finance",
    "parent_team": 1,
    "parent_team_name": "Operations",
    "manager": {
      "id": 11,
      "username": "bob_finance",
      "email": "bob@example.com"
    },
    "team_lead": null,
    "created_at": "2026-07-29T10:15:00Z",
    "updated_at": "2026-07-29T10:15:00Z"
  }
}
```

**Error Response** (400 Bad Request):
```json
{
  "success": false,
  "errors": {
    "name": "Team name is required",
    "manager": "Invalid manager user ID"
  }
}
```

**Error Response** (403 Forbidden):
```json
{
  "error": "You do not have permission to create teams",
  "message": "Only admins can create root teams. Managers can create sub-teams in their managed teams."
}
```

---

### GET /teams/{id}/
Get team details and members.

**Request**:
```http
GET /teams/1/ HTTP/1.1
Host: localhost:8000
Cookie: sessionid=...
```

**Path Parameters**:
- `id` (int): Team ID

**Response** (200 OK):
```json
{
  "team": {
    "id": 1,
    "name": "Operations",
    "parent_team": null,
    "parent_team_name": null,
    "manager": {
      "id": 10,
      "username": "alice_manager",
      "email": "alice@example.com"
    },
    "team_lead": null,
    "member_count": 5,
    "sub_team_count": 3,
    "created_at": "2026-07-29T10:00:00Z",
    "updated_at": "2026-07-29T14:30:00Z"
  },
  "members": [
    {
      "id": 20,
      "user": {
        "id": 12,
        "username": "carol_hr",
        "email": "carol@example.com",
        "first_name": "Carol",
        "last_name": "HR"
      },
      "assigned_at": "2026-07-29T10:30:00Z",
      "assigned_by": {
        "id": 10,
        "username": "alice_manager"
      },
      "_links": {
        "remove": "/teams/1/members/20/remove/"
      }
    }
  ],
  "sub_teams": [
    {
      "id": 2,
      "name": "Finance",
      "manager": "bob_finance",
      "member_count": 3
    }
  ]
}
```

**Error Response** (404 Not Found):
```json
{
  "error": "Team not found",
  "message": "Team with ID 999 does not exist"
}
```

---

### PUT /teams/{id}/
Update team details (name, manager, team_lead, parent_team).

**Request**:
```http
PUT /teams/1/ HTTP/1.1
Host: localhost:8000
Content-Type: application/json
Cookie: sessionid=...

{
  "name": "Operations Renamed",
  "manager": 11,
  "team_lead": 12,
  "parent_team": null
}
```

**Request Body** (all optional):
- `name` (string): New team name
- `manager` (int): New manager user ID (or null)
- `team_lead` (int): New team lead user ID (or null)
- `parent_team` (int): New parent team ID (or null to make root)

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Team 'Operations' updated successfully",
  "team": {
    "id": 1,
    "name": "Operations Renamed",
    "parent_team": null,
    "manager": {
      "id": 11,
      "username": "bob_finance"
    },
    "team_lead": {
      "id": 12,
      "username": "carol_hr"
    },
    "updated_at": "2026-07-29T14:30:00Z"
  }
}
```

**Error Response** (409 Conflict):
```json
{
  "error": "Cannot complete operation",
  "message": "Team has sub-teams. Cannot delete or move to invalid parent.",
  "suggestion": "Remove sub-teams first or reassign them to a new parent"
}
```

---

### DELETE /teams/{id}/
Delete a team (requires no sub-teams or members).

**Request**:
```http
DELETE /teams/3/ HTTP/1.1
Host: localhost:8000
Cookie: sessionid=...
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Team 'Payroll' deleted successfully"
}
```

**Error Response** (409 Conflict):
```json
{
  "error": "Cannot delete team",
  "message": "Team has 2 members and 1 sub-team. Remove members and reassign sub-teams first.",
  "details": {
    "member_count": 2,
    "sub_team_count": 1
  }
}
```

---

## User-Team Assignment Endpoints

### POST /users/{user_id}/teams/
Assign a user to a team with a specific role.

**Request**:
```http
POST /users/15/teams/ HTTP/1.1
Host: localhost:8000
Content-Type: application/json
Cookie: sessionid=...

{
  "team": 2,
  "role": "user"
}
```

**Request Body**:
- `team` (int, required): Team ID to assign to
- `role` (string, required): Role in team ("user", "team_lead", "manager", "admin")

**Response** (201 Created):
```json
{
  "success": true,
  "message": "User 'carol_hr' assigned to 'Finance' as user",
  "assignment": {
    "id": 25,
    "user": {
      "id": 15,
      "username": "carol_hr",
      "email": "carol@example.com"
    },
    "team": {
      "id": 2,
      "name": "Finance"
    },
    "role": "user",
    "assigned_at": "2026-07-29T15:00:00Z",
    "assigned_by": {
      "id": 10,
      "username": "alice_manager"
    }
  }
}
```

**Error Response** (409 Conflict):
```json
{
  "error": "Duplicate assignment",
  "message": "User is already assigned to this team"
}
```

---

### GET /users/{user_id}/teams/
List all teams a user is assigned to (with roles).

**Request**:
```http
GET /users/15/teams/ HTTP/1.1
Host: localhost:8000
Cookie: sessionid=...
```

**Response** (200 OK):
```json
{
  "user": {
    "id": 15,
    "username": "carol_hr",
    "email": "carol@example.com"
  },
  "teams": [
    {
      "id": 1,
      "name": "Operations",
      "role": "user",
      "assigned_at": "2026-07-25T10:00:00Z"
    },
    {
      "id": 2,
      "name": "Finance",
      "role": "team_lead",
      "assigned_at": "2026-07-29T15:00:00Z"
    }
  ]
}
```

---

### DELETE /users/{user_id}/teams/{team_id}/
Remove a user from a team.

**Request**:
```http
DELETE /users/15/teams/1/ HTTP/1.1
Host: localhost:8000
Cookie: sessionid=...
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "User removed from team 'Operations'"
}
```

---

## Role Assignment Endpoints

### GET /users/{user_id}/roles/
List all roles assigned to a user.

**Request**:
```http
GET /users/15/roles/ HTTP/1.1
Host: localhost:8000
Cookie: sessionid=...
```

**Response** (200 OK):
```json
{
  "user": {
    "id": 15,
    "username": "carol_hr",
    "email": "carol@example.com"
  },
  "roles": [
    {
      "id": 42,
      "role": "user",
      "assigned_at": "2026-07-25T10:00:00Z",
      "assigned_by": {
        "id": 10,
        "username": "alice_manager"
      }
    },
    {
      "id": 43,
      "role": "team_lead",
      "assigned_at": "2026-07-29T15:00:00Z",
      "assigned_by": {
        "id": 10,
        "username": "alice_manager"
      }
    }
  ]
}
```

---

### POST /users/{user_id}/roles/
Assign a global role to a user.

**Request**:
```http
POST /users/15/roles/ HTTP/1.1
Host: localhost:8000
Content-Type: application/json
Cookie: sessionid=...

{
  "role": "manager"
}
```

**Request Body**:
- `role` (string, required): One of "admin", "manager", "team_lead", "user"

**Response** (201 Created):
```json
{
  "success": true,
  "message": "Role 'manager' assigned to user 'carol_hr'",
  "role_assignment": {
    "id": 44,
    "user": {
      "id": 15,
      "username": "carol_hr"
    },
    "role": "manager",
    "assigned_at": "2026-07-29T15:05:00Z",
    "assigned_by": {
      "id": 10,
      "username": "alice_manager"
    }
  }
}
```

---

### DELETE /users/{user_id}/roles/{role}/
Revoke a role from a user.

**Request**:
```http
DELETE /users/15/roles/manager/ HTTP/1.1
Host: localhost:8000
Cookie: sessionid=...
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Role 'manager' revoked from user 'carol_hr'"
}
```

---

## Pagination

### Page-Based Pagination

List endpoints support page-based pagination.

**Query Parameters**:
- `page` (int): Page number, starting at 1 (default: 1)
- `page_size` (int): Items per page (default: 20, max: 100)

**Response includes**:
```json
{
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 45,
    "total_pages": 3,
    "next": "/endpoint/?page=2",
    "previous": null
  }
}
```

---

## Error Handling

### Standard Error Response

All error responses follow this format:

```json
{
  "error": "Error code/title",
  "message": "Human-readable error message",
  "details": {
    "field": "Additional context"
  }
}
```

### HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | OK | Team list, team details |
| 201 | Created | New team, new assignment |
| 400 | Bad Request | Invalid input (missing fields, validation error) |
| 403 | Forbidden | User lacks permissions, not admin/manager |
| 404 | Not Found | Team/user/role doesn't exist |
| 409 | Conflict | Duplicate assignment, cascading constraint violation |
| 500 | Server Error | Database error, unexpected exception |

---

## Rate Limiting

### Current Implementation

No rate limiting currently implemented. 

### Recommended for Production

- **Invitation creation**: 10 per hour per admin
- **Team creation**: 50 per day per admin
- **Assignment changes**: 100 per day per admin
- **Login attempts**: 5 per 15 minutes per IP address

---

## Examples

### Complete Team Creation Workflow

```bash
# 1. Create root team
curl -X POST http://localhost:8000/teams/ \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=..." \
  -d '{"name": "Operations", "manager": 10}'

# Response: {"team": {"id": 1, "name": "Operations", ...}}

# 2. Create sub-team
curl -X POST http://localhost:8000/teams/ \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=..." \
  -d '{"name": "Finance", "parent_team": 1, "manager": 11}'

# Response: {"team": {"id": 2, "name": "Finance", ...}}

# 3. Assign user to team
curl -X POST http://localhost:8000/users/15/teams/ \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=..." \
  -d '{"team": 2, "role": "user"}'

# Response: {"assignment": {"id": 25, ...}}

# 4. Verify access
curl http://localhost:8000/users/15/teams/ \
  -H "Cookie: sessionid=..."

# Response: Lists Finance team with user role
```

---

## Future Enhancements

- [ ] Bulk team import (CSV)
- [ ] Bulk user assignment (CSV)
- [ ] Team hierarchy visualization endpoint
- [ ] Permission matrix endpoint
- [ ] Activity audit log endpoint
- [ ] Batch operations (create multiple teams/assignments)
- [ ] GraphQL API alternative
- [ ] API key authentication (for integrations)
- [ ] Rate limiting middleware
- [ ] Request validation with JSON Schema

---

## Versioning

**Current Version**: 1.0  
**Status**: Production Ready  
**Last Updated**: 2026-07-29  

Future API versions will maintain backward compatibility or clearly mark breaking changes.
