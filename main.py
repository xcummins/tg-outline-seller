import telebot
import os
import json
import subprocess
import time
import asyncio
from pycoingecko import CoinGeckoAPI
from utf-cleaner import UTFStringCleaner
from web3 import Web3

# --- Configuration ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")  # Get your bot token from BotFather
OUTLINE_API_URL = os.environ.get("OUTLINE_API_URL")  # Your Outline server API URL (e.g., "https://your-server-ip:port/your-access-key")
ADMIN_CHAT_ID = int(os.environ.get("ADMIN_CHAT_ID"))  # Your Telegram chat ID for admin notifications
PRICE_USD = 5  # Price of a key in USD
PAYMENT_TIMEOUT = 900  # Payment timeout in seconds (15 minutes)
ACCEPTED_COINS = ["BTC", "ETH", "USDT"] # Accepted coins symbols on CoinGecko

# --- Ethereum Configuration (If accepting ETH or ERC20 tokens like USDT) ---
ETH_NODE_URL = os.environ.get("ETH_NODE_URL") # Infura or your own node (e.g., "https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID")
ETH_WALLET_ADDRESS = os.environ.get("ETH_WALLET_ADDRESS")  # Your Ethereum wallet address to receive payments
USDT_CONTRACT_ADDRESS = "0xdAC17F958D2ee523a2206206994597C13D831ec7" # USDT Contract address on Mainnet (Change if needed for different networks)
# Minimal ABI for checking ERC20 balance (balanceOf function)
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
]
# --- Bitcoin Configuration (If accepting BTC) ---
# You'll likely need to integrate with a Bitcoin payment processor API like:
# - BitPay (https://bitpay.com/api/)
# - BTCPay Server (https://btcpayserver.org/)
# - Coinbase Commerce (https://commerce.coinbase.com/)
# For simplicity in this example, we'll demonstrate a basic address generation and manual verification process.
BTC_WALLET_ADDRESS = os.environ.get("BTC_WALLET_ADDRESS") # Your receiving BTC Address. Replace with address generation logic using your preferred method
# --- Initialize ---
bot = telebot.TeleBot(BOT_TOKEN)
cleaner = UTFStringCleaner()
cg = CoinGeckoAPI()
if ETH_NODE_URL:
  w3 = Web3(Web3.HTTPProvider(ETH_NODE_URL))
  usdt_contract = w3.eth.contract(address=USDT_CONTRACT_ADDRESS, abi=ERC20_ABI) if ETH_NODE_URL and USDT_CONTRACT_ADDRESS else None

