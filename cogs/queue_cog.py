import traceback
from typing import Coroutine, Dict, List, Optional

import discord
from discord import app_commands
from discord.ext import commands

from event import *
from exceptions import *
from queuemanager import *
from ui import QueueListView


class QueueCog(commands.GroupCog, name="queue"):
    def __init__(self, bot):
        from bot import Bot
        self.bot: Bot = bot

    async def cog_load(self):
        _handlers: Dict[Coroutine, Event] = {
            self._notify_queue_owner_full: Event.QUEUE_FILLED,
        }
        for coro, event in _handlers.items():
            self.bot.add_listener(coro, f"on_{event}")

        self.bot.logger.info("[QueueCog] Successfully loaded")

    async def _notify_queue_owner_full(self, payload: QueueFilledPayload) -> None:
        content = "\n".join([
            f"A queue you own is full. Details are as follows:",
            f"> Server: {self.bot.get_guild(payload.guild_id)}"
            f"> Name: {payload.name}",
            "> Players:",
            "\n".join([
                f"> - <@{_id}>" for _id in payload.entry.players
            ])
        ])
        await self.bot.get_user(payload.entry.owner_id).send(content=content)

    @app_commands.command(name="create", description="Creates a new queue for a custom match")
    @app_commands.rename(queue_type="type")
    @app_commands.describe(
        queue_type="The ruleset used for this queue",
        name="The name given to this queue instance",
    )
    async def _create_queue(self, interaction: discord.Interaction, queue_type: QueueType, name: str):
        ephemeral = True
        try:
            await self.bot.queue_manager.create_queue(
                guild_id=interaction.guild_id,
                owner_id=interaction.user.id,
                name=name,
                queue_type=queue_type
            )
            msg = f"The queue \"{name}\" has been created for {queue_type}"
            ephemeral = False
        except QueueAlreadyExists:
            msg = "A queue already exists with the specified name"
        except ValueError:
            msg = f"The specified name must be no longer than 100 characters"
        except Exception as e:
            msg = f"An error has occurred: {e}"
            ephemeral = False
        finally:
            await interaction.response.send_message(msg, ephemeral=ephemeral)

    @app_commands.command(name="delete", description="Delete a queue you created")
    @app_commands.describe(name="The name of the queue you are trying to delete")
    async def _delete_queue(self, interaction: discord.Interaction, name: str):
        ephemeral = True
        try:
            await self.bot.queue_manager.delete_queue(interaction.guild_id, name, interaction.user.id)
            msg = f"Successfully deleted the queue \"{name}\""
            ephemeral = False
        except QueueDoesNotExist:
            msg = f"No queue exists with the name \"{name}\""
        except NotQueueOwner:
            msg = "Unable to delete the specified queue, as you are not its owner"
        except Exception as e:
            msg = f"An error has occurred: {e}"
            ephemeral = False
        finally:
            await interaction.response.send_message(msg, ephemeral=ephemeral)

    @_delete_queue.autocomplete("name")
    async def _delete_queue_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        queues = await self.bot.queue_manager.get_all_queues(interaction.guild_id)
        owned_queues = [
            name for name, entry in queues.items() if entry.owner_id == interaction.user.id
        ]
        return self.get_sorted_choices(owned_queues, current)

    @app_commands.command(name="join", description="Join an existing queue")
    @app_commands.describe(name="The name of the queue you are trying to join")
    async def _join_queue(self, interaction: discord.Interaction, name: str):
        ephemeral = True
        try:
            q = await self.bot.queue_manager.join_user_to_queue(interaction.guild_id, interaction.user.id, name)
            msg = f"You successfully joined the queue \"{name}\""
        except QueueDoesNotExist:
            msg = "Unable to find a queue with the specified name"
        except AlreadyInQueue:
            msg = "You are already in the specified queue"
        except QueueIsFull:
            msg = "Unable to join the specified queue, as it is already full"
        except QueueIsLocked:
            msg = "Unable to join the specified queue, as it is locked"
        except Exception as e:
            msg = f"An error has occurred: {e}"
            ephemeral = False
        else:
            if q.full:
                # Notify the queue owner that their queue has been filled
                self.bot.dispatch(Event.QUEUE_FILLED, QueueFilledPayload({
                    "guild_id": interaction.guild_id,
                    "name": name,
                    "entry": q,
                }))
        finally:
            await interaction.response.send_message(msg, ephemeral=ephemeral)

    @_join_queue.autocomplete("name")
    async def _join_queue_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        queues = await self.bot.queue_manager.get_all_queues(interaction.guild_id)
        joinable_queues = [
            name for name, entry in queues.items() if len(entry.players) < entry.max_players and interaction.user.id not in entry.players
        ]
        return self.get_sorted_choices(joinable_queues, current)

    @app_commands.command(name="leave", description="Leave an existing queue")
    @app_commands.describe(name="The name of the queue you are trying to leave")
    async def _leave_queue(self, interaction: discord.Interaction, name: str):
        ephemeral = True
        try:
            await self.bot.queue_manager.leave_user_from_queue(interaction.guild_id, interaction.user.id, name)
            msg = f"You successfully left the queue \"{name}\""
        except QueueDoesNotExist:
            msg = "Unable to find a queue with the specified name"
        except NotInQueue:
            msg = "You are not in the specified queue"
        except QueueIsLocked:
            msg = "Unable to leave the specified queue, as it is locked"
        except Exception as e:
            msg = f"An error has occurred: {e}"
            ephemeral = False
        finally:
            await interaction.response.send_message(msg, ephemeral=ephemeral)

    @_leave_queue.autocomplete("name")
    async def _leave_queue_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        queues = await self.bot.queue_manager.get_all_queues(interaction.guild_id)
        leaveable_queues = [
            name for name, entry in queues.items() if interaction.user.id in entry.players
        ]
        return self.get_sorted_choices(leaveable_queues, current)

    @app_commands.command(name="lock", description="Lock an existing queue")
    @app_commands.describe(name="The name of the queue you are trying to lock")
    async def _lock_queue(self, interaction: discord.Interaction, name: str):
        ephemeral = True
        try:
            await self.bot.queue_manager.set_queue_lock_state(interaction.guild_id, interaction.user.id, name, True)
            msg = f"Queue \"{name}\" has been locked"
            ephemeral = False
        except QueueDoesNotExist:
            msg = "Unable to find a queue with the specified name"
        except QueueLockStateError:
            msg = "The specified queue is alreaedy locked"
        except NotQueueOwner:
            msg = "Unable to lock the specified queue, as you are not its owner"
        except QueueProgressStateError:
            msg = "The specified queue currently has a match in progress and cannot be modified"
        except Exception as e:
            msg = f"An error has occurred: {e}"
            ephemeral = False
        finally:
            await interaction.response.send_message(msg, ephemeral=ephemeral)

    @_lock_queue.autocomplete("name")
    async def _lock_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        queues = await self.bot.queue_manager.get_all_queues(interaction.guild_id)
        lockable_queues = [
            name for name, entry in queues.items() if entry.locked == False and interaction.user.id == entry.owner_id
        ]
        return self.get_sorted_choices(lockable_queues, current)

    @app_commands.command(name="unlock", description="Unlock an existing queue")
    @app_commands.describe(name="The name of the queue you are trying to unlock")
    async def _unlock_queue(self, interaction: discord.Interaction, name: str):
        ephemeral = True
        try:
            await self.bot.queue_manager.set_queue_lock_state(interaction.guild_id, interaction.user.id, name, False)
            msg = f"Queue \"{name}\" has been unlocked"
            ephemeral = False
        except QueueDoesNotExist:
            msg = "Unable to find a queue with the specified name"
        except QueueLockStateError:
            msg = "The specified queue is alreaedy unlocked"
        except NotQueueOwner:
            msg = "Unable to unlock the specified queue, as you are not its owner"
        except QueueProgressStateError:
            msg = "The specified queue currently has a match in progress and cannot be modified"
        except Exception as e:
            msg = f"An error has occurred: {e}"
            ephemeral = False
        finally:
            await interaction.response.send_message(msg, ephemeral=ephemeral)

    @_unlock_queue.autocomplete("name")
    async def _unlock_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        queues = await self.bot.queue_manager.get_all_queues(interaction.guild_id)
        unlockable_queues = [
            name for name, entry in queues.items() if entry.locked == True and interaction.user.id == entry.owner_id
        ]
        return self.get_sorted_choices(unlockable_queues, current)

    @app_commands.command(name="list", description="List all queues with filters")
    @app_commands.rename(queue_type="type")
    @app_commands.describe(
        member="Filter only queues this member is a part of",
        queue_type="Filter only queues of this type"
    )
    async def _list_queue(self, interaction: discord.Interaction, member: Optional[discord.Member] = None, queue_type: Optional[QueueType] = None):
        msg = None
        ephemeral = True
        try:
            # Obtain list of criteria submitted
            criteria = []
            if member:
                criteria.append(f"Member {member.mention}")
            if queue_type:
                criteria.append(f"Type {queue_type}")

            # Filter results by submitted criteria and convert to list
            results: Dict[str, QueueEntry] = await self.bot.queue_manager.list_queues(interaction.guild_id, member=member, queue_type=queue_type)
            results = [(name, entry) for name, entry in results.items()]

            # Initialise QueueListView
            qlview = QueueListView(
                source_interaction=interaction,
                data=results,
                criteria=criteria,
            )
            qlview.init_components()

            # Send message containing interactive QueueListView
            await interaction.response.send_message(
                view=qlview,
                allowed_mentions=discord.AllowedMentions.none(),
                ephemeral=ephemeral
            )
        except NoListResults:
            msg = "Could not find any queues matching specified criteria"
        except Exception as e:
            msg = f"An error has occurred: {e}"
            self.bot.logger.error(f"An exception occurred when trying to list queue: {e}")
            traceback.print_exception(type(e), e, e.__traceback__)
            ephemeral = False
        finally:
            if msg is not None:
                await interaction.response.send_message(msg, ephemeral=ephemeral)

    @staticmethod
    def get_sorted_choices(entries: List[str], current: str) -> List[app_commands.Choice[str]]:
        choices = [
            app_commands.Choice(name=choice, value=choice)
            for choice in entries if current.lower() in choice.lower()
        ]
        return sorted(choices, key=lambda x: x.name)


async def setup(bot):
    await bot.add_cog(QueueCog(bot))
