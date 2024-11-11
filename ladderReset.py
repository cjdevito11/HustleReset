import discord
from discord.ext import commands
from discord.utils import get
import asyncio
import json
import os

intents = discord.Intents.default()
intents.messages = True
intents.members = True 
intents.guilds = True
intents.reactions = True

bot = discord.Bot(intents=intents)

# Helper functions to read/write JSON data
def load_data(file_path):
    if not os.path.exists(file_path):
        return {}
    with open(file_path, 'r') as f:
        return json.load(f)

def save_data(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)


# Data storage files
DATA_DIR = 'data/ladderReset'
if not os.path.exists(DATA_DIR):    # Ensure data directory exists
    os.makedirs(DATA_DIR)
    
PLAYERS_FILE = os.path.join(DATA_DIR, 'players.json')
TEAMS_FILE = os.path.join(DATA_DIR, 'teams.json')
TEAM_COMPS_FILE = os.path.join(DATA_DIR, 'team_compositions.json')
APPLICATIONS_FILE = os.path.join(DATA_DIR, 'applications.json')
INVITATIONS_FILE = os.path.join(DATA_DIR, 'invitations.json')
BUILDS_FILE = os.path.join(DATA_DIR, 'builds.json')

build_data = load_data(BUILDS_FILE)
secret = load_data('secret.json')

## REGISTER SELECTS ##

