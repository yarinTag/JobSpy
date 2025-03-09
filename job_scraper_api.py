import datetime
from fp.fp import FreeProxy
from flask import Flask, request, jsonify
from src.jobspy import scrape_jobs

app = Flask(__name__)

VALID_SITES = ['indeed', 'linkedin', 'zip_recruiter', 'glassdoor', 'google']

def get_random_proxy():
    """Fetches a fresh proxy from free-proxy."""
    proxy = FreeProxy(timeout=1, rand=True).get()
    return {"http": proxy, "https": proxy}

def scrape_jobs_map(location: str, position: str, siteName: str, hourOld: int):
    try:
        if siteName not in VALID_SITES:
            raise ValueError(f"Invalid site name: {siteName}. Expected one of {VALID_SITES}.")
        proxies = get_random_proxy()

        jobs = scrape_jobs(
            site_name=[siteName],
            search_term=position,
            google_search_term=f"{position} engineer jobs in {location} since past month",
            location=location,
            results_wanted=200,
            hours_old=hourOld,
            linkedin_fetch_description=True,
            country_indeed='ISRAEL' if siteName == 'indeed' else 'USA',
            proxies=proxies
        )
        jobs = jobs.fillna(value='')
        # Convert jobs DataFrame to a dictionary with job URLs as keys
        jobs_map = {job_url: data for job_url, data in jobs.to_dict(orient='index').items()}

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
    hourOld = data.get("hourOld")


    if not location or not position or not siteName:
        return jsonify({"error": "Missing required fields: location, position, siteName"}), 400

    try:
        jobs_map = scrape_jobs_map(location, position, siteName, hourOld)
        return jsonify(jobs_map)
    except ValueError as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)