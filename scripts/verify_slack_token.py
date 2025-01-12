from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

def verify_slack_token():
    token = input("Enter your Slack Bot User OAuth Token (starts with xoxb-): ")
    
    client = WebClient(token=token)
    try:
        # Test the API call
        response = client.auth_test()
        print("\nSuccess! Token is valid.")
        print(f"Connected to workspace: {response['team']}")
        print(f"Bot name: {response['user']}")
        
        print("\nAdd this line to your .env file:")
        print(f"SLACK_API_KEY={token}")
        
    except SlackApiError as e:
        print(f"\nError: {e.response['error']}")
        print("Please check your token and try again.")

if __name__ == "__main__":
    verify_slack_token()
