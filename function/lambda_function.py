import os
import re
import time
import praw
import boto3

try:
    import dotenv

    dotenv.load_dotenv("../.env")
except ImportError:
    pass


########################################################################################################################
# Configuration
########################################################################################################################
VERSION = "v1.0.0"
AUTHOR = os.getenv("AUTHOR")
APP_ID = os.getenv("REDDIT_APP_ID")
APP_SECRET = os.getenv("REDDIT_APP_SECRET")
SUBMISSION_ID = os.getenv("SUBMISSION_ID")
USER_AGENT = f"{os.name}:{APP_ID}:{VERSION} (by {AUTHOR})"
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE")
MATRICULATION = os.getenv("MATRICULATION")

########################################################################################################################
# RegEx
########################################################################################################################
R_APPLIED = re.compile(r"(status)(.*)(applied|review|n/a)", flags=re.IGNORECASE)
R_ACCEPTED = re.compile(r"(status)(.*)(accept)", flags=re.IGNORECASE)
R_REJECTED = re.compile(r"(status)(.*)(reject)", flags=re.IGNORECASE)


########################################################################################################################
# Application
########################################################################################################################
def lambda_handler(event: dict, context):
    # Setup client and payload
    reddit = praw.Reddit(
        client_id=APP_ID, client_secret=APP_SECRET, user_agent=USER_AGENT
    )
    payload = {
        "Matriculation": MATRICULATION,
        "ProcessEpoch": int(time.time() * 1000),
        "Pending": 0,
        "Accepted": 0,
        "Rejected": 0,
    }

    # Parse submission comments
    submission = reddit.submission(SUBMISSION_ID)
    submission.comments.replace_more(limit=100)
    for comment in submission.comments:
        if R_APPLIED.search(comment.body):
            payload["Pending"] += 1
        elif R_ACCEPTED.search(comment.body):
            payload["Accepted"] += 1
        elif R_REJECTED.search(comment.body):
            payload["Rejected"] += 1

    # Load to DynamoDB
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(DYNAMODB_TABLE)
    table.put_item(Item=payload)
    return payload
