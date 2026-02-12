from typing import Dict, List, Optional

import discord
from discord import app_commands
from discord.ext import commands, tasks

from exceptions import *
from queuemanager import *


class QueueCog(commands.Cog):
    def __init__(self, bot):
        from bot import Bot
        self.bot: Bot = bot
        self.queue_loc = f"{self.bot.config.data_loc}/queue"
        self.queue_manager = QueueManager(self)
        self._clean_queues_file.start()

    async def cog_load(self):
        await self.reload()
        print("[QueueCog] Successfully loaded")

    async def reload(self) -> None:
        await self.queue_manager.reload()

    @tasks.loop(hours=24.0)
    async def _clean_queues_file(self):
        await self.queue_manager.clean_queues_file()

    @_clean_queues_file.before_loop
    async def _wait_until_ready(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="createqueue", description="Creates a new queue for a custom match")
    @app_commands.rename(queue_type="type")
    @app_commands.describe(
        queue_type="The ruleset used for this queue",
        name="The name given to this queue instance",
    )
    async def _create_queue(self, interaction: discord.Interaction, queue_type: QueueType, name: str):
        try:
            await self.queue_manager.create_queue(
                guild_id=interaction.guild_id,
                owner_id=interaction.user.id,
                name=name,
                queue_type=queue_type
            )
            msg = f"The queue \"{name}\" has been created for {queue_type}"
        except QueueAlreadyExists:
            msg = "A queue already exists with the specified name"
        except Exception as e:
            raise e
        finally:
            await interaction.response.send_message(msg)

    @app_commands.command(name="deletequeue", description="Delete a queue you created")
    @app_commands.describe(name="The name of the queue you are trying to delete")
    async def _delete_queue(self, interaction: discord.Interaction, name: str):
        try:
            await self.queue_manager.delete_queue(name, interaction.user.id)
            msg = f"Successfully deleted the queue \"{name}\""
        except QueueDoesNotExist:
            msg = f"No queue exists with the name \"{name}\""
        except NotQueueOwner:
            msg = f"Unable to delete queue, as you are not its owner"
        except Exception as e:
            raise e
        finally:
            await interaction.response.send_message(msg)

    @_delete_queue.autocomplete("name")
    async def _delete_queue_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        queues = await self.queue_manager.get_all_queues(interaction.guild_id)
        owned_queues = [
            name for name, entry in queues.items() if entry.owner_id == interaction.user.id
        ]
        return [app_commands.Choice(name=choice, value=choice) for choice in owned_queues if current.lower() in choice]

    @app_commands.command(name="joinqueue", description="Join an existing queue")
    @app_commands.describe(name="The name of the queue you are trying to join")
    async def _join_queue(self, interaction: discord.Interaction, name: str):
        try:
            await self.queue_manager.join_user_to_queue(interaction.user.id, name)
            msg = f"You successfully joined the queue"
        except QueueDoesNotExist:
            msg = "Unable to find a queue with the specified name"
        except AlreadyInQueue:
            msg = "You are already in the specified queue"
        except QueueIsFull:
            msg = "Unable to join the specified queue, as it is already full"
        except Exception as e:
            raise e
        finally:
            await interaction.response.send_message(msg)

    @_join_queue.autocomplete("name")
    async def _join_queue_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        queues = await self.queue_manager.get_all_queues(interaction.guild_id)
        joinable_queues = [
            name for name, entry in queues.items() if interaction.user.id not in entry.players
        ]
        return [app_commands.Choice(name=choice, value=choice) for choice in joinable_queues]

    @app_commands.command(name="leavequeue", description="Leave an existing queue")
    @app_commands.describe(name="The name of the queue you are trying to leave")
    async def _leave_queue(self, interaction: discord.Interaction, name: str):
        try:
            await self.queue_manager.leave_user_from_queue(interaction.user.id, name)
            msg = f"You successfully left the queue"
        except QueueDoesNotExist:
            msg = "Unable to find a queue with the specified name"
        except NotInQueue:
            msg = "You are not in the specified queue"
        except Exception as e:
            raise e
        finally:
            await interaction.response.send_message(msg)

    @_leave_queue.autocomplete("name")
    async def _leave_queue_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        queues = await self.queue_manager.get_all_queues(interaction.guild_id)
        queues_user_is_in = [
            name for name, entry in queues.items() if interaction.user.id in entry.players
        ]
        return [app_commands.Choice(name=choice, value=choice) for choice in queues_user_is_in if current.lower() in choice.lower()]

    @app_commands.command(name="listqueue", description="List all queues with filters")
    @app_commands.rename(queue_type="type")
    @app_commands.describe(
        member="Filter only queues this member is a part of",
        queue_type="Filter only queues of this type"
    )
    async def _list_queue(self, interaction: discord.Interaction, member: Optional[discord.Member] = None, queue_type: Optional[QueueType] = None):
        try:
            results: Dict[str, QueueEntry] = await self.queue_manager.list_queues(interaction.guild_id, member=member, queue_type=queue_type)
            msg = "The following queues matched criteria " +\
                " and ".join([f"{criterion} \"{value}\"" for criterion, value in {
                    "member": member, "type": queue_type}.items() if value is not None]) +\
                ":"
            additions = []
            for name, entry in results.items():
                additions.append(
                    "\n".join([
                        f"**{name} - {entry.type}**",
                        f">  Players: {len(entry.players)}/{entry.max_players}",
                        f">  Created on {entry.created_date}",
                        f">  Owner: {interaction.guild.get_member(entry.owner_id).name}"
                        f">  Locked: {"Yes" if entry.locked else "No"}"
                        "\n",
                    ])
                )
            msg += "\n\n" + "\n".join(additions)
        except NoListResults:
            msg = "Could not find any queues matching specified criteria"
        except Exception as e:
            raise e
        finally:
            await interaction.response.send_message(msg)


async def setup(bot):
    await bot.add_cog(QueueCog(bot))
