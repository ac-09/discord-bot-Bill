# discord-bot-Bill

Bill (or Billl) is your friendly Discord bot to keep track of who owes how much to others. Data can be saved on replit's in-built database (default) or in a local `.json` file. This is toggled by changing the `JSON_DATABASE` parameter in `main.py`.

A server profile is created for the user when the user first uses the bot in a new server, and saves the user's value and account details. A user profile is also created if the user does not already have one (e.g. from using the bot in other servers). A user profile may contain more than one server profile, but their server profile will only be visible to those in the same server.

__Slash commands__

Two commands to view and change account details:
- `bank [user]`, to view the user's account details, and
- `bank_update <sort_code> <account_number> [full_name]`, to update the database with new account details. The `full_name` field will accept upper and lowercase letters, whitespace characters and hyphens.

 The account details can only be viewed by those in the same server and account details are not shared across servers for the same user (i.e. user will be required to enter their details again for a new server). Account details saved for this server from the database can be removed by entering `000000` as the sort code and `00000000` as the account number.

Two commands to change the user value in the database:
- `new <payee> <amount> <payer> [additional_payers]`, creates a new request for the payer(s) to pay the payee (includes functionality for splitting a sum between two or more people), and
- `paid <payer> <amount> <payee>`, when a payment has been made from the payer to the payee.

Two commands to suggest how the payments should be settled:
- `settle [user]`, which suggests transactions for the user (where the number of transactions is minimised and, where possible, the number of people who are still owed money are minimised), and
- `settle_all`, which suggests transactions for all users (where the total number of transactions is minimised).

Contains two commands to display the current amount owed:
- `show [user]` displays how much the user owes / is owed, and
- `show_all` displays how much each user owes / is owed altogether.

The commands above are included in `help`.

__Admin commands__

A user can be granted admin commands by adding their 18-digit Discord user ID in the `.env` file. Admin commands are accessed by using the command prefix (default=`!`) followed by the command.
- `assign <user> <value>`, which overwrites the value the user has on the database;
- `remove <user>`, which removes the user's server profile (if the user has only one server profile saved, the user is removed completely from the database), and
- `reset`, which sets the values of all users to 0.
