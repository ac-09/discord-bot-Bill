# main.py
import asyncio
import discord
from discord.ext import commands
from discord.utils import get
from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import create_choice, create_option
from dotenv import load_dotenv
# import json
from keep_alive import keep_alive
import os
import random
import re
from replit import db

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
ADMINS = [x.strip() for x in os.getenv('BOT_ADMINS').replace('[', '').replace(']', '').split(',')]
GUILD_IDS = [int(x.strip()) for x in os.getenv('GUILD_IDS').replace('[', '').replace(']', '').split(',')]
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
bot.intents.members = True
slash = SlashCommand(bot, sync_commands=True)
n_payees = 9

# JSON_DATABASE = False
# if JSON_DATABASE:
# 	DATABASE = "db.json"


@bot.event
async def on_ready():
	await bot.change_presence(
		activity=discord.Activity(
			type=discord.ActivityType.watching,
			name=os.getenv('BOT_PRESENCE'),
		),
	)
	print(f'{bot.user.name} has connected to Discord!')


@bot.event
async def on_command_error(ctx, error):
	if isinstance(error, commands.CommandNotFound):
		await ctx.reply("Unknown command. Type `/help` for commands.")


# SLASH COMMANDS


@slash.slash(
	name="bank",
	description="View a user's account details (this will notify the user)",
	guild_ids=GUILD_IDS,
	options=[
		create_option(
			name="user",
			description="Choose user",
			required=False,
			option_type=6,
		),
	],
)
async def bank(ctx, user=None):
	viewer = await id_to_name(ctx, int(ctx.author_id))
	if user:
		search_id = str(user.id)
	else:
		search_id = str(ctx.author_id)

	# if JSON_DATABASE:
	# 	db = await get_db()
	if search_id not in db.keys():
		await ctx.reply("User not found. Open an account first with `show`.", hidden=True)

	name = await id_to_name(ctx, int(search_id))
	guild_id = str(bot.get_guild(ctx.guild.id).id)

	if db[search_id][guild_id]['bank'] == [None, None, None]:
		em = discord.Embed(
			title=f"__{name}'s account details__",
			description=f"{name} has not yet saved their account details.",
			color=ctx.guild.me.top_role.color,
		)
		await ctx.reply(embed=em, hidden=True)
	else:
		em = discord.Embed(
			title=f"__{name}'s account details__",
			color=ctx.guild.me.top_role.color,
		)
		em.set_footer(text="This message will delete after 30 seconds.")
		em.add_field(
			name="Sort code",
			value=f"||{db[search_id][guild_id]['bank'][0]}||",
			inline=False,
		)
		em.add_field(
			name="Account number",
			value=f"||{db[search_id][guild_id]['bank'][1]}||",
			inline=False,
		)
		if db[search_id][guild_id]['bank'][2]:
			em.add_field(
				name="Full name",
				value=f"||{db[search_id][guild_id]['bank'][2]}||",
				inline=False,
			)
		else:
			em.add_field(
				name="Full name",
				value=f"*{name} has not saved their full name.*",
				inline=False,
			)
		if int(ctx.author.id) != int(search_id):
			await bot.get_user(int(search_id)).send(f"{viewer} viewed your account details.")
		await ctx.reply(f"You viewed {name}'s account details.", hidden=True)
		await ctx.author.send(embed=em, delete_after=30)
	return


