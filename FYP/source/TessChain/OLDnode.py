# from uuid import uuid4

from blockchain import Blockchain
from utility.verificationHelper import VerficationHelper
from wallet import Wallet

class Node:
     
    def __init__(self):
        self.wallet = Wallet()
        self.blockchain = None

    def get_transaction_value(self):
        """ Returns the inputted transaction value of the user as float. """
        tx_recipient = input('Enter the recipient of the transaction:')
        tx_amount = float(input('Your transaction amount please: '))
        print('-' * 30)
        return (tx_recipient,tx_amount)

    def get_user_choice(self):
        user_input = input('Your choice: ')
        return user_input
  

    def print_blocks(self):
        """ Prints the blockchain, one block after the other"""
        for block in self.blockchain.chain:
            print('Outputting block')
            print(block)
            print('-' * 80)
    
    def listenForInput(self):
        is_waiting = True

        while is_waiting:
            if not self.blockchain == None:
                """ Get the input from the user to either add a new transaction or print the blockchain"""
                print('1: Add a new transaction value')
                print('2: Mine a new block')
                print('3: Output the blocks')
                print('4: Check transactions validity')
                print('q: Quit')
                print('-' * 30)

                user_choice = self.get_user_choice()

                if user_choice == '1':
                    tx_data = self.get_transaction_value()
                    recipient, amount = tx_data

                    signature = self.wallet.sign_trax(self.wallet.public_key, recipient, amount)
                    if self.blockchain.add_trax(recipient,self.wallet.public_key, signature,amount = amount):
                        print('Transaction added to open transactions :') 
                        print(self.blockchain.get_open_trax())

                    else:
                        print('Transaction failed!')

                elif user_choice == '2':
                    if not self.blockchain.mine_block():
                        print('The signature doesnot match')

                elif user_choice == '3':
                    self.print_blocks()

                elif user_choice == '4':
                    if(VerficationHelper.verify_allTrax(self.blockchain.get_open_trax(),self.blockchain.get_balance)):
                        print('All transactions are valid')

                    else:
                        print('There are invalid transaction!')

                elif user_choice == 'q':
                    is_waiting = False

                else:
                    print('Invalid input! ')

                if not VerficationHelper.verify_chain(self.blockchain.chain):
                    self.print_blocks()
                    print('Invalid blockchain')
                    break

                print('Balance of {}: {:6.2f}'.format(self.wallet.public_key,self.blockchain.get_balance()))

            else:
                print('c: To create a wallet')
                print('l: To load a wallet')
                print('-' * 30)

                user_choice = self.get_user_choice()
                
                if user_choice == 'c':
                    self.wallet.create_keys()
                    self.blockchain = Blockchain(self.wallet.public_key) 
                
                elif user_choice == 'l':
                    self.wallet.load_keys()
                    self.blockchain = Blockchain(self.wallet.public_key)

        else:
            print('User left!')

        print('Done!')

node = Node()
node.listenForInput()