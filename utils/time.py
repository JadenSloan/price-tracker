from datetime import datetime, timezone


def days_old(posted_time):
    posted = datetime.fromisoformat(posted_time.replace("Z", "+00:00"))
    today = datetime.now(timezone.utc) 

    return (today - posted).days



def create_time_delta(posted_time, bumped_time):
    posted_dt = datetime.fromisoformat(posted_time.replace("Z", "+00:00"))
    bumped_dt = datetime.fromisoformat(bumped_time.replace("Z", "+00:00")) 
                                    
