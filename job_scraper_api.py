import datetime
from flask import Flask, request, jsonify
from src.jobspy import scrape_jobs

app = Flask(__name__)

VALID_SITES = ['indeed', 'linkedin', 'zip_recruiter', 'glassdoor', 'google']

def scrape_jobs_map(location: str, position: str, siteName: str):
    try:
        if siteName not in VALID_SITES:
            raise ValueError(f"Invalid site name: {siteName}. Expected one of {VALID_SITES}.")
        jobs = scrape_jobs(
            site_name=[siteName],
            search_term=position,
            google_search_term=f"{position} engineer jobs in {location} since past month",
            location=location,
            results_wanted=200,
            hours_old=200,
            linkedin_fetch_description=True,
            country_indeed='ISRAEL' if siteName == 'indeed' else 'USA',
        )
        jobs = jobs.fillna(value='')
        # Convert jobs DataFrame to a dictionary with job URLs as keys
        jobs_map = jobs.set_index('job_url').to_dict(orient='index')

        # Serialize dates in the dictionary to ISO format
        for job_data in jobs_map.values():
            for key, value in job_data.items():
                if isinstance(value, (datetime.date, datetime.datetime)):
                    job_data[key] = value.isoformat()

        return jobs_map
    except Exception as e:
        raise ValueError(f"Error fetching jobs: {e}")

@app.route("/")
def root():
    """
    Root endpoint to test the API.
    """
    return jsonify({"message": "Job Scraper API is running!"})

@app.route("/scrape-jobs", methods=["POST"])
def fetch_jobs():
    """
    Fetch jobs from the specified site, location, and position.
    """
    data = request.get_json()
    location = data.get("location")
    position = data.get("position")
    siteName = data.get("siteName")

    if not location or not position or not siteName:
        return jsonify({"error": "Missing required fields: location, position, siteName"}), 400

    try:
        jobs_map = scrape_jobs_map(location, position, siteName)
        return jsonify(jobs_map)
    except ValueError as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)