# Job Application Tracker

A full-stack web application that helps users track job applications. This project uses **MySQL** for the database, **Python with Flask** for the backend, and **HTML/CSS** for the frontend.

## Features

- Dashboard with summary counts, applications by status and recent activity
- Full CRUD for:
  - Companies
  - Jobs
  - Applications
  - Contacts
- Job Match feature using JSON job requirements and skill comparison
- MySQL relational database with foreign keys
- Modern responsive interface (light and dark mode), search/filter on applications
- Form validation, friendly error messages and protection against deleting records that are still in use

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
- .env.example
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

## Configure the database password

The password is no longer stored in the code. Copy `.env.example` to `.env` and fill in your MySQL settings:

```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password_here
DB_NAME=job_tracker
```

`.env` is ignored by git, so it is never uploaded.

## Run the app

```bash
python database.py   # optional: checks the database connection
python app.py
```

Then open http://127.0.0.1:5000 in your browser.

## Tips

- Add a company first, then jobs, then applications. Jobs and applications depend on the records before them.
- In Job Match, give each job required/preferred skills (comma separated) on the job form, then enter your own skills to see a match score.
