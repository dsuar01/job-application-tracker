import json
from flask import Flask, render_template, request, redirect, url_for
from database import get_db_connection

app = Flask(__name__)


@app.route("/")
def dashboard():
    connection = get_db_connection()

    if connection is None:
        return "Database connection failed."

    cursor = connection.cursor(dictionary=True)

    stats = {}

    cursor.execute("SELECT COUNT(*) AS count FROM companies")
    stats["companies"] = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) AS count FROM jobs")
    stats["jobs"] = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) AS count FROM applications")
    stats["applications"] = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) AS count FROM contacts")
    stats["contacts"] = cursor.fetchone()["count"]

    cursor.close()
    connection.close()

    return render_template("dashboard.html", stats=stats)


@app.route("/companies")
def companies():
    connection = get_db_connection()

    if connection is None:
        return "Database connection failed."

    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM companies ORDER BY company_id")
    companies_list = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("companies.html", companies=companies_list)


@app.route("/jobs")
def jobs():
    connection = get_db_connection()

    if connection is None:
        return "Database connection failed."

    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT jobs.job_id,
               jobs.job_title,
               companies.company_name,
               jobs.job_type,
               jobs.salary_min,
               jobs.salary_max,
               jobs.date_posted
        FROM jobs
        INNER JOIN companies ON jobs.company_id = companies.company_id
        ORDER BY jobs.job_id
    """
    cursor.execute(query)
    jobs_list = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("jobs.html", jobs=jobs_list)


@app.route("/jobs/add", methods=["GET", "POST"])
def add_job():
    connection = get_db_connection()

    if connection is None:
        return "Database connection failed."

    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":
        company_id = request.form["company_id"]
        job_title = request.form["job_title"]
        job_type = request.form["job_type"]
        salary_min = request.form["salary_min"]
        salary_max = request.form["salary_max"]
        date_posted = request.form["date_posted"]

        insert_query = """
            INSERT INTO jobs (company_id, job_title, job_type, salary_min, salary_max, date_posted)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = (company_id, job_title, job_type,
                  salary_min, salary_max, date_posted)

        cursor.execute(insert_query, values)
        connection.commit()

        cursor.close()
        connection.close()

        return redirect(url_for("jobs"))

    cursor.execute(
        "SELECT company_id, company_name FROM companies ORDER BY company_name")
    companies_list = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("add_job.html", companies=companies_list)


@app.route("/jobs/edit/<int:job_id>", methods=["GET", "POST"])
def edit_job(job_id):
    connection = get_db_connection()

    if connection is None:
        return "Database connection failed."

    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":
        company_id = request.form["company_id"]
        job_title = request.form["job_title"]
        job_type = request.form["job_type"]
        salary_min = request.form["salary_min"]
        salary_max = request.form["salary_max"]
        date_posted = request.form["date_posted"]

        update_query = """
            UPDATE jobs
            SET company_id = %s,
                job_title = %s,
                job_type = %s,
                salary_min = %s,
                salary_max = %s,
                date_posted = %s
            WHERE job_id = %s
        """
        values = (company_id, job_title, job_type,
                  salary_min, salary_max, date_posted, job_id)

        cursor.execute(update_query, values)
        connection.commit()

        cursor.close()
        connection.close()

        return redirect(url_for("jobs"))

    cursor.execute("SELECT * FROM jobs WHERE job_id = %s", (job_id,))
    job = cursor.fetchone()

    cursor.execute(
        "SELECT company_id, company_name FROM companies ORDER BY company_name")
    companies_list = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("edit_job.html", job=job, companies=companies_list)


@app.route("/jobs/delete/<int:job_id>", methods=["POST"])
def delete_job(job_id):
    connection = get_db_connection()

    if connection is None:
        return "Database connection failed."

    cursor = connection.cursor()

    query = "DELETE FROM jobs WHERE job_id = %s"
    cursor.execute(query, (job_id,))
    connection.commit()

    cursor.close()
    connection.close()

    return redirect(url_for("jobs"))