# --- Data Storage (Using a JSON file for simplicity) ---
def load_data():
    try:
        with open("data.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"pending_payments": {}}

def save_data(data):
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

# --- Outline API Interaction ---
def create_outline_key():
    try:
        # Use outline-cli to create a new key (assuming it's installed)
        result = subprocess.run(
            ["outline-cli", "createKey", OUTLINE_API_URL],
            capture_output=True,
            text=True,
            check=True,
        )
        key_data = json.loads(result.stdout)
        return key_data["accessUrl"]
    except subprocess.CalledProcessError as e:
        print(f"Error creating Outline key: {e}")
        bot.send_message(ADMIN_CHAT_ID, f"Error creating Outline key: {e.stderr}")
        return None

# --- Helper Functions ---
def get_crypto_price(crypto_symbol):
  """Gets the current price of a cryptocurrency in USD from CoinGecko."""
  try:
      price_data = cg.get_price(ids=crypto_symbol.lower(), vs_currencies="usd")
      return price_data[crypto_symbol.lower()]["usd"]
  except Exception as e:
      print(f"Error getting {crypto_symbol} price: {e}")
      return None
async def check_btc_payment(payment_id, amount_btc, address):
  """Placeholder for checking Bitcoin payment status."""
  # In a real implementation, you would use a Bitcoin library or payment processor API
  # to check for incoming transactions to the generated address with the correct amount.
  data = load_data()
  payment_data = data["pending_payments"].get(payment_id)
  if not payment_data:
      return  # Payment ID not found

  bot.send_message(payment_data["chat_id"], f"Checking for your BTC payment of {amount_btc} BTC to {address}...")
  
  # Simulate checking for payment for demonstration.
  # Replace this with actual Bitcoin payment verification.
  await asyncio.sleep(60)  # Wait for 1 minute to simulate initial check
  # ... (Implementation to check for BTC transaction on the blockchain) ...
  
  # For this example, let's assume we manually verify the payment
  # and update the status in data.json.

  if payment_data.get("status") == "paid":
    return

  bot.send_message(payment_data["chat_id"], f"BTC payment not yet received. I will keep checking.")
  
  # Check every 5 minutes, for example: 
  await asyncio.sleep(300)
  if payment_data.get("status") == "paid":
    return
  bot.send_message(payment_data["chat_id"], f"Still waiting for BTC payment.")


async def check_eth_payment(payment_id, amount_eth, address):
  """Checks for Ethereum payment status."""
  data = load_data()
  payment_data = data["pending_payments"].get(payment_id)
  if not payment_data:
      return  # Payment ID not found

  bot.send_message(payment_data["chat_id"], f"Checking for your ETH payment of {amount_eth} ETH to {address}...")
  
  try:
    start_balance = w3.eth.get_balance(ETH_WALLET_ADDRESS)
    await asyncio.sleep(60)
    current_balance = w3.eth.get_balance(ETH_WALLET_ADDRESS)
    
    if current_balance > start_balance:
      received_eth = w3.from_wei(current_balance - start_balance, 'ether')
      if received_eth >= amount_eth:
        payment_data["status"] = "paid"
        save_data(data)
        await fulfill_order(payment_id)
      else:
        bot.send_message(payment_data["chat_id"], f"Insufficient ETH received. Expected: {amount_eth}, Received: {received_eth}")  
    else:
        bot.send_message(payment_data["chat_id"], f"ETH payment not yet received. I will keep checking.")
        await asyncio.sleep(300) # Check after 5 minutes
        current_balance = w3.eth.get_balance(ETH_WALLET_ADDRESS)
        if current_balance > start_balance:
          received_eth = w3.from_wei(current_balance - start_balance, 'ether')
          if received_eth >= amount_eth:
            payment_data["status"] = "paid"
            save_data(data)
            await fulfill_order(payment_id)
          else:
            bot.send_message(payment_data["chat_id"], f"Insufficient ETH received. Expected: {amount_eth}, Received: {received_eth}")  
  except Exception as e:
      print(f"Error checking ETH payment: {e}")
      bot.send_message(payment_data["chat_id"], "Error checking ETH payment. Please contact support.")

async def check_usdt_payment(payment_id, amount_usdt, address):
    """Checks for USDT payment status."""
    data = load_data()
    payment_data = data["pending_payments"].get(payment_id)
    if not payment_data:
        return  # Payment ID not found
    bot.send_message(payment_data["chat_id"], f"Checking for your USDT payment of {amount_usdt} USDT to {address}...")
    
    try:
        start_balance = usdt_contract.functions.balanceOf(ETH_WALLET_ADDRESS).call()
        await asyncio.sleep(60)
        current_balance = usdt_contract.functions.balanceOf(ETH_WALLET_ADDRESS).call()
        
        if current_balance > start_balance:
            received_usdt = current_balance - start_balance
            received_usdt_decimal = received_usdt / (10 ** 6) # USDT has 6 decimals
            if received_usdt_decimal >= amount_usdt:
                payment_data["status"] = "paid"
                save_data(data)
                await fulfill_order(payment_id)
            else:
                bot.send_message(payment_data["chat_id"], f"Insufficient USDT received. Expected: {amount_usdt}, Received: {received_usdt_decimal}")
        else:
            bot.send_message(payment_data["chat_id"], "USDT payment not yet received. I will keep checking.")
            await asyncio.sleep(300)
            current_balance = usdt_contract.functions.balanceOf(ETH_WALLET_ADDRESS).call()
            if current_balance > start_balance:
              received_usdt = current_balance - start_balance
              received_usdt_decimal = received_usdt / (10 ** 6)
              if received_usdt_decimal >= amount_usdt:
                payment_data["status"] = "paid"
                save_data(data)
                await fulfill_order(payment_id)
              else:
                bot.send_message(payment_data["chat_id"], f"Insufficient USDT received. Expected: {amount_usdt}, Received: {received_usdt_decimal}")
    except Exception as e:
        print(f"Error checking USDT payment: {e}")
        bot.send_message(payment_data["chat_id"], "Error checking USDT payment. Please contact support.")

async def fulfill_order(payment_id):
  """Creates an Outline key and sends it to the user."""
  data = load_data()
  payment_data = data["pending_payments"].get(payment_id)

  if not payment_data:
      return

  chat_id = payment_data["chat_id"]

  bot.send_message(chat_id, "Payment confirmed! Creating your Outline VPN key...")
  outline_key = create_outline_key()

  if outline_key:
      bot.send_message(chat_id, f"Your Outline VPN key is:\n\n`{outline_key}`", parse_mode="Markdown")
      bot.send_message(chat_id, "Enjoy your VPN access! If you have any questions, type /help.")
      bot.send_message(ADMIN_CHAT_ID, f"New key sold to user: {chat_id} Payment ID: {payment_id}")
  else:
      bot.send_message(chat_id, "There was an error creating your key. Please contact support.")

# --- Bot Handlers ---
@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    bot.reply_to(
        message,
        "Welcome to the Outline VPN Key Bot!\n\n"
        "I can sell you an Outline VPN key for fast and secure internet access.\n\n"
        f"The price of a key is ${PRICE_USD}.\n\n"
        "To buy a key, use the /buy command.\n"
        "Accepted cryptocurrencies: " + ", ".join(ACCEPTED_COINS)
    )

@bot.message_handler(commands=["buy"])
def buy_key(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=len(ACCEPTED_COINS))
    buttons = []
    for coin in ACCEPTED_COINS:
      buttons.append(telebot.types.InlineKeyboardButton(coin, callback_data=f"pay_{coin}"))
    markup.add(*buttons)

    bot.reply_to(message, "Choose your payment method:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_"))
