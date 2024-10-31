"""
@Time    : 2024/2/01
@Author  : Zekai Chen
@File    : Socratic dialogue.py
"""
import asyncio
import platform
from typing import Any

import fire

from metagpt.actions import Action, UserRequirement
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.team import Team


class Dialogue(Action):
    """Action: Express your point of view in a dialogue"""

    PROMPT_TEMPLATE: str = """
    ## BACKGROUND
    Suppose you are {name}, you are in a dialogue with {opponent_name}.
    ## DEBATE HISTORY
    Previous rounds:
    {context}
    ## YOUR TURN
    Now it's your turn to talk, you must closely use {name}'s rhetoric and viewpoints, respond to your communicator's latest sentences, may state your position and defend your arguments,
    craft a response that can be short or long but no longer than 80 words, your will say:
    """
    name: str = "Dialogue"

    async def run(self, context: str, name: str, opponent_name: str):
        prompt = self.PROMPT_TEMPLATE.format(context=context, name=name, opponent_name=opponent_name)
        # logger.info(prompt)

        rsp = await self._aask(prompt)

        return rsp


class Debator(Role):
    name: str = ""
    profile: str = ""
    opponent_name: str = ""

    def __init__(self, **data: Any):
        super().__init__(**data)
        self.set_actions([Dialogue])
        self._watch([UserRequirement, Dialogue])

    async def _observe(self) -> int:
        await super()._observe()
        # accept messages sent (from opponent) to self, disregard own messages from the last round
        self.rc.news = [msg for msg in self.rc.news if msg.send_to == {self.name}]
        return len(self.rc.news)

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo  # An instance of Dialogue

        memories = self.get_memories()
        context = "\n".join(f"{msg.sent_from}: {msg.content}" for msg in memories)
        # print(context)

        rsp = await todo.run(context=context, name=self.name, opponent_name=self.opponent_name)

        msg = Message(
            content=rsp,
            role=self.profile,
            cause_by=type(todo),
            sent_from=self.name,
            send_to=self.opponent_name,
        )
        self.rc.memory.add(msg)

        return msg


async def debate(idea: str = "Euthyphro: the pious is what all the gods love, and the opposite, what all the gods hate, is the impious", investment: float = 3.0, n_round: int = 10):
    """Run a team of philosophers and watch they Dialogue. :)"""
    Socrates = Debator(name="Socrates", profile="Greek philosopher known as the Father of Western Philosophy", opponent_name="Euthyphro")
    Euthyphro = Debator(name="Euthyphro", profile="An ancient Athenian religious prophet (mantis)", opponent_name="Socrates")
    team = Team()
    team.hire([Socrates, Euthyphro])
    team.invest(investment)
    team.run_project(idea, send_to="Socrates")  # send debate topic to Socrates and let him speak first
    await team.run(n_round=n_round)


def main(idea: str = "Euthyphro: the pious is what all the gods love, and the opposite, what all the gods hate, is the impious", investment: float = 3.0, n_round: int = 10):
    """
    :param idea: Debate topic, such as "Topic: Do gods like pious people?"
    :param investment: contribute a certain dollar amount to watch the debate
    :param n_round: maximum rounds of the debate
    :return:
    """
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(debate(idea, investment, n_round))


if __name__ == "__main__":
    fire.Fire(main)