@app.route("/applications")
def applications():
    connection = get_db_connection()

    if connection is None:
        return "Database connection failed."

    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT applications.application_id,
               jobs.job_title,
               companies.company_name,
               applications.application_date,
               applications.status,
               applications.resume_version,
               applications.cover_letter_sent
        FROM applications
        INNER JOIN jobs ON applications.job_id = jobs.job_id
        INNER JOIN companies ON jobs.company_id = companies.company_id
        ORDER BY applications.application_id
    """
    cursor.execute(query)
    applications_list = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("applications.html", applications=applications_list)


@app.route("/applications/add", methods=["GET", "POST"])
def add_application():
    connection = get_db_connection()

    if connection is None:
        return "Database connection failed."

    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":
        job_id = request.form["job_id"]
        application_date = request.form["application_date"]
        status = request.form["status"]
        resume_version = request.form["resume_version"]
        cover_letter_sent = 1 if request.form.get(
            "cover_letter_sent") == "on" else 0

        insert_query = """
            INSERT INTO applications (job_id, application_date, status, resume_version, cover_letter_sent)
            VALUES (%s, %s, %s, %s, %s)
        """
        values = (job_id, application_date, status,
                  resume_version, cover_letter_sent)

        cursor.execute(insert_query, values)
        connection.commit()

        cursor.close()
        connection.close()

        return redirect(url_for("applications"))

    cursor.execute("""
        SELECT jobs.job_id, jobs.job_title, companies.company_name
        FROM jobs
        INNER JOIN companies ON jobs.company_id = companies.company_id
        ORDER BY jobs.job_title
    """)
    jobs_list = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("add_application.html", jobs=jobs_list)


@app.route("/applications/edit/<int:application_id>", methods=["GET", "POST"])
def edit_application(application_id):
    connection = get_db_connection()

    if connection is None:
        return "Database connection failed."

    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":
        job_id = request.form["job_id"]
        application_date = request.form["application_date"]
        status = request.form["status"]
        resume_version = request.form["resume_version"]
        cover_letter_sent = 1 if request.form.get(
            "cover_letter_sent") == "on" else 0

        update_query = """
            UPDATE applications
            SET job_id = %s,
                application_date = %s,
                status = %s,
                resume_version = %s,
                cover_letter_sent = %s
            WHERE application_id = %s
        """
        values = (
            job_id,
            application_date,
            status,
            resume_version,
            cover_letter_sent,
            application_id
        )

        cursor.execute(update_query, values)
        connection.commit()

        cursor.close()
        connection.close()

        return redirect(url_for("applications"))

    cursor.execute(
        "SELECT * FROM applications WHERE application_id = %s", (application_id,))
    application = cursor.fetchone()

    cursor.execute("""
        SELECT jobs.job_id, jobs.job_title, companies.company_name
        FROM jobs
        INNER JOIN companies ON jobs.company_id = companies.company_id
        ORDER BY jobs.job_title
    """)
    jobs_list = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "edit_application.html",
        application=application,
        jobs=jobs_list
    )


@app.route("/applications/delete/<int:application_id>", methods=["POST"])
def delete_application(application_id):
    connection = get_db_connection()

    if connection is None:
        return "Database connection failed."

    cursor = connection.cursor()

    query = "DELETE FROM applications WHERE application_id = %s"
    cursor.execute(query, (application_id,))
    connection.commit()

    cursor.close()
    connection.close()

    return redirect(url_for("applications"))


@app.route("/contacts")
def contacts():
    connection = get_db_connection()

    if connection is None:
        return "Database connection failed."

    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT contacts.contact_id,
               contacts.first_name,
               contacts.last_name,
               companies.company_name,
               contacts.email,
               contacts.phone,
               contacts.job_title
        FROM contacts
        INNER JOIN companies ON contacts.company_id = companies.company_id
        ORDER BY contacts.contact_id
    """
    cursor.execute(query)
    contacts_list = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("contacts.html", contacts=contacts_list)