def payment_choice_callback(call):
    """Handles payment method selection."""
    chat_id = call.message.chat.id
    payment_method = call.data.split("_")[1]
    payment_id = str(time.time())  # Unique ID for this payment

    data = load_data()
    data["pending_payments"][payment_id] = {
        "chat_id": chat_id,
        "payment_method": payment_method,
        "status": "pending",
        "time_created": int(time.time())
    }

    if payment_method == "BTC":
        price_btc = PRICE_USD / get_crypto_price("BTC")
        data["pending_payments"][payment_id]["amount"] = price_btc
        data["pending_payments"][payment_id]["address"] = BTC_WALLET_ADDRESS
        
        bot.edit_message_text(f"Please send exactly {price_btc:.8f} BTC to this address:\n\n`{BTC_WALLET_ADDRESS}`\n\n"
                              f"I will create your key after the payment is confirmed. Payment ID: `{payment_id}`",
                              chat_id=chat_id,
                              message_id=call.message.message_id,
                              parse_mode="Markdown")
        save_data(data)
        asyncio.create_task(check_btc_payment(payment_id, price_btc, BTC_WALLET_ADDRESS))


    elif payment_method == "ETH":
      if not ETH_NODE_URL:
        bot.send_message(chat_id, "ETH payments are not currently configured.")
        return
      price_eth = PRICE_USD / get_crypto_price("ETH")
      data["pending_payments"][payment_id]["amount"] = price_eth
      data["pending_payments"][payment_id]["address"] = ETH_WALLET_ADDRESS

      bot.edit_message_text(f"Please send exactly {price_eth:.8f} ETH to this address:\n\n`{ETH_WALLET_ADDRESS}`\n\n"
                            f"I will create your key after the payment is confirmed. Payment ID: `{payment_id}`",
                            chat_id=chat_id,
                            message_id=call.message.message_id,
                            parse_mode="Markdown")
      save_data(data)
      asyncio.create_task(check_eth_payment(payment_id, price_eth, ETH_WALLET_ADDRESS))
      

    elif payment_method == "USDT":
      if not ETH_NODE_URL or not USDT_CONTRACT_ADDRESS:
        bot.send_message(chat_id, "USDT payments are not currently configured.")
        return
      price_usdt = PRICE_USD / get_crypto_price("USDT") # Should be very close to 1
      data["pending_payments"][payment_id]["amount"] = price_usdt
      data["pending_payments"][payment_id]["address"] = ETH_WALLET_ADDRESS
      bot.edit_message_text(f"Please send exactly {price_usdt:.2f} USDT (ERC20) to this address:\n\n`{ETH_WALLET_ADDRESS}`\n\n"
                            f"Make sure to send USDT on the **Ethereum Network (ERC20)**. "
                            f"I will create your key after the payment is confirmed. Payment ID: `{payment_id}`",
                            chat_id=chat_id,
                            message_id=call.message.message_id,
                            parse_mode="Markdown")
      save_data(data)
      asyncio.create_task(check_usdt_payment(payment_id, price_usdt, ETH_WALLET_ADDRESS))
    else:
        bot.edit_message_text("Invalid payment method.", chat_id=chat_id, message_id=call.message.message_id)


