from google_auth_oauthlib.flow import InstalledAppFlow
import json
import os

# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]

def main():
    """Shows basic usage of the Gmail API.
    Prints the user's email address.
    """
    # Load client secrets from a local file
    client_secrets_file = input("Enter the path to your client_secrets.json file: ")
    
    if not os.path.exists(client_secrets_file):
        print(f"Error: File {client_secrets_file} not found!")
        return

    flow = InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, SCOPES)
    creds = flow.run_local_server(port=0)

    # Get the credentials as a dictionary
    creds_dict = {
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri
    }

    # Print the credentials in .env format
    print("\nAdd these lines to your .env file:")
    print("GMAIL_API_KEY='" + json.dumps(creds_dict) + "'")
    print("DRIVE_API_KEY=${GMAIL_API_KEY}")

if __name__ == '__main__':
    main()