class ClassSelect(discord.ui.Select):
    def __init__(self):
        print('Init Class Select')
        options = [
            discord.SelectOption(label=class_name, description=f"{class_name} class") 
            for class_name in build_data['classes'].keys()
        ]
        super().__init__(placeholder="Choose your class...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        user_data = load_data(PLAYERS_FILE)
        player_id = str(interaction.user.id)

        # Update only the class field
        if player_id in user_data:
            user_data[player_id]['class'] = self.values[0]
            save_data(PLAYERS_FILE, user_data)

        # Send a follow-up message
        await interaction.response.send_message(f"Class selected: {self.values[0]}. Now select your build.", ephemeral=True)

        # Follow-up: Build selection dropdown
        await interaction.followup.send(embed=discord.Embed(title="Build Selection"), view=BuildSelectView(self.values[0]), ephemeral=True)

class BuildSelect(discord.ui.Select):
    def __init__(self, selected_class):
        options = [
            discord.SelectOption(label=build, description=f"{build} build")
            for build in build_data['classes'][selected_class]
        ]
        super().__init__(placeholder="Choose your build...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        user_data = load_data(PLAYERS_FILE)
        player_id = str(interaction.user.id)

        # Update only the build field
        if player_id in user_data:
            user_data[player_id]['build'] = self.values[0]
            save_data(PLAYERS_FILE, user_data)

        await interaction.response.send_message(f"Build selected: {self.values[0]}. Now select your seriousness level.", ephemeral=True)
        await interaction.followup.send(embed=discord.Embed(title="Seriousness Level"), view=SeriousnessSelectView(), ephemeral=True)

class SeriousnessSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Noob", description="Still learning, need to take it slow..."),
            discord.SelectOption(label="Casual", description="Just here to have fun"),
            discord.SelectOption(label="Serious", description="I like to win, but it's not everything"),
            discord.SelectOption(label="RaceTo99", description="All in, ladder reset is serious business!"),
        ]
        super().__init__(placeholder="Choose your seriousness level...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        user_data = load_data(PLAYERS_FILE)
        player_id = str(interaction.user.id)

        # Update only the seriousness field
        if player_id in user_data:
            user_data[player_id]['seriousness'] = self.values[0]
            save_data(PLAYERS_FILE, user_data)
            
        await interaction.response.send_message(f"Seriousness level: {self.values[0]}. Now select your timezone", ephemeral=True)
        await interaction.followup.send(embed=discord.Embed(title="Timezone"), view=TimezoneSelectView(), ephemeral=True)

class TimezoneSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="EST", description="Eastern"),
            discord.SelectOption(label="CST", description="Central"),
            discord.SelectOption(label="MTN", description="Mountain"),
            discord.SelectOption(label="PST", description="Pacific"),
            discord.SelectOption(label="AST", description="Austrailia"),
            discord.SelectOption(label="CET", description="Central European"),
            discord.SelectOption(label="EET", description="Eastern European"),
            discord.SelectOption(label="GMT", description="Greenwich Mean"),
            discord.SelectOption(label="JST", description="Japan Standard"),
            discord.SelectOption(label="CHS", description="China Standard")
        ]
        super().__init__(placeholder="Choose your timezone... (Or closest one)", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        user_data = load_data(PLAYERS_FILE)
        player_id = str(interaction.user.id)

        # Update only the seriousness field
        if player_id in user_data:
            user_data[player_id]['timezone'] = self.values[0]
            save_data(PLAYERS_FILE, user_data)

        await interaction.response.send_message(f"Timezone: {self.values[0]}. Thank you for registering!", ephemeral=True)



# Team Comp Selects
class TeamCompClassSelect(discord.ui.Select):
    def __init__(self, role_index, team_name, num_roles, ctx):
        self.role_index = role_index
        self.team_name = team_name
        self.num_roles = num_roles
        self.ctx = ctx  # Add ctx here to pass it along for use in callbacks
        options = [
            discord.SelectOption(label=class_name, description=f"{class_name} class") 
            for class_name in build_data['classes'].keys()
        ]
        super().__init__(placeholder=f"Choose class for Role {role_index}", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        # Load team composition data and update the role class
        team_comps_data = load_data(TEAM_COMPS_FILE)
        if self.team_name not in team_comps_data:
            team_comps_data[self.team_name] = {'team_id': self.team_name, 'roles': []}

        if len(team_comps_data[self.team_name]['roles']) < self.role_index:
            team_comps_data[self.team_name]['roles'].append({'class': self.values[0]})
        else:
            team_comps_data[self.team_name]['roles'][self.role_index - 1]['class'] = self.values[0]

        save_data(TEAM_COMPS_FILE, team_comps_data)

        # Send message and proceed to the build selection
        await interaction.response.send_message(f"Class for Role {self.role_index} set to: {self.values[0]}. Now select the build.", ephemeral=True)
        await interaction.followup.send(embed=discord.Embed(title="Build Selection"), view=TeamCompBuildSelectView(self.role_index, self.team_name, self.num_roles, self.ctx), ephemeral=True)

class TeamCompBuildSelect(discord.ui.Select):
    def __init__(self, role_index, team_name, num_roles, ctx):
        self.role_index = role_index
        self.team_name = team_name
        self.num_roles = num_roles
        self.ctx = ctx  # Pass ctx for subsequent steps

        # Load builds based on the previously selected class for this role
        team_comps_data = load_data(TEAM_COMPS_FILE)
        selected_class = team_comps_data[self.team_name]['roles'][self.role_index - 1]['class']

        options = [
            discord.SelectOption(label=build, description=f"{build} build") 
            for build in build_data['classes'][selected_class]
        ]
        super().__init__(placeholder=f"Choose build for Role {role_index}", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        # Load team composition data and update the build
        team_comps_data = load_data(TEAM_COMPS_FILE)
        team_comps_data[self.team_name]['roles'][self.role_index - 1]['build'] = self.values[0]
        save_data(TEAM_COMPS_FILE, team_comps_data)

        await interaction.response.send_message(f"Build for Role {self.role_index} set to: {self.values[0]}. Now select the seriousness level.", ephemeral=True)

        # Proceed to seriousness selection
        await interaction.followup.send(view=TeamCompSeriousnessSelectView(self.role_index, self.team_name, self.num_roles, self.ctx), ephemeral=True)

class TeamCompSeriousnessSelect(discord.ui.Select):
    def __init__(self, role_index, team_name, num_roles, ctx):
        self.role_index = role_index
        self.team_name = team_name
        self.num_roles = num_roles
        self.ctx = ctx
        options = [
            discord.SelectOption(label="Casual", description="Just here to have fun"),
            discord.SelectOption(label="Serious", description="I like to win, but it's not everything"),
            discord.SelectOption(label="Hardcore", description="All in, ladder reset is serious business!"),
        ]
        super().__init__(placeholder=f"Choose seriousness for Role {role_index}", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        # Load team composition data and update the seriousness level
        team_comps_data = load_data(TEAM_COMPS_FILE)
        team_comps_data[self.team_name]['roles'][self.role_index - 1]['seriousness'] = self.values[0]
        save_data(TEAM_COMPS_FILE, team_comps_data)

        await interaction.response.send_message(f"Seriousness for Role {self.role_index} set to: {self.values[0]}.", ephemeral=True)

        # Check if we need to move to the next role or complete the process
        if self.role_index < self.num_roles:
            # Proceed to the next role selection
            await start_role_selection(self.ctx, self.team_name, self.role_index, self.num_roles)
        else:
            # All roles have been completed
            await interaction.followup.send(f"Team composition for {self.team_name} has been completed.", ephemeral=True)


## CLASS VIEWS

class ClassSelectView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(ClassSelect())

class BuildSelectView(discord.ui.View):
    def __init__(self, selected_class):
        super().__init__()
        self.add_item(BuildSelect(selected_class))  # Pass the selected class to BuildSelect

class SeriousnessSelectView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(SeriousnessSelect())

class TimezoneSelectView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(TimezoneSelect())

## TEAM VIEWS

class TeamCompClassSelectView(discord.ui.View):
    def __init__(self, role_index, team_name, num_roles, ctx):
        super().__init__()
        self.add_item(TeamCompClassSelect(role_index, team_name, num_roles, ctx))
class TeamCompBuildSelectView(discord.ui.View):
    def __init__(self, role_index, team_name, num_roles, ctx):
        super().__init__()
        self.add_item(TeamCompBuildSelect(role_index, team_name, num_roles, ctx))
class TeamCompSeriousnessSelectView(discord.ui.View):
    def __init__(self, role_index, team_name, num_roles, ctx):
        super().__init__()
        self.add_item(TeamCompSeriousnessSelect(role_index, team_name, num_roles, ctx))
#class TeamCompTimezoneSelectView(discord.ui.View):
#    def __init__(self):
#        super().__init__()
#        self.add_item(TeamCompTimezoneSelect())

## CREATE TEAM MODAL

# Team creation modal
class CreateTeamModal(discord.ui.Modal):
    def __init__(self):
        # Define the inputs that will be shown in the modal
        super().__init__(title="Create a New Team")

        self.add_item(discord.ui.InputText(label="Team Name", placeholder="Enter your team name", min_length=3, max_length=50))

        self.add_item(discord.ui.InputText(label="Do you want to join the team? (yes/no)", placeholder="yes/no", min_length=2, max_length=3))

    async def callback(self, interaction: discord.Interaction):
        team_name = self.children[0].value  # Get the team name input
        join_decision = self.children[1].value
        await create_team(interaction, team_name, join_decision)















        
## BOT
         
@bot.event
async def on_ready():
    #load_data()  # Ensure that data is loaded from JSON when the bot starts
    #await bot.tree.sync()  # Sync commands with Discord
    print(f'Bot is online as {bot.user}')

# Custom check for council role
def is_council():
    async def predicate(interaction: discord.Interaction):
        council_role = discord.utils.get(interaction.user.roles, name='Council')
        if council_role:
            return True
        await interaction.response.send_message("You must have the 'Council' role to use this command.", ephemeral=True)
        return False
    return commands.check(predicate)

@bot.slash_command(name="register", description="Register as a player.")
async def register(ctx):
    players_data = load_data(PLAYERS_FILE)
    player_id = str(ctx.user.id)
    
    print('Register Command')
    player_entry = {
        'discord_id': player_id,   # Store Discord ID
        'username': ctx.user.name,   # Store Discord Username
        'class': '',                         # Class to be filled by user
        'build': '',                         # Build to be filled by user
        'seriousness': '',                   # Seriousness to be filled by user
        'timezone': '',                      # Timezone to be filled by user
        'first_reset': False,                # Default value for first ladder reset
        'experience': False,                 # Default experience flag
        'availability': ''                   # Availability to be filled by user
    }

    players_data[player_id] = player_entry
    save_data(PLAYERS_FILE, players_data)
    
    await ctx.respond(embed=discord.Embed(title="Class Selection"), view=ClassSelectView())
    
    
@bot.slash_command(name="list_players", description="List all registered players with their details in a table.")
async def list_players(ctx, sort_by: str = None):
    players = load_data(PLAYERS_FILE)
    teams = load_data(TEAMS_FILE)

    if not players:
        await ctx.send("No players are registered yet.")
        return

    title_row = "| {:<15} | {:<5} | {:<5} | {:<10} | {:<10} | {:<3} | {:<3} | {:<10} |".format(
    # Title Row with '|' as separator
        "Name", "Class", "Build", "Serious", "Team", "Exp", "Loc", "Availability"
    )
    # Separator row using '-' for visual separation
    separator = "+{:-<17}+{:-<7}+{:-<7}+{:-<12}+{:-<12}+{:-<5}+{:-<5}+{:-<14}+".format('', '', '', '', '', '', '', '')

    # Prepare list for sorting
    player_list = []
    for player_id, player_info in players.items():
        member = ctx.guild.get_member(int(player_id))
        member_name = member.name if member else "Unknown"

        # Determine team membership
        team_name = "No team"
        for team, team_data in teams.items():
            if int(player_id) in team_data['members']:
                team_name = team
                break

        # Add player info to the list
        player_data = {
            'name': member_name,
            'class': player_info.get('class', 'N/A'),
            'build': player_info.get('build', 'N/A'),
            'seriousness': player_info.get('seriousness', 'N/A'),
            'team': team_name,
            'experience': 'Yes' if player_info.get('experience') else 'No',
            'timezone': player_info.get('timezone', 'N/A'),
            'availability': player_info.get('availability', 'N/A')
        }
        player_list.append(player_data)

    # Sorting Logic
    if sort_by:
        if sort_by.lower() in ['name', 'class', 'build', 'seriousness', 'team', 'experience', 'timezone', 'availability']:
            player_list = sorted(player_list, key=lambda x: x[sort_by.lower()])
        else:
            await ctx.send(f"Invalid sort_by value: {sort_by}. Please use one of: Name, Class, Build, Seriousness, Team, Experience, Timezone, Availability.")
            return

    # Table Body (Rows of Player Data)
    rows = ""
    for player in player_list:
        rows += "| {:<15} | {:<5} | {:<5} | {:<10} | {:<10} | {:<3} | {:<3} | {:<12} |\n".format(
            player['name'], player['class'], player['build'], player['seriousness'], player['team'], player['experience'], player['timezone'], player['availability']
        )

    # Combine the table parts
    table = f"```{separator}\n{title_row}\n{separator}\n{rows}{separator}```"

    # Send the table as a formatted code block
    await ctx.send(table)

#@bot.slash_command(name="create_team", description="Create a new team.")

@commands.has_role('Captain')
async def create_team(interaction, team_name, join_decision):
    teams = load_data(TEAMS_FILE)

    if team_name in teams:
        await interaction.response.send_message("A team with that name already exists.")
        return

    team_data = {
        'team_name': team_name,
        'captain_id': interaction.user.id,
        'captain_name': interaction.user.name,
        'members': [interaction.user.id] if join_decision == 'yes' or join_decision == 'Yes' or join_decision == 'YES' else [] # IF JOIN = TRUE SET CAPTAIN AS FIRST MEMBER
    }

    teams[team_name] = team_data
    save_data(TEAMS_FILE, teams)

    await interaction.response.send_message(f"Team {team_name} has been created!")

# Slash command for setting team composition
@bot.slash_command(name="set_team_comp", description="Set your ideal team composition.")
@commands.has_role('Captain')
async def set_team_comp(ctx, team_name: str, num_roles: int):
    teams = load_data(TEAMS_FILE)
    
    if team_name not in teams:
        await ctx.send("Team not found.")
        return
    if teams[team_name]['captain_id'] != ctx.author.id:
        await ctx.send("You are not the captain of this team.")
        return

    # Start the dropdown process for the first role
    await ctx.respond(f"Setting team composition for {team_name}. Number of roles: {num_roles}.", ephemeral=True)
    
    # Start the role selection for the first role
    await start_role_selection(ctx, team_name, 0, num_roles)


# Helper function to handle role selection process
async def start_role_selection(ctx, team_name: str, role_index: int, num_roles: int):
    if role_index < num_roles:
        # Start the class selection for the next role
        await ctx.send(embed=discord.Embed(title=f"Select Class for Role {role_index + 1}"), view=TeamCompClassSelectView(role_index + 1, team_name, num_roles, ctx), ephemeral=True)
    else:
        # All roles have been completed
        await ctx.send(f"Team composition for {team_name} has been set.")



@bot.slash_command(name="suggest_autofill", description="Get suggested players to fill your team.")
@commands.has_role('Captain')
async def suggest_autofill(ctx, team_name):
    teams = load_data(TEAMS_FILE)
    if team_name not in teams:
        await ctx.send("Team not found.")
        return
    if teams[team_name]['captain_id'] != ctx.author.id:
        await ctx.send("You are not the captain of this team.")
        return

    team_comps = load_data(TEAM_COMPS_FILE)
    if team_name not in team_comps:
        await ctx.send("No team composition found. Please set it using !set_team_comp.")
        return

    players = load_data(PLAYERS_FILE)
    applications = load_data(APPLICATIONS_FILE)
    invitations = load_data(INVITATIONS_FILE)

    # Exclude players already on a team or with pending invitations
    team_members = teams[team_name]['members']
    pending_invites = [inv['player_id'] for inv in invitations.values() if inv['status'] == 'Pending']
    excluded_players = set(team_members + pending_invites)

    embed = discord.Embed(title=f"Suggested Autofills for {team_name}")

    for role in team_comps[team_name]['roles']:
        matched_players = []
        for player_id, player in players.items():
            if int(player_id) in excluded_players:
                continue
            if role['class'].lower() not in player['classes'].lower():
                continue
            if role['build'].lower() != 'any' and role['build'].lower() not in player['builds'].lower():
                continue
            if role['experience_required'] and not player['experience']:
                continue
            if role['seriousness'].lower() != player['seriousness'].lower():
                continue
            # Simple availability check (can be improved)
            if role['availability'].lower() not in player['availability'].lower():
                continue
            matched_players.append(player)
            if len(matched_players) >= role['count']:
                break

        if not matched_players:
            embed.add_field(
                name=f"{role['class']} ({role['build']}) x{role['count']}",
                value="No matching players found.",
                inline=False
            )
            continue

        player_list = ""
        for player in matched_players:
            member = ctx.guild.get_member(int(player['discord_id']))
            player_info = f"{member.name if member else 'Unknown'} - Build: {player['builds']}, Exp: {'Yes' if player['experience'] else 'No'}, Avail: {player['availability']}"
            player_list += player_info + "\n"
            # Add to excluded players to avoid duplicates
            excluded_players.add(int(player['discord_id']))

            # Optionally notify the player
            try:
                await member.send(f"You have been suggested for a role in team {team_name}. The captain may contact you soon.")
            except:
                pass  # Ignore if DM fails

        embed.add_field(
            name=f"{role['class']} ({role['build']}) x{role['count']}",
            value=player_list,
            inline=False
        )

    await ctx.send(embed=embed)

@bot.slash_command(name="invite_player", description="Invite player to your team.")
@commands.has_role('Captain')
async def invite_player(ctx, member: discord.Member, team_name):
    teams = load_data(TEAMS_FILE)
    if team_name not in teams:
        await ctx.send("Team not found.")
        return
    if teams[team_name]['captain_id'] != ctx.author.id:
        await ctx.send("You are not the captain of this team.")
        return

    players = load_data(PLAYERS_FILE)
    if str(member.id) not in players:
        await ctx.send("This player is not registered.")
        return

    invitations = load_data(INVITATIONS_FILE)

    # Check if player already has a pending invitation or is on a team
    for inv in invitations.values():
        if inv['player_id'] == member.id and inv['team_id'] == team_name and inv['status'] == 'Pending':
            await ctx.send("An invitation has already been sent to this player.")
            return

    if member.id in teams[team_name]['members']:
        await ctx.send("This player is already on your team.")
        return

    # Create a pending invitation
    invitation_id = str(len(invitations) + 1)
    invitation = {
        'id': invitation_id,
        'team_id': team_name,
        'player_id': member.id,
        'status': 'Pending'
    }
    invitations[invitation_id] = invitation
    save_data(INVITATIONS_FILE, invitations)

    # Notify the player
    try:
        await member.send(f"You have been invited to join team {team_name}. Use !accept_invite {team_name} to accept or !decline_invite {team_name} to decline.")
        await ctx.send(f"Invitation sent to {member.name}.")
    except:
        await ctx.send("Failed to send DM to the player. They may have DMs disabled.")

@bot.slash_command(name="accept_invite", description="Accept invite to team.")
async def accept_invite(ctx, team_name):
    players = load_data(PLAYERS_FILE)
    if str(ctx.author.id) not in players:
        await ctx.send("You are not registered.")
        return

    teams = load_data(TEAMS_FILE)
    if team_name not in teams:
        await ctx.send("Team not found.")
        return

    invitations = load_data(INVITATIONS_FILE)

    # Find the pending invitation
    invitation_id = None
    for inv_id, inv in invitations.items():
        if inv['player_id'] == ctx.author.id and inv['team_id'] == team_name and inv['status'] == 'Pending':
            invitation_id = inv_id
            break
    if not invitation_id:
        await ctx.send("You do not have a pending invitation from this team.")
        return

    # Update invitation status and add player to team
    invitations[invitation_id]['status'] = 'Accepted'
    save_data(INVITATIONS_FILE, invitations)

    teams[team_name]['members'].append(ctx.author.id)
    save_data(TEAMS_FILE, teams)

    # Notify the captain
    captain_member = ctx.guild.get_member(teams[team_name]['captain_id'])
    if captain_member:
        try:
            await captain_member.send(f"{ctx.author.name} has accepted your invitation to join team {team_name}.")
        except:
            pass  # Ignore if DM fails

    await ctx.send(f"You have joined team {team_name}!")
    
@bot.slash_command(name="decline_invite", description="Decline invite to team.")
async def decline_invite(ctx, team_name):
    players = load_data(PLAYERS_FILE)
    if str(ctx.author.id) not in players:
        await ctx.send("You are not registered.")
        return

    teams = load_data(TEAMS_FILE)
    if team_name not in teams:
        await ctx.send("Team not found.")
        return

    invitations = load_data(INVITATIONS_FILE)

    # Find the pending invitation
    invitation_id = None
    for inv_id, inv in invitations.items():
        if inv['player_id'] == ctx.author.id and inv['team_id'] == team_name and inv['status'] == 'Pending':
            invitation_id = inv_id
            break
    if not invitation_id:
        await ctx.send("You do not have a pending invitation from this team.")
        return

    # Update invitation status
    invitations[invitation_id]['status'] = 'Declined'
    save_data(INVITATIONS_FILE, invitations)

    # Notify the captain
    captain_member = ctx.guild.get_member(teams[team_name]['captain_id'])
    if captain_member:
        try:
            await captain_member.send(f"{ctx.author.name} has declined your invitation to join team {team_name}.")
        except:
            pass  # Ignore if DM fails

    await ctx.send(f"You have declined the invitation to join team {team_name}.")

@bot.slash_command(name="leave_team", description="Leave the current team.")
async def leave_team(ctx, team_name: str = None):
    teams = load_data(TEAMS_FILE)
    players = load_data(PLAYERS_FILE)
    
    if str(ctx.user.id) not in players:
        await ctx.send("You are not registered.")
        return
    
    player_id = str(ctx.user.id)
    
    if team_name == None:
        for team, team_data in teams.items():
            if player_id in team_data['members']:
                team_name = team['team_name']
                break
    
    if not team_name:
        await ctx.send("You are not part of any team.")
        return

    team = teams[team_name]
    members = team['members']

    teams[team_name]['members'].remove(ctx.user.id)

    save_data(TEAMS_FILE, teams)
    
    captain_member = ctx.guild.get_member(teams[team_name]['captain_id'])
    if captain_member:
        try:
            await captain_member.send(f"{ctx.user.name} has left your team {team_name}.")
        except:
            print('Alert Captain of Member Leaving failed.')
            pass  # Ignore if DM fails

    # Send confirmation to the player
    await ctx.send(f"You have successfully left the team {team_name}.")

def getTeamsList(show_members = True, show_member_info = False):
    teams = load_data(TEAMS_FILE)
    players = load_data(PLAYERS_FILE)

    if not teams:
        return None

    table = ""
    
    for team_name, team in teams.items():
        print(f'Team: {team}')
        print(f'Team Name: {team_name}')
        
        captain_name = team['captain_name']
        members = team['members']

       # print(f'Team: {team}')
        #print(f'members: {members}')

        table += f"Team: {team_name} | Captain: {captain_name}\n"
        
        if show_members:
            table += "Members:\n"

            for member_id in members:
                #print(f'Member Id: {member_id}')
                member = players[str(member_id)]
                #(f'Member: {member}')
                member_name = member['username'] if member else 'Unknown'
                #print(f'Member_name: {member_name}')

                if show_member_info and str(member_id) in players.items():
                    player_info = players[str(member_id)]
                    table += "| {:<15} | {:<5} | {:<5} | {:<10} | {:<10} | {:<3} | {:<3} | {:<12} |\n".format(
                        member_name,
                        player_info.get('class', 'N/A'),
                        player_info.get('build', 'N/A'),
                        player_info.get('seriousness', 'N/A'),
                        team_name,
                        'Yes' if player_info.get('experience') else 'No',
                        player_info.get('timezone', 'N/A'),
                        player_info.get('availability', 'N/A')
                    )
                else:
                    table += f" - {member_name}\n"
            
            # Add a separator between teams
            table += "-" * 60 + "\n"

    # Send the table as a formatted code block
    table = f"```{table}```"
    return table

@bot.slash_command(name="list_teams", description="List all current teams")
async def list_teams(ctx, show_members: bool = True, show_member_info: bool = False):

    teams = getTeamsList(show_members, show_member_info)

    if not teams:
        await ctx.send("No teams have been created yet.")
        return

    await ctx.send(teams)

@bot.slash_command(name="show_team", description="Show team by Team Name")
async def show_team(ctx, team_name: str = '', show_member_info: bool = False):
    teams = load_data(TEAMS_FILE)
    players = load_data(PLAYERS_FILE)
    user = ctx.user

    if not teams:
        await ctx.send("No teams have been created yet.")
        return
    
    table = "```"
    if team_name == '':
        for team in teams.values():
            members = team['members']
            if user.id in members:
                team_name = team['team_name']
                break

    if teams[team_name]:
        team = teams[team_name]
        captain_member = ctx.guild.get_member(team['captain_id'])
        captain_name = captain_member.name if captain_member else 'Unknown'

        # Start building team details
        table += f"Team: {team_name} | Captain: {captain_name}\n"
        
        table += "Members:\n"

        # Show details for each member if requested
        for member_id in team['members']:
            member = ctx.guild.get_member(member_id)
            member_name = member.name if member else 'Unknown'
            
            # Show member info or just their name
            if show_member_info and str(member_id) in players:
                player_info = players[str(member_id)]
                table += "| {:<15} | {:<5} | {:<5} | {:<10} | {:<10} | {:<3} | {:<3} | {:<12} |\n".format(
                    member_name,
                    player_info.get('class', 'N/A'),
                    player_info.get('build', 'N/A'),
                    player_info.get('seriousness', 'N/A'),
                    team_name,
                    'Yes' if player_info.get('experience') else 'No',
                    player_info.get('timezone', 'N/A'),
                    player_info.get('availability', 'N/A')
                )
            else:
                table += f" - {member_name}\n"
            
            table += "-" * 60 + "\n"

    # Send the table as a formatted code block
    table = f"```{table}```"
    await ctx.send(table)


@bot.slash_command(name="apply_team", description="Apply to join a team")
async def apply_team(ctx, team_name):
    players = load_data(PLAYERS_FILE)
    if str(ctx.author.id) not in players:
        await ctx.send("You are not registered.")
        return

    teams = load_data(TEAMS_FILE)
    if team_name not in teams:
        await ctx.send("Team not found.")
        return

    applications = load_data(APPLICATIONS_FILE)

    # Check if application already exists
    for app in applications.values():
        if app['player_id'] == ctx.author.id and app['team_id'] == team_name and app['status'] == 'Pending':
            await ctx.send("You have already applied to this team.")
            return

    # Create a new application
    application_id = str(len(applications) + 1)
    application = {
        'id': application_id,
        'player_id': ctx.author.id,
        'team_id': team_name,
        'status': 'Pending'
    }
    applications[application_id] = application
    save_data(APPLICATIONS_FILE, applications)

    # Notify the captain
    captain_member = ctx.guild.get_member(teams[team_name]['captain_id'])
    if captain_member:
        try:
            await captain_member.send(f"{ctx.author.name} has applied to join your team {team_name}.")
        except:
            pass  # Ignore if DM fails

    await ctx.send(f"You have applied to join team {team_name}.")

@bot.slash_command(name="view_applications", description="View your teams applications")
@commands.has_role('Captain')
async def view_applications(ctx, team_name):
    teams = load_data(TEAMS_FILE)
    if team_name not in teams:
        await ctx.send("Team not found.")
        return
    if teams[team_name]['captain_id'] != ctx.author.id:
        await ctx.send("You are not the captain of this team.")
        return

    applications = load_data(APPLICATIONS_FILE)
    players = load_data(PLAYERS_FILE)

    pending_apps = [app for app in applications.values() if app['team_id'] == team_name and app['status'] == 'Pending']

    if not pending_apps:
        await ctx.send("No pending applications.")
        return

    embed = discord.Embed(title=f"Pending Applications for {team_name}")
    for app in pending_apps:
        player = players.get(str(app['player_id']))
        if not player:
            continue
        member = ctx.guild.get_member(player.get('discord_id', 0))

        # Use get method to safely access fields, provide default values if they are missing
        embed.add_field(
            #name=member.name if member else "Unknown",
            name=player.get('username', 'N/A'),
            value=(
                f"Classes: {player.get('class', 'N/A')}\n"
                f"Builds: {player.get('build', 'N/A')}\n"
                f"Experience: {'Yes' if player.get('experience') else 'No'}\n"
                f"Seriousness: {player.get('seriousness', 'N/A')}\n"
                f"Availability: {player.get('availability', 'N/A')}"
            ),
            inline=False
        )

    await ctx.send(embed=embed)



@bot.slash_command(name="accept_member", description="Accept member to your team")
@commands.has_role('Captain')
async def accept_member(ctx, member: discord.Member, team_name):
    teams = load_data(TEAMS_FILE)
    if team_name not in teams:
        await ctx.send("Team not found.")
        return
    if teams[team_name]['captain_id'] != ctx.author.id:
        await ctx.send("You are not the captain of this team.")
        return

    players = load_data(PLAYERS_FILE)
    if str(member.id) not in players:
        await ctx.send("Player is not registered.")
        return

    applications = load_data(APPLICATIONS_FILE)

    # Find the application
    application_id = None
    for app_id, app in applications.items():
        if app['player_id'] == member.id and app['team_id'] == team_name and app['status'] == 'Pending':
            application_id = app_id
            break
    if not application_id:
        await ctx.send("This player has not applied to your team.")
        return

    # Accept the application
    applications[application_id]['status'] = 'Accepted'
    save_data(APPLICATIONS_FILE, applications)

    teams[team_name]['members'].append(member.id)
    save_data(TEAMS_FILE, teams)

    # Notify the player
    try:
        await member.send(f"Your application to join team {team_name} has been accepted!")
    except:
        pass  # Ignore if DM fails

    await ctx.send(f"{member.name} has been added to your team.")

@bot.slash_command(name="decline_member", description="Decline a members team application")
@commands.has_role('Captain')
async def decline_member(ctx, member: discord.Member, team_name):
    teams = load_data(TEAMS_FILE)
    if team_name not in teams:
        await ctx.send("Team not found.")
        return
    if teams[team_name]['captain_id'] != ctx.author.id:
        await ctx.send("You are not the captain of this team.")
        return

    players = load_data(PLAYERS_FILE)
    if str(member.id) not in players:
        await ctx.send("Player is not registered.")
        return

    applications = load_data(APPLICATIONS_FILE)

    # Find the application
    application_id = None
    for app_id, app in applications.items():
        if app['player_id'] == member.id and app['team_id'] == team_name and app['status'] == 'Pending':
            application_id = app_id
            break
    if not application_id:
        await ctx.send("This player has not applied to your team.")
        return

    # Decline the application
    applications[application_id]['status'] = 'Declined'
    save_data(APPLICATIONS_FILE, applications)

    # Notify the player
    try:
        await member.send(f"Your application to join team {team_name} has been declined.")
    except:
        pass  # Ignore if DM fails

    await ctx.send(f"{member.name}'s application has been declined.")



@bot.slash_command(name="set_team_plan", description="Set your teams plan for ladder reset")
@commands.has_role('Captain')
async def set_team_plan(ctx, team_name):
    teams = load_data(TEAMS_FILE)
    if team_name not in teams:
        await ctx.send("Team not found.")
        return
    if teams[team_name]['captain_id'] != ctx.author.id:
        await ctx.send("You are not the captain of this team.")
        return

    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel

    await ctx.send("Please enter your team plan. Type 'cancel' to cancel.")

    plan_messages = []
    while True:
        msg = await bot.wait_for('message', check=check)
        if msg.content.lower() == 'cancel':
            await ctx.send("Team plan setting canceled.")
            return
        elif msg.content.lower() == 'done':
            break
        else:
            plan_messages.append(msg.content)
            await ctx.send("Added to plan. Type 'done' when finished or continue typing.")

    plan_text = "\n".join(plan_messages)
    teams[team_name]['plan'] = plan_text
    save_data(TEAMS_FILE, teams)
    await ctx.send(f"Team plan for {team_name} has been set.")
    
     # Notify team members
    for member_id in member_ids:
        if member_id != ctx.author.id:
            member = ctx.guild.get_member(member_id)
            if member:
                try:
                    await member.send(f"The team plan for {team_name} has been updated by your captain.")
                except:
                    pass  # Ignore if DM fails


@bot.slash_command(name="view_team_plan", description="View your teams plan for ladder reset")
async def view_team_plan(ctx, team_name):
    teams = load_data(TEAMS_FILE)
    if team_name not in teams:
        await ctx.send("Team not found.")
        return

    team = teams[team_name]
    member_ids = team['members']
    captain_id = team['captain_id']
    member_ids.append(captain_id)  # Include captain in team members

    if ctx.author.id not in member_ids:
        await ctx.send("You are not a member of this team.")
        return

    plan = team.get('plan')
    if not plan:
        await ctx.send(f"No plan has been set for team {team_name}.")
        return

    embed = discord.Embed(title=f"Team Plan for {team_name}", description=plan)
    await ctx.send(embed=embed)

@bot.slash_command(name="view_team_comp", description="View the current team composition.")
@commands.has_role('Captain')
async def view_team_comp(ctx, team_name: str):
    team_comps = load_data(TEAM_COMPS_FILE)
    
    if team_name not in team_comps:
        await ctx.send(f"Team {team_name} does not have a composition set yet.")
        return
    
    roles = team_comps[team_name]['roles']
    
    embed = discord.Embed(title=f"Current Team Composition for {team_name}")
    
    for index, role in enumerate(roles, start=1):
        embed.add_field(
            name=f"Role {index}",
            value=f"Class: {role['class']}\nBuild: {role['build']}\nSeriousness: {role['seriousness']}",
            inline=False
        )
    
    await ctx.send(embed=embed)

@bot.slash_command(name="compare_team_comp", description="Compare the current team composition and see which slots are filled or empty.")
@commands.has_role('Captain')
async def compare_team_comp(ctx, team_name: str):
    teams = load_data(TEAMS_FILE)
    team_comps = load_data(TEAM_COMPS_FILE)

    if team_name not in team_comps:
        await ctx.send(f"No team composition set for {team_name}.")
        return

    if team_name not in teams:
        await ctx.send(f"No team found for {team_name}.")
        return

    # Get roles and members
    roles = team_comps[team_name]['roles']
    team_members = teams[team_name]['members']

    # Prepare embed for comparison
    embed = discord.Embed(title=f"Team Composition Comparison for {team_name}")

    # Step 1: Compare roles and team members
    filled_roles = []
    unfilled_roles = []
    extra_players = []

    # Match players to roles
    for index, role in enumerate(roles, start=1):
        if index - 1 < len(team_members):  # If a member exists for this role slot
            member = ctx.guild.get_member(team_members[index - 1])
            if member:
                filled_roles.append(f"**Role {index}:** {role['class']} - {role['build']} - {role['seriousness']} - Filled by: {member.name}")
            else:
                unfilled_roles.append(f"**Role {index}:** {role['class']} - {role['build']} - {role['seriousness']} - No player assigned")
        else:
            unfilled_roles.append(f"**Role {index}:** {role['class']} - {role['build']} - {role['seriousness']} - No player assigned")

    # Step 2: Extra members not fitting into the defined roles
    if len(team_members) > len(roles):
        for extra_index in range(len(roles), len(team_members)):
            member = ctx.guild.get_member(team_members[extra_index])
            if member:
                extra_players.append(f"Extra Player: {member.name} (No defined role)")

    # Add filled roles to the embed
    if filled_roles:
        embed.add_field(name="Filled Roles", value="\n".join(filled_roles), inline=False)

    # Add unfilled roles to the embed
    if unfilled_roles:
        embed.add_field(name="Unfilled Roles", value="\n".join(unfilled_roles), inline=False)

    # Add extra players to the embed
    if extra_players:
        embed.add_field(name="Extra Players", value="\n".join(extra_players), inline=False)

    await ctx.send(embed=embed)











@bot.slash_command(name="helpme", description="Get help with how to use this bot")
async def helpme(ctx):
    embed = discord.Embed(title="Bot Commands", description="List of available commands:", color=0x3498db)

    # General Commands
    embed.add_field(name="/register", value="Register yourself as a player for ladder reset.", inline=False)
    embed.add_field(name="/list_teams", value="List all available teams.", inline=False)
    embed.add_field(name="/apply_team [team_name]", value="Apply to join a team.", inline=False)
    embed.add_field(name="/accept_invite [team_name]", value="Accept an invitation to join a team.", inline=False)
    embed.add_field(name="/decline_invite [team_name]", value="Decline an invitation to join a team.", inline=False)
    embed.add_field(name="/view_team_plan [team_name]", value="View your team's ladder reset plan.", inline=False)

    # Captain Commands
    embed.add_field(name="\u200b", value="**Captain Commands**", inline=False)
    embed.add_field(name="/create_team [team_name]", value="Create a new team.", inline=False)
    embed.add_field(name="/set_team_comp [team_name] [num_roles]", value="Set your team's ideal composition.", inline=False)
    embed.add_field(name="/set_team_plan [team_name]", value="Set or update your team's plan.", inline=False)
    embed.add_field(name="/suggest_autofill [team_name]", value="Get suggested players to fill your team.", inline=False)
    embed.add_field(name="/invite_player [@player] [team_name]", value="Invite a player to your team.", inline=False)
    embed.add_field(name="/view_applications [team_name]", value="View pending applications to your team.", inline=False)
    embed.add_field(name="/accept_member [@player] [team_name]", value="Accept a player's application.", inline=False)
    embed.add_field(name="/decline_member [@player] [team_name]", value="Decline a player's application.", inline=False)

    # Extra Information
    embed.add_field(name="\u200b", value="**Team Composition Management**", inline=False)
    embed.add_field(name="/view_team_comp [team_name]", value="View your team's current composition.", inline=False)
    embed.add_field(name="/compare_team_comp [team_name]", value="Compare the current team composition and see which slots are filled or empty.", inline=False)

    await ctx.send(embed=embed)

    
    
## INCOMPLETE

@bot.slash_command(name="remove_player", description="Council override to remove player from team")
@commands.has_role('Council')
async def remove_player(ctx, player_name):
    # Logic to remove a player from the system
    pass

@bot.command()
async def feedback(ctx, *, message):
    feedback_channel = bot.get_channel(YOUR_FEEDBACK_CHANNEL_ID)
    await feedback_channel.send(f"Feedback from {ctx.author.name}: {message}")
    await ctx.send("Thank you for your feedback!")


## INCOMPLETE 
    
    

async def assign_role(member, role_name):
    role = discord.utils.get(member.guild.roles, name=role_name)
    if role:
        await member.add_roles(role)

async def create_team_channels(guild, team_name, member_ids):
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
    }
    for member_id in member_ids:
        member = guild.get_member(member_id)
        overwrites[member] = discord.PermissionOverwrite(read_messages=True)
    await guild.create_text_channel(team_name, overwrites=overwrites)





class ResetButtons(discord.ui.View):
    def __init__(self):
        super().__init__()


    @discord.ui.button(label="Register", style=discord.ButtonStyle.primary, custom_id="register")
    async def register(self, button: discord.ui.Button, interaction: discord.Interaction):
        players_data = load_data(PLAYERS_FILE)
        player_id = str(interaction.user.id)
        
        print('Register Command')
        player_entry = {
            'discord_id': player_id,   # Store Discord ID
            'username': interaction.user.name,   # Store Discord Username
            'class': '',                         # Class to be filled by user
            'build': '',                         # Build to be filled by user
            'seriousness': '',                   # Seriousness to be filled by user
            'timezone': '',                      # Timezone to be filled by user
            'first_reset': False,                # Default value for first ladder reset
            'experience': False,                 # Default experience flag
            'availability': ''                   # Availability to be filled by user
        }

        players_data[player_id] = player_entry
        save_data(PLAYERS_FILE, players_data)
        await interaction.response.send_message("Fill out everything to register for Ladder Reset.", ephemeral=True)
        await interaction.followup.send(view=ClassSelectView(), ephemeral=True)

    @discord.ui.button(label="Show Teams", style=discord.ButtonStyle.primary, custom_id="show_teams")
    async def show_teams(self, button: discord.ui.Button, interaction: discord.Interaction):
        
        teams = getTeamsList()
        if not teams:
            await interaction.response.send_message("No teams have been created yet.", ephemeral=True)
            return
        await interaction.response.send_message(teams, ephemeral=True)

    @discord.ui.button(label="Create Team", style=discord.ButtonStyle.primary, custom_id="create_team_button")
    async def create_team_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        modal = CreateTeamModal()
        await interaction.response.send_modal(modal)


@bot.slash_command(name="show_reset_buttons", description="Show the ladder reset related buttons")
async def show_reset_buttons(ctx):
    await ctx.send("Ladder Season 9:", view=ResetButtons())


bot.run(secret['token'])