# Job Application Tracker

A full-stack web application that helps users track job applications. This project uses **MySQL** for the database, **Python with Flask** for the backend, and **HTML/CSS** for the frontend.

## Features

- Dashboard with summary counts
- Full CRUD for:
  - Companies
  - Jobs
  - Applications
  - Contacts
- Job Match feature using JSON job requirements and skill comparison
- MySQL relational database with foreign keys
- HTML templates and CSS styling

## Technologies Used

- Python 3.13
- Flask
- MySQL
- HTML
- CSS

## Project Structure

job-application-tracker/

- app.py
- database.py
- schema.sql
- README.md
- AI_USAGE.md
- requirements.txt
- templates/
- static/

## Database Setup

1. Open MySQL Workbench.
2. Create or use your MySQL local instance.
3. Open the `schema.sql` file.
4. Run the script to create the `job_tracker` database and tables.

## Python Setup

1. Open the project folder in VS Code.
2. Open a terminal in the project folder.
3. Install the required packages:

```bash
pip install -r requirements.txt
```
