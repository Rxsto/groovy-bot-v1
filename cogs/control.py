import asyncio
import discord
import lavalink

from discord.ext import commands
from discord.errors import NotFound

from cogs.music import Music

from threading import Timer


class Control:
    def __init__(self, user, guild, message, player, channel):
        self.user = user
        self.guild = guild
        self.message = message
        self.channel = channel
        self.player = player

    async def handle_reaction(self, reaction):
        emoji = reaction.emoji
        if emoji == '⏯':
            resume_response = '✅ Successfully resumed the music!' if self.player.paused else '✅ Successfully paused music!'
            await self.player.set_pause(not self.player.paused)
            await self.send_response(resume_response)
        elif emoji == '⏭':
            await Music.fade_out(self.player)
            await self.player.skip()
            await Music.fade_in(self.player)
            await self.send_response('✅ Successfully skipped current song!')
        elif emoji == '⏹':
            self.player.queue.clear()
            await Music.fade_out(self.player)
            await self.player.stop()
            await Music.fade_in(self.player)
            await self.send_response('⏹ Successfully stopped the music!')
        elif emoji == '🔂':
            repeat_response = '✅ Successfully enabled loop mode!' if not self.player.repeat else '✅ Successfully disabled loop mode!'
            self.player.repeat = not self.player.repeat
            await self.send_response(repeat_response)
        elif emoji == '🔁':
            await self.send_response(':warning: **This feature is currently under development!**')
        elif emoji == '🔀':
            shuffle_response = '✅ Successfully enabled shuffle mode!' if not self.player.shuffle else '✅ Successfully disabled shuffle mode!'
            self.player.shuffle = not self.player.shuffle
            await self.send_response(shuffle_response)
        elif emoji == '🔄':
            await self.player.seek(0)
            await self.send_response('✅ Successfully reset the current progress!')
        elif emoji == '🔊':
            if self.player.volume == 150:
               return await self.send_response(':no_entry: The volume is already at the maximum!')
            elif self.player.volume >= 490:
                await self.player.set_volume(150)
            else:
                await self.player.set_volume(self.player.volume + 10)
            await self.send_response(f'✅ Successfully set volume to `{self.player.volume}`!')
        elif emoji == '🔉':
            if self.player.volume == 0:
                return await self.send_response(':no_entry: The volume is already at the minimum!')
            elif self.player.volume <= 10:
                await self.player.set_volume(0)
            else:
                await self.player.set_volume(self.player.volume - 10)
            await self.send_response(f'✅ Successfully set volume to `{self.player.volume}`!') 
        await self.update_message(False)

    async def send_response(self, response):
        async with self.channel.typing():
            message = await self.channel.send(response)
        await asyncio.sleep(3.5)
        try:
            await message.delete()
        except NotFound:
            pass

    async def update_message(self, loop):
        if self.player.current is None:
            await self.message.channel.send('✅ Successfully stopped playing!')
            if self.message:
                try:
                    return await self.message.delete()
                except NotFound:
                    return
            del self
            return
        pos = lavalink.Utils.format_time(self.player.position)
        if self.player.current.stream:
            dur = 'LIVE'
        else:
            dur = lavalink.Utils.format_time(self.player.current.duration)
        play_type = '⏸' if self.player.paused else '▶'
        loop_type = '🔂' if self.player.repeat else ''
        shuffle_type = '🔀' if self.player.shuffle else ''
        desc = f'{play_type}{loop_type}{shuffle_type} ' \
               f'{self.get_percentage(self.player.position, self.player.current.duration)} **[{pos} / {dur}]**'
        song = self.player.current
        embed = discord.Embed(
            colour=self.guild.me.top_role.colour,
            description=desc,
        )
        try:
            await self.message.edit(embed=embed)
        except NotFound:
            pass           
        if loop: 
            await asyncio.sleep(10)
            if self.message:
                await self.update_message(True)

    @staticmethod
    def get_percentage(progress, full):
        percent = round(progress / full, 2)
        bar = ''
        for x in range(0, 15):
            if int(percent * 15) == x:
                bar += '🔘'
            else:
                bar += '▬'
        return bar


class ControlCommand:
    def __init__(self, bot):
        self.bot = bot
        self.map = dict({})
        self.reacts = ['⏯', '⏭', '⏹', '🔂', '🔁', '🔀', '🔄', '🔉', '🔊']

    @commands.command(aliases=['cp', 'panel'])
    async def control(self, ctx):
        player = self.bot.lavalink.players.get(ctx.guild.id)

        if not player.is_playing:
            return await ctx.send('🚫 I\'m not playing.')

        embed = discord.Embed(
            title='Control Panel - Loading',
            description='<a:groovyloading:487681291010179072> Please wait while the control panel is loading'
        )

        msg = await ctx.send(embed=embed)
        for react in self.reacts:
            await msg.add_reaction(react)
        panel = Control(ctx.message.author, ctx.guild,
                        msg, player, ctx.channel)
        self.map[ctx.guild.id] = panel
        await panel.update_message(True)

    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return
        if reaction.message.guild.id not in self.map:
            return
        await reaction.message.remove_reaction(reaction.emoji, user)
        if reaction.emoji not in self.reacts:
            return
        user_panel = self.map[reaction.message.guild.id]
        if user.id is not user_panel.user.id:
            return
        await user_panel.handle_reaction(reaction)

    async def on_message_delete(self, message):
        if message.id in self.map.keys():
            del self.map[message.id]


def setup(bot):
    bot.add_cog(ControlCommand(bot))