@slash.slash(
	name="bank_update",
	description="Update your account details",
	guild_ids=GUILD_IDS,
	options=[
		create_option(
			name="sort_code",
			description="6-digit sort code",
			required=True,
			option_type=3,
		),
		create_option(
			name="account_number",
			description="8-digit account number",
			required=True,
			option_type=3,
		),
		create_option(
			name="full_name",
			description="Your full name",
			required=False,
			option_type=3,
		),
	],
)
async def bank_update(ctx, sort_code, account_number, full_name=None, user=None):
	sc = re.match(r'^\d{6}$', sort_code.replace("-", ""))
	if sc:
		sc = str(sc.group())
	an = re.match(r'^\d{8}$', account_number)
	if an:
		an = str(an.group())

	if not sc and not an:
		await ctx.reply("Invalid sort code and account number. Please try again or type `/help`.", hidden=True)
		return
	elif not sc:
		await ctx.reply("Invalid sort code. Please try again or type `/help`.", hidden=True)
		return
	elif not an:
		await ctx.reply("Invalid account number. Please try again or type `/help`.", hidden=True)
		return

	fn = full_name
	if full_name:
		fn = re.match(r'^[A-Za-z -]+$', full_name)
		if fn:
			fn = fn.group().strip().title()
		else:
			await ctx.reply("Invalid name entered. Please try again or type `/help`.", hidden=True)
			return

	user_id = str(ctx.author.id)
	if user and str(ctx.author.id) in ADMINS:
		s = user.replace(",", "").split()
		user_id = await search_member(ctx, s[0])
		if not user_id:
			user_id = str(ctx.author.id)

	opened = await open_account(ctx, user_id)
	name = await id_to_name(ctx, user_id)

	guild_id = str(bot.get_guild(ctx.guild.id).id)
	# if JSON_DATABASE:
	# 	db = await get_db()

	if sort_code == "000000" and account_number == "00000000":
		db[user_id][guild_id]['bank'] = [None, None, None]
		# if JSON_DATABASE:
		# 	with open(DATABASE, "w") as f:
		# 		json.dump(db, f, indent=4)
		state = f"Your account details were reset."
		em = discord.Embed(
			title=f"__{name}'s account details__",
			description=opened,
			color=ctx.guild.me.top_role.color,
		)
		em.add_field(name="Sort code", value="*None*", inline=False)
		em.add_field(name="Account number", value="*None*", inline=False)
		em.add_field(name="Full name", value="*None*", inline=False)
		em.set_footer(text="This message will delete after 30 seconds.")
		await ctx.author.send(embed=em, delete_after=30)
		await ctx.reply(state, hidden=True)
		return
	elif fn:
		db[user_id][guild_id]['bank'] = [sc, an, fn]
	else:
		db[user_id][guild_id]['bank'] = [sc, an, None]

	# if JSON_DATABASE:
	# 	with open(DATABASE, "w") as f:
	# 		json.dump(db, f, indent=4)

	state = "Your account details were updated."
	em = discord.Embed(
		title=f"__{name}'s account details__",
		description=opened,
		color=ctx.guild.me.top_role.color,
	)
	em.set_footer(text="This message will delete after 30 seconds.")
	em.add_field(name="Sort code", value=f"||{sc}||", inline=False)
	em.add_field(name="Account number", value=f"||{an}||", inline=False)
	if fn:
		em.add_field(name="Full name", value=f"||{fn}||", inline=False)
	else:
		em.add_field(name="Full name", value="*Full name was not provided*.", inline=False)
	await ctx.author.send(embed=em, delete_after=30)
	await ctx.reply(state, hidden=True)
	return


options = [
	create_option(
		name="payee",
		description="Person expecting payment",
		required=True,
		option_type=6,
	),
	create_option(
		name="amount",
		description="Total amount payable to the payee",
		required=True,
		option_type=3,
	),
	create_option(
		name="payer",
		description="Person expecting to pay",
		required=True,
		option_type=6,
	),
]

for i in range(n_payees):
	options.append(
		create_option(
			name=f"additional_payer_{i + 1}",
			description="Additional person who is expecting to pay",
			required=False,
			option_type=6,
		),
	)


