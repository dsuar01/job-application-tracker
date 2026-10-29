import json
import os
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from flask import Flask, abort, flash, redirect, render_template, request, url_for
from mysql.connector import Error as MySQLError
from mysql.connector.errors import IntegrityError

from database import get_db_connection

app = Flask(__name__)
# Only used to sign the little "flash" messages shown after saving. Set SECRET_KEY in .env for real use.
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")

APPLICATION_STATUSES = [
    "Applied", "Screening", "Phone Screen", "Interview", "Interview Completed",
    "Offer", "Offer Accepted", "Rejected", "Withdrawn",
]
JOB_TYPES = ["Full-time", "Part-time", "Contract", "Internship"]


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------
class DatabaseUnavailable(Exception):
    """Raised when we cannot connect to MySQL."""


def run(sql, params=(), *, one=False, many=False, commit=False):
    """Run one SQL statement and always close the connection.

    one=True  -> return the first row (or None)
    many=True -> return all rows
    commit=True -> save changes and return the new row id
    """
    connection = get_db_connection()
    if connection is None:
        raise DatabaseUnavailable()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(sql, params)
        if commit:
            connection.commit()
            return cursor.lastrowid
        if one:
            return cursor.fetchone()
        if many:
            return cursor.fetchall()
        return None
    finally:
        cursor.close()
        connection.close()


@app.errorhandler(DatabaseUnavailable)
def database_down(_error):
    return render_template("error.html", title="Database not reachable",
                           message="The app could not connect to MySQL. Make sure MySQL is running "
                                   "and that your .env file has the right DB_USER and DB_PASSWORD."), 503


@app.errorhandler(404)
def not_found(_error):
    return render_template("error.html", title="Page not found",
                           message="That page or record does not exist (it may have been deleted)."), 404


@app.errorhandler(MySQLError)
def database_error(error):
    return render_template("error.html", title="Database error",
                           message=f"MySQL reported a problem: {error}"), 500


@app.template_filter("money")
def money(value):
    if value in (None, ""):
        return "—"
    return f"${Decimal(value):,.0f}"


@app.template_filter("pretty_date")
def pretty_date(value):
    if not value:
        return "—"
    if isinstance(value, (date, datetime)):
        return value.strftime("%b %d, %Y").replace(" 0", " ")
    return str(value)


@app.template_filter("status_class")
def status_class(status):
    return (status or "").lower().replace(" ", "-")


# ---------------------------------------------------------------------------
# Form helpers
# ---------------------------------------------------------------------------
def text(form, name, *, required=False, label=None, errors=None, max_len=None):
    value = (form.get(name) or "").strip()
    label = label or name.replace("_", " ").title()
    if required and not value:
        errors.append(f"{label} is required.")
    if max_len and len(value) > max_len:
        errors.append(f"{label} must be {max_len} characters or fewer.")
    return value or None


def number(form, name, errors, label):
    raw = (form.get(name) or "").strip()
    if not raw:
        return None
    try:
        value = Decimal(raw)
    except InvalidOperation:
        errors.append(f"{label} must be a number.")
        return None
    if value < 0:
        errors.append(f"{label} cannot be negative.")
    return value


def date_field(form, name, errors, label, required=False):
    raw = (form.get(name) or "").strip()
    if not raw:
        if required:
            errors.append(f"{label} is required.")
        return None
    try:
        datetime.strptime(raw, "%Y-%m-%d")
    except ValueError:
        errors.append(f"{label} is not a valid date.")
        return None
    return raw


def choose_id(form, name, label, errors):
    raw = (form.get(name) or "").strip()
    if not raw.isdigit():
        errors.append(f"Please choose a {label}.")
        return None
    return int(raw)


def show_errors(errors):
    for message in errors:
        flash(message, "error")


def skills_to_list(raw):
    seen, skills = set(), []
    for item in (raw or "").split(","):
        item = item.strip()
        if item and item.lower() not in seen:
            seen.add(item.lower())
            skills.append(item)
    return skills


