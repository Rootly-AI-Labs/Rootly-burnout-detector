# Slack Bot Token Setup Guide

## Step 1: Create a Slack App

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Click **"Create New App"**
3. Choose **"From scratch"**
4. Enter:
   - App Name: `Burnout Detector Test` (or any name you prefer)
   - Pick your workspace from the dropdown
5. Click **"Create App"**

## Step 2: Configure OAuth & Permissions

1. In the left sidebar, click **"OAuth & Permissions"**
2. Scroll down to **"Scopes"** section
3. Under **"Bot Token Scopes"**, add these permissions:
   - `channels:read` - View basic channel info
   - `channels:manage` - Create channels for testing
   - `channels:history` - Read message history
   - `chat:write` - Post messages
   - `users:read` - View user info
   - `users:read.email` - View user emails

## Step 3: Install App to Workspace

1. Scroll up to **"OAuth Tokens for Your Workspace"**
2. Click **"Install to Workspace"**
3. Review permissions and click **"Allow"**
4. You'll see your **Bot User OAuth Token** (starts with `xoxb-`)
5. Copy this token!

## Step 4: Add Token to Your Project

Add the token to your `secrets.env` file:

```bash
SLACK_BOT_TOKEN=xoxb-your-workspace-12345-67890-abcdefghijklmnop
```

## Step 5: Invite Bot to Channels

Before the bot can post to channels, you need to invite it:

1. In Slack, go to any channel you want to use for testing
2. Type `/invite @Burnout Detector Test` (or your app name)
3. The bot can now read and post in that channel

## Optional: User Token (for Advanced Features)

If you want to post messages as different users (not just the bot):

1. Under **"OAuth & Permissions"**
2. Add **"User Token Scopes"**:
   - `chat:write` - Post as user
   - `users:read` - Read user info
3. Reinstall the app
4. Copy the **User OAuth Token** (starts with `xoxp-`)
5. Add to `secrets.env`:

```bash
SLACK_USER_TOKEN=xoxp-your-workspace-12345-67890-abcdefghijklmnop
```

## Quick Test

After setup, test your bot token:

```bash
curl -X POST https://slack.com/api/auth.test \
  -H "Authorization: Bearer xoxb-your-token-here" \
  -H "Content-type: application/json"
```

You should see:
```json
{
  "ok": true,
  "url": "https://yourworkspace.slack.com/",
  "team": "Your Workspace",
  "user": "burnout_detector_test",
  "team_id": "T12345",
  "user_id": "U12345",
  "bot_id": "B12345"
}
```

## Common Issues

- **"not_authed"**: Token is invalid or not added to request
- **"invalid_auth"**: Token format is wrong or expired
- **"channel_not_found"**: Bot needs to be invited to the channel
- **"missing_scope"**: Add the required scope in OAuth settings

## Next Steps

Once you have your bot token:

```bash
# Add token to secrets.env
echo "SLACK_BOT_TOKEN=xoxb-your-token" >> secrets.env

# Run the test data generator
python test_slack_integration.py

# Populate your Slack workspace
python slack_workspace_populator.py
```