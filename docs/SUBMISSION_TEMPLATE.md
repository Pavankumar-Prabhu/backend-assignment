# Submission Template

## GitHub Link

`<replace-with-your-github-repository-url>`

## Live Demo or API Documentation URL

Choose one of these after you push or deploy:

- Deployed docs URL: `<replace-with-your-live-docs-or-demo-url>`
- GitHub docs URL: `<replace-with-your-github-url-to-docs/API.md>`

## Primary Framework or Library Used

Python 3.12 standard library WSGI stack with SQLite.

## Features Implemented

- Role-based access control for viewer, analyst, and admin
- Token login/logout
- User management APIs
- Financial record CRUD APIs with filtering and pagination
- Dashboard summary APIs for totals, category breakdown, trends, and recent activity
- Input validation and structured error responses
- SQLite persistence with seeded demo data
- Integration tests
- API docs page and OpenAPI-style JSON

## Technical Decisions and Trade-offs

- Chose Python standard library plus SQLite to minimize setup friction and keep the business logic visible for review.
- Implemented bearer-token auth to demonstrate backend access control more realistically than a custom header.
- Stored monetary values as integer cents to avoid floating-point precision issues.
- Used soft deletes for users and records to preserve audit safety.
- Avoided third-party frameworks, which keeps the project lightweight but means fewer built-in conveniences like automatic docs generation and ORM migrations.

