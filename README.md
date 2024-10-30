# album-bot
This utilizes telegram and google photos api to automatically upload images sent to a chat to an album in google photos
## When creds don't work
Go to [google cloud website](https://console.cloud.google.com/), then click on APIs and Services, click Credentials off to the left, make a new one with OAuth Client ID, application type Desktop App. After created, download json and replace text in client_id.json with the new one. It will automatically update it after first attempted use.
