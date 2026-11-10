import mysql.connector
from decimal import Decimal 
try:
    con = mysql.connector.connect(
        host="localhost",
        user="root",
        password="durgam@2003",
        database="bank_management_system"
    )
    if con.is_connected():
        print("connected to MySQL successfully!")

        #Display database tables
        cursor = con.cursor()
        cursor.execute("Show Tables")
        print("tables in the database:")
        for table in cursor.fetchall():
            print(table[0])

        cursor.close()

        #bank class
        class Bank:
            def __init__(self,con):
                self.con = con

            #Create a bank account
            def create_account(self):
                cursor=None

                try:
                    customer_name=input("\nEnter customer name:").strip()

                    if not customer_name:
                        print("customer name cannot be empty")
                        return
                    
                    initial_deposit=float(input("Enter initial deposit:"))

                    if not 0 < initial_deposit < 10000000000:
                        print("Enter a valid positive deposit")
                        return   
                    
                    cursor=self.con.cursor()

                    #Generate account number 
                    cursor.execute(
                        """
                        select COALESCE(max(account_number), 100000) + 1
                        FROM accounts
                        """
                    )
                    account_number = cursor.fetchone()[0]

                    #Insert account details
                    cursor.execute(
                        """
                        insert into accounts
                        (account_number, customer_name, balance)
                        values (%s, %s, %s)
                        """,(account_number,customer_name,initial_deposit)
                    ) 
                    #Record the initial deposit
                    cursor.execute(
                         """
                        insert into transactions
                        (account_number, transaction_type,
                         amount, balance_after)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (account_number,"Initial Deposit", initial_deposit,initial_deposit
                        )
                    )
                    #Save both database changes
                    self.con.commit()
                    print("\nAccount created successfully!")
                    print("Account Number:", account_number)
                    print("Customer Name:", customer_name)
                    print("Initial Balance:",f"{initial_deposit:.2f}")
                except ValueError:
                    print(
                        "Invalid input! Enter a valid numeric deposit."
                    )
                except mysql.connector.Error as e:
                    self.con.rollback()
                    print("Database error:", e)
                finally:
                    if cursor is not None:
                        cursor.close()

            #Check account balance
            def check_balance(self):
                cursor=None
                try:
                    account_number = int(input("\nEnter account number:"))
                    cursor = self.con.cursor()
                    cursor.execute("""
                        select customer_name,balance
                        from accounts
                        where account_number = %s
                    """, (account_number,))
                    result = cursor.fetchone()

                    if result:
                        print("\nAccount Details")
                        print("Account Number:", account_number)
                        print("Customer Name:", result[0])
                        print("Current Balance:", f"{result[1]:.2f}")    
                    else:
                        print("Account not found.")

                except mysql.connector.Error as e:
                    print("Database error:", e)

                finally:
                    if cursor is not None:
                        cursor.close()  

            #Deposit money
            def deposit_money(self):
                cursor=None
                try:
                    account_number = int(input("\nEnter account number: "))
                    amount = Decimal(input("Enter deposit amount: "))
                    if not 0 < amount < 10000000000:
                        print("Enter a valid positive amount.")
                        return
                    cursor = self.con.cursor()

                    #Check whether the account exists
                    cursor.execute("""select balance from accounts where account_number = %s""", (account_number,))
                    result = cursor.fetchone()
                    if result is None:
                        print("Account not found.")
                        return
                    
                    # Calculate the new balance
                    new_balance = result[0] + amount

                    # Update account balance
                    cursor.execute("""UPDATE accounts SET balance = %s WHERE account_number = %s """,
                    (new_balance, account_number))
                    
                    # Store the deposit transaction
                    cursor.execute("""insert into transactions(account_number, transaction_type,amount,
                    balance_after) values (%s, %s, %s, %s)""",(account_number,"Deposit",amount,new_balance))

                    self.con.commit()
                    print("\nDeposit successful!")
                    print("Deposited Amount:", f"{amount:.2f}")
                    print("Updated Balance:", f"{new_balance:.2f}")
                except ValueError:
                    print("Invalid input! Enter valid numeric values.")
                except mysql.connector.Error as e:
                    self.con.rollback() 
                    print("Database error:", e)
                finally:
                    if cursor is not None:
                        cursor.close()
            
            #Withdraw money
            def withdraw_money(self):
                cursor = None
                try:
                    account_number = int(input("\nEnter account number: "))
                    amount = Decimal(input("Enter withdrawal amount: "))
                    if not amount.is_finite() or amount <= 0:
                        print("Enter a valid positive amount.")
                        return
                    cursor = self.con.cursor()
                    #Check account balance
                    cursor.execute("""select balance from accounts where account_number = %s""",(account_number,))
                    result = cursor.fetchone()

                    if result is None:
                        print("Account not found.")
                        return
                    current_balance = result[0]

                    #Check sufficient balance
                    if amount > current_balance:
                        print("Insufficient balance!")
                        print("Available Balance:", f"{current_balance:.2f}")
                        return
                    new_balance = current_balance - amount
                    
                    #Update account balance
                    cursor.execute("""update accounts set balance = %s where account_number = %s""", 
                    (new_balance, account_number))
                    
                    # Record withdrawal transaction
                    cursor.execute("""insert into transactions(account_number, transaction_type,amount, balance_after)
                    values (%s, %s, %s, %s)""", (account_number,"Withdrawal",amount,new_balance))
                    
                    self.con.commit()
                    print("\nWithdrawal successful!")
                    print("Withdrawn Amount:", f"{amount:.2f}")
                    print("Remaining Balance:", f"{new_balance:.2f}")
                
                except (ValueError, ArithmeticError):
                    print("Invalid amount or account number.")
                except mysql.connector.Error as e:
                    self.con.rollback()
                    print("Database error:", e)
                finally:
                    if cursor is not None:
                        cursor.close()
            
            #Credit simple interest
            def credit_interest(self):
                cursor = None
                try:
                    account_number = int(input("\nEnter account number: "))
                    rate = Decimal(input("Enter annual interest rate (%): "))
                    years = Decimal(input("Enter time period (years): "))
                    
                    if (not rate.is_finite()
                        or not years.is_finite()
                        or rate < 0
                        or years <= 0
                        or rate > 100
                        or years > 100
                    ):
                        print("Enter a valid interest rate and time period.")
                        return

                    cursor = self.con.cursor()

                    # Get current account balance
                    cursor.execute("""select balance from accounts where account_number = %s""", (account_number,))

                    result = cursor.fetchone()

                    if result is None:
                        print("Account not found.")
                        return

                    principal = result[0]

                    #Calculate simple interest
                    interest = (
                        principal * rate * years / Decimal("100")
                    ).quantize(Decimal("0.01"))

                    if interest <= 0:
                        print("Interest amount is zero. No credit made.")
                        return

                    new_balance = principal + interest

                    # Update account balance
                    cursor.execute("""update accounts set balance = %s where account_number = %s""",
                    (new_balance, account_number))

                    #Record interest transaction
                    cursor.execute("""insert into transactions(account_number, transaction_type,amount, balance_after)values (%s, %s, %s, %s)""", 
                    (account_number,"Interest",interest,new_balance)) 

                    self.con.commit()
                    print("\nInterest credited successfully!")
                    print("Interest Amount:", f"{interest:.2f}")
                    print("Updated Balance:", f"{new_balance:.2f}")

                except (ValueError, ArithmeticError):
                    print("Invalid input. Please enter valid numeric values.")

                except mysql.connector.Error as e:
                    self.con.rollback()
                    print("Database error:", e)

                finally:
                    if cursor is not None:
                        cursor.close()
            
            #Display transaction history
            def transaction_history(self):
                cursor = None
                try:
                    account_number = int(input("\nEnter account number: "))
                    cursor = self.con.cursor()
                    
                    #Check whether the account exists
                    cursor.execute("""select customer_name from accounts where account_number = %s""",
                    (account_number,))
                    
                    account = cursor.fetchone()
                    if account is None:
                        print("Account not found.")
                        return
                    print("\nTransaction History")
                    print("Customer Name:", account[0])
                    print("Account Number:", account_number)

                    # Retrieve all transactions
                    cursor.execute("""select transaction_type, amount,transaction_date, balance_after from transactions
                    where account_number = %s order by transaction_date, transaction_id """, (account_number,))

                    transactions = cursor.fetchall()

                    if not transactions:
                        print("No transactions found.")
                        return

                    print("-" * 85)
                    print(f"{'Type':<20}"f"{'Amount':>12}"f"{'Date':>25}"f"{'Balance':>15}"
                    )
                    print("-" * 85)

                    for transaction in transactions:
                        transaction_type, amount, date, balance = transaction

                        print(
                            f"{transaction_type:<20}"
                            f"{amount:>12.2f}"
                            f"{str(date):>25}"
                            f"{balance:>15.2f}"
                        )

                    print("-" * 85)

                except ValueError:
                    print("Invalid input! Enter a valid account number.")

                except mysql.connector.Error as e:
                    print("Database error:", e)

                finally:
                    if cursor is not None:
                        cursor.close()                            
        #Create bank object 
        bank = Bank(con)

       #Menu-driven program
        while True:
            print("\n===== BANK MANAGEMENT SYSTEM =====")
            print("1. Create Account")
            print("2. Check Balance")
            print("3. Deposit Money")
            print("4. Withdraw Money")
            print("5. Credit Simple Interest")
            print("6. Transaction History")
            print("7. Exit")

            try:
                choice = int(input("Enter your choice:"))

                if choice == 1:
                    bank.create_account()

                elif choice == 2:
                    bank.check_balance()

                elif choice == 3:
                    bank.deposit_money()

                elif choice == 4:
                    bank.withdraw_money()

                elif choice == 5:  
                    bank.credit_interest()

                elif choice == 6: 
                    bank.transaction_history()

                elif choice == 7:    
                    print("Thank you for using our Bank System!")
                    break

                else:
                    print("Invalid choice! Select 1 to 7.")

            except ValueError:
                print("Please enter a number from 1 to 7.")

except mysql.connector.Error as e:
    print("Database connection failed:", e)

finally:
    if 'con' in locals() and con.is_connected():
        con.close()