@app.route("/contacts/add", methods=["GET", "POST"])
def add_contact():
    connection = get_db_connection()

    if connection is None:
        return "Database connection failed."

    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":
        company_id = request.form["company_id"]
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        email = request.form["email"]
        phone = request.form["phone"]
        job_title = request.form["job_title"]
        linkedin_url = request.form["linkedin_url"]
        notes = request.form["notes"]

        insert_query = """
            INSERT INTO contacts (
                company_id, first_name, last_name, email, phone, job_title, linkedin_url, notes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            company_id,
            first_name,
            last_name,
            email,
            phone,
            job_title,
            linkedin_url,
            notes
        )

        cursor.execute(insert_query, values)
        connection.commit()

        cursor.close()
        connection.close()

        return redirect(url_for("contacts"))

    cursor.execute(
        "SELECT company_id, company_name FROM companies ORDER BY company_name")
    companies_list = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("add_contact.html", companies=companies_list)


@app.route("/contacts/edit/<int:contact_id>", methods=["GET", "POST"])
def edit_contact(contact_id):
    connection = get_db_connection()

    if connection is None:
        return "Database connection failed."

    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":
        company_id = request.form["company_id"]
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        email = request.form["email"]
        phone = request.form["phone"]
        job_title = request.form["job_title"]
        linkedin_url = request.form["linkedin_url"]
        notes = request.form["notes"]

        update_query = """
            UPDATE contacts
            SET company_id = %s,
                first_name = %s,
                last_name = %s,
                email = %s,
                phone = %s,
                job_title = %s,
                linkedin_url = %s,
                notes = %s
            WHERE contact_id = %s
        """
        values = (
            company_id,
            first_name,
            last_name,
            email,
            phone,
            job_title,
            linkedin_url,
            notes,
            contact_id
        )

        cursor.execute(update_query, values)
        connection.commit()

        cursor.close()
        connection.close()

        return redirect(url_for("contacts"))

    cursor.execute(
        "SELECT * FROM contacts WHERE contact_id = %s", (contact_id,))
    contact = cursor.fetchone()

    cursor.execute(
        "SELECT company_id, company_name FROM companies ORDER BY company_name")
    companies_list = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "edit_contact.html",
        contact=contact,
        companies=companies_list
    )


@app.route("/contacts/delete/<int:contact_id>", methods=["POST"])
def delete_contact(contact_id):
    connection = get_db_connection()

    if connection is None:
        return "Database connection failed."

    cursor = connection.cursor()

    query = "DELETE FROM contacts WHERE contact_id = %s"
    cursor.execute(query, (contact_id,))
    connection.commit()

    cursor.close()
    connection.close()

    return redirect(url_for("contacts"))


@app.route("/job-match", methods=["GET", "POST"])
def job_match():
    results = []
    entered_skills = ""

    if request.method == "POST":
        entered_skills = request.form["skills"]

        user_skills = {
            skill.strip().lower()
            for skill in entered_skills.split(",")
            if skill.strip()
        }

        connection = get_db_connection()

        if connection is None:
            return "Database connection failed."

        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT jobs.job_id,
                   jobs.job_title,
                   companies.company_name,
                   jobs.requirements
            FROM jobs
            INNER JOIN companies ON jobs.company_id = companies.company_id
            WHERE jobs.requirements IS NOT NULL
        """
        cursor.execute(query)
        jobs_list = cursor.fetchall()

        cursor.close()
        connection.close()

        for job in jobs_list:
            requirements = job["requirements"]

            if isinstance(requirements, str):
                requirements = json.loads(requirements)

            required_skills = {
                skill.lower() for skill in requirements.get("required_skills", [])
            }
            preferred_skills = {
                skill.lower() for skill in requirements.get("preferred_skills", [])
            }

            matched_required = sorted(required_skills & user_skills)
            matched_preferred = sorted(preferred_skills & user_skills)
            missing_required = sorted(required_skills - user_skills)

            required_weight = 2
            preferred_weight = 1

            total_weight = (len(required_skills) * required_weight) + (
                len(preferred_skills) * preferred_weight
            )

            earned_weight = (len(matched_required) * required_weight) + (
                len(matched_preferred) * preferred_weight
            )

            match_percentage = round(
                (earned_weight / total_weight) * 100) if total_weight > 0 else 0

            results.append({
                "job_id": job["job_id"],
                "job_title": job["job_title"],
                "company_name": job["company_name"],
                "match_percentage": match_percentage,
                "matched_required": matched_required,
                "matched_preferred": matched_preferred,
                "missing_required": missing_required,
                "required_skills": sorted(required_skills),
                "preferred_skills": sorted(preferred_skills),
            })

        results.sort(key=lambda x: x["match_percentage"], reverse=True)

    return render_template(
        "job_match.html",
        results=results,
        entered_skills=entered_skills
    )


@app.route("/companies/add", methods=["GET", "POST"])
def add_company():
    if request.method == "POST":
        company_name = request.form["company_name"]
        industry = request.form["industry"]
        website = request.form["website"]
        city = request.form["city"]
        state = request.form["state"]
        notes = request.form["notes"]

        connection = get_db_connection()

        if connection is None:
            return "Database connection failed."

        cursor = connection.cursor()
        query = """
            INSERT INTO companies (company_name, industry, website, city, state, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = (company_name, industry, website, city, state, notes)

        cursor.execute(query, values)
        connection.commit()

        cursor.close()
        connection.close()

        return redirect(url_for("companies"))

    return render_template("add_company.html")


@app.route("/companies/edit/<int:company_id>", methods=["GET", "POST"])
def edit_company(company_id):
    connection = get_db_connection()

    if connection is None:
        return "Database connection failed."

    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":
        company_name = request.form["company_name"]
        industry = request.form["industry"]
        website = request.form["website"]
        city = request.form["city"]
        state = request.form["state"]
        notes = request.form["notes"]

        query = """
            UPDATE companies
            SET company_name = %s,
                industry = %s,
                website = %s,
                city = %s,
                state = %s,
                notes = %s
            WHERE company_id = %s
        """
        values = (company_name, industry, website,
                  city, state, notes, company_id)

        cursor.execute(query, values)
        connection.commit()

        cursor.close()
        connection.close()

        return redirect(url_for("companies"))

    cursor.execute(
        "SELECT * FROM companies WHERE company_id = %s", (company_id,))
    company = cursor.fetchone()

    cursor.close()
    connection.close()

    return render_template("edit_company.html", company=company)


@app.route("/companies/delete/<int:company_id>", methods=["POST"])
def delete_company(company_id):
    connection = get_db_connection()

    if connection is None:
        return "Database connection failed."

    cursor = connection.cursor()

    query = "DELETE FROM companies WHERE company_id = %s"
    cursor.execute(query, (company_id,))
    connection.commit()

    cursor.close()
    connection.close()

    return redirect(url_for("companies"))


if __name__ == "__main__":
    app.run(debug=True)