async def check_payment_timeouts():
  """Checks for timed-out payments and cancels them."""
  while True:
      data = load_data()
      now = int(time.time())
      for payment_id, payment_data in list(data["pending_payments"].items()):
          if payment_data["status"] == "pending" and now - payment_data["time_created"] > PAYMENT_TIMEOUT:
              chat_id = payment_data["chat_id"]
              bot.send_message(chat_id, f"Payment ID {payment_id} has expired. Please use /buy to start a new order.")
              del data["pending_payments"][payment_id]

      save_data(data)
      await asyncio.sleep(60)  # Check every minute

# --- Admin Commands ---
@bot.message_handler(commands=["stats"])
def get_stats(message):
    if message.chat.id == ADMIN_CHAT_ID:
        data = load_data()
        pending_count = len([p for p in data["pending_payments"].values() if p["status"] == "pending"])
        paid_count = len([p for p in data["pending_payments"].values() if p["status"] == "paid"])
        
        bot.reply_to(message, f"Pending payments: {pending_count}\nCompleted Payments: {paid_count}")

@bot.message_handler(commands=["markpaid"])
def mark_as_paid(message):
  """Manually marks a payment as paid (for BTC or other manual verification)."""
  if message.chat.id == ADMIN_CHAT_ID:
      try:
          payment_id = message.text.split(" ")[1]
          data = load_data()
          if payment_id in data["pending_payments"]:
              data["pending_payments"][payment_id]["status"] = "paid"
              save_data(data)
              asyncio.create_task(fulfill_order(payment_id))
              bot.reply_to(message, f"Payment ID {payment_id} marked as paid.")
          else:
              bot.reply_to(message, "Payment ID not found.")
      except IndexError:
          bot.reply_to(message, "Please provide a payment ID. Usage: /markpaid [payment_id]")

# --- Polling and Background Tasks ---
async def main():
  # Start the background task for checking payment timeouts
  asyncio.create_task(check_payment_timeouts())

  # Start polling for Telegram updates
  print("Bot started...")
  await bot.polling(none_stop=True)

if __name__ == "__main__":
  asyncio.run(main())