@slash.slash(
	name="new",
	description="Create a new request for payment",
	guild_ids=GUILD_IDS,
	options=options,
)
async def new(
	ctx, payee, amount, payer, additional_payer_1=None, additional_payer_2=None, additional_payer_3=None,
	additional_payer_4=None, additional_payer_5=None, additional_payer_6=None, additional_payer_7=None,
	additional_payer_8=None, additional_payer_9=None,
):
	payee = str(payee.id)
	payer = str(payer.id)

	s = [
		additional_payer_1, additional_payer_2, additional_payer_3, additional_payer_4, additional_payer_5,
		additional_payer_6, additional_payer_7, additional_payer_8, additional_payer_9,
	]
	s = [str(x.id) for x in s if x]

	total = re.match(r'^-?\d+(?:\.\d{,2})?$', amount.replace("£", ""))
	if total:
		total = round(float(total.group()), 0) * 100
		if total < 0:
			await ctx.reply("Please enter a positive value and try again.")
			return
		elif total > 99999 and str(ctx.author.id) not in ADMINS:
			await ctx.reply("The limit is £999.99. Please try again.")
			return
	else:
		await ctx.reply("Invalid amount entered. Please try again or type `/help`.", hidden=True)
		return

	op = ""
	for p in s:
		opened = await open_account(ctx, p)
		op += opened

	s.append(payer)
	if len(set(s)) != len(s):
		await ctx.reply("Duplicate found in payers. Please try again or type `/help`.", hidden=True)
		return

	base = int(total // len(s))
	arr = [base] * len(s)
	rem = total - base * len(s)
	while rem > 0:
		roll = random.randint(0, len(s) - 1)
		if arr[roll] == base:
			arr[roll] += 1
			rem -= 1

	if payee in s:
		arr.pop(s.index(payee))
		s.remove(payee)
	total = sum(x for x in arr)

	em = discord.Embed(
		title="__Applied changes__",
		description=f"{op}",
		color=ctx.guild.me.top_role.color,
	)
	em.set_footer(text="Positive value: person expecting to pay.\nNegative value: person expecting payment.")
	name = await id_to_name(ctx, payee)

	if total == 0:
		em.add_field(name=name, value=f"£{total / 100:.2f}")
	else:
		em.add_field(name=name, value=f"-£{total / 100:.2f}")

	em.add_field(name="\u200b", value="\u200b")

	for i, p in enumerate(s):
		name = await id_to_name(ctx, p)
		if arr[i] == 0:
			em.add_field(name=name, value=f"£{arr[i] / 100:.2f}")
		else:
			em.add_field(name=name, value=f"+£{arr[i] / 100:.2f}")
		if i % 2 and i != len(s) - 1:
			em.add_field(name="\u200b", value="\u200b")

	guild_id = str(bot.get_guild(ctx.guild.id).id)
	# if JSON_DATABASE:
	# 	db = await get_db()

	db[payee][guild_id]['val'] = int(int(db[payee][guild_id]['val']) - total)
	for i, p in enumerate(s):
		db[p][guild_id]['val'] = int(int(db[p][guild_id]['val']) + arr[i])

	# if JSON_DATABASE:
	# 	with open(DATABASE, "w") as f:
	# 		json.dump(db, f, indent=4)

	await ctx.reply(embed=em)
	return


@slash.slash(
	name="paid",
	description="Update database after a payment has been made",
	guild_ids=GUILD_IDS,
	options=[
		create_option(
			name="payer",
			description="Person who sent the payment",
			required=True,
			option_type=6,
		),
		create_option(
			name="amount",
			description="Amount paid",
			required=True,
			option_type=3,
		),
		create_option(
			name="payee",
			description="Person who received the payment",
			required=True,
			option_type=6,
		),
	],
)
async def paid(ctx, payer, amount, payee):
	payer = str(payer.id)
	payee = str(payee.id)

	total = re.match(r'^-?\d+(?:\.\d{,2})?$', amount.replace("£", ""))
	if total:
		total = round(float(total.group()), 0) * 100
		if total < 0:
			await ctx.reply("Please enter a positive value and try again.", hidden=True)
			return
		if total > 99999 and str(ctx.author.id) not in ADMINS:
			await ctx.reply("The limit is £999.99. Please try again.", hidden=True)
			return
	else:
		await ctx.reply("Invalid amount entered. Please try again or type `/help`.", hidden=True)
		return

	em = discord.Embed(title="__Applied changes__", color=ctx.guild.me.top_role.color)
	em.set_footer(text="Positive value: person who received the payment.\nNegative value: person who sent the payment.")

	name = await id_to_name(ctx, payer)
	em.add_field(name=name, value=f"-£{total / 100:.2f}")
	em.add_field(name="\u200b", value="\u200b")

	name = await id_to_name(ctx, payee)
	em.add_field(name=name, value=f"+£{total / 100:.2f}")

	guild_id = str(bot.get_guild(ctx.guild.id).id)
	# if JSON_DATABASE:
	# 	db = await get_db()

	db[payer][guild_id]['val'] = int(int(db[payer][guild_id]['val']) - total)
	db[payee][guild_id]['val'] = int(int(db[payee][guild_id]['val']) + total)

	# if JSON_DATABASE:
	# 	with open(DATABASE, "w") as f:
	# 		json.dump(db, f, indent=4)

	await ctx.reply(embed=em)
	return


@slash.slash(
	name="settle",
	description="Bot suggests transaction(s) for the user to settle their outstanding payments",
	guild_ids=GUILD_IDS,
	options=[
		create_option(
			name="user",
			description="Choose user",
			required=False,
			option_type=6,
		),
	],
)
async def settle(ctx, user=None):
	if user:
		search_id = str(user.id)
	else:
		search_id = str(ctx.author_id)
	name = await id_to_name(ctx, int(search_id))
	guild_id = str(bot.get_guild(ctx.guild.id).id)
	# if JSON_DATABASE:
	# 	db = await get_db()
	guild_db = [[user_id, db[user_id][guild_id]['val']] for user_id in db if guild_id in db[user_id]]
	if not len(guild_db):
		await ctx.reply("No users found in database. Open an account first with `show`.", hidden=True)
		return
	elif search_id not in [x[0] for x in guild_db]:
		await ctx.reply("User not found in database. Open an account first with `show`.", hidden=True)
		return

	user_found = False
	if db[search_id][guild_id]['val'] <= 0:
		await ctx.reply(f"No action required for {name}.", hidden=True)
		return
	else:
		user_found = [search_id, db[search_id][guild_id]['val']]

	if user_found:
		net_neg = sorted([x for x in guild_db if int(x[1]) < 0], key=lambda x: x[1])
		em = discord.Embed(
			title=f"__Settle {name}'s outstanding payments__",
			color=ctx.guild.me.top_role.color,
		)
		while int(user_found[1]) > 0 and len(net_neg):  # loop until debt is clear
			fields, tmp = 0, -1
			for k, l in enumerate(net_neg):  # loop through users who are owed money
				if int(abs(l[1])) == int(user_found[1]):  # found match; direct transfer between the two and exit loop
					recipient = await id_to_name(ctx, net_neg[k][0])
					em.add_field(
						name=f"{name} to {recipient}",
						value=f"£{abs(l[1]) / 100:.2f}",
					)
					await ctx.reply(embed=em, hidden=True)
					return
				elif int(abs(l[1])) < int(user_found[1]):  # find first user where there's still debt after transfer
					if k > 0:
						if tmp < 0:
							recipient = await id_to_name(ctx, net_neg[k - 1][0])  # transfer to previous user, exit loop
							em.add_field(
								name=f"{name} to {recipient}",
								value=f"£{abs(l[1]) / 100:.2f}",
							)
							await ctx.reply(embed=em, hidden=True)
							return
					else:  # debt after transfer after transferring to user owed the most money;
						# try to find match for the remaining debt
						if tmp < 0:
							tmp = k  # save user in case a match is not found
				else:
					recipient = await id_to_name(ctx, net_neg[0][0])
					em.add_field(
						name=f"{name} to {recipient}",
						value=f"£{int(user_found[1]) / 100:.2f}",
					)
					await ctx.reply(embed=em, hidden=True)
					return
			try:
				recipient = await id_to_name(ctx, net_neg[tmp][0])  # match not found, transfer to user owed most money
				em.add_field(
					name=f"{name} to {recipient}",
					value=f"£{abs(net_neg[0][1]) / 100:.2f}",
				)
				user_found[1] = int(user_found[1]) + int(net_neg[0][1])  # subtract from debt to find remainder
				net_neg.pop(0)  # remove from net_neg list
				if fields % 2:
					em.add_field(name="\u200b", value="\u200b")
				fields += 1
			except IndexError:
				await ctx.reply("Error. Please contact admin.", hidden=True)
				return
		await ctx.reply(embed=em, hidden=True)
		return
	await ctx.reply("User not found in database. Please try again.", hidden=True)
	return


@slash.slash(
	name="settle_all",
	description="Bot suggests transaction(s) for all users to settle their outstanding payments",
	guild_ids=GUILD_IDS,
)
async def settle_all(ctx):
	guild_id = str(bot.get_guild(ctx.guild.id).id)
	# if JSON_DATABASE:
	# 	db = await get_db()
	guild_db = [[user_id, db[user_id][guild_id]['val']] for user_id in db if guild_id in db[user_id]]
	if not len(guild_db):
		await ctx.reply("No users found in database. Open an account first with `show`.")
		return

	net_neg = sorted(
		[x for x in guild_db if int(x[1]) < 0],
		key=lambda x: x[1],
		reverse=True,
	)
	net_pos = sorted(
		[x for x in guild_db if int(x[1]) > 0],
		key=lambda x: x[1],
	)
	if not len(net_neg) and not len(net_pos):
		await ctx.reply("No outstanding payments. No transactions required!")
		return

	em = discord.Embed(
		title="__Settle all outstanding payments__",
		color=ctx.guild.me.top_role.color,
	)

	i = 0
	while len(net_neg) and len(net_pos):
		if abs(net_neg[0][1]) > net_pos[0][1]:
			net_neg[0][1] += net_pos[0][1]
			name_neg = await id_to_name(ctx, net_neg[0][0])
			name_pos = await id_to_name(ctx, net_pos[0][0])
			em.add_field(
				name=f"{name_pos} to {name_neg}:",
				value=f"£{abs(net_pos[0][1]) / 100:.2f}",
			)
			net_pos.pop(0)
		elif abs(net_neg[0][1]) < net_pos[0][1]:
			net_pos[0][1] += net_neg[0][1]
			name_neg = await id_to_name(ctx, net_neg[0][0])
			name_pos = await id_to_name(ctx, net_pos[0][0])
			em.add_field(
				name=f"{name_pos} to {name_neg}:",
				value=f"£{abs(net_neg[0][1]) / 100:.2f}",
			)
			net_neg.pop(0)
		elif abs(net_neg[0][1]) == net_pos[0][1]:
			name_neg = await id_to_name(ctx, net_neg[0][0])
			name_pos = await id_to_name(ctx, net_pos[0][0])
			em.add_field(
				name=f"{name_pos} to {name_neg}:",
				value=f"£{abs(net_neg[0][1]) / 100:.2f}",
			)
			net_neg.pop(0)
			net_pos.pop(0)
		if i % 2:
			em.add_field(name="\u200b", value="\u200b")
		i += 1
	await ctx.reply(embed=em)
	return


@slash.slash(
	name="show",
	description="Shows how much the user owes / is owed",
	guild_ids=GUILD_IDS,
	options=[
		create_option(
			name="user",
			description="Choose user",
			required=False,
			option_type=6,
		),
	],
)
async def show(ctx, user=None):
	if user:
		search_id = str(user.id)
	else:
		search_id = str(ctx.author_id)

	opened = await open_account(ctx, str(search_id))
	name = await id_to_name(ctx, int(search_id))
	guild_id = str(bot.get_guild(ctx.guild.id).id)
	# if JSON_DATABASE:
	# 	db = await get_db()

	if int(db[search_id][guild_id]['val']) < 0:
		em = discord.Embed(
			title=f"__{name}'s balance__",
			description=f"-£{abs(int(db[search_id][guild_id]['val'])) / 100:.2f}",
			color=ctx.guild.me.top_role.color,
		)
		em.set_footer(text="Positive value: user owes money.\nNegative value: user is owed money.")
		await ctx.reply(content=opened, embed=em, hidden=True)
	else:
		em = discord.Embed(
			title=f"__{name}'s balance__",
			description=f"£{abs(int(db[search_id][guild_id]['val'])) / 100:.2f}",
			color=ctx.guild.me.top_role.color,
		)
		em.set_footer(text="Positive value: user owes money.\nNegative value: user is owed money.")
		await ctx.reply(content=opened, embed=em, hidden=True)
	return


@slash.slash(
	name="show_all",
	description="Shows how much each user owed / is owed altogether",
	guild_ids=GUILD_IDS
)
async def show_all(ctx):
	guild_id = str(bot.get_guild(ctx.guild.id).id)
	# if JSON_DATABASE:
	# 	db = await get_db()
	guild_db = [[user_id, db[user_id][guild_id]['val']] for user_id in db if guild_id in db[user_id]]

	if not len(guild_db):
		await ctx.reply("No users found in database. Open an account first with `show`.")
		return
	guild_db = sorted([x for x in guild_db], key=lambda x: int(x[1]), reverse=True)
	em = discord.Embed(title="__All balances__", color=ctx.guild.me.top_role.color)
	em.set_footer(text="Positive value: user owes money.\nNegative value: user is owed money.")

	for i, row in enumerate(guild_db):
		try:
			name = await id_to_name(ctx, int(row[0]))
			if int(row[1]) < 0:
				em.add_field(name=name, value=f"-£{abs(int(row[1])) / 100:.2f}")
			else:
				em.add_field(name=name, value=f"£{abs(int(row[1])) / 100:.2f}")
			if not i % 2 and i != len(guild_db) - 1:
				em.add_field(name="\u200b", value="\u200b")
		except discord.errors.NotFound:
			pass
	await ctx.reply(embed=em)
	return


# ADMIN COMMANDS


@bot.command()
async def assign(ctx, *args):
	if str(ctx.message.author.id) not in ADMINS:
		await ctx.reply("You do not have permission to use this command.")
		return

	await ctx.message.delete()
	s = [arg for arg in args]
	if not len(s):
		return

	tmp = -1
	for i, arg in enumerate(s):
		total = re.match(r'^-?\d+(?:\.\d{,2})?$', arg.replace("£", ""))
		if total:
			total = int(round(float(total.group()), 0) * 100)
			tmp = i
	if tmp < 0:
		return
	else:
		s.pop(tmp)

	if not len(s):
		search_id = str(ctx.message.author.id)
	else:
		search_id = await search_member(ctx, s[0])
		if not search_id:
			return

	await open_account(ctx, search_id)
	name = await id_to_name(ctx, search_id)

	if total < 0:
		em = discord.Embed(
			title=f"Confirm: assign value -£{abs(int(total)) / 100:.2f} to {name}",
			color=ctx.guild.me.top_role.color,
		)
	else:
		em = discord.Embed(
			title=f"Confirm: assign value £{total / 100:.2f} to {name}",
			color=ctx.guild.me.top_role.color,
		)

	proceed = await confirm_action(ctx, em)

	if proceed:
		await open_account(ctx, search_id)
		guild_id = str(bot.get_guild(ctx.guild.id).id)
		# if JSON_DATABASE:
		# 	db = await get_db()
		db[search_id][guild_id]['val'] = total
		# if JSON_DATABASE:
		# 	with open(DATABASE, "w") as f:
		# 		json.dump(db, f, indent=4)
		if total < 0:
			await ctx.author.send(f"{name} assigned with value -£{abs(int(total)) / 100:.2f}.")
		else:
			await ctx.author.send(f"{name} assigned with value £{total / 100:.2f}.")
		return
	elif proceed is False:
		await ctx.author.send(f"Value not assigned to {name}.")
		return
	else:
		return


@bot.command()
async def remove(ctx, *args):
	if str(ctx.author.id) not in ADMINS:
		await ctx.reply("You do not have permission to use this command.")
		return
	await ctx.message.delete()
	s = [arg for arg in args]
	if not len(s):
		search_id = str(ctx.message.author.id)
	else:
		search_id = await search_member(ctx, s[0])
		if not search_id:
			return

	name = await id_to_name(ctx, search_id)
	em = discord.Embed(title=f"Confirm: remove {name}", color=ctx.guild.me.top_role.color)

	proceed = await confirm_action(ctx, em)

	if proceed:
		guild_id = str(bot.get_guild(ctx.guild.id).id)
		# if JSON_DATABASE:
		# 	db = await get_db()
		del db[search_id][guild_id]
		if not len(db[search_id]):
			del db[search_id]
		# if JSON_DATABASE:
		# 	with open(DATABASE, "w") as f:
		# 		json.dump(db, f, indent=4)
		await ctx.author.send(f"{name} removed.")
		return
	elif proceed is False:
		await ctx.author.send(f"{name} not removed.")
		return
	else:
		return


@bot.command()
async def reset(ctx):
	if str(ctx.message.author.id) not in ADMINS:
		await ctx.reply("You do not have permission to use this command.")
		return
	await ctx.message.delete()
	em = discord.Embed(title=f"Confirm: reset values for all users", color=ctx.guild.me.top_role.color)

	proceed = await confirm_action(ctx, em)

	if proceed:
		guild_id = str(bot.get_guild(ctx.guild.id).id)
		# if JSON_DATABASE:
		# 	db = await get_db()
		for k in db:
			db[k][guild_id]['val'] = 0
		# if JSON_DATABASE:
		# 	with open(DATABASE, "w") as f:
		# 		json.dump(db, f, indent=4)
		await ctx.author.send(f"Reset successful.")
		return
	elif proceed is False:
		await ctx.author.send(f"Reset cancelled.")
		return
	else:
		return


# HELPER FUNCTIONS

async def confirm_action(ctx, em):
	m = await ctx.author.send(embed=em)
	valid_reacts = ["✅", "❎"]
	for react in valid_reacts:
		emoji = get(ctx.guild.emojis, name=react)
		await m.add_reaction(emoji or react)

	def check(r, u):
		return u == ctx.author and str(r.emoji) in valid_reacts

	try:
		reaction, user = await bot.wait_for("reaction_add", check=check, timeout=30)
	except asyncio.TimeoutError:
		await ctx.author.send("Time out, please try again.")
		return None

	if str(reaction.emoji) == "✅":
		return True
	elif str(reaction.emoji) == "❎":
		return False


'''
async def get_db():
	try:
		f = open(DATABASE, "r")
	except FileNotFoundError:
		f = open(DATABASE, "w")
		db = {}
	else:
		try:
			db = json.load(f)
		except ValueError:
			db = {}
	finally:
		f.close()
		return db
'''


async def id_to_name(ctx, user_id):
	guild = bot.get_guild(ctx.guild.id)
	user = await guild.fetch_member(int(user_id))
	if user.nick:
		return user.nick
	else:
		return user.name


async def open_account(ctx, user_id):
	user_id = str(user_id)
	guild = bot.get_guild(ctx.guild.id)
	guild_id = str(guild.id)

	if user_id in db.keys():
		if guild_id in db[user_id].keys():
			return ""
	else:
		db[user_id] = {}
	db[user_id][guild_id] = {'val': 0, 'bank': [None, None, None]}

	# if JSON_DATABASE:
	# 	with open(DATABASE, "w") as f:
	# 		json.dump(db, f, indent=4)

	user = await guild.fetch_member(int(user_id))
	if user.nick:
		name = user.nick
	else:
		name = user.name

	return f"{name}'s account was successfully opened.\n"


async def search_member(ctx, name):
	if name == '@everyone':
		await ctx.reply("The 'everyone' tag is an invalid user. Please try again.", hidden=True)
		return
	guild = bot.get_guild(ctx.guild.id)
	guild_members = await guild.fetch_members(limit=None).flatten()
	guild_members = [[user.name, user.nick, user.bot, str(user.id)] for user in guild_members]
	user_found = bot_flag = False

	for guild_member in guild_members:
		if re.search(r"<@!\d{18}>", name) and name[3:-1] == guild_member[3]:
			user_found = True
		elif guild_member[0] and ''.join((guild_member[0]).split()).lower() == name.lower():
			user_found = True
		elif guild_member[1] and ''.join((guild_member[1]).split()).lower() == name.lower():
			user_found = True
		if user_found:
			if not guild_member[2]:
				return guild_member[3]
			else:
				bot_flag = True
				user_found = False
	if bot_flag:
		await ctx.reply("User entered was a bot. Please try again.")
	else:
		await ctx.reply("User not found. Please try again.")
	return None


# BOT HELP

choices = ["bank", "bank_update", "new", "paid", "settle", "settle_all", "show", "show_all"]
create_choices = [create_choice(name=x, value=x) for x in choices]


@slash.slash(
	name="help",
	description="Help on available commands",
	guild_ids=GUILD_IDS,
	options=[
		create_option(
			name="command",
			description="View help on specific commands. Leave blank to view all available commands.",
			required=False,
			option_type=3,
			choices=create_choices,
		),
	],
)
async def help(ctx, command=None):
	em = discord.Embed(title="__Help on commands__", color=ctx.guild.me.top_role.color)
	if not command:
		em = discord.Embed(
			title="__discord-bot-Bill__",
			description="Bill (or Billl) is your friendly Discord bot to keep track of who owes how much to others."
			"\n\u200b\nA server profile is created for the user when the user first uses the bot in a new "
			"server, and saves the user's value and account details. A user profile is also created if the "
			"user does not already have one (e.g. from using the bot in other servers). A user profile may "
			"contain more than one server profile, but their server profile will only be visible to those "
			"in the same server.\n\u200b",
			color=ctx.guild.me.top_role.color,
		)
		em.add_field(
			name="Available commands",
			value=", ".join([f"`{x}`" for x in choices]),
		)
	elif command == "bank":
		em.add_field(
			name="`bank [user]`",
			value="Shows the user's account details.",
			inline=False,
		)
	elif command == "bank_update":
		em.add_field(
			name="`bank_update <sort_code> <account_number> [full_name]`",
			value="Update your account details. The optional `full_name` field will accept upper and lowercase letters,"
			" whitespace characters and hyphens.\n\u200b\n"
			"This can only be viewed by those in the same server and account details are not shared across servers for "
			"he same user (i.e. user will be required to enter their details again for a new server).\n\u200b\n"
			"To remove your details for this server from the database, enter `000000` for the sort code and `00000000` "
			"for the account number.",
			inline=False,
		)
	elif command == "new":
		em.add_field(
			name="`new <payee> <amount> <payer> [additional_payers]`",
			value="`<payer(s)>` owe(s) `<payee>` the specified `<amount>`.\n If there is more than one payer, the "
			"`<amount>` is split evenly between the payers (maximum {n_payees + 1}).\n"
			"`<amount>` only accepts positive `int` or `float` values up to a limit of £999.99. If the outstanding "
			"payment was made, use `paid` to update the database.\n\u200b\n"
			"_Example: if **B** owes **A** £10:_ `new A 10 B`_._\n"
			"_Example: if **A** paid for a bill of £40 to be split evenly between **A**, **B**, **C** and **D**: "
			"either_ `new A 40 A B C D` _or_ `new A 30 B C D`_._",
			inline=False,
		)
	elif command == "paid":
		em.add_field(
			name="`paid <payer> <amount> <payee>`",
			value="Update the database when the `<payer>` has sent `<amount>` "
			"to the `<payee>` up to a limit of £999.99.\n\u200b\n"
			"_Example: if **A** sent **B** £10:_ `paid A 10 B`_._",
			inline=False,
		)
	elif command == "settle":
		em.add_field(
			name="`settle [user]`",
			value=f"Bot suggests transaction(s) to settle outstanding payments for the user.",
			inline=False,
		)
	elif command == "settle_all":
		em.add_field(
			name="`settle_all`",
			value="Bot suggests transaction(s) to settle outstanding payments for all users.",
			inline=False,
		)
	elif command == "show":
		em.add_field(
			name="`show [user]`",
			value="Shows the user's current outstanding payment.",
			inline=False,
		)
	elif command == "show_all":
		em.add_field(
			name="`show_all`",
			value="Shows everyone's outstanding payments in decreasing order "
			"(greater positive value: greater amount owed).",
			inline=False,
		)
	em.set_thumbnail(url=os.getenv('THUMBNAIL'))
	await ctx.reply(embed=em, hidden=True)
	return


if __name__ == "__main__":
	try:
		keep_alive()
		bot.run(TOKEN)
	except discord.HTTPException:
		os.system("kill 1")