def load_requirements(raw):
    """Return (required, preferred) lists from the JSON column, whatever shape it has."""
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode("utf-8")
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except ValueError:
            return [], []
    if not isinstance(raw, dict):
        return [], []

    def as_list(value):
        return [str(s) for s in value] if isinstance(value, list) else []

    return as_list(raw.get("required_skills")), as_list(raw.get("preferred_skills"))


def delete_record(table, id_column, record_id, endpoint, label, blocked_by):
    try:
        run(f"DELETE FROM {table} WHERE {id_column} = %s", (record_id,), commit=True)
        flash(f"{label} deleted.", "success")
    except IntegrityError:
        flash(f"This {label.lower()} can't be deleted because it still has {blocked_by}. "
              f"Delete those first.", "error")
    return redirect(url_for(endpoint))


def get_or_404(sql, params):
    row = run(sql, params, one=True)
    if row is None:
        abort(404)
    return row


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@app.route("/")
def dashboard():
    stats = {
        "companies": run("SELECT COUNT(*) AS c FROM companies", one=True)["c"],
        "jobs": run("SELECT COUNT(*) AS c FROM jobs", one=True)["c"],
        "applications": run("SELECT COUNT(*) AS c FROM applications", one=True)["c"],
        "contacts": run("SELECT COUNT(*) AS c FROM contacts", one=True)["c"],
    }
    status_counts = run(
        "SELECT status, COUNT(*) AS c FROM applications GROUP BY status ORDER BY c DESC, status",
        many=True)
    recent = run("""
        SELECT applications.application_id, jobs.job_title, companies.company_name,
               applications.application_date, applications.status
        FROM applications
        INNER JOIN jobs ON applications.job_id = jobs.job_id
        INNER JOIN companies ON jobs.company_id = companies.company_id
        ORDER BY applications.application_date DESC, applications.application_id DESC
        LIMIT 5""", many=True)
    return render_template("dashboard.html", stats=stats, status_counts=status_counts, recent=recent)


# ---------------------------------------------------------------------------
# Companies
# ---------------------------------------------------------------------------
@app.route("/companies")
def companies():
    rows = run("""
        SELECT companies.*,
               (SELECT COUNT(*) FROM jobs WHERE jobs.company_id = companies.company_id) AS job_count
        FROM companies ORDER BY company_name""", many=True)
    return render_template("companies.html", companies=rows)


def read_company_form():
    errors = []
    data = {
        "company_name": text(request.form, "company_name", required=True, label="Company name",
                             errors=errors, max_len=100),
        "industry": text(request.form, "industry", errors=errors, max_len=50),
        "website": text(request.form, "website", errors=errors, max_len=200),
        "city": text(request.form, "city", errors=errors, max_len=50),
        "state": text(request.form, "state", errors=errors, max_len=50),
        "notes": text(request.form, "notes", errors=errors),
    }
    return data, errors


COMPANY_FIELDS = ("company_name", "industry", "website", "city", "state", "notes")


