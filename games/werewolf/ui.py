from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from game.player import Player


def prompt_for_choice(
    player: "Player",
    prompt_text: str,
    valid_choices: List[str],
    allow_skip: bool = False,
) -> str:
    """根据玩家类型提示选择。"""
    if player.is_human:
        return player.call_human_response(prompt_text, valid_choices, allow_skip)
    else:
        return player.call_ai_response(prompt_text, valid_choices)
