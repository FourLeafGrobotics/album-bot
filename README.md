# album-bot
This utilizes telegram and google photos api to automatically upload images sent to a chat to an album in google photos
## When creds don't work
Go to [google cloud website](https://console.cloud.google.com/), then click on APIs and Services, click Credentials off to the left, make a new one with OAuth Client ID, application type Desktop App. After created, download json and replace text in client_id.json with the new one. It will automatically update it after first attempted use.
## Manual Chat
I don't have it create a new album I don't think. The chat name needs updated manually for this. As well as the chat id needing updated manually for this. Also, it's conda activate telegram. The albumBot env was never set up properly.
Also, once you've run the auth once and uploaded a picture, you'll need to manually update the start message with the new link to the album that it creates automatically.