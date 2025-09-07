from datetime import datetime, timezone


def listing_age_time(posted_time):
    posted = datetime.fromisoformat(posted_time.replace("Z", "+00:00"))
    today = datetime.now(timezone.utc) 
    days_old = (today - posted).days

    return days_old < 180 


def create_time_delta(posted_time, bumped_time):
    posted_dt = datetime.fromisoformat(posted_time.replace("Z", "+00:00"))
    bumped_dt = datetime.fromisoformat(bumped_time.replace("Z", "+00:00")) 
                                    


posted_time="2025-08-29T18:26:51.005Z"
posted = datetime.fromisoformat(posted_time.replace("Z", "+00:00"))


print(listing_age_time(posted_time))