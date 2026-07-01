# Personal Finance Manager

A comprehensive, secure, and user-friendly desktop application for managing personal budgets, tracking expenditures, planning card installments, analyzing asset portfolios with live market updates, and generating analytical financial reports.

## Student Information
- **Student Name/Surname:** İlhami Arda Karaman
- **Student ID:** 202413709060
- **Project Topic:** Personal Finance Desktop Application

---

## Key Features

1. **Transaction Ledger:** Add and categorize incomes and expenses, with native support for monthly recurring transactions.
2. **Credit Card Installments:** Track credit card purchases, plan monthly payments, and automatically calculate remaining card limits.
3. **Asset Portfolio:** Manage investments (stocks, gold, silver, etc.) with real-time price tracking integrated via Yahoo Finance (`yfinance`) API for automated profit/loss calculation.
4. **Debt & Receivable Book:** Log outstanding debts and personal loans.
5. **Saving Goals:** Create progress-tracked saving goals with graphical indicator bars.
6. **Detailed Reports (Excel/CSV):** Export complete transaction history and financial status tables to Excel-compatible CSV formats.
7. **Executive Summary (PDF):** Generate professional, print-ready PDF summaries of monthly budgets and assets.
8. **Multi-profile & Security:** Password-encrypted local user databases, secure login flows, session countdown timer, and profile recovery security questions.
9. **Localization & Themes:** Full Turkish/English translation support and Dark/Light UI themes.

---

## Installation & Running

### Requirements
The application runs on Python 3 and requires several external dependencies. 

> [!NOTE]
> The helper script `run.bat` will automatically check your Python environment, verify packages, and install dependencies from `requirements.txt` via `pip` if they are missing.

### 1. Windows Run (Recommended)
1. Double-click **[run.bat](run.bat)** in the root folder.
2. The application will initialize, check dependencies, and launch in the background.

### 2. Manual Run (Command Line)
1. Open your terminal in the project directory and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the Python application:
   ```bash
   python personal_finance.py
   ```