@app.route("/companies/add", methods=["GET", "POST"])
def add_company():
    company = {}
    if request.method == "POST":
        company, errors = read_company_form()
        if not errors:
            run("INSERT INTO companies (company_name, industry, website, city, state, notes) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                tuple(company[f] for f in COMPANY_FIELDS), commit=True)
            flash("Company added.", "success")
            return redirect(url_for("companies"))
        show_errors(errors)
    return render_template("company_form.html", company=company, editing=False)


@app.route("/companies/edit/<int:company_id>", methods=["GET", "POST"])
def edit_company(company_id):
    existing = get_or_404("SELECT * FROM companies WHERE company_id = %s", (company_id,))
    company = existing
    if request.method == "POST":
        company, errors = read_company_form()
        company["company_id"] = company_id
        if not errors:
            run("""UPDATE companies SET company_name = %s, industry = %s, website = %s,
                   city = %s, state = %s, notes = %s WHERE company_id = %s""",
                tuple(company[f] for f in COMPANY_FIELDS) + (company_id,), commit=True)
            flash("Company updated.", "success")
            return redirect(url_for("companies"))
        show_errors(errors)
    return render_template("company_form.html", company=company, editing=True)


@app.route("/companies/delete/<int:company_id>", methods=["POST"])
def delete_company(company_id):
    return delete_record("companies", "company_id", company_id, "companies", "Company",
                         "jobs or contacts")


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------
@app.route("/jobs")
def jobs():
    rows = run("""
        SELECT jobs.job_id, jobs.job_title, companies.company_name, jobs.job_type,
               jobs.salary_min, jobs.salary_max, jobs.date_posted, jobs.is_active, jobs.posting_url
        FROM jobs INNER JOIN companies ON jobs.company_id = companies.company_id
        ORDER BY jobs.job_id DESC""", many=True)
    return render_template("jobs.html", jobs=rows)


def all_companies():
    return run("SELECT company_id, company_name FROM companies ORDER BY company_name", many=True)


def read_job_form():
    errors = []
    f = request.form
    required = skills_to_list(f.get("required_skills"))
    preferred = skills_to_list(f.get("preferred_skills"))
    job = {
        "company_id": choose_id(f, "company_id", "company", errors),
        "job_title": text(f, "job_title", required=True, label="Job title", errors=errors, max_len=100),
        "job_type": f.get("job_type") if f.get("job_type") in JOB_TYPES else None,
        "salary_min": number(f, "salary_min", errors, "Minimum salary"),
        "salary_max": number(f, "salary_max", errors, "Maximum salary"),
        "date_posted": date_field(f, "date_posted", errors, "Date posted"),
        "posting_url": text(f, "posting_url", errors=errors, label="Posting URL", max_len=500),
        "job_description": text(f, "job_description", errors=errors, label="Description"),
        "is_active": 1 if f.get("is_active") == "on" else 0,
        "requirements": json.dumps({"required_skills": required, "preferred_skills": preferred})
        if (required or preferred) else None,
        # kept for re-filling the form
        "required_skills": ", ".join(required),
        "preferred_skills": ", ".join(preferred),
    }
    if job["salary_min"] is not None and job["salary_max"] is not None \
            and job["salary_min"] > job["salary_max"]:
        errors.append("Minimum salary cannot be higher than maximum salary.")
    return job, errors


JOB_COLUMNS = ("company_id", "job_title", "job_type", "salary_min", "salary_max", "date_posted",
               "posting_url", "job_description", "is_active", "requirements")


@app.route("/jobs/add", methods=["GET", "POST"])
def add_job():
    job = {"is_active": 1}
    if request.method == "POST":
        job, errors = read_job_form()
        if not errors:
            run(f"INSERT INTO jobs ({', '.join(JOB_COLUMNS)}) VALUES ({', '.join(['%s'] * len(JOB_COLUMNS))})",
                tuple(job[c] for c in JOB_COLUMNS), commit=True)
            flash("Job added.", "success")
            return redirect(url_for("jobs"))
        show_errors(errors)
    return render_template("job_form.html", job=job, companies=all_companies(),
                           job_types=JOB_TYPES, editing=False)


@app.route("/jobs/edit/<int:job_id>", methods=["GET", "POST"])
def edit_job(job_id):
    job = get_or_404("SELECT * FROM jobs WHERE job_id = %s", (job_id,))
    required, preferred = load_requirements(job.get("requirements"))
    job["required_skills"], job["preferred_skills"] = ", ".join(required), ", ".join(preferred)
    if request.method == "POST":
        job, errors = read_job_form()
        job["job_id"] = job_id
        if not errors:
            assignments = ", ".join(f"{c} = %s" for c in JOB_COLUMNS)
            run(f"UPDATE jobs SET {assignments} WHERE job_id = %s",
                tuple(job[c] for c in JOB_COLUMNS) + (job_id,), commit=True)
            flash("Job updated.", "success")
            return redirect(url_for("jobs"))
        show_errors(errors)
    return render_template("job_form.html", job=job, companies=all_companies(),
                           job_types=JOB_TYPES, editing=True)


@app.route("/jobs/delete/<int:job_id>", methods=["POST"])
def delete_job(job_id):
    return delete_record("jobs", "job_id", job_id, "jobs", "Job", "applications")


# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
@app.route("/applications")
def applications():
    rows = run("""
        SELECT applications.application_id, jobs.job_title, companies.company_name,
               applications.application_date, applications.status,
               applications.resume_version, applications.cover_letter_sent
        FROM applications
        INNER JOIN jobs ON applications.job_id = jobs.job_id
        INNER JOIN companies ON jobs.company_id = companies.company_id
        ORDER BY applications.application_date DESC, applications.application_id DESC""", many=True)
    return render_template("applications.html", applications=rows, statuses=APPLICATION_STATUSES)


def all_jobs():
    return run("""
        SELECT jobs.job_id, jobs.job_title, companies.company_name
        FROM jobs INNER JOIN companies ON jobs.company_id = companies.company_id
        ORDER BY jobs.job_title""", many=True)


def read_application_form():
    errors = []
    f = request.form
    status = f.get("status")
    if status not in APPLICATION_STATUSES:
        errors.append("Please choose a valid status.")
    application = {
        "job_id": choose_id(f, "job_id", "job", errors),
        "application_date": date_field(f, "application_date", errors, "Application date", required=True),
        "status": status,
        "resume_version": text(f, "resume_version", errors=errors, label="Resume version", max_len=50),
        "cover_letter_sent": 1 if f.get("cover_letter_sent") == "on" else 0,
        "response_date": date_field(f, "response_date", errors, "Response date"),
        "notes": text(f, "notes", errors=errors),
    }
    if application["response_date"] and application["application_date"] \
            and application["response_date"] < application["application_date"]:
        errors.append("Response date cannot be before the application date.")
    return application, errors


APPLICATION_COLUMNS = ("job_id", "application_date", "status", "resume_version",
                       "cover_letter_sent", "response_date", "notes")


@app.route("/applications/add", methods=["GET", "POST"])
def add_application():
    application = {"status": "Applied", "application_date": date.today().isoformat()}
    if request.method == "POST":
        application, errors = read_application_form()
        if not errors:
            run(f"INSERT INTO applications ({', '.join(APPLICATION_COLUMNS)}) "
                f"VALUES ({', '.join(['%s'] * len(APPLICATION_COLUMNS))})",
                tuple(application[c] for c in APPLICATION_COLUMNS), commit=True)
            flash("Application added.", "success")
            return redirect(url_for("applications"))
        show_errors(errors)
    return render_template("application_form.html", application=application, jobs=all_jobs(),
                           statuses=APPLICATION_STATUSES, editing=False)


@app.route("/applications/edit/<int:application_id>", methods=["GET", "POST"])
def edit_application(application_id):
    application = get_or_404("SELECT * FROM applications WHERE application_id = %s", (application_id,))
    if request.method == "POST":
        application, errors = read_application_form()
        application["application_id"] = application_id
        if not errors:
            assignments = ", ".join(f"{c} = %s" for c in APPLICATION_COLUMNS)
            run(f"UPDATE applications SET {assignments} WHERE application_id = %s",
                tuple(application[c] for c in APPLICATION_COLUMNS) + (application_id,), commit=True)
            flash("Application updated.", "success")
            return redirect(url_for("applications"))
        show_errors(errors)
    return render_template("application_form.html", application=application, jobs=all_jobs(),
                           statuses=APPLICATION_STATUSES, editing=True)


@app.route("/applications/delete/<int:application_id>", methods=["POST"])
def delete_application(application_id):
    return delete_record("applications", "application_id", application_id, "applications",
                         "Application", "linked records")


# ---------------------------------------------------------------------------
# Contacts
# ---------------------------------------------------------------------------
@app.route("/contacts")
def contacts():
    rows = run("""
        SELECT contacts.contact_id, contacts.first_name, contacts.last_name, companies.company_name,
               contacts.email, contacts.phone, contacts.job_title, contacts.linkedin_url
        FROM contacts INNER JOIN companies ON contacts.company_id = companies.company_id
        ORDER BY contacts.last_name, contacts.first_name""", many=True)
    return render_template("contacts.html", contacts=rows)


CONTACT_COLUMNS = ("company_id", "first_name", "last_name", "email", "phone", "job_title",
                   "linkedin_url", "notes")


def read_contact_form():
    errors = []
    f = request.form
    contact = {
        "company_id": choose_id(f, "company_id", "company", errors),
        "first_name": text(f, "first_name", required=True, label="First name", errors=errors, max_len=50),
        "last_name": text(f, "last_name", required=True, label="Last name", errors=errors, max_len=50),
        "email": text(f, "email", errors=errors, max_len=100),
        "phone": text(f, "phone", errors=errors, max_len=20),
        "job_title": text(f, "job_title", errors=errors, label="Job title", max_len=100),
        "linkedin_url": text(f, "linkedin_url", errors=errors, label="LinkedIn URL", max_len=200),
        "notes": text(f, "notes", errors=errors),
    }
    if contact["email"] and ("@" not in contact["email"] or "." not in contact["email"].split("@")[-1]):
        errors.append("Email does not look valid.")
    return contact, errors


@app.route("/contacts/add", methods=["GET", "POST"])
def add_contact():
    contact = {}
    if request.method == "POST":
        contact, errors = read_contact_form()
        if not errors:
            run(f"INSERT INTO contacts ({', '.join(CONTACT_COLUMNS)}) "
                f"VALUES ({', '.join(['%s'] * len(CONTACT_COLUMNS))})",
                tuple(contact[c] for c in CONTACT_COLUMNS), commit=True)
            flash("Contact added.", "success")
            return redirect(url_for("contacts"))
        show_errors(errors)
    return render_template("contact_form.html", contact=contact, companies=all_companies(), editing=False)


@app.route("/contacts/edit/<int:contact_id>", methods=["GET", "POST"])
def edit_contact(contact_id):
    contact = get_or_404("SELECT * FROM contacts WHERE contact_id = %s", (contact_id,))
    if request.method == "POST":
        contact, errors = read_contact_form()
        contact["contact_id"] = contact_id
        if not errors:
            assignments = ", ".join(f"{c} = %s" for c in CONTACT_COLUMNS)
            run(f"UPDATE contacts SET {assignments} WHERE contact_id = %s",
                tuple(contact[c] for c in CONTACT_COLUMNS) + (contact_id,), commit=True)
            flash("Contact updated.", "success")
            return redirect(url_for("contacts"))
        show_errors(errors)
    return render_template("contact_form.html", contact=contact, companies=all_companies(), editing=True)


@app.route("/contacts/delete/<int:contact_id>", methods=["POST"])
def delete_contact(contact_id):
    return delete_record("contacts", "contact_id", contact_id, "contacts", "Contact", "linked records")


# ---------------------------------------------------------------------------
# Job Match
# ---------------------------------------------------------------------------
@app.route("/job-match", methods=["GET", "POST"])
def job_match():
    results = []
    entered_skills = ""
    searched = False

    if request.method == "POST":
        searched = True
        entered_skills = request.form.get("skills", "")
        user_skills = {s.lower() for s in skills_to_list(entered_skills)}

        jobs_list = run("""
            SELECT jobs.job_id, jobs.job_title, companies.company_name, jobs.requirements
            FROM jobs INNER JOIN companies ON jobs.company_id = companies.company_id
            WHERE jobs.requirements IS NOT NULL AND jobs.is_active = 1""", many=True)

        for job in jobs_list:
            required_list, preferred_list = load_requirements(job["requirements"])
            required = {s.lower() for s in required_list}
            preferred = {s.lower() for s in preferred_list}

            matched_required = sorted(required & user_skills)
            matched_preferred = sorted(preferred & user_skills)
            missing_required = sorted(required - user_skills)

            # Required skills count double.
            total = len(required) * 2 + len(preferred)
            earned = len(matched_required) * 2 + len(matched_preferred)
            results.append({
                "job_id": job["job_id"],
                "job_title": job["job_title"],
                "company_name": job["company_name"],
                "match_percentage": round(earned / total * 100) if total else 0,
                "matched_required": matched_required,
                "matched_preferred": matched_preferred,
                "missing_required": missing_required,
            })

        results.sort(key=lambda r: r["match_percentage"], reverse=True)

    return render_template("job_match.html", results=results, entered_skills=entered_skills,
                           searched=searched)


if __name__ == "__main__":
    app.run(debug=True)
