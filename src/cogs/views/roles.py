import discord


class SelfRoles(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.quo_updates_role = 838370690050687016
        self.black_role = 838372794093404160
        self.events_role = 855468654883504148
        self.discord_staus = 884465056983691264

    @discord.ui.button(style=discord.ButtonStyle.blurple, custom_id="quotient_updates", label="Quotient-Updates", row=1)
    async def quo_updates(self, button: discord.Button, interaction: discord.Interaction):
        if self.quo_updates_role in (role.id for role in interaction.user.roles):
            await interaction.user.remove_roles(discord.Object(id=self.quo_updates_role))
            return await interaction.response.send_message("Quotient-Updates role removed.", ephemeral=True)

        await interaction.user.add_roles(discord.Object(id=self.quo_updates_role))
        return await interaction.response.send_message("Quotient-Updates role added.", ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.blurple, custom_id="events", label="Events (Giveaways)", row=1)
    async def quo_events(self, button: discord.Button, interaction: discord.Interaction):
        if self.events_role in (role.id for role in interaction.user.roles):
            await interaction.user.remove_roles(discord.Object(id=self.events_role))
            return await interaction.response.send_message("Events (Giveaways) role removed.", ephemeral=True)

        await interaction.user.add_roles(discord.Object(id=self.events_role))
        return await interaction.response.send_message("Events (Giveaways) role  added.", ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.blurple, custom_id="black", label="Black Color", row=1)
    async def quo_blacky(self, button: discord.Button, interaction: discord.Interaction):
        if self.black_role in (role.id for role in interaction.user.roles):
            await interaction.user.remove_roles(discord.Object(id=self.black_role))
            return await interaction.response.send_message("Black-Color role removed.", ephemeral=True)

        await interaction.user.add_roles(discord.Object(id=self.black_role))
        return await interaction.response.send_message("Black-Color role added.", ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.blurple, custom_id="status", label="Discord-Status", row=1)
    async def quo_status(self, button: discord.Button, interaction: discord.Interaction):
        if self.discord_staus in (role.id for role in interaction.user.roles):
            await interaction.user.remove_roles(discord.Object(id=self.discord_staus))
            return await interaction.response.send_message("Discord-Status role removed.", ephemeral=True)

        await interaction.user.add_roles(discord.Object(id=self.discord_staus))
        return await interaction.response.send_message("Discord-Status role added.", ephemeral=True)
