# Telegram Outline VPN Key Selling Bot

This Telegram bot allows you to sell Outline VPN keys and accept payments in various cryptocurrencies. It automates the process of generating Outline keys, receiving crypto payments, and delivering the keys to your customers.

## Features

*   **Automated Key Generation:**  Generates new Outline VPN keys using the `outline-cli` tool upon successful payment.
*   **Multiple Cryptocurrency Support:** Accepts payments in Bitcoin (BTC), Ethereum (ETH), and USDT (ERC20).
*   **Price Conversion:** Automatically converts the USD price of a key to the equivalent amount in the chosen cryptocurrency using the CoinGecko API.
*   **Payment Verification:**
    *   **ETH/USDT:**  Monitors your Ethereum wallet for incoming payments using `web3.py` and Infura.
    *   **BTC:** Provides a basic framework for Bitcoin payment verification. You'll need to integrate with a Bitcoin library or payment processor (e.g., BitPay, BTCPay Server) for full automation.
*   **Payment Timeouts:** Cancels pending payments after a configurable timeout period (default: 15 minutes).
*   **Admin Commands:**
    *   `/stats`: Displays statistics about pending and completed payments.
    *   `/markpaid`: Manually marks a payment as paid (useful for manual verification).
*   **User-Friendly Interface:** Provides a simple and intuitive interface for users to purchase keys.

## Prerequisites

1.  **Outline VPN Server:**
    *   You need a running Outline VPN server.
    *   Install the `outline-cli` tool on your server:
        ```bash
        sudo bash -c "$(wget -qO- https://raw.githubusercontent.com/Jigsaw-Code/outline-server/master/src/server_manager/install_scripts/install_server.sh)"
        ```

2.  **Telegram Bot Token:**
    *   Create a new bot using BotFather on Telegram and get your bot token.

3.  **Ethereum Node (for ETH/USDT):**
    *   You'll need access to an Ethereum node. You can use a service like Infura (recommended) or run your own node.

4.  **Bitcoin Node/Payment Processor (for BTC):**
    *   **Option 1 (Recommended):** Integrate with a Bitcoin payment processor like BitPay, BTCPay Server, or Coinbase Commerce. This handles payment verification for you.
    *   **Option 2:** Run a full Bitcoin node and use a library like `python-bitcoinlib` to monitor for incoming transactions.

5.  **Python 3.7+:** Ensure you have Python 3.7 or a later version installed.

6.  **Dependencies:** Install the required Python packages:

    ```bash
    pip install pyTelegramBotAPI python-dotenv pycoingecko web3
    ```

## Setup and Configuration

1.  **Clone the Repository:**

    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Environment Variables:**

    *   Create a `.env` file in the root directory of the project.
    *   Fill in the following variables in your `.env` file:

        ```
        BOT_TOKEN=your_telegram_bot_token
        OUTLINE_API_URL=your_outline_server_api_url  # e.g., https://your-server-ip:port/your-access-key
        ADMIN_CHAT_ID=your_telegram_chat_id
        PRICE_USD=5  # Price of a key in USD
        PAYMENT_TIMEOUT=900 # Payment timeout in seconds (default: 900 seconds = 15 minutes)
        ACCEPTED_COINS="BTC,ETH,USDT" # Comma-separated list of accepted cryptocurrencies

        # Ethereum (if accepting ETH/USDT)
        ETH_NODE_URL=your_ethereum_node_url # e.g., https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID
        ETH_WALLET_ADDRESS=your_ethereum_wallet_address
        USDT_CONTRACT_ADDRESS=0xdAC17F958D2ee523a2206206994597C13D831ec7 # USDT on Mainnet, change if necessary

        # Bitcoin (if accepting BTC) - Replace with your payment processor integration
        BTC_WALLET_ADDRESS=your_bitcoin_receiving_address
        ```

3.  **Bitcoin Payment Verification (Important):**

    *   **If using a payment processor (BitPay, BTCPay, etc.):**
        *   Modify the `check_btc_payment` function in the Python script to integrate with your chosen processor's API.
        *   You'll need to handle payment notifications (webhooks) from the processor and update the payment status in `data.json` or your database.
    *   **If using a Bitcoin library and your own node:**
        *   Replace the placeholder code in `check_btc_payment` with logic to monitor the blockchain for transactions to your `BTC_WALLET_ADDRESS` using a library like `python-bitcoinlib`.

4.  **USDT Contract Address:**

    *   The `USDT_CONTRACT_ADDRESS` is set to the mainnet USDT contract by default. If you are accepting USDT on a different network (e.g., Binance Smart Chain), update this address accordingly.

## Running the Bot

1.  **Start the bot:**

    ```bash
    python your_bot_script.py  # Replace 'your_bot_script.py' with the actual filename
    ```

2.  **Interact with the bot on Telegram:**

    *   Find your bot using its username (set in BotFather).
    *   Use the `/start` or `/help` command to get started.

## Commands

*   `/start`, `/help`: Displays a welcome message and instructions.
*   `/buy`: Initiates the process of purchasing an Outline VPN key.
*   `/stats` (Admin only): Shows statistics about pending and completed payments.
*   `/markpaid [payment_id]` (Admin only): Manually marks a payment as paid.

## Data Storage

*   The bot uses a `data.json` file to store pending payment information.
*   **For production, it's highly recommended to use a database like PostgreSQL or MongoDB for more robust data management.**

## Security Considerations

*   **Environment Variables:** Store sensitive information (API keys, tokens, wallet addresses) securely in environment variables, **not** directly in the code.
*   **Error Handling:** Implement thorough error handling to prevent crashes and log errors appropriately.
*   **Input Validation:** Sanitize all user inputs to prevent potential security vulnerabilities.
*   **Rate Limiting:** Consider rate limiting to prevent abuse.
*   **Transaction Monitoring:** Monitor your cryptocurrency wallets for any suspicious activity.
*   **Auditing:** Keep detailed logs of all transactions and bot actions.
*   **Code Review:** Before deploying, have someone else review your code for security vulnerabilities.
*   **Dependency Updates:** Regularly update your dependencies to patch known vulnerabilities.

## Further Development

*   **Database Integration:** Replace `data.json` with a database (PostgreSQL, MongoDB).
*   **Full Bitcoin Automation:** Implement automated Bitcoin payment verification.
*   **More Cryptocurrencies:** Add support for other cryptocurrencies.
*   **Improved UI/UX:** Enhance the user interface and user experience.
*   **Subscription Management:** Allow users to purchase recurring subscriptions.
*   **Usage Statistics:** Provide users with their VPN usage data.
*   **Advanced Admin Features:** Add more admin commands for managing users, keys, and payments.
*   **Testing:** Write comprehensive unit and integration tests.
*   **Refactoring:** Refactor the code to make it more modular and maintainable as the bot grows.
*   **KYC/AML:** If handling larger amounts of money, consider implementing Know Your Customer (KYC) and Anti-Money Laundering (AML) procedures.

## Disclaimer

This code is provided as a starting point and for educational purposes. It is your responsibility to ensure the security and reliability of your bot before deploying it to production. The author is not responsible for any financial losses or security breaches that may occur. Use this code at your own risk.
