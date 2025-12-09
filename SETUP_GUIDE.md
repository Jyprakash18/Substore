# SUB-MAN-BOT - Complete Setup & Deployment Guide

## 📋 Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Configuration Setup](#configuration-setup)
4. [Database Setup](#database-setup)
5. [Razorpay Integration](#razorpay-integration)
6. [Deployment Options](#deployment-options)
7. [Bot Commands](#bot-commands)
8. [Admin Usage Guide](#admin-usage-guide)
9. [User Workflow](#user-workflow)
10. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

**SUB-MAN-BOT** is a Telegram subscription management bot that automates paid service subscriptions with integrated Razorpay payment processing. It's designed to monetize Telegram group access by selling time-based subscriptions with automated payment processing and membership management.

### Key Features:
- ✅ Automated subscription management
- ✅ Razorpay payment integration
- ✅ Multiple service support with custom pricing plans
- ✅ Auto-expiry handling and user removal
- ✅ Invite link generation for paid groups
- ✅ MongoDB database integration
- ✅ Docker deployment ready

---

## 📦 Prerequisites

### Required Accounts & API Keys:

1. **Telegram Bot Token**
   - Create a bot via [@BotFather](https://t.me/BotFather)
   - Use `/newbot` command and follow instructions
   - Save the bot token

2. **Telegram API Credentials**
   - Visit https://my.telegram.org
   - Login with your phone number
   - Go to "API Development Tools"
   - Create a new application
   - Save `API_ID` and `API_HASH`

3. **MongoDB Database**
   - Create a free cluster at https://mongodb.com/cloud/atlas
   - Get the connection string (URI)
   - Format: `mongodb+srv://username:password@cluster.mongodb.net/`

4. **Razorpay Account** (Critical for payments)
   - Sign up at https://razorpay.com
   - Complete KYC verification
   - Get API Keys from Dashboard → Settings → API Keys
   - Save `Key ID` and `Key Secret`

5. **Hosting Platform**
   - Any platform with 24/7 uptime (DigitalOcean, Railway, Render, Heroku, VPS)
   - Must support Python 3.12+ and Docker (optional)

---

## ⚙️ Configuration Setup

### Step 1: Clone or Download the Project

```bash
git clone <your-repository-url>
cd SUB-MAN-BOT
```

### Step 2: Configure Environment Variables

Edit the `config.py` file or set environment variables:

```python
# Required Telegram Configurations
TG_BOT_TOKEN = "your_bot_token_here"
APP_ID = 12345678  # Your API ID
API_HASH = "your_api_hash_here"
OWNER_ID = 123456789  # Your Telegram User ID

# Database Configuration
DATABASE_URL = "mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority"
DATABASE_NAME = "subsmanage"

# Razorpay Credentials (IMPORTANT)
RAZORPAY_KEY_ID = "rzp_live_xxxxxxxxxxxxx"  # Or rzp_test_ for testing
RAZORPAY_SECRET_KEY = "your_razorpay_secret_key"

# Server Configuration
PORT = "8080"
BASE_URL = "https://your-app-url.com/"  # Your deployed app URL (IMPORTANT for webhooks)

# Admin & Auth Users
ADMINS = "123456789 987654321"  # Space-separated user IDs
AUTHS = "111111111 222222222"   # Authorized users

# Log Channels
LOG_CHAT = "-1001234567890 -1009876543210"  # Space-separated channel/group IDs

# Customization
IMG_URL = "https://your-image-url.jpg"
POWERED_BY = "@YourChannel"
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🗄️ Database Setup

### MongoDB Collections

The bot automatically creates three collections:

1. **users** - Stores user information
   ```json
   {
     "_id": 123456789,
     "joined_at": 1702123456.789
   }
   ```

2. **services** - Stores available services
   ```json
   {
     "_id": ObjectId,
     "service_name": "Mirror Leech Group",
     "description": "Premium features...",
     "group_ids": ["-1001234567890"],
     "plans": {
       "1month": {"price": 30},
       "3month": {"price": 75}
     },
     "created_at": 1702123456.789
   }
   ```

3. **subscriptions** - Tracks active subscriptions
   ```json
   {
     "_id": ObjectId,
     "user_id": 123456789,
     "service_id": "service_object_id",
     "pay_id": "pay_xxxxxxxxxxxxx",
     "expiry": 1702123456.789,
     "added_at": 1702123456.789
   }
   ```

4. **temps** - Temporary payment data
   ```json
   {
     "_id": ObjectId,
     "user_id": 123456789,
     "service_id": "service_object_id",
     "plan_duration": "1month",
     "order_id": "plink_xxxxxxxxxxxxx"
   }
   ```

### Database Configuration

Ensure your MongoDB user has read/write permissions on the database.

---

## 💳 Razorpay Integration

### Step 1: Setup Razorpay Account

1. **Create Account**
   - Visit https://razorpay.com
   - Sign up and complete KYC verification
   - Switch to Test Mode for testing (recommended initially)

2. **Get API Keys**
   - Go to Settings → API Keys
   - Generate new keys if needed
   - Copy `Key ID` (starts with `rzp_test_` or `rzp_live_`)
   - Copy `Key Secret`
   - Add these to `config.py`

### Step 2: Configure Webhook (CRITICAL STEP)

Webhooks are essential for the bot to receive payment notifications.

#### Method 1: Using Razorpay Dashboard

1. **Login to Razorpay Dashboard**
   - Go to https://dashboard.razorpay.com

2. **Navigate to Webhooks**
   - Settings → Webhooks
   - Click "Create New Webhook" or "Add New Webhook"

3. **Configure Webhook URL**
   - **Webhook URL**: `https://your-app-url.com/payment-success`
   - Example: `https://starfish-app-kj4sn.ondigitalocean.app/payment-success`
   - ⚠️ **IMPORTANT**: This must be your actual deployed app URL with HTTPS

4. **Select Events** (Important)
   - Check: `payment.captured`
   - Check: `payment_link.paid`
   - These events notify the bot when payment is successful

5. **Alert Email** (Optional)
   - Add your email for webhook failure notifications

6. **Secret** (Optional but Recommended)
   - Razorpay will generate a webhook secret
   - Save this for signature verification (future enhancement)

7. **Save Webhook**
   - Click "Create Webhook"
   - Status should show "Active"

#### Method 2: Using Razorpay API (Advanced)

```bash
curl -X POST https://api.razorpay.com/v1/webhooks \
  -u rzp_test_xxxxx:your_secret_key \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-app-url.com/payment-success",
    "active": true,
    "events": ["payment.captured", "payment_link.paid"]
  }'
```

### Step 3: Test Webhook Connection

After deployment, test the webhook:

1. **Create a test service** using `/addservice`
2. **Try to purchase** using `/buyservice`
3. **Complete test payment** (use Razorpay test cards)
4. **Check bot logs** for payment confirmation
5. **Verify subscription** is added to database

**Test Card for Razorpay Test Mode:**
- Card Number: `4111 1111 1111 1111`
- CVV: Any 3 digits
- Expiry: Any future date
- OTP: `1234` (for test mode)

### Webhook Endpoints in the Bot

The bot has the following endpoints:

1. **`/` (Root)** - Redirects to your Telegram channel
2. **`/payment-success`** - Handles successful payment callbacks
   - Receives: `razorpay_payment_id`, `razorpay_payment_link_status`, `razorpay_payment_link_id`
   - Validates payment status
   - Creates subscription in database
   - Redirects user back to bot

### Important Notes for Razorpay:

- ✅ Always use **HTTPS** URLs (HTTP won't work in production)
- ✅ Update `BASE_URL` in config.py with your actual deployment URL
- ✅ Test in **Test Mode** before going live
- ✅ Switch to **Live Mode** keys when ready for production
- ✅ Monitor webhook logs in Razorpay dashboard
- ⚠️ Payment links expire after default time (can be configured)
- ⚠️ Failed webhooks will retry automatically (up to 3 times)

---

## 🚀 Deployment Options

### Option 1: Docker Deployment (Recommended)

#### Build and Run

```bash
# Build Docker image
docker build -t sub-man-bot .

# Run container
docker run -d -p 8080:8080 \
  -e TG_BOT_TOKEN="your_token" \
  -e APP_ID="your_app_id" \
  -e API_HASH="your_api_hash" \
  -e DATABASE_URL="your_mongodb_uri" \
  -e RAZORPAY_KEY_ID="your_key" \
  -e RAZORPAY_SECRET_KEY="your_secret" \
  -e BASE_URL="https://your-app-url.com/" \
  --name sub-man-bot \
  sub-man-bot
```

#### Docker Compose (Alternative)

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  bot:
    build: .
    ports:
      - "8080:8080"
    environment:
      - TG_BOT_TOKEN=${TG_BOT_TOKEN}
      - APP_ID=${APP_ID}
      - API_HASH=${API_HASH}
      - DATABASE_URL=${DATABASE_URL}
      - RAZORPAY_KEY_ID=${RAZORPAY_KEY_ID}
      - RAZORPAY_SECRET_KEY=${RAZORPAY_SECRET_KEY}
      - BASE_URL=${BASE_URL}
    restart: unless-stopped
```

Run with:
```bash
docker-compose up -d
```

### Option 2: DigitalOcean App Platform

1. **Connect Repository**
   - Go to DigitalOcean → Apps → Create App
   - Connect your GitHub/GitLab repository

2. **Configure Build**
   - Dockerfile detected automatically
   - Set port to `8080`

3. **Add Environment Variables**
   - Add all variables from config.py
   - Don't forget `BASE_URL` (will be provided by DigitalOcean)

4. **Deploy**
   - Click "Create Resources"
   - Copy the app URL and update `BASE_URL` in environment variables
   - Update Razorpay webhook URL

### Option 3: Railway.app

1. **New Project**
   - Visit https://railway.app
   - Click "New Project" → "Deploy from GitHub"

2. **Add Variables**
   - Go to Variables tab
   - Add all environment variables

3. **Generate Domain**
   - Go to Settings → Generate Domain
   - Copy the URL and set as `BASE_URL`

4. **Deploy**
   - Auto-deploys on git push

### Option 4: VPS (Manual Deployment)

```bash
# Install dependencies
sudo apt update
sudo apt install python3.12 python3-pip git

# Clone repository
git clone <your-repo>
cd SUB-MAN-BOT

# Install requirements
pip3 install -r requirements.txt

# Run with screen/tmux
screen -S subbot
python3 main.py

# Or use systemd service (recommended)
sudo nano /etc/systemd/system/subbot.service
```

**systemd service file:**

```ini
[Unit]
Description=Subscription Management Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/SUB-MAN-BOT
ExecStart=/usr/bin/python3 /path/to/SUB-MAN-BOT/main.py
Restart=always
Environment="TG_BOT_TOKEN=your_token"
Environment="APP_ID=your_id"
Environment="API_HASH=your_hash"
Environment="DATABASE_URL=your_db_uri"
Environment="RAZORPAY_KEY_ID=your_key"
Environment="RAZORPAY_SECRET_KEY=your_secret"
Environment="BASE_URL=https://your-domain.com/"

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable subbot
sudo systemctl start subbot
sudo systemctl status subbot
```

### Post-Deployment Checklist

- [ ] Bot is running and responding to `/start`
- [ ] Web server is accessible (visit `https://your-url.com/`)
- [ ] MongoDB connection is successful
- [ ] Razorpay webhook is configured and active
- [ ] Test payment flow works end-to-end
- [ ] Bot is added as admin in all service groups
- [ ] Log channels receive notifications
- [ ] Environment variables are set correctly

---

## 🤖 Bot Commands

### User Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Start the bot, view welcome message | `/start` |
| `/buyservice` | Browse and purchase available services | `/buyservice` |
| `/mysub` | Check your active subscription details | `/mysub` |
| `/plans` | View all available subscription plans | `/plans` |

### Admin Commands

| Command | Description | Example | Access |
|---------|-------------|---------|--------|
| `/addservice` | Add a new service with plans | `/addservice` | Admins only |
| `/broadcast` | Send message to all users | `/broadcast` | Admins only |
| `/stats` | View bot statistics | `/stats` | Admins only |
| `/addsub` | Manually add subscription to user | `/addsub` | Admins only |
| `/delsub` | Remove user's subscription | `/delsub` | Admins only |

---

## 👨‍💼 Admin Usage Guide

### 1. Adding a New Service

**Command:** `/addservice`

**Process:**
1. Send `/addservice` to the bot
2. Bot asks: "Please provide the service name:"
   - Reply: `Mirror Leech Premium`
   
3. Bot asks: "Please provide a description for the service:"
   - Reply: `Access to premium mirror/leech features with unlimited storage and fast speeds`
   
4. Bot asks: "Now provide the group IDs (space or comma-separated):"
   - Reply: `-1001234567890 -1009876543210`
   - ⚠️ **Important**: Bot must be admin in these groups
   
5. Bot asks: "Now provide the plans in the format `1day:price, 7day:price, 1month:price`:"
   - Reply: `1month:30, 3month:75, 6month:140, 1year:250`
   - Supported durations: `1day`, `7day`, `1week`, `1month`, `3month`, `6month`, `1year`
   
6. Bot confirms: "Service 'Mirror Leech Premium' with plans and description has been successfully added!"

**Example Plan Formats:**
- Daily: `1day:10, 7day:60`
- Weekly: `1week:50, 4week:180`
- Monthly: `1month:30, 3month:80, 6month:150, 1year:280`
- Hourly (for testing): `1hour:5, 24hour:100`
- Minutes (for testing): `30min:1, 60min:2`

### 2. Managing Groups

**Requirements:**
- Bot must be added to all service groups
- Bot must have admin privileges with permissions:
  - ✅ Invite users via link
  - ✅ Ban users (optional, for expired users)
  - ✅ Manage invite links

**Adding Bot to Group:**
1. Go to your Telegram group
2. Add your bot as a member
3. Promote to admin
4. Grant necessary permissions

### 3. Manually Adding Subscriptions

**Command:** `/addsub`

**Process:**
1. Send `/addsub`
2. Bot asks for user ID
3. Bot asks for service selection
4. Bot asks for duration
5. Subscription is added without payment

**Use Cases:**
- Free trials
- Promotional subscriptions
- Customer support compensations
- Testing

### 4. Removing Subscriptions

**Command:** `/delsub`

**Process:**
1. Send `/delsub`
2. Select user
3. Select service
4. Subscription is removed immediately

### 5. Broadcasting Messages

**Command:** `/broadcast`

**Process:**
1. Send `/broadcast`
2. Send the message to broadcast
3. Bot sends to all users in database
4. Shows success/failure statistics

### 6. Viewing Statistics

**Command:** `/stats`

**Shows:**
- Total users
- Total active subscriptions
- Total revenue (if tracked)
- Service-wise breakdown
- Bot uptime

---

## 👥 User Workflow

### Step-by-Step User Journey

#### 1. Discovery & Start
```
User → Sends /start to bot
Bot → Sends welcome message with service info
```

#### 2. Viewing Plans
```
User → Sends /plans
Bot → Shows all available services and pricing
```

#### 3. Purchasing Subscription
```
User → Sends /buyservice
Bot → Shows service selection buttons
User → Clicks on a service
Bot → Shows available plans for that service
User → Clicks on a plan (e.g., "1month - ₹30")
Bot → Generates Razorpay payment link
User → Clicks "Pay Now" button
```

#### 4. Payment Process
```
User → Redirected to Razorpay payment page
User → Completes payment (card/UPI/netbanking)
Razorpay → Sends webhook to bot
Bot → Verifies payment
Bot → Adds subscription to database
User → Redirected back to bot (Telegram deeplink)
```

#### 5. Accessing Service
```
User → Receives success message in bot
Bot → Shows "Generate Link" button
User → Clicks "Generate Link"
Bot → Creates invite link for the group
User → Clicks invite link
User → Joins the premium group
```

#### 6. Checking Subscription
```
User → Sends /mysub
Bot → Shows:
  - Active services
  - Expiry dates
  - Remaining time
  - Payment ID
```

#### 7. Subscription Expiry
```
Bot → Checks subscriptions every 5 minutes
Bot → Detects expired subscription
Bot → Removes subscription from database
Bot → (Optional) Removes user from group
User → Sends /mysub
Bot → Shows "No active subscriptions"
```

---

## 🔧 Troubleshooting

### Common Issues & Solutions

#### 1. Bot Not Responding

**Problem:** Bot doesn't reply to commands

**Solutions:**
- Check if bot is running: `docker ps` or `systemctl status subbot`
- Check logs for errors: `docker logs sub-man-bot`
- Verify `TG_BOT_TOKEN` is correct
- Ensure bot is not blocked by user

#### 2. Payment Not Working

**Problem:** Payment link not generating or payment not confirming

**Solutions:**
- Verify Razorpay credentials are correct
- Check if Razorpay account is activated (not in test mode if using live keys)
- Ensure `BASE_URL` in config matches your deployment URL
- Check webhook is configured correctly
- Test webhook: Razorpay Dashboard → Webhooks → Send Test Webhook
- Check bot logs during payment

**Common Webhook Issues:**
```
Error: Webhook URL returns 404
→ Ensure route.py is loaded correctly
→ Check BASE_URL has no trailing issues

Error: Payment successful but subscription not added
→ Check webhook events include "payment_link.paid"
→ Verify payment_id is being received
→ Check database connection

Error: Invalid signature
→ Currently not implemented, will work anyway
→ Future: verify webhook signature with secret
```

#### 3. Database Connection Failed

**Problem:** Bot can't connect to MongoDB

**Solutions:**
- Verify `DATABASE_URL` is correct
- Check MongoDB cluster is running
- Ensure IP address is whitelisted (or allow all: `0.0.0.0/0`)
- Test connection: `pip install pymongo` then:
  ```python
  from pymongo import MongoClient
  client = MongoClient("your_uri")
  print(client.list_database_names())
  ```

#### 4. User Can't Join Group

**Problem:** Invite link doesn't work or user kicked immediately

**Solutions:**
- Ensure bot is admin in the group
- Check bot has "Invite users via link" permission
- Verify group ID is correct (use `/id` command in group)
- Check if user is banned from group
- Ensure subscription hasn't expired

#### 5. Subscription Not Expiring

**Problem:** Users still have access after expiry

**Solutions:**
- Check if background task is running: Look for "5 mins Checking Function" in logs
- Verify system time is correct (use Asia/Kolkata timezone)
- Manually run: `remove_expired_subscriptions()` function
- Check `expiry` timestamp in database is correct

#### 6. Webhook Not Receiving Data

**Problem:** Razorpay sends webhook but bot doesn't process

**Solutions:**
```python
# Add debug logging to route.py
@routes.get("/payment-success")
async def handle_payment_success(request):
    print("=" * 50)
    print("WEBHOOK RECEIVED")
    print(f"Query params: {request.query}")
    print(f"Headers: {request.headers}")
    print("=" * 50)
    # ... rest of code
```

Check logs for this output when payment completes.

#### 7. Docker Container Exits

**Problem:** Docker container stops after starting

**Solutions:**
```bash
# Check logs
docker logs sub-man-bot

# Common issues:
# - Missing environment variables
# - Port already in use
# - Python import errors

# Run interactively to debug
docker run -it sub-man-bot python3 main.py
```

#### 8. Port Already in Use

**Problem:** Error: "Address already in use"

**Solutions:**
```bash
# Windows (PowerShell)
netstat -ano | findstr :8080
taskkill /PID <PID> /F

# Linux
sudo lsof -i :8080
sudo kill -9 <PID>

# Or change PORT in config.py
PORT = "8081"
```

---

## 📊 Monitoring & Maintenance

### Log Monitoring

**Check logs regularly:**
```bash
# Docker
docker logs -f sub-man-bot

# Systemd
sudo journalctl -u subbot -f

# Look for:
# - Payment confirmations
# - Subscription additions/removals
# - Database connection issues
# - Webhook errors
```

### Database Maintenance

**Regular checks:**
- Monitor database size
- Check for orphaned subscriptions
- Backup database regularly
- Clean up old temp_data entries

**Backup MongoDB:**
```bash
mongodump --uri="your_mongodb_uri" --out=/backup/path
```

### Health Checks

The bot pings itself every 2 minutes:
- Keeps server awake (important for free hosting)
- Verifies web server is running
- Check BASE_URL is accessible

### Security Best Practices

1. **Never commit secrets**
   - Use environment variables
   - Add `.env` to `.gitignore`

2. **Secure Razorpay keys**
   - Use test keys for development
   - Rotate keys periodically
   - Monitor unauthorized access

3. **Database security**
   - Use strong passwords
   - Limit IP access
   - Enable authentication

4. **Bot token security**
   - Revoke old tokens
   - Don't share publicly
   - Monitor bot usage

---

## 🎉 Quick Start Checklist

- [ ] Create Telegram bot with BotFather
- [ ] Get Telegram API credentials
- [ ] Setup MongoDB cluster
- [ ] Create Razorpay account and get API keys
- [ ] Configure config.py with all credentials
- [ ] Deploy bot to hosting platform
- [ ] Get deployment URL and update BASE_URL
- [ ] Configure Razorpay webhook with deployment URL
- [ ] Add bot as admin to service groups
- [ ] Test with `/start` command
- [ ] Add first service with `/addservice`
- [ ] Test complete payment flow
- [ ] Monitor logs for issues

---

## 📞 Support & Resources

### Useful Links
- Telegram Bot API: https://core.telegram.org/bots/api
- Pyrogram Documentation: https://docs.pyrogram.org
- Razorpay Docs: https://razorpay.com/docs/
- MongoDB Docs: https://docs.mongodb.com/

### Getting Help
- Check logs first
- Review this guide thoroughly
- Test in small steps
- Use test mode for Razorpay initially
- Monitor webhook logs in Razorpay dashboard

---

## 📝 Notes

- **Currency**: Currently hardcoded to INR (₹). Modify code for other currencies.
- **Timezone**: Uses Asia/Kolkata (IST). Change in config if needed.
- **Auto-cleanup**: Runs every 5 minutes (300 seconds). Adjust in `helper_func.py`.
- **Payment Links**: Default Razorpay expiry is 30 minutes. Configure in Razorpay settings.
- **Group Limits**: Telegram allows 200,000 members per group. Plan accordingly.

---

## 🚀 Going to Production

Before launching:

1. **Switch to Live Keys**
   - Change Razorpay test keys to live keys
   - Update `RAZORPAY_KEY_ID` and `RAZORPAY_SECRET_KEY`

2. **Update Webhook**
   - Configure webhook in Razorpay **Live Mode**
   - Use same URL: `https://your-url.com/payment-success`

3. **Test Everything**
   - Complete test transaction with real payment
   - Verify subscription is added
   - Check user can join group
   - Test expiry flow

4. **Legal Compliance**
   - Add Terms & Conditions
   - Privacy Policy
   - Refund Policy
   - Contact information

5. **Customer Support**
   - Setup support channel/group
   - Add contact details in bot messages
   - Monitor payment issues

6. **Backup Strategy**
   - Daily database backups
   - Store API keys securely
   - Document all configurations

---

**Version:** 1.0  
**Last Updated:** December 9, 2025  
**Created by:** MadxBotz

For more information or support, contact: @MadxBotz
