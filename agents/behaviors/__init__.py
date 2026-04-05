"""Agent behaviors module"""
from agents.behaviors.post_behavior import PostBehavior
from agents.behaviors.comment_behavior import CommentBehavior
from agents.behaviors.reaction_behavior import ReactionBehavior
from agents.behaviors.follow_behavior import FollowBehavior
from agents.behaviors.group_behavior import CreateGroupBehavior, JoinGroupBehavior
from agents.behaviors.debate_behavior import DebateBehavior

__all__ = [
    "PostBehavior",
    "CommentBehavior",
    "ReactionBehavior",
    "FollowBehavior",
    "CreateGroupBehavior",
    "JoinGroupBehavior",
    "DebateBehavior",
]
